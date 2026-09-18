#!/usr/bin/env python3
"""A/B the current Hy4 W8A8 MoE config against a stage-aware GEMM2 config.

This is a diagnostic single-operator benchmark.  It deliberately changes the
module's plain-half config tuple only around the candidate calls, which makes
the existing fused_experts_impl select its already-supported gemm2 config
without changing the checked-out FlagGems source.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time

import torch

import flag_gems.fused.fused_moe as fm
from flag_gems.runtime import torch_device_fn


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m", type=int, default=2048)
    parser.add_argument("--experts", type=int, default=256)
    parser.add_argument("--hidden", type=int, default=6144)
    parser.add_argument("--local-intermediate", type=int, default=128)
    parser.add_argument("--topk", type=int, default=8)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--iterations", type=int, default=20)
    return parser.parse_args()


def synchronize() -> None:
    torch_device_fn.synchronize()


def run_once(kwargs: dict[str, object], candidate: bool) -> torch.Tensor:
    original = fm._PLAIN_HALF_CONFIG_DTYPES
    try:
        if candidate:
            fm._PLAIN_HALF_CONFIG_DTYPES = original + ("int8_w8a8",)
        return fm.fused_experts_impl(**kwargs)
    finally:
        fm._PLAIN_HALF_CONFIG_DTYPES = original


def measure(kwargs: dict[str, object], candidate: bool, warmup: int, iterations: int) -> list[float]:
    for _ in range(warmup):
        run_once(kwargs, candidate)
    synchronize()
    samples: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        run_once(kwargs, candidate)
        synchronize()
        samples.append((time.perf_counter() - start) * 1000.0)
    return samples


def summarize(samples: list[float]) -> dict[str, float]:
    ordered = sorted(samples)
    return {
        "mean_ms": statistics.fmean(samples),
        "median_ms": statistics.median(samples),
        "min_ms": ordered[0],
        "max_ms": ordered[-1],
        "p90_ms": ordered[max(0, int(len(ordered) * 0.9) - 1)],
    }


def main() -> None:
    args = parse_args()
    torch.manual_seed(20260916)
    device = torch.device("cuda")
    w1_n = args.local_intermediate * 2

    hidden_states = torch.randn(
        (args.m, args.hidden), device=device, dtype=torch.bfloat16
    )
    # Weight values do not affect launch geometry; zeros make setup deterministic.
    w1 = torch.zeros(
        (args.experts, w1_n, args.hidden), device=device, dtype=torch.int8
    )
    w2 = torch.zeros(
        (args.experts, args.hidden, args.local_intermediate),
        device=device,
        dtype=torch.int8,
    )
    w1_scale = torch.ones(
        (args.experts, w1_n, 1), device=device, dtype=torch.float32
    )
    w2_scale = torch.ones(
        (args.experts, args.hidden, 1), device=device, dtype=torch.float32
    )
    row = torch.arange(args.m, device=device, dtype=torch.int64).view(-1, 1)
    lane = torch.arange(args.topk, device=device, dtype=torch.int64).view(1, -1)
    topk_ids = ((row * args.topk + lane * 31) % args.experts).to(torch.int32)
    topk_weights = torch.full(
        (args.m, args.topk),
        1.0 / args.topk,
        device=device,
        dtype=torch.float32,
    )
    kwargs: dict[str, object] = {
        "hidden_states": hidden_states,
        "w1": w1,
        "w2": w2,
        "topk_weights": topk_weights,
        "topk_ids": topk_ids,
        "inplace": False,
        "activation": "silu",
        "apply_router_weight_on_input": False,
        "use_int8_w8a8": True,
        "per_channel_quant": True,
        "global_num_experts": args.experts,
        "w1_scale": w1_scale,
        "w2_scale": w2_scale,
    }

    baseline_out = run_once(kwargs, False)
    candidate_out = run_once(kwargs, True)
    synchronize()
    diff = (baseline_out.float() - candidate_out.float()).abs()

    # Interleave the two variants to reduce temperature/order bias.
    baseline_samples: list[float] = []
    candidate_samples: list[float] = []
    for round_index in range(4):
        if round_index % 2 == 0:
            baseline_samples.extend(measure(kwargs, False, args.warmup, args.iterations))
            candidate_samples.extend(measure(kwargs, True, args.warmup, args.iterations))
        else:
            candidate_samples.extend(measure(kwargs, True, args.warmup, args.iterations))
            baseline_samples.extend(measure(kwargs, False, args.warmup, args.iterations))

    baseline = summarize(baseline_samples)
    candidate = summarize(candidate_samples)
    result = {
        "shape": {
            "M": args.m,
            "E": args.experts,
            "K": args.hidden,
            "local_intermediate": args.local_intermediate,
            "topk": args.topk,
            "w1": list(w1.shape),
            "w2": list(w2.shape),
        },
        "device_name": fm._get_device_name(),
        "gemm1_config": fm.try_get_optimal_moe_config(
            tuple(w1.shape), tuple(w2.shape), args.topk, "int8_w8a8", args.m,
            args.experts, gemm_stage="gemm1"
        ),
        "gemm2_config": fm.try_get_optimal_moe_config(
            tuple(w1.shape), tuple(w2.shape), args.topk, "int8_w8a8", args.m,
            args.experts, gemm_stage="gemm2"
        ),
        "baseline": baseline,
        "candidate": candidate,
        "speedup_mean": baseline["mean_ms"] / candidate["mean_ms"],
        "speedup_median": baseline["median_ms"] / candidate["median_ms"],
        "correctness": {
            "exact": bool(torch.equal(baseline_out, candidate_out)),
            "max_abs_diff": float(diff.max().item()),
            "mean_abs_diff": float(diff.mean().item()),
        },
        "sample_count_per_variant": len(baseline_samples),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
