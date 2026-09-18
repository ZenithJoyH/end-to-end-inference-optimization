#!/usr/bin/env python3
"""Sweep moe_sum tiles for HY4's [M, 8, 6144] BF16 output."""

from __future__ import annotations

import json
import statistics
import time

import torch
import triton

from flag_gems.fused.moe_sum import moe_sum, moe_sum_kernel
from flag_gems.runtime import torch_device_fn


TOPK, HIDDEN = 8, 6144
CONFIGS = ((64, 1), (64, 2), (128, 2), (256, 4), (512, 8), (1024, 8), (2048, 8))


def sync() -> None:
    torch_device_fn.synchronize()


def fixed_sum(inp: torch.Tensor, block: int, warps: int) -> torch.Tensor:
    m = inp.shape[0]
    out = torch.empty((m, HIDDEN), device=inp.device, dtype=inp.dtype)
    moe_sum_kernel.fn[(m, triton.cdiv(HIDDEN, block))](
        inp, out, m, TOPK, HIDDEN,
        inp.stride(0), inp.stride(1), inp.stride(2),
        out.stride(0), out.stride(1),
        BLOCK_SIZE=block, num_warps=warps,
    )
    return out


def baseline_sum(inp: torch.Tensor) -> torch.Tensor:
    out = torch.empty((inp.shape[0], HIDDEN), device=inp.device, dtype=inp.dtype)
    moe_sum(inp, out)
    return out


def measure(fn) -> tuple[dict[str, float], torch.Tensor]:
    out = fn()
    for _ in range(5):
        out = fn()
    sync()
    samples = []
    for _ in range(80):
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
    for m in (256, 2048):
        inp = torch.randn((m, TOPK, HIDDEN), device=dev, dtype=torch.bfloat16)
        baseline, ref = measure(lambda: baseline_sum(inp))
        selected = repr(moe_sum_kernel.cache.get((HIDDEN, TOPK)))
        row = {"baseline": baseline, "autotune_selected": selected, "configs": {}}
        for block, warps in CONFIGS:
            timing, out = measure(lambda b=block, w=warps: fixed_sum(inp, b, w))
            delta = (ref.float() - out.float()).abs()
            row["configs"][f"block{block}-w{warps}"] = {
                "timing": timing,
                "speedup": baseline["median_us"] / timing["median_us"],
                "exact": bool(torch.equal(ref, out)),
                "max_abs_diff": float(delta.max().item()),
            }
        results[str(m)] = row
    print(json.dumps({"shape": {"topk": TOPK, "hidden": HIDDEN}, "results": results}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
