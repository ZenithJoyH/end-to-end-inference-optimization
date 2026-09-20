#!/usr/bin/env python3
"""Compare the live scalar QSA scorer with the existing Qwen4 tl.dot scorer.

The score width and all surrounding selection/sparse-attention work stay fixed.
This isolates an operator replacement from the independent score-column-bound
experiment.  Run only after the selected accelerator has been released.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Callable

import torch

from flag_gems.fused.qsa import qsa_mqa_paged
from flaggems_vllm.ops.qwen4.qsa import qwen4_qsa_mqa_paged_dot


def _load_base(path: Path):
    spec = importlib.util.spec_from_file_location("qsa_column_bound_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import base microbenchmark: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _select(
    base,
    scorer: Callable[..., tuple[torch.Tensor, torch.Tensor]],
    workload,
    out: torch.Tensor,
) -> torch.Tensor:
    rows = workload.index_q.shape[0]
    columns = workload.full_columns
    rows_per_chunk = max(
        1, base.LOGITS_WORKSPACE_BYTES // max(columns * 4, 1)
    )
    for row_start in range(0, rows, rows_per_chunk):
        row_end = min(row_start + rows_per_chunk, rows)
        row_slice = slice(row_start, row_end)
        logits, _ = scorer(
            workload.index_q[row_slice],
            workload.compressed_k,
            workload.compressed_table,
            workload.token_to_req[row_slice],
            workload.query_positions[row_slice],
            workload.sequence_lengths,
            base.COMPRESS_RATIO,
            num_columns=columns,
        )
        _, blocks = torch.topk(
            logits, base.BLOCK_TOPK, dim=-1, largest=True, sorted=True
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


def _transaction(base, scorer, workload, selected, sparse_output):
    _select(base, scorer, workload, selected)
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
    scalar_selected = torch.empty(
        (rows, base.OUTPUT_WIDTH), device="cuda", dtype=torch.int32
    )
    dot_selected = torch.empty_like(scalar_selected)
    scalar_sparse = torch.empty_like(workload.sparse_q)
    dot_sparse = torch.empty_like(workload.sparse_q)
    scalar_fn = lambda: _transaction(
        base,
        qsa_mqa_paged,
        workload,
        scalar_selected,
        scalar_sparse,
    )
    dot_fn = lambda: _transaction(
        base,
        qwen4_qsa_mqa_paged_dot,
        workload,
        dot_selected,
        dot_sparse,
    )

    scalar_fn()
    dot_fn()
    torch.cuda.synchronize()
    base._assert_same_selection(scalar_selected, dot_selected)
    torch.testing.assert_close(
        scalar_sparse, dot_sparse, atol=0.05, rtol=0.05
    )

    scalar_selection_ms = base._event_ms(
        lambda: _select(base, qsa_mqa_paged, workload, scalar_selected),
        warmup,
        repeat,
    )
    dot_selection_ms = base._event_ms(
        lambda: _select(
            base, qwen4_qsa_mqa_paged_dot, workload, dot_selected
        ),
        warmup,
        repeat,
    )
    scalar_transaction_ms = base._event_ms(scalar_fn, warmup, repeat)
    dot_transaction_ms = base._event_ms(dot_fn, warmup, repeat)

    scalar_graph, scalar_capture = base._capture(
        scalar_fn, (scalar_selected, scalar_sparse)
    )
    dot_graph, dot_capture = base._capture(dot_fn, (dot_selected, dot_sparse))
    scalar_replays = base._replay_snapshots(
        scalar_graph, (scalar_selected, scalar_sparse)
    )
    dot_replays = base._replay_snapshots(
        dot_graph, (dot_selected, dot_sparse)
    )
    for capture, replays in (
        (scalar_capture, scalar_replays),
        (dot_capture, dot_replays),
    ):
        for replay in replays:
            torch.testing.assert_close(capture[0], replay[0], atol=0, rtol=0)
            torch.testing.assert_close(capture[1], replay[1], atol=0, rtol=0)
    base._assert_same_selection(scalar_capture[0], dot_capture[0])
    torch.testing.assert_close(
        scalar_capture[1], dot_capture[1], atol=0.05, rtol=0.05
    )
    scalar_graph_ms = base._graph_replay_ms(scalar_graph, repeat)
    dot_graph_ms = base._graph_replay_ms(dot_graph, repeat)
    return {
        "rows": rows,
        "capacity": capacity,
        "score_columns": capacity,
        "scalar_selection_ms": scalar_selection_ms,
        "dot_selection_ms": dot_selection_ms,
        "selection_speedup": scalar_selection_ms / dot_selection_ms,
        "scalar_transaction_ms": scalar_transaction_ms,
        "dot_transaction_ms": dot_transaction_ms,
        "transaction_speedup": scalar_transaction_ms / dot_transaction_ms,
        "scalar_graph_replay_ms": scalar_graph_ms,
        "dot_graph_replay_ms": dot_graph_ms,
        "graph_speedup": scalar_graph_ms / dot_graph_ms,
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
    if not torch.cuda.is_available():
        raise RuntimeError("an accelerator exposed through torch.cuda is required")
    base = _load_base(args.base_script)
    results = [
        run_case(base, int(rows), args.capacity, args.warmup, args.repeat)
        for rows in args.rows.split(",")
    ]
    payload = {
        "schema_version": 1,
        "experiment": "qsa-scalar-vs-existing-qwen4-dot",
        "capacity": args.capacity,
        "warmup": args.warmup,
        "repeat": args.repeat,
        "results": results,
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "result.json").write_text(
        encoded + "\n", encoding="utf-8"
    )
    print(encoded)


if __name__ == "__main__":
    main()
