#!/usr/bin/env python3
"""Repeatable current-vs-4-warp full MoE benchmark for one token shape."""

from __future__ import annotations

import argparse
import json
import statistics
import time

import torch

import flag_gems.fused.fused_moe as fm
from flag_gems.runtime import torch_device_fn


E, HIDDEN, LOCAL_I, TOPK = 256, 6144, 128, 8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m", type=int, required=True)
    parser.add_argument("--rounds", type=int, default=6)
    parser.add_argument("--iterations", type=int, default=20)
    return parser.parse_args()


def sync() -> None:
    torch_device_fn.synchronize()


def candidate_config(m: int, stage: str) -> dict[str, int]:
    config = fm.try_get_optimal_moe_config(
        (E, 2 * LOCAL_I, HIDDEN),
        (E, HIDDEN, LOCAL_I),
        TOPK,
        "int8_w8a8",
        m,
        E,
        gemm_stage=stage,
    )
    config["num_warps"] = 4
    # Keep the current shared BLOCK_N=128 behavior; stage2 BN256 was negative.
    if stage == "gemm2":
        config["BLOCK_SIZE_N"] = fm.try_get_optimal_moe_config(
            (E, 2 * LOCAL_I, HIDDEN),
            (E, HIDDEN, LOCAL_I),
            TOPK,
            "int8_w8a8",
            m,
            E,
            gemm_stage="gemm1",
        )["BLOCK_SIZE_N"]
    return config


def call(kwargs: dict[str, object], m: int, candidate: bool) -> torch.Tensor:
    if not candidate:
        return fm.fused_experts_impl(**kwargs)
    c1 = candidate_config(m, "gemm1")
    c2 = candidate_config(m, "gemm2")
    original_dtypes = fm._PLAIN_HALF_CONFIG_DTYPES
    original_get = fm.try_get_optimal_moe_config

    def override(*args: object, **kw: object):
        chosen = c2 if kw.get("gemm_stage", "gemm1") == "gemm2" else c1
        result = dict(chosen)
        return (result, False) if kw.get("return_is_embedded", False) else result

    try:
        fm._PLAIN_HALF_CONFIG_DTYPES = original_dtypes + ("int8_w8a8",)
        fm.try_get_optimal_moe_config = override
        return fm.fused_experts_impl(**kwargs)
    finally:
        fm.try_get_optimal_moe_config = original_get
        fm._PLAIN_HALF_CONFIG_DTYPES = original_dtypes


def sample(kwargs: dict[str, object], m: int, candidate: bool, iterations: int) -> list[float]:
    for _ in range(3):
        call(kwargs, m, candidate)
    sync()
    samples: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        call(kwargs, m, candidate)
        sync()
        samples.append((time.perf_counter() - start) * 1000)
    return samples


def summary(samples: list[float]) -> dict[str, float]:
    return {
        "mean_ms": statistics.fmean(samples),
        "median_ms": statistics.median(samples),
        "min_ms": min(samples),
        "max_ms": max(samples),
    }


def main() -> None:
    args = parse_args()
    torch.manual_seed(20260916 + args.m)
    device = torch.device("cuda")
    hidden = torch.randn((args.m, HIDDEN), device=device, dtype=torch.bfloat16)
    w1 = torch.randint(-8, 9, (E, 2 * LOCAL_I, HIDDEN), device=device, dtype=torch.int8)
    w2 = torch.randint(-8, 9, (E, HIDDEN, LOCAL_I), device=device, dtype=torch.int8)
    topk_ids = torch.randint(0, E, (args.m, TOPK), device=device, dtype=torch.int32)
    topk_weights = torch.rand((args.m, TOPK), device=device, dtype=torch.float32)
    topk_weights /= topk_weights.sum(dim=-1, keepdim=True)
    kwargs: dict[str, object] = {
        "hidden_states": hidden,
        "w1": w1,
        "w2": w2,
        "topk_weights": topk_weights.contiguous(),
        "topk_ids": topk_ids.contiguous(),
        "inplace": False,
        "activation": "silu",
        "apply_router_weight_on_input": False,
        "use_int8_w8a8": True,
        "per_channel_quant": True,
        "global_num_experts": E,
        "w1_scale": torch.full((E, 2 * LOCAL_I, 1), 0.01, device=device),
        "w2_scale": torch.full((E, HIDDEN, 1), 0.01, device=device),
    }
    reference = call(kwargs, args.m, False)
    candidate_output = call(kwargs, args.m, True)
    sync()
    diff = (reference.float() - candidate_output.float()).abs()
    baseline_samples: list[float] = []
    candidate_samples: list[float] = []
    for round_index in range(args.rounds):
        order = (False, True) if round_index % 2 == 0 else (True, False)
        for use_candidate in order:
            target = candidate_samples if use_candidate else baseline_samples
            target.extend(sample(kwargs, args.m, use_candidate, args.iterations))
    baseline = summary(baseline_samples)
    candidate = summary(candidate_samples)
    print(json.dumps({
        "M": args.m,
        "device_name": fm._get_device_name(),
        "baseline": baseline,
        "candidate": candidate,
        "speedup_mean": baseline["mean_ms"] / candidate["mean_ms"],
        "speedup_median": baseline["median_ms"] / candidate["median_ms"],
        "gemm1_candidate": candidate_config(args.m, "gemm1"),
        "gemm2_candidate": candidate_config(args.m, "gemm2"),
        "correctness": {
            "exact": bool(torch.equal(reference, candidate_output)),
            "max_abs_diff": float(diff.max().item()),
            "mean_abs_diff": float(diff.mean().item()),
        },
        "samples_per_variant": len(baseline_samples),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
