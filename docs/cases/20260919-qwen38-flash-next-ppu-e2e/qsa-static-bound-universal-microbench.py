#!/usr/bin/env python3
"""Compare full QSA score capacity with static workload-safe bounds."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import torch

BASE_PATH = Path(
    "/mnt/nfs/users/jinghao/qwen3.8-flash/"
    "20260919-qwen38-flash-next-ppu-e2e/commands/46-qsa-column-bound-microbench.py"
)


def load_base():
    spec = importlib.util.spec_from_file_location("qsa_column_bound_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


base = load_base()


def make_workload(rows: int, sequence_length: int, bound: int):
    device = torch.device("cuda")
    workload = base._make_workload(rows, 20000, device)
    if rows == 4096:
        # A 4096-token scheduler step. Mapping details do not change the grid.
        query_positions = torch.arange(4096, device=device, dtype=torch.int64)
        token_to_req = torch.zeros(4096, device=device, dtype=torch.int32)
        sequence_lengths = torch.tensor(
            [sequence_length], device=device, dtype=torch.int32
        )
        compressed_table = workload.compressed_table[:1].contiguous()
    else:
        query_positions = torch.full(
            (rows,), sequence_length - 1, device=device, dtype=torch.int64
        )
        token_to_req = torch.arange(rows, device=device, dtype=torch.int32)
        sequence_lengths = torch.full(
            (rows,), sequence_length, device=device, dtype=torch.int32
        )
        compressed_table = workload.compressed_table[:rows].contiguous()

    main_pages = math.ceil(sequence_length / base.PAGE_SIZE)
    main_table = torch.arange(
        main_pages, device=device, dtype=torch.int32
    ).expand(sequence_lengths.numel(), -1).contiguous()
    main_k = torch.randn(
        (main_pages, base.PAGE_SIZE, 1, 256),
        device=device,
        dtype=torch.bfloat16,
    )
    main_v = torch.randn_like(main_k)
    return base.Workload(
        index_q=workload.index_q,
        compressed_k=workload.compressed_k,
        compressed_table=compressed_table,
        token_to_req=token_to_req,
        query_positions=query_positions,
        sequence_lengths=sequence_lengths,
        sparse_q=workload.sparse_q,
        main_k=main_k,
        main_v=main_v,
        main_table=main_table,
        full_columns=20000,
        bounded_columns=bound,
    )


@torch.inference_mode()
def run_case(
    name: str,
    rows: int,
    sequence_length: int,
    bound: int,
    warmup: int,
    repeat: int,
) -> dict[str, object]:
    visible_groups = math.ceil(sequence_length / base.COMPRESS_RATIO)
    if not base.BLOCK_TOPK <= bound <= 20000:
        raise ValueError("bound outside [block_topk, capacity]")
    if bound < visible_groups:
        raise ValueError(f"unsafe bound {bound} < visible groups {visible_groups}")
    workload = make_workload(rows, sequence_length, bound)
    full_selected = torch.empty(
        (rows, base.OUTPUT_WIDTH), device="cuda", dtype=torch.int32
    )
    bound_selected = torch.empty_like(full_selected)
    full_sparse = torch.empty_like(workload.sparse_q)
    bound_sparse = torch.empty_like(workload.sparse_q)

    full_fn = lambda: base._transaction(
        workload, workload.full_columns, full_selected, full_sparse
    )
    bound_fn = lambda: base._transaction(
        workload, workload.bounded_columns, bound_selected, bound_sparse
    )
    full_fn()
    bound_fn()
    torch.cuda.synchronize()
    base._assert_same_selection(full_selected, bound_selected)
    torch.testing.assert_close(full_sparse, bound_sparse, atol=0.05, rtol=0.05)

    full_selection_ms = base._event_ms(
        lambda: base._select_static(workload, 20000, full_selected), warmup, repeat
    )
    bound_selection_ms = base._event_ms(
        lambda: base._select_static(workload, bound, bound_selected), warmup, repeat
    )
    full_transaction_ms = base._event_ms(full_fn, warmup, repeat)
    bound_transaction_ms = base._event_ms(bound_fn, warmup, repeat)

    full_graph, full_capture = base._capture(
        full_fn, (full_selected, full_sparse)
    )
    bound_graph, bound_capture = base._capture(
        bound_fn, (bound_selected, bound_sparse)
    )
    full_r1, full_r2 = base._replay_snapshots(
        full_graph, (full_selected, full_sparse)
    )
    bound_r1, bound_r2 = base._replay_snapshots(
        bound_graph, (bound_selected, bound_sparse)
    )
    for captured, replayed in (
        (full_capture, full_r1),
        (full_capture, full_r2),
        (bound_capture, bound_r1),
        (bound_capture, bound_r2),
    ):
        torch.testing.assert_close(captured[0], replayed[0], atol=0, rtol=0)
        torch.testing.assert_close(captured[1], replayed[1], atol=0, rtol=0)
    base._assert_same_selection(full_capture[0], bound_capture[0])
    torch.testing.assert_close(
        full_capture[1], bound_capture[1], atol=0.05, rtol=0.05
    )

    full_graph_ms = base._graph_replay_ms(full_graph, repeat)
    bound_graph_ms = base._graph_replay_ms(bound_graph, repeat)
    result = {
        "name": name,
        "rows": rows,
        "sequence_length": sequence_length,
        "visible_groups": visible_groups,
        "capacity": 20000,
        "bound": bound,
        "selection_correct": True,
        "downstream_sparse_correct": True,
        "graph_capture_and_two_replays": True,
        "full_selection_ms": full_selection_ms,
        "bound_selection_ms": bound_selection_ms,
        "selection_speedup": full_selection_ms / bound_selection_ms,
        "full_transaction_ms": full_transaction_ms,
        "bound_transaction_ms": bound_transaction_ms,
        "transaction_speedup": full_transaction_ms / bound_transaction_ms,
        "full_graph_replay_ms": full_graph_ms,
        "bound_graph_replay_ms": bound_graph_ms,
        "graph_speedup": full_graph_ms / bound_graph_ms,
    }
    del full_graph, bound_graph, workload
    torch.cuda.empty_cache()
    return result


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--repeat", type=int, default=20)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    cases = (
        ("p4k_prefill_universal", 4096, 4096, 8448),
        ("p4k_decode_universal", 64, 5120, 8448),
        ("p4k_prefill_specific", 4096, 4096, 1280),
        ("p4k_decode_specific", 64, 5120, 1280),
        ("p32k_decode_universal", 64, 33792, 8448),
    )
    results = [run_case(*case, args.warmup, args.repeat) for case in cases]
    payload = {
        "schema_version": 1,
        "experiment": "qsa-static-score-bound-universal",
        "full_capacity": 20000,
        "universal_bound": 8448,
        "p4k_specific_bound": 1280,
        "warmup": args.warmup,
        "repeat": args.repeat,
        "results": results,
        "checks": {
            "all_correct": all(
                row["selection_correct"]
                and row["downstream_sparse_correct"]
                and row["graph_capture_and_two_replays"]
                for row in results
            ),
            "universal_p4k_transaction_ge_1_05x": all(
                row["transaction_speedup"] >= 1.05
                for row in results
                if row["name"].startswith("p4k_")
                and row["name"].endswith("universal")
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
