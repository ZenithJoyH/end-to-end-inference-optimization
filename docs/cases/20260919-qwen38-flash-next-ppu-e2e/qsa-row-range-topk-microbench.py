#!/usr/bin/env python3
"""Compare QSA torch.topk with the existing row-range TopK provider.

Scoring remains full-capacity and unchanged.  This experiment isolates only
the safe device-side TopK replacement using per-row visible block counts.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import torch

from flag_gems.fused.qsa import qsa_mqa_paged
from flag_gems.fused.top_k_per_row_prefill import top_k_per_row_prefill


def _load_base(path: Path):
    spec = importlib.util.spec_from_file_location("qsa_column_bound_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import base microbenchmark: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _select_provider(base, workload, out: torch.Tensor) -> torch.Tensor:
    rows = workload.index_q.shape[0]
    columns = workload.full_columns
    rows_per_chunk = max(
        1, base.LOGITS_WORKSPACE_BYTES // max(columns * 4, 1)
    )
    for row_start in range(0, rows, rows_per_chunk):
        row_end = min(row_start + rows_per_chunk, rows)
        row_slice = slice(row_start, row_end)
        logits, visible_blocks = qsa_mqa_paged(
            workload.index_q[row_slice],
            workload.compressed_k,
            workload.compressed_table,
            workload.token_to_req[row_slice],
            workload.query_positions[row_slice],
            workload.sequence_lengths,
            base.COMPRESS_RATIO,
            num_columns=columns,
        )
        blocks = torch.empty(
            (row_end - row_start, base.BLOCK_TOPK),
            device=logits.device,
            dtype=torch.int32,
        )
        range_starts = torch.zeros_like(visible_blocks)
        top_k_per_row_prefill(
            logits,
            range_starts,
            visible_blocks,
            blocks,
            logits.shape[0],
            logits.stride(0),
            logits.stride(1),
            base.BLOCK_TOPK,
        )
        base.expand_qsa_block_indices(
            blocks,
            workload.query_positions[row_slice],
            workload.sequence_lengths,
            workload.token_to_req[row_slice],
            base.COMPRESS_RATIO,
            base.TOKEN_TOPK,
            out[row_slice],
        )
    return out


def _provider_transaction(base, workload, selected, sparse_output):
    _select_provider(base, workload, selected)
    base.qsa_sparse_paged_attention(
        workload.sparse_q,
        workload.main_k,
        workload.main_v,
        selected,
        workload.main_table,
        workload.token_to_req,
        out=sparse_output,
    )
    return selected, sparse_output


@torch.inference_mode()
def run_case(base, rows: int, capacity: int, warmup: int, repeat: int):
    workload = base._make_workload(rows, capacity, torch.device("cuda"))
    torch_selected = torch.empty(
        (rows, base.OUTPUT_WIDTH), device="cuda", dtype=torch.int32
    )
    provider_selected = torch.empty_like(torch_selected)
    torch_sparse = torch.empty_like(workload.sparse_q)
    provider_sparse = torch.empty_like(workload.sparse_q)
    torch_fn = lambda: base._transaction(
        workload, workload.full_columns, torch_selected, torch_sparse
    )
    provider_fn = lambda: _provider_transaction(
        base, workload, provider_selected, provider_sparse
    )

    torch_fn()
    provider_fn()
    torch.cuda.synchronize()
    base._assert_same_selection(torch_selected, provider_selected)
    torch.testing.assert_close(
        torch_sparse, provider_sparse, atol=0.05, rtol=0.05
    )

    torch_selection_ms = base._event_ms(
        lambda: base._select_static(
            workload, workload.full_columns, torch_selected
        ),
        warmup,
        repeat,
    )
    provider_selection_ms = base._event_ms(
        lambda: _select_provider(base, workload, provider_selected),
        warmup,
        repeat,
    )
    torch_transaction_ms = base._event_ms(torch_fn, warmup, repeat)
    provider_transaction_ms = base._event_ms(provider_fn, warmup, repeat)

    torch_graph, torch_capture = base._capture(
        torch_fn, (torch_selected, torch_sparse)
    )
    provider_graph, provider_capture = base._capture(
        provider_fn, (provider_selected, provider_sparse)
    )
    torch_replays = base._replay_snapshots(
        torch_graph, (torch_selected, torch_sparse)
    )
    provider_replays = base._replay_snapshots(
        provider_graph, (provider_selected, provider_sparse)
    )
    for capture, replays in (
        (torch_capture, torch_replays),
        (provider_capture, provider_replays),
    ):
        for replay in replays:
            torch.testing.assert_close(capture[0], replay[0], atol=0, rtol=0)
            torch.testing.assert_close(capture[1], replay[1], atol=0, rtol=0)
    base._assert_same_selection(torch_capture[0], provider_capture[0])
    torch.testing.assert_close(
        torch_capture[1], provider_capture[1], atol=0.05, rtol=0.05
    )
    torch_graph_ms = base._graph_replay_ms(torch_graph, repeat)
    provider_graph_ms = base._graph_replay_ms(provider_graph, repeat)
    return {
        "rows": rows,
        "capacity": capacity,
        "score_columns": capacity,
        "torch_selection_ms": torch_selection_ms,
        "provider_selection_ms": provider_selection_ms,
        "selection_speedup": torch_selection_ms / provider_selection_ms,
        "torch_transaction_ms": torch_transaction_ms,
        "provider_transaction_ms": provider_transaction_ms,
        "transaction_speedup": torch_transaction_ms / provider_transaction_ms,
        "torch_graph_replay_ms": torch_graph_ms,
        "provider_graph_replay_ms": provider_graph_ms,
        "graph_speedup": torch_graph_ms / provider_graph_ms,
        "selection_sets_equal": True,
        "downstream_sparse_close": True,
        "capture_and_two_replays": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-script", type=Path, required=True)
    parser.add_argument("--rows", default="1,64,4096")
    parser.add_argument("--capacity", type=int, default=20000)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--repeat", type=int, default=20)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base = _load_base(args.base_script)
    results = [
        run_case(base, int(rows), args.capacity, args.warmup, args.repeat)
        for rows in args.rows.split(",")
    ]
    payload = {
        "schema_version": 1,
        "experiment": "qsa-torch-topk-vs-row-range-provider",
        "capacity": args.capacity,
        "warmup": args.warmup,
        "repeat": args.repeat,
        "results": results,
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "result.json").write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
