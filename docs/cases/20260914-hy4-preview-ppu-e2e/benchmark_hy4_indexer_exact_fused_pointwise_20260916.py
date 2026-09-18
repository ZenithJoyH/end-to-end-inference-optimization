#!/usr/bin/env python3
"""Benchmark an exact hybrid: fused ReLU/mul plus native PyTorch sum."""

from __future__ import annotations

import json
import statistics

import torch
import triton
import triton.language as tl


ROWS = 128
KEYS = 4096
HEADS = 32
BLOCK = 256
WARMUP = 5
RUNS = 10
REPEATS = 5


@triton.jit
def fused_relu_weight_kernel(
    scores,
    weights,
    products,
    numel,
    row_width: tl.constexpr,
    heads: tl.constexpr,
    BLOCK: tl.constexpr,
):
    offsets = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
    valid = offsets < numel
    head = offsets % heads
    row = offsets // row_width
    score = tl.load(scores + offsets, mask=valid, other=0.0)
    weight = tl.load(
        weights + row * heads + head, mask=valid, other=0.0
    ).to(tl.bfloat16)
    product = (tl.maximum(score, 0.0) * weight).to(tl.bfloat16)
    tl.store(products + offsets, product, mask=valid)


def baseline(scores, weights, output) -> None:
    output.copy_(
        (
            torch.relu(scores)
            * weights.to(scores.dtype).unsqueeze(1)
        )
        .sum(dim=-1)
        .float()
    )


def candidate(scores, weights, products, output) -> None:
    numel = scores.numel()
    fused_relu_weight_kernel[(triton.cdiv(numel, BLOCK),)](
        scores,
        weights,
        products,
        numel,
        scores.shape[1] * scores.shape[2],
        scores.shape[2],
        BLOCK=BLOCK,
        num_warps=4,
        num_stages=1,
    )
    output.copy_(products.sum(dim=-1).float())


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


def main() -> None:
    torch.manual_seed(20260916)
    scores = torch.randn(
        (ROWS, KEYS, HEADS), device="cuda", dtype=torch.bfloat16
    )
    weights = torch.randn((ROWS, HEADS), device="cuda", dtype=torch.float32)
    reference_products = torch.relu(scores) * weights.to(scores.dtype).unsqueeze(1)
    products = torch.empty_like(scores)
    baseline_output = torch.empty((ROWS, KEYS), device="cuda", dtype=torch.float32)
    candidate_output = torch.empty_like(baseline_output)
    baseline(scores, weights, baseline_output)
    candidate(scores, weights, products, candidate_output)
    torch.cuda.synchronize()

    product_exact_fraction = float(
        (products == reference_products).float().mean().item()
    )
    logits_exact_fraction = float(
        (candidate_output == baseline_output).float().mean().item()
    )
    max_abs_diff = float((candidate_output - baseline_output).abs().max().item())
    baseline_samples = elapsed_us(
        lambda: baseline(scores, weights, baseline_output)
    )
    candidate_samples = elapsed_us(
        lambda: candidate(
            scores, weights, products, candidate_output
        )
    )
    baseline_median = statistics.median(baseline_samples)
    candidate_median = statistics.median(candidate_samples)
    print(
        "SUMMARY="
        + json.dumps(
            {
                "status": "passed",
                "shape": {"rows": ROWS, "keys": KEYS, "heads": HEADS},
                "product_exact_fraction": product_exact_fraction,
                "logits_exact_fraction": logits_exact_fraction,
                "max_abs_diff": max_abs_diff,
                "baseline_samples_us": baseline_samples,
                "candidate_samples_us": candidate_samples,
                "baseline_median_us": baseline_median,
                "candidate_median_us": candidate_median,
                "speedup": baseline_median / candidate_median,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
