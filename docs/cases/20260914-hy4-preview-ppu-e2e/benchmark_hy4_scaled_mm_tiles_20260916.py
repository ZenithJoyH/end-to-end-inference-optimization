#!/usr/bin/env python3
"""Sweep scaled-mm Triton tiles on the dominant Hy4 P4K Prefill shapes."""

from __future__ import annotations

import importlib
import json
import statistics
from dataclasses import dataclass

import torch
import triton
import triton.language as tl


SHAPES = (
    (2048, 6144, 256),
    (2048, 2048, 1024),
    (2048, 1024, 6144),
    (2048, 6144, 576),
    (2048, 128, 6144),
    (2048, 6144, 2048),
)
WARMUP = 3
RUNS = 5
REPEATS = 3


@dataclass(frozen=True)
class Config:
    name: str
    block_m: int
    block_n: int
    block_k: int
    num_warps: int
    num_stages: int


CONFIGS = (
    Config("existing_bm64_bn64_bk64_s4", 64, 64, 64, 4, 4),
    Config("existing_bm64_bn128_bk64_s3", 64, 128, 64, 4, 3),
    Config("existing_bm64_bn64_bk128_s3", 64, 64, 128, 4, 3),
    Config("existing_bm32_bn64_bk128_s4", 32, 64, 128, 4, 4),
    Config("bm128_bn64_bk64_s3", 128, 64, 64, 4, 3),
    Config("bm128_bn128_bk64_s3", 128, 128, 64, 4, 3),
    Config("bm64_bn256_bk64_s3", 64, 256, 64, 4, 3),
    Config("bm128_bn64_bk128_s3", 128, 64, 128, 4, 3),
    Config("bm128_bn128_bk128_s3", 128, 128, 128, 4, 3),
    Config("bm64_bn128_bk128_s3", 64, 128, 128, 4, 3),
    Config("bm128_bn128_bk64_s2", 128, 128, 64, 4, 2),
    Config("bm64_bn128_bk64_s2", 64, 128, 64, 4, 2),
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


def launch(jit_kernel, cfg: Config, a, b, scale_a, scale_b, out) -> None:
    m, k = a.shape
    n = b.shape[1]
    grid = (
        triton.cdiv(m, cfg.block_m) * triton.cdiv(n, cfg.block_n),
    )
    jit_kernel[grid](
        a,
        b,
        scale_a,
        scale_b,
        None,
        out,
        m,
        n,
        k,
        a.stride(0),
        a.stride(1),
        b.stride(0),
        b.stride(1),
        out.stride(0),
        out.stride(1),
        ACC_DTYPE=tl.int32,
        SCALE_A_MODE=1,
        SCALE_B_MODE=1,
        HAS_BIAS=False,
        BLOCK_M=cfg.block_m,
        BLOCK_N=cfg.block_n,
        BLOCK_K=cfg.block_k,
        GROUP_M=8,
        EVEN_K=(k % cfg.block_k == 0),
        num_warps=cfg.num_warps,
        num_stages=cfg.num_stages,
    )


def main() -> None:
    torch.manual_seed(20260916)
    scaled_mm_module = importlib.import_module("flag_gems.ops.scaled_mm")
    scaled_mm_out = scaled_mm_module.scaled_mm_out
    jit_kernel = scaled_mm_module.scaled_mm_kernel.fn.fn.fn
    report = {
        "schema_version": 1,
        "device": "cuda",
        "dtype": "int8_x_int8_to_bfloat16",
        "timing": {
            "warmup": WARMUP,
            "runs_per_sample": RUNS,
            "repeats": REPEATS,
        },
        "shapes": [],
    }

    for m, k, n in SHAPES:
        a = torch.randint(-127, 128, (m, k), device="cuda", dtype=torch.int8)
        b = torch.randint(-127, 128, (k, n), device="cuda", dtype=torch.int8)
        scale_a = torch.rand((m, 1), device="cuda", dtype=torch.float32) * 0.02
        scale_b = torch.rand((n,), device="cuda", dtype=torch.float32) * 0.02
        baseline_out = torch.empty((m, n), device="cuda", dtype=torch.bfloat16)
        candidate_out = torch.empty_like(baseline_out)

        def baseline() -> None:
            scaled_mm_out(
                a,
                b,
                scale_a,
                scale_b,
                out_dtype=torch.bfloat16,
                out=baseline_out,
            )

        baseline()
        torch.cuda.synchronize()
        baseline_samples = elapsed_us(baseline)
        baseline_median = statistics.median(baseline_samples)
        shape_result = {
            "M": m,
            "N": n,
            "K": k,
            "baseline_samples_us": baseline_samples,
            "baseline_median_us": baseline_median,
            "configs": [],
        }

        for cfg in CONFIGS:
            try:
                launch(jit_kernel, cfg, a, b, scale_a, scale_b, candidate_out)
                torch.cuda.synchronize()
                max_abs_diff = float(
                    (candidate_out.float() - baseline_out.float()).abs().max().item()
                )
                exact_fraction = float(
                    (candidate_out == baseline_out).float().mean().item()
                )
                samples = elapsed_us(
                    lambda cfg=cfg: launch(
                        jit_kernel,
                        cfg,
                        a,
                        b,
                        scale_a,
                        scale_b,
                        candidate_out,
                    )
                )
                median_us = statistics.median(samples)
                shape_result["configs"].append(
                    {
                        "name": cfg.name,
                        "status": "passed",
                        "samples_us": samples,
                        "median_us": median_us,
                        "speedup_vs_autotuned_baseline": baseline_median / median_us,
                        "exact_fraction": exact_fraction,
                        "max_abs_diff": max_abs_diff,
                    }
                )
            except Exception as exc:
                shape_result["configs"].append(
                    {
                        "name": cfg.name,
                        "status": "failed",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
        passed = [x for x in shape_result["configs"] if x["status"] == "passed"]
        shape_result["best"] = min(passed, key=lambda row: row["median_us"])
        report["shapes"].append(shape_result)
        del a, b, scale_a, scale_b, baseline_out, candidate_out

    print("SUMMARY=" + json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
