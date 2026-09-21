#!/usr/bin/env python3
"""Benchmark int32 address offsets for the trace-observed HY4 scaled-MM shapes."""

from __future__ import annotations

import argparse
import importlib
import json
import statistics
from pathlib import Path

import torch
import triton
import triton.language as tl

from flag_gems.ops.scaled_mm import scaled_mm_kernel
from flag_gems.utils import libentry
from flag_gems.utils import triton_lang_extension as tle


SHAPES = (
    (2048, 6144, 2048),
    (2029, 6144, 2048),
    (2048, 2048, 6144),
    (2029, 2048, 6144),
    (2048, 6144, 576),
    (2029, 6144, 576),
)
scaled_mm_op = importlib.import_module("flag_gems.ops.scaled_mm")
WARMUP = 3
RUNS = 4
REPEATS = 5


@libentry()
@triton.jit
def scaled_mm_int32_offsets_kernel(
    A,
    B,
    ScaleA,
    ScaleB,
    C,
    M: tl.constexpr,
    N: tl.constexpr,
    K: tl.constexpr,
    stride_am: tl.constexpr,
    stride_ak: tl.constexpr,
    stride_bk: tl.constexpr,
    stride_bn: tl.constexpr,
    stride_cm: tl.constexpr,
    stride_cn: tl.constexpr,
    BLOCK_M: tl.constexpr,
    BLOCK_N: tl.constexpr,
    BLOCK_K: tl.constexpr,
    GROUP_M: tl.constexpr,
    EVEN_K: tl.constexpr,
):
    pid = tle.program_id(0)
    grid_m = tl.cdiv(M, BLOCK_M)
    grid_n = tl.cdiv(N, BLOCK_N)
    width = GROUP_M * grid_n
    group_id = pid // width
    group_size = min(grid_m - group_id * GROUP_M, GROUP_M)
    pid_m = group_id * GROUP_M + (pid % group_size)
    pid_n = (pid % width) // group_size

    # Trace-observed HY4 matrices are safely below the signed-int32 address
    # product limit. Keep logical offsets in int32 instead of forcing the
    # generic kernel's int64 conversions.
    offs_m = pid_m * BLOCK_M + tl.arange(0, BLOCK_M)
    offs_n = pid_n * BLOCK_N + tl.arange(0, BLOCK_N)
    offs_k = tl.arange(0, BLOCK_K)
    a_ptrs = A + offs_m[:, None] * stride_am + offs_k[None, :] * stride_ak
    b_ptrs = B + offs_k[:, None] * stride_bk + offs_n[None, :] * stride_bn
    acc = tl.zeros((BLOCK_M, BLOCK_N), dtype=tl.int32)
    for block_index in range(0, tl.cdiv(K, BLOCK_K)):
        if EVEN_K:
            a = tl.load(a_ptrs, mask=offs_m[:, None] < M, other=0)
            b = tl.load(b_ptrs, mask=offs_n[None, :] < N, other=0)
        else:
            remaining = K - block_index * BLOCK_K
            a = tl.load(
                a_ptrs,
                mask=(offs_m[:, None] < M) & (offs_k[None, :] < remaining),
                other=0,
            )
            b = tl.load(
                b_ptrs,
                mask=(offs_k[:, None] < remaining) & (offs_n[None, :] < N),
                other=0,
            )
        acc += tl.dot(a, b, out_dtype=tl.int32, allow_tf32=False)
        a_ptrs += BLOCK_K * stride_ak
        b_ptrs += BLOCK_K * stride_bk
    scale_a = tl.load(ScaleA + offs_m, mask=offs_m < M, other=0.0)
    scale_b = tl.load(ScaleB + offs_n, mask=offs_n < N, other=0.0)
    values = acc.to(tl.float32) * scale_a[:, None] * scale_b[None, :]
    c_ptrs = C + offs_m[:, None] * stride_cm + offs_n[None, :] * stride_cn
    tl.store(
        c_ptrs,
        values,
        mask=(offs_m[:, None] < M) & (offs_n[None, :] < N),
    )


def elapsed_us(fn):
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")
    torch.manual_seed(20260920)
    rows = []
    for m, k, n in SHAPES:
        a = torch.randint(-127, 128, (m, k), device="cuda", dtype=torch.int8)
        # Match the transposed linear-weight layout used by vLLM.
        b_storage = torch.randint(-127, 128, (n, k), device="cuda", dtype=torch.int8)
        b = b_storage.t()
        scale_a = torch.rand((m,), device="cuda", dtype=torch.float32) * 0.02
        scale_b = torch.rand((n,), device="cuda", dtype=torch.float32) * 0.02
        expected = torch.empty((m, n), device="cuda", dtype=torch.bfloat16)
        actual = torch.empty_like(expected)

        def baseline():
            return scaled_mm_op.scaled_mm_out(
                a,
                b,
                scale_a,
                scale_b,
                out_dtype=torch.bfloat16,
                out=expected,
            )

        baseline()
        torch.cuda.synchronize()
        config = scaled_mm_kernel.fn.best_config.all_kwargs()
        block_m = config["BLOCK_M"]
        block_n = config["BLOCK_N"]
        block_k = config["BLOCK_K"]
        grid = (triton.cdiv(m, block_m) * triton.cdiv(n, block_n),)

        def candidate():
            scaled_mm_int32_offsets_kernel[grid](
                a,
                b,
                scale_a,
                scale_b,
                actual,
                m,
                n,
                k,
                a.stride(0),
                a.stride(1),
                b.stride(0),
                b.stride(1),
                actual.stride(0),
                actual.stride(1),
                BLOCK_M=block_m,
                BLOCK_N=block_n,
                BLOCK_K=block_k,
                GROUP_M=8,
                EVEN_K=k % block_k == 0,
                num_warps=config["num_warps"],
                num_stages=config["num_stages"],
            )
            return actual

        candidate()
        torch.cuda.synchronize()
        torch.testing.assert_close(actual, expected, atol=0, rtol=0)
        baseline_samples = elapsed_us(baseline)
        candidate_samples = elapsed_us(candidate)
        baseline_median = statistics.median(baseline_samples)
        candidate_median = statistics.median(candidate_samples)
        row = {
            "M": m,
            "K": k,
            "N": n,
            "config": config,
            "baseline_samples_us": baseline_samples,
            "candidate_samples_us": candidate_samples,
            "baseline_median_us": baseline_median,
            "candidate_median_us": candidate_median,
            "speedup": baseline_median / candidate_median,
            "exact": True,
        }
        rows.append(row)
        print(json.dumps(row), flush=True)
        del a, b, b_storage, scale_a, scale_b, expected, actual

    dominant = [row for row in rows if row["M"] in (2029, 2048)]
    status = (
        "candidate"
        if min(row["speedup"] for row in dominant) >= 0.98
        and statistics.geometric_mean(row["speedup"] for row in dominant) >= 1.05
        else "rejected"
    )
    result = {
        "schema_version": 1,
        "status": status,
        "candidate": "scaled_mm_int32_logical_offsets",
        "baseline": "active_flaggems_scaled_mm",
        "threshold": "all observed shapes >=0.98x and geometric mean >=1.05x; exact output",
        "rows": rows,
        "geometric_mean_speedup": statistics.geometric_mean(
            row["speedup"] for row in dominant
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("SUMMARY=" + json.dumps(result), flush=True)
    return 0 if status == "candidate" else 2


if __name__ == "__main__":
    raise SystemExit(main())
