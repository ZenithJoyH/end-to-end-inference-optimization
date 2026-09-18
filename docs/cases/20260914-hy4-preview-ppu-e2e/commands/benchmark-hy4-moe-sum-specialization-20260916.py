#!/usr/bin/env python3
"""Validate the proposed HY4 moe_sum specialization across runtime token counts."""

from __future__ import annotations

import json
import statistics
import time

import torch
import triton

from flag_gems.fused.moe_sum import moe_sum, moe_sum_kernel
from flag_gems.runtime import torch_device_fn


TOPK, HIDDEN = 8, 6144


def sync() -> None:
    torch_device_fn.synchronize()


def baseline(inp: torch.Tensor) -> torch.Tensor:
    out = torch.empty((inp.shape[0], HIDDEN), device=inp.device, dtype=inp.dtype)
    moe_sum(inp, out)
    return out


def candidate(inp: torch.Tensor) -> torch.Tensor:
    m = inp.shape[0]
    block, warps = (256, 4) if m <= 512 else (512, 8)
    out = torch.empty((m, HIDDEN), device=inp.device, dtype=inp.dtype)
    moe_sum_kernel.fn[(m, triton.cdiv(HIDDEN, block))](
        inp, out, m, TOPK, HIDDEN,
        inp.stride(0), inp.stride(1), inp.stride(2),
        out.stride(0), out.stride(1),
        BLOCK_SIZE=block, num_warps=warps,
    )
    return out


def measure(fn) -> tuple[dict[str, float], torch.Tensor]:
    out = fn()
    for _ in range(5):
        out = fn()
    sync()
    samples = []
    for _ in range(60):
        start = time.perf_counter()
        out = fn()
        sync()
        samples.append((time.perf_counter() - start) * 1_000_000)
    return {
        "mean_us": statistics.fmean(samples),
        "median_us": statistics.median(samples),
        "min_us": min(samples),
        "max_us": max(samples),
    }, out


def main() -> None:
    torch.manual_seed(20260916)
    dev = torch.device("cuda")
    results = {}
    for m in (1, 16, 64, 128, 256, 512, 1024, 2048):
        inp = torch.randn((m, TOPK, HIDDEN), device=dev, dtype=torch.bfloat16)
        baseline_timing, ref = measure(lambda: baseline(inp))
        candidate_timing, out = measure(lambda: candidate(inp))
        delta = (ref.float() - out.float()).abs()
        results[str(m)] = {
            "baseline": baseline_timing,
            "candidate": candidate_timing,
            "speedup": baseline_timing["median_us"] / candidate_timing["median_us"],
            "exact": bool(torch.equal(ref, out)),
            "max_abs_diff": float(delta.max().item()),
            "config": "block256-w4" if m <= 512 else "block512-w8",
        }
    print(json.dumps({"shape": {"topk": TOPK, "hidden": HIDDEN}, "results": results}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
