#!/usr/bin/env python3
"""Compare the current FlagGems FP32 router linear with native torch.mm."""

from __future__ import annotations

import json
import statistics
import time

import torch

from flag_gems.ops.linear import linear as flaggems_linear
from flag_gems.runtime import torch_device_fn


K, N = 6144, 256


def sync() -> None:
    torch_device_fn.synchronize()


def summarize(samples: list[float]) -> dict[str, float]:
    return {
        "mean_us": statistics.fmean(samples),
        "median_us": statistics.median(samples),
        "min_us": min(samples),
        "max_us": max(samples),
    }


def measure(fn, x: torch.Tensor, w: torch.Tensor) -> tuple[dict[str, float], torch.Tensor]:
    output = fn(x, w)
    for _ in range(8):
        output = fn(x, w)
    sync()
    samples: list[float] = []
    for _ in range(100):
        start = time.perf_counter()
        output = fn(x, w)
        sync()
        samples.append((time.perf_counter() - start) * 1_000_000)
    return summarize(samples), output


def diff(reference: torch.Tensor, candidate: torch.Tensor) -> dict[str, object]:
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


def main() -> None:
    torch.manual_seed(20260916)
    device = torch.device("cuda")
    w = torch.randn((N, K), device=device, dtype=torch.float32)
    results: dict[str, object] = {}
    for m in (1, 16, 64, 128, 256, 512, 1024, 2048):
        x = torch.randn((m, K), device=device, dtype=torch.float32)
        baseline_timing, baseline = measure(
            lambda a, b: flaggems_linear(a, b), x, w
        )
        mm_timing, mm_output = measure(lambda a, b: torch.mm(a, b.T), x, w)
        matmul_timing, matmul_output = measure(lambda a, b: a @ b.T, x, w)
        results[str(m)] = {
            "baseline_flaggems_linear": baseline_timing,
            "torch_mm": mm_timing,
            "torch_matmul": matmul_timing,
            "speedup_mm": baseline_timing["median_us"] / mm_timing["median_us"],
            "speedup_matmul": baseline_timing["median_us"] / matmul_timing["median_us"],
            "mm_correctness": diff(baseline, mm_output),
            "matmul_correctness": diff(baseline, matmul_output),
        }
    print(json.dumps({"shape": {"K": K, "N": N}, "results": results}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
