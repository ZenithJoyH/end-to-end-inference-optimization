#!/usr/bin/env python3
"""Probe reduction orders for bitwise agreement with PyTorch BF16 sum."""

from __future__ import annotations

import json
import statistics

import torch
import triton
import triton.language as tl


ROWS = 128
KEYS = 4096
HEADS = 32
BLOCK_M = 128
WARMUP = 3
RUNS = 10
REPEATS = 3


@triton.jit
def reduce_order_kernel(
    scores,
    weights,
    logits,
    num_positions,
    keys_per_row: tl.constexpr,
    heads: tl.constexpr,
    VARIANT: tl.constexpr,
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
    if VARIANT == 0:
        reduced = tl.sum(products, axis=1)
    elif VARIANT == 1:
        reduced = tl.zeros([BLOCK_M], tl.float32)
        for head in tl.static_range(0, heads):
            reduced += products[:, head].to(tl.float32)
    elif VARIANT == 2:
        grouped = tl.reshape(products, [BLOCK_M, 4, 8])
        partial = tl.sum(grouped, axis=2)
        reduced = tl.sum(partial, axis=1)
    elif VARIANT == 3:
        grouped = tl.reshape(products, [BLOCK_M, 8, 4])
        partial = tl.sum(grouped, axis=2)
        reduced = tl.sum(partial, axis=1)
    else:
        grouped = tl.reshape(products, [BLOCK_M, 16, 2])
        partial = tl.sum(grouped, axis=2)
        reduced = tl.sum(partial, axis=1)
    tl.store(
        logits + positions,
        reduced.to(tl.bfloat16).to(tl.float32),
        mask=valid,
    )


def launch(scores, weights, output, variant) -> None:
    num_positions = scores.shape[0] * scores.shape[1]
    reduce_order_kernel[(triton.cdiv(num_positions, BLOCK_M),)](
        scores,
        weights,
        output,
        num_positions,
        scores.shape[1],
        scores.shape[2],
        VARIANT=variant,
        BLOCK_M=BLOCK_M,
        num_warps=8,
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


def main() -> None:
    torch.manual_seed(20260916)
    scores = torch.randn(
        (ROWS, KEYS, HEADS), device="cuda", dtype=torch.bfloat16
    )
    weights = torch.randn((ROWS, HEADS), device="cuda", dtype=torch.float32)
    reference = (
        torch.relu(scores) * weights.to(scores.dtype).unsqueeze(1)
    ).sum(dim=-1).float()
    output = torch.empty_like(reference)
    torch.cuda.synchronize()

    rows = []
    for variant, name in (
        (0, "default"),
        (2, "group_4x8"),
        (3, "group_8x4"),
        (4, "group_16x2"),
    ):
        launch(scores, weights, output, variant)
        torch.cuda.synchronize()
        diff = (output - reference).abs()
        samples = elapsed_us(
            lambda variant=variant: launch(scores, weights, output, variant)
        )
        row = {
            "variant": variant,
            "name": name,
            "samples_us": samples,
            "median_us": statistics.median(samples),
            "exact_fraction": float((output == reference).float().mean().item()),
            "max_abs_diff": float(diff.max().item()),
            "mean_abs_diff": float(diff.mean().item()),
        }
        rows.append(row)
        print(json.dumps(row), flush=True)

    best_exact = max(
        rows, key=lambda row: (row["exact_fraction"], -row["median_us"])
    )
    print(
        "SUMMARY="
        + json.dumps(
            {
                "status": "passed",
                "shape": {"rows": ROWS, "keys": KEYS, "heads": HEADS},
                "best_exact": best_exact,
                "rows": rows,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
