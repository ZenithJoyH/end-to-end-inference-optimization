#!/usr/bin/env python3
"""Benchmark fusing Hy4 Indexer ReLU, weight multiply, and head reduction."""

from __future__ import annotations

import json
import statistics

import torch
import triton
import triton.language as tl

from vllm_fl.models import hy_v4


ROWS = 128
KEYS = 4096
HEADS = 32
TOPK = 2048
WARMUP = 5
RUNS = 10
REPEATS = 5


@triton.jit
def fused_weighted_relu_reduce_kernel(
    scores,
    weights,
    output,
    num_positions,
    keys_per_row: tl.constexpr,
    heads: tl.constexpr,
    BLOCK_M: tl.constexpr,
):
    pid = tl.program_id(0)
    positions = pid * BLOCK_M + tl.arange(0, BLOCK_M)
    head_offsets = tl.arange(0, heads)
    valid = positions < num_positions
    row = positions // keys_per_row
    score_values = tl.load(
        scores + positions[:, None] * heads + head_offsets[None, :],
        mask=valid[:, None],
        other=0.0,
    )
    weight_values = tl.load(
        weights + row[:, None] * heads + head_offsets[None, :],
        mask=valid[:, None],
        other=0.0,
    ).to(tl.bfloat16)
    products = (
        tl.maximum(score_values, 0.0) * weight_values
    ).to(tl.bfloat16)
    reduced = tl.sum(products, axis=1).to(tl.bfloat16)
    tl.store(output + positions, reduced.to(tl.float32), mask=valid)


def baseline(scores, weights, output) -> None:
    output.copy_(
        (
            torch.relu(scores)
            * weights.to(scores.dtype).unsqueeze(1)
        )
        .sum(dim=-1)
        .float()
    )


def candidate(scores, weights, output, block_m, warps) -> None:
    num_positions = scores.shape[0] * scores.shape[1]
    fused_weighted_relu_reduce_kernel[(triton.cdiv(num_positions, block_m),)](
        scores,
        weights,
        output,
        num_positions,
        scores.shape[1],
        scores.shape[2],
        BLOCK_M=block_m,
        num_warps=warps,
        num_stages=1,
    )


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


def selected_set_overlap(logits_a, logits_b, row_ends) -> dict:
    starts = torch.zeros(ROWS, device="cuda", dtype=torch.int32)
    out_a = torch.empty((ROWS, TOPK), device="cuda", dtype=torch.int32)
    out_b = torch.empty_like(out_a)
    hy_v4._top_k_per_row_prefill(logits_a, starts, row_ends, out_a)
    hy_v4._top_k_per_row_prefill(logits_b, starts, row_ends, out_b)
    mask_a = torch.zeros((ROWS, KEYS), device="cuda", dtype=torch.bool)
    mask_b = torch.zeros_like(mask_a)
    mask_a.scatter_(1, out_a.to(torch.long), True)
    mask_b.scatter_(1, out_b.to(torch.long), True)
    intersection = (mask_a & mask_b).sum(dim=1)
    return {
        "mean_overlap_fraction": float(intersection.sum().item() / (ROWS * TOPK)),
        "minimum_row_overlap_fraction": float(intersection.min().item() / TOPK),
        "exact_row_count": int((intersection == TOPK).sum().item()),
    }


def main() -> None:
    torch.manual_seed(20260916)
    scores = torch.randn(
        (ROWS, KEYS, HEADS), device="cuda", dtype=torch.bfloat16
    )
    weights = torch.randn((ROWS, HEADS), device="cuda", dtype=torch.float32)
    baseline_output = torch.empty((ROWS, KEYS), device="cuda", dtype=torch.float32)
    candidate_output = torch.empty_like(baseline_output)
    row_ends = torch.linspace(TOPK + 1, KEYS, ROWS, device="cuda").to(
        torch.int32
    )

    baseline(scores, weights, baseline_output)
    torch.cuda.synchronize()
    baseline_samples = elapsed_us(
        lambda: baseline(scores, weights, baseline_output)
    )
    baseline_median = statistics.median(baseline_samples)

    rows = []
    for block_m, warps in ((32, 4), (64, 4), (128, 4), (256, 4), (128, 8)):
        candidate(scores, weights, candidate_output, block_m, warps)
        torch.cuda.synchronize()
        diff = (candidate_output - baseline_output).abs()
        overlap = selected_set_overlap(
            baseline_output, candidate_output, row_ends
        )
        samples = elapsed_us(
            lambda: candidate(
                scores, weights, candidate_output, block_m, warps
            )
        )
        median = statistics.median(samples)
        row = {
            "block_m": block_m,
            "warps": warps,
            "samples_us": samples,
            "median_us": median,
            "speedup_vs_eager_chain": baseline_median / median,
            "max_abs_diff": float(diff.max().item()),
            "mean_abs_diff": float(diff.mean().item()),
            **overlap,
        }
        rows.append(row)
        print(json.dumps(row), flush=True)

    best = min(rows, key=lambda row: row["median_us"])
    candidate(
        scores,
        weights,
        candidate_output,
        best["block_m"],
        best["warps"],
    )
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        candidate(
            scores,
            weights,
            candidate_output,
            best["block_m"],
            best["warps"],
        )
    for _ in range(2):
        graph.replay()
    scores.add_(torch.tensor(0.25, device="cuda", dtype=torch.bfloat16))
    graph.replay()
    torch.cuda.synchronize()

    print(
        "SUMMARY="
        + json.dumps(
            {
                "status": "passed",
                "shape": {"rows": ROWS, "keys": KEYS, "heads": HEADS},
                "baseline_samples_us": baseline_samples,
                "baseline_median_us": baseline_median,
                "best": best,
                "graph": {
                    "capture": "passed",
                    "replays": 3,
                    "changed_input_replay": True,
                },
                "boundary": (
                    "operator-only reduction benchmark; implementation and "
                    "service-level validation required before retention"
                ),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
