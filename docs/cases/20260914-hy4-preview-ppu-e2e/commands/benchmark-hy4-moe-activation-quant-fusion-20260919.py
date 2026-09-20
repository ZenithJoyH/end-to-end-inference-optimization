#!/usr/bin/env python3
"""Benchmark exact SiLU-mul plus per-token INT8 quant fusion for Hy4 MoE."""

from __future__ import annotations

import argparse
import json
import statistics
import time

import torch
import triton
import triton.language as tl
import triton.language.extra.libdevice as libdevice

from flaggems_vllm.runtime.backend._thead.ops import fused_moe as fm


@triton.jit
def fused_silu_mul_quant_kernel(
    input_ptr,
    output_ptr,
    scale_ptr,
    hidden_size: tl.constexpr,
    BLOCK_SIZE: tl.constexpr,
):
    row = tl.program_id(0)
    offsets = tl.arange(0, BLOCK_SIZE)
    mask = offsets < hidden_size
    base = row * hidden_size * 2
    gate = tl.load(input_ptr + base + offsets, mask=mask, other=0.0).to(tl.float32)
    up = tl.load(input_ptr + base + hidden_size + offsets, mask=mask, other=0.0)
    activated = (tl.fdiv(gate, 1.0 + tl.exp(-gate)) * up).to(tl.bfloat16).to(tl.float32)
    absmax = tl.maximum(tl.max(tl.abs(activated), axis=0), 1e-10)
    scale = absmax / 127.0
    quantized = libdevice.rint(libdevice.div_rn(activated, scale))
    quantized = tl.minimum(tl.maximum(quantized, -128.0), 127.0)
    tl.store(output_ptr + row * hidden_size + offsets, quantized.to(tl.int8), mask=mask)
    tl.store(scale_ptr + row, scale)


def stats(values):
    return {
        "median_us": statistics.median(values),
        "mean_us": statistics.fmean(values),
        "min_us": min(values),
        "max_us": max(values),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    rows, hidden = 2048 * 8, 128
    torch.manual_seed(20260919)
    source = torch.randn((rows, hidden * 2), device="cuda", dtype=torch.bfloat16)
    intermediate = torch.empty((rows, hidden), device="cuda", dtype=torch.bfloat16)
    baseline_q = torch.empty((rows, hidden), device="cuda", dtype=torch.int8)
    baseline_scale = torch.empty((rows, 1), device="cuda", dtype=torch.float32)
    fused_q = torch.empty_like(baseline_q)
    fused_scale = torch.empty_like(baseline_scale)

    def baseline():
        fm._silu_and_mul_kernel(source[:, :hidden], source[:, hidden:], out0=intermediate)
        fm._dynamic_per_token_int8_quant_kernel[(rows,)](
            intermediate, baseline_q, baseline_scale,
            hidden_size=hidden, BLOCK_SIZE=triton.next_power_of_2(hidden),
        )

    def candidate():
        fused_silu_mul_quant_kernel[(rows,)](
            source, fused_q, fused_scale,
            hidden_size=hidden, BLOCK_SIZE=triton.next_power_of_2(hidden),
            num_warps=4, num_stages=1,
        )

    for _ in range(20):
        baseline()
        candidate()
    torch.cuda.synchronize()
    old, new = [], []
    for index in range(300):
        ordered = ((candidate, new), (baseline, old)) if index % 2 else ((baseline, old), (candidate, new))
        for fn, samples in ordered:
            start = time.perf_counter()
            fn()
            torch.cuda.synchronize()
            samples.append((time.perf_counter() - start) * 1e6)

    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        candidate()
    graph.replay()
    graph.replay()
    torch.cuda.synchronize()
    old_stats, new_stats = stats(old), stats(new)
    report = {
        "shape": [rows, hidden],
        "baseline": old_stats,
        "candidate": new_stats,
        "speedup_median": old_stats["median_us"] / new_stats["median_us"],
        "q_exact": bool(torch.equal(baseline_q, fused_q)),
        "scale_exact": bool(torch.equal(baseline_scale, fused_scale)),
        "scale_max_abs_diff": float((baseline_scale - fused_scale).abs().max().item()),
        "graph_capture": "passed",
        "graph_replays": 2,
    }
    with open(args.output, "x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
