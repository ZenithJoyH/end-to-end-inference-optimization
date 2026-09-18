#!/usr/bin/env python3
"""Sweep fixed FlagGems linear tiles for the HY4 FP32 router shape."""

from __future__ import annotations

import json
import statistics
import time

import torch
import triton

from flag_gems.ops.linear import linear as flaggems_linear
from flag_gems.ops.linear import linear_kernel
from flag_gems.runtime import torch_device_fn


K, N = 6144, 256

# Include both current candidates and larger-K candidates.  The first pass is
# deliberately small because each (shape, config) pair needs compilation.
CONFIGS = (
    (128, 256, 64, 8, 3),
    (64, 256, 32, 4, 4),
    (32, 256, 64, 4, 3),
    (16, 256, 64, 4, 3),
    (16, 256, 128, 4, 3),
    (16, 256, 256, 4, 3),
    (32, 256, 128, 4, 3),
    (64, 256, 128, 8, 3),
    (128, 256, 128, 8, 3),
    (64, 128, 64, 4, 3),
    (128, 128, 64, 8, 3),
    (64, 128, 128, 8, 3),
    (128, 256, 256, 8, 3),
)


def sync() -> None:
    torch_device_fn.synchronize()


def fixed_linear(x: torch.Tensor, w: torch.Tensor, config: tuple[int, ...]) -> torch.Tensor:
    bm, bn, bk, warps, stages = config
    m = x.shape[0]
    output = torch.empty((m, N), device=x.device, dtype=x.dtype)
    grid = (triton.cdiv(m, bm), triton.cdiv(N, bn))
    linear_kernel.jit_function[grid](
        x,
        w,
        w,
        output,
        m,
        N,
        K,
        x.stride(0),
        x.stride(1),
        w.stride(0),
        w.stride(1),
        output.stride(0),
        output.stride(1),
        0,
        BIAS=False,
        BLOCK_SIZE_M=bm,
        BLOCK_SIZE_N=bn,
        BLOCK_SIZE_K=bk,
        num_warps=warps,
        num_stages=stages,
    )
    return output


def measure(fn) -> tuple[dict[str, float], torch.Tensor]:
    output = fn()
    for _ in range(5):
        output = fn()
    sync()
    samples = []
    for _ in range(40):
        start = time.perf_counter()
        output = fn()
        sync()
        samples.append((time.perf_counter() - start) * 1_000_000)
    return {
        "mean_us": statistics.fmean(samples),
        "median_us": statistics.median(samples),
        "min_us": min(samples),
        "max_us": max(samples),
    }, output


def compare(reference: torch.Tensor, candidate: torch.Tensor) -> dict[str, object]:
    delta = (reference - candidate).abs()
    return {
        "exact": bool(torch.equal(reference, candidate)),
        "max_abs_diff": float(delta.max().item()),
        "mean_abs_diff": float(delta.mean().item()),
        "top8_equal_fraction": float(
            (reference.topk(8, dim=-1).indices == candidate.topk(8, dim=-1).indices)
            .all(dim=-1)
            .float()
            .mean()
            .item()
        ),
    }


def config_name(config: tuple[int, ...]) -> str:
    bm, bn, bk, warps, stages = config
    return f"bm{bm}-bn{bn}-bk{bk}-w{warps}-s{stages}"


def main() -> None:
    torch.manual_seed(20260916)
    device = torch.device("cuda")
    w = torch.randn((N, K), device=device, dtype=torch.float32)
    all_results: dict[str, object] = {}
    for m in (1, 16, 256, 2048):
        x = torch.randn((m, K), device=device, dtype=torch.float32)
        baseline_timing, baseline = measure(lambda: flaggems_linear(x, w))
        result: dict[str, object] = {"baseline": baseline_timing, "configs": {}}
        for config in CONFIGS:
            name = config_name(config)
            try:
                timing, output = measure(lambda c=config: fixed_linear(x, w, c))
                result["configs"][name] = {
                    "timing": timing,
                    "speedup": baseline_timing["median_us"] / timing["median_us"],
                    "correctness": compare(baseline, output),
                }
            except Exception as error:
                result["configs"][name] = {"error": repr(error)}
        all_results[str(m)] = result
    print(json.dumps({"shape": {"K": K, "N": N}, "results": all_results}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
