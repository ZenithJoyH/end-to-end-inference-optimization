#!/usr/bin/env python3
"""Narrow, cache-friendly tile check for the HY4 FP32 router linear."""

from __future__ import annotations

import json
import statistics
import sys
import time

import torch
import triton

from flag_gems.ops.linear import linear_kernel
from flag_gems.runtime import torch_device_fn


K, N = 6144, 256
SMALL = (
    (32, 32, 32, 4, 4),
    (32, 64, 32, 2, 5),
    (64, 32, 32, 2, 5),
    (64, 128, 32, 4, 4),
)
LARGE = (
    (64, 32, 32, 2, 5),
    (64, 128, 32, 4, 4),
    (64, 256, 32, 4, 4),
    (128, 128, 32, 4, 4),
    (128, 256, 32, 8, 3),
)


def sync() -> None:
    torch_device_fn.synchronize()


def run(x: torch.Tensor, w: torch.Tensor, cfg: tuple[int, ...]) -> torch.Tensor:
    bm, bn, bk, warps, stages = cfg
    m = x.shape[0]
    out = torch.empty((m, N), device=x.device, dtype=x.dtype)
    linear_kernel.jit_function[(triton.cdiv(m, bm), triton.cdiv(N, bn))](
        x, w, w, out, m, N, K,
        x.stride(0), x.stride(1), w.stride(0), w.stride(1),
        out.stride(0), out.stride(1), 0,
        BIAS=False,
        BLOCK_SIZE_M=bm, BLOCK_SIZE_N=bn, BLOCK_SIZE_K=bk,
        num_warps=warps, num_stages=stages,
    )
    return out


def measure(fn) -> tuple[dict[str, float], torch.Tensor]:
    out = fn()
    for _ in range(3):
        out = fn()
    sync()
    samples = []
    for _ in range(30):
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


def name(cfg: tuple[int, ...]) -> str:
    return "bm%d-bn%d-bk%d-w%d-s%d" % cfg


def compare(ref: torch.Tensor, out: torch.Tensor) -> dict[str, object]:
    delta = (ref - out).abs()
    return {
        "exact": bool(torch.equal(ref, out)),
        "max_abs_diff": float(delta.max().item()),
        "top8_equal_fraction": float(
            (ref.topk(8, dim=-1).indices == out.topk(8, dim=-1).indices)
            .all(dim=-1).float().mean().item()
        ),
    }


def main() -> None:
    torch.manual_seed(20260916)
    dev = torch.device("cuda")
    w = torch.randn((N, K), device=dev, dtype=torch.float32)
    result = {}
    for m in (1, 16, 256, 2048):
        x = torch.randn((m, K), device=dev, dtype=torch.float32)
        configs = SMALL if m <= 16 else LARGE
        base_cfg = configs[0]
        base_timing, ref = measure(lambda: run(x, w, base_cfg))
        row = {"baseline_config": name(base_cfg), "baseline": base_timing, "configs": {}}
        print(f"M={m} baseline {base_timing['median_us']:.3f} us", file=sys.stderr, flush=True)
        for cfg in configs:
            timing, out = measure(lambda c=cfg: run(x, w, c))
            row["configs"][name(cfg)] = {
                "timing": timing,
                "speedup": base_timing["median_us"] / timing["median_us"],
                "correctness": compare(ref, out),
            }
            print(f"M={m} {name(cfg)} {timing['median_us']:.3f} us", file=sys.stderr, flush=True)
        result[str(m)] = row
    print(json.dumps({"shape": {"K": K, "N": N}, "results": result}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
