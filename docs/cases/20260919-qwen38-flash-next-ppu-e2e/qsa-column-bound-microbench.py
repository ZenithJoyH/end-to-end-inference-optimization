#!/usr/bin/env python3
"""Microbenchmark a graph-safe static QSA score-column bound.

This script is an experiment artifact.  It does not patch the live service and
uses only the current public FlagGems QSA functions.  Run it inside the cloned
optimization container after the live service has released the selected card.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import torch

from flag_gems.fused.qsa import (
    expand_qsa_block_indices,
    qsa_mqa_paged,
    qsa_sparse_paged_attention,
)


TOKEN_TOPK = 2048
COMPRESS_RATIO = 4
BLOCK_TOPK = TOKEN_TOPK // COMPRESS_RATIO
OUTPUT_WIDTH = TOKEN_TOPK + COMPRESS_RATIO - 1
LOGITS_WORKSPACE_BYTES = 128 * 1024 * 1024
PAGE_SIZE = 16


@dataclass
class Workload:
    index_q: torch.Tensor
    compressed_k: torch.Tensor
    compressed_table: torch.Tensor
    token_to_req: torch.Tensor
    query_positions: torch.Tensor
    sequence_lengths: torch.Tensor
    sparse_q: torch.Tensor
    main_k: torch.Tensor
    main_v: torch.Tensor
    main_table: torch.Tensor
    full_columns: int
    bounded_columns: int


def _round_up(value: int, multiple: int) -> int:
    return (value + multiple - 1) // multiple * multiple


def _make_workload(rows: int, capacity: int, device: torch.device) -> Workload:
    if capacity < BLOCK_TOPK or capacity % PAGE_SIZE:
        raise ValueError("capacity must be page-aligned and at least TopK/ratio")
    if rows == 4096:
        # Match one live 4096-token Prefill scheduling step: four P1K requests.
        num_requests = 4
        tokens_per_request = 1024
        token_to_req = torch.arange(
            num_requests, device=device, dtype=torch.int32
        ).repeat_interleave(tokens_per_request)
        query_positions = torch.arange(
            tokens_per_request, device=device, dtype=torch.int64
        ).repeat(num_requests)
        sequence_lengths = torch.full(
            (num_requests,), tokens_per_request, device=device, dtype=torch.int32
        )
    else:
        # Match late P1024/D128 decode while keeping one row per request.
        num_requests = rows
        max_sequence_length = 1152
        token_to_req = torch.arange(rows, device=device, dtype=torch.int32)
        query_positions = torch.full(
            (rows,), max_sequence_length - 1, device=device, dtype=torch.int64
        )
        sequence_lengths = torch.full(
            (num_requests,),
            max_sequence_length,
            device=device,
            dtype=torch.int32,
        )

    compressed_pages = capacity // PAGE_SIZE
    compressed_table = torch.arange(
        compressed_pages, device=device, dtype=torch.int32
    ).expand(num_requests, -1).contiguous()
    compressed_k = torch.randn(
        (compressed_pages, PAGE_SIZE, 1, 128),
        device=device,
        dtype=torch.bfloat16,
    )
    index_q = torch.randn((rows, 4, 128), device=device, dtype=torch.bfloat16)

    max_visible = int(sequence_lengths.max().cpu()) // COMPRESS_RATIO
    bounded_columns = max(BLOCK_TOPK, _round_up(max_visible, 32))
    bounded_columns = min(bounded_columns, capacity)

    max_main_length = int(sequence_lengths.max().cpu())
    main_pages = math.ceil(max_main_length / PAGE_SIZE)
    main_table = torch.arange(
        main_pages, device=device, dtype=torch.int32
    ).expand(num_requests, -1).contiguous()
    main_k = torch.randn(
        (main_pages, PAGE_SIZE, 1, 256),
        device=device,
        dtype=torch.bfloat16,
    )
    main_v = torch.randn_like(main_k)
    sparse_q = torch.randn((rows, 3, 256), device=device, dtype=torch.bfloat16)
    return Workload(
        index_q=index_q,
        compressed_k=compressed_k,
        compressed_table=compressed_table,
        token_to_req=token_to_req,
        query_positions=query_positions,
        sequence_lengths=sequence_lengths,
        sparse_q=sparse_q,
        main_k=main_k,
        main_v=main_v,
        main_table=main_table,
        full_columns=capacity,
        bounded_columns=bounded_columns,
    )


def _select_static(
    workload: Workload,
    score_columns: int,
    out: torch.Tensor,
) -> torch.Tensor:
    """Mirror current qsa_select_paged_tokens with a host-static width."""

    if not BLOCK_TOPK <= score_columns <= workload.full_columns:
        raise ValueError("score_columns must be in [block_topk, cache capacity]")
    rows = workload.index_q.shape[0]
    rows_per_chunk = max(
        1, LOGITS_WORKSPACE_BYTES // max(score_columns * 4, 1)
    )
    for row_start in range(0, rows, rows_per_chunk):
        row_end = min(row_start + rows_per_chunk, rows)
        row_slice = slice(row_start, row_end)
        logits, _visible = qsa_mqa_paged(
            workload.index_q[row_slice],
            workload.compressed_k,
            workload.compressed_table,
            workload.token_to_req[row_slice],
            workload.query_positions[row_slice],
            workload.sequence_lengths,
            COMPRESS_RATIO,
            num_columns=score_columns,
        )
        _, blocks = torch.topk(
            logits, BLOCK_TOPK, dim=-1, largest=True, sorted=True
        )
        expand_qsa_block_indices(
            blocks,
            workload.query_positions[row_slice],
            workload.sequence_lengths,
            workload.token_to_req[row_slice],
            COMPRESS_RATIO,
            TOKEN_TOPK,
            out[row_slice],
        )
    return out


def _transaction(
    workload: Workload,
    score_columns: int,
    selected: torch.Tensor,
    sparse_output: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    _select_static(workload, score_columns, selected)
    qsa_sparse_paged_attention(
        workload.sparse_q,
        workload.main_k,
        workload.main_v,
        selected,
        workload.main_table,
        workload.token_to_req,
        out=sparse_output,
    )
    return selected, sparse_output


def _assert_same_selection(full: torch.Tensor, bounded: torch.Tensor) -> None:
    full_cpu = full.cpu()
    bounded_cpu = bounded.cpu()
    for row in range(full.shape[0]):
        full_valid = full_cpu[row][full_cpu[row] >= 0].sort().values
        bounded_valid = bounded_cpu[row][bounded_cpu[row] >= 0].sort().values
        torch.testing.assert_close(full_valid, bounded_valid, atol=0, rtol=0)
        assert int((full_cpu[row] < 0).sum()) == int(
            (bounded_cpu[row] < 0).sum()
        )


def _event_ms(fn: Callable[[], object], warmup: int, repeat: int) -> float:
    for _ in range(warmup):
        fn()
    torch.cuda.synchronize()
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    start.record()
    for _ in range(repeat):
        fn()
    end.record()
    torch.cuda.synchronize()
    return float(start.elapsed_time(end)) / repeat


def _capture(
    fn: Callable[[], object],
    outputs: tuple[torch.Tensor, torch.Tensor],
) -> tuple[torch.cuda.CUDAGraph, tuple[torch.Tensor, torch.Tensor]]:
    for _ in range(3):
        fn()
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, capture_error_mode="thread_local"):
        fn()
    torch.cuda.synchronize()
    captured = tuple(output.clone() for output in outputs)
    return graph, captured


def _replay_snapshots(
    graph: torch.cuda.CUDAGraph,
    outputs: tuple[torch.Tensor, torch.Tensor],
) -> tuple[tuple[torch.Tensor, torch.Tensor], tuple[torch.Tensor, torch.Tensor]]:
    snapshots = []
    for _ in range(2):
        graph.replay()
        torch.cuda.synchronize()
        snapshots.append(tuple(output.clone() for output in outputs))
    return snapshots[0], snapshots[1]


def _graph_replay_ms(graph: torch.cuda.CUDAGraph, repeat: int) -> float:
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    start.record()
    for _ in range(repeat):
        graph.replay()
    end.record()
    torch.cuda.synchronize()
    return float(start.elapsed_time(end)) / repeat


@torch.inference_mode()
def run_case(
    rows: int, capacity: int, warmup: int, repeat: int
) -> dict[str, object]:
    device = torch.device("cuda")
    workload = _make_workload(rows, capacity, device)
    full_selected = torch.empty(
        (rows, OUTPUT_WIDTH), device=device, dtype=torch.int32
    )
    bound_selected = torch.empty_like(full_selected)
    full_sparse = torch.empty_like(workload.sparse_q)
    bound_sparse = torch.empty_like(workload.sparse_q)

    full_fn = lambda: _transaction(
        workload,
        workload.full_columns,
        full_selected,
        full_sparse,
    )
    bound_fn = lambda: _transaction(
        workload,
        workload.bounded_columns,
        bound_selected,
        bound_sparse,
    )

    full_fn()
    bound_fn()
    torch.cuda.synchronize()
    _assert_same_selection(full_selected, bound_selected)
    torch.testing.assert_close(full_sparse, bound_sparse, atol=0.05, rtol=0.05)

    full_selection_ms = _event_ms(
        lambda: _select_static(
            workload, workload.full_columns, full_selected
        ),
        warmup,
        repeat,
    )
    bound_selection_ms = _event_ms(
        lambda: _select_static(
            workload, workload.bounded_columns, bound_selected
        ),
        warmup,
        repeat,
    )
    full_transaction_ms = _event_ms(full_fn, warmup, repeat)
    bound_transaction_ms = _event_ms(bound_fn, warmup, repeat)

    full_graph, full_capture = _capture(
        full_fn, (full_selected, full_sparse)
    )
    bound_graph, bound_capture = _capture(
        bound_fn, (bound_selected, bound_sparse)
    )
    full_replay_one, full_replay_two = _replay_snapshots(
        full_graph, (full_selected, full_sparse)
    )
    bound_replay_one, bound_replay_two = _replay_snapshots(
        bound_graph, (bound_selected, bound_sparse)
    )

    for first, second in (
        (full_capture, full_replay_one),
        (full_capture, full_replay_two),
        (bound_capture, bound_replay_one),
        (bound_capture, bound_replay_two),
    ):
        torch.testing.assert_close(first[0], second[0], atol=0, rtol=0)
        torch.testing.assert_close(first[1], second[1], atol=0, rtol=0)
    _assert_same_selection(full_capture[0], bound_capture[0])
    torch.testing.assert_close(
        full_capture[1], bound_capture[1], atol=0.05, rtol=0.05
    )

    full_graph_ms = _graph_replay_ms(full_graph, repeat)
    bound_graph_ms = _graph_replay_ms(bound_graph, repeat)
    return {
        "rows": rows,
        "dtype": "bfloat16",
        "full_columns": workload.full_columns,
        "bounded_columns": workload.bounded_columns,
        "block_topk": BLOCK_TOPK,
        "output_width": OUTPUT_WIDTH,
        "full_selection_ms": full_selection_ms,
        "bounded_selection_ms": bound_selection_ms,
        "selection_speedup": full_selection_ms / bound_selection_ms,
        "full_transaction_ms": full_transaction_ms,
        "bounded_transaction_ms": bound_transaction_ms,
        "transaction_speedup": full_transaction_ms / bound_transaction_ms,
        "full_graph_replay_ms": full_graph_ms,
        "bounded_graph_replay_ms": bound_graph_ms,
        "graph_speedup": full_graph_ms / bound_graph_ms,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", default="1,8,64,4096")
    parser.add_argument("--capacity", type=int, default=20000)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--repeat", type=int, default=20)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("an accelerator exposed through torch.cuda is required")
    rows_values = [int(value) for value in args.rows.split(",")]
    if rows_values != [1, 8, 64, 4096]:
        print({"note": "non-default rows", "rows": rows_values})
    results = [
        run_case(rows, args.capacity, args.warmup, args.repeat)
        for rows in rows_values
    ]
    payload = {
        "schema_version": 1,
        "experiment": "qsa-static-score-column-bound",
        "capacity": args.capacity,
        "warmup": args.warmup,
        "repeat": args.repeat,
        "graph_capture_replays": 2,
        "results": results,
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
