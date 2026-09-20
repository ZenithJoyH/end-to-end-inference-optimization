#!/usr/bin/env python3
"""Benchmark reusing Indexer scores for the exact BF16 pointwise output."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import torch
import triton

from vllm_fl.models import hy_v4


WARMUP = 3
RUNS = 5
REPEATS = 7
HEADS = 32
HEAD_DIM = 128
TOPK = 2048


def inplace_reduce(
    scores: torch.Tensor,
    weights: torch.Tensor,
) -> torch.Tensor:
    rows, keys_per_row, heads = scores.shape
    numel = scores.numel()
    block = 256
    hy_v4._hyv4_fused_relu_weight_kernel[
        (triton.cdiv(numel, block),)
    ](
        scores,
        weights,
        scores,
        numel,
        keys_per_row * heads,
        heads,
        BLOCK=block,
        num_warps=4,
        num_stages=1,
    )
    return scores.sum(dim=-1).float()


def elapsed_us(fn) -> list[float]:
    for _ in range(WARMUP):
        fn()
    torch.cuda.synchronize()
    samples = []
    for _ in range(REPEATS):
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        for _ in range(RUNS):
            fn()
        end.record()
        end.synchronize()
        samples.append(start.elapsed_time(end) * 1000.0 / RUNS)
    return samples


def timing(samples: list[float]) -> dict[str, object]:
    return {
        "median_us": statistics.median(samples),
        "min_us": min(samples),
        "max_us": max(samples),
        "samples_us": samples,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")
    assert torch.cuda.is_available()
    assert hy_v4.current_platform.vendor_name == "thead"

    torch.manual_seed(20260919)
    baseline_reduce = hy_v4._hyv4_weighted_relu_reduce
    reduction_rows = []
    block_rows = []
    for rows, keys_count in ((26, 4096), (128, 2048), (128, 4096)):
        source = torch.randn(
            (rows, keys_count, HEADS),
            device="cuda",
            dtype=torch.bfloat16,
        )
        weights = torch.randn(
            (rows, HEADS), device="cuda", dtype=torch.bfloat16
        )
        expected_products = source.clone()
        expected = baseline_reduce(expected_products, weights)
        actual_products = source.clone()
        actual = inplace_reduce(actual_products, weights)
        torch.cuda.synchronize()
        reference_products = (
            torch.relu(source) * weights.to(source.dtype).unsqueeze(1)
        )
        products_exact = bool(torch.equal(reference_products, actual_products))
        logits_exact = bool(torch.equal(expected, actual))
        assert products_exact and logits_exact

        baseline_work = source.clone()
        candidate_work = source.clone()

        def baseline_chain() -> None:
            baseline_work.copy_(source)
            baseline_reduce(baseline_work, weights)

        def candidate_chain() -> None:
            candidate_work.copy_(source)
            inplace_reduce(candidate_work, weights)

        baseline_stats = timing(elapsed_us(baseline_chain))
        candidate_stats = timing(elapsed_us(candidate_chain))
        reduction_rows.append(
            {
                "rows": rows,
                "keys": keys_count,
                "heads": HEADS,
                "products_exact": products_exact,
                "logits_exact": logits_exact,
                "baseline": baseline_stats,
                "candidate": candidate_stats,
                "speedup": baseline_stats["median_us"]
                / candidate_stats["median_us"],
                "delta_us": baseline_stats["median_us"]
                - candidate_stats["median_us"],
            }
        )

        if keys_count != 4096:
            continue
        q = torch.randn(
            (rows, HEADS, HEAD_DIM), device="cuda", dtype=torch.bfloat16
        )
        keys = torch.randn(
            (keys_count, HEAD_DIM), device="cuda", dtype=torch.bfloat16
        )
        row_starts = torch.zeros((rows,), device="cuda", dtype=torch.int32)
        row_ends = torch.arange(
            keys_count - rows + 1,
            keys_count + 1,
            device="cuda",
            dtype=torch.int32,
        )
        output = torch.empty((rows, TOPK), device="cuda", dtype=torch.int32)

        def invoke() -> None:
            hy_v4._select_topk_block(
                q,
                weights,
                keys,
                row_starts,
                row_ends,
                key_start=0,
                key_end=keys_count,
                request_start=0,
                topk=TOPK,
                output=output,
            )

        hy_v4._hyv4_weighted_relu_reduce = baseline_reduce
        baseline_block = timing(elapsed_us(invoke))
        hy_v4._hyv4_weighted_relu_reduce = inplace_reduce
        candidate_block = timing(elapsed_us(invoke))
        block_rows.append(
            {
                "rows": rows,
                "keys": keys_count,
                "topk": TOPK,
                "baseline": baseline_block,
                "candidate": candidate_block,
                "speedup": baseline_block["median_us"]
                / candidate_block["median_us"],
                "delta_us": baseline_block["median_us"]
                - candidate_block["median_us"],
            }
        )
        hy_v4._hyv4_weighted_relu_reduce = baseline_reduce

    graph_source = torch.randn(
        (128, 2048, HEADS), device="cuda", dtype=torch.bfloat16
    )
    graph_weights = torch.randn(
        (128, HEADS), device="cuda", dtype=torch.bfloat16
    )
    graph_expected = baseline_reduce(graph_source, graph_weights)
    graph_work = graph_source.clone()
    graph = torch.cuda.CUDAGraph()
    torch.cuda.synchronize()
    with torch.cuda.graph(graph):
        graph_output = inplace_reduce(graph_work, graph_weights)
    graph_replays = []
    for replay in range(2):
        graph_work.copy_(graph_source)
        graph.replay()
        torch.cuda.synchronize()
        graph_replays.append(
            {
                "replay": replay + 1,
                "exact": bool(torch.equal(graph_expected, graph_output)),
            }
        )
    assert all(row["exact"] for row in graph_replays)

    result = {
        "schema_version": 1,
        "device": torch.cuda.get_device_name(0),
        "vendor": hy_v4.current_platform.vendor_name,
        "reduction_chain": reduction_rows,
        "complete_block": block_rows,
        "graph_capture": "passed",
        "graph_replays": graph_replays,
        "conclusion_boundary": (
            "synthetic exact pointwise/reduction and complete Indexer block "
            "timings; not an end-to-end result"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
