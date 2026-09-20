#!/usr/bin/env python3
"""Sweep T-Head W8A8 MoE tiles that trade expert padding for launch count."""

from __future__ import annotations

import argparse
import json
import statistics
import time

import torch

from flaggems_vllm.ops.moe_align_block_size import moe_align_block_size_no_tle
from flaggems_vllm.runtime.backend._thead.ops import fused_moe as fm


M, E, HIDDEN, LOCAL_I, TOPK = 2048, 256, 6144, 128, 8


def cfg(
    bm: int,
    bn1: int = 128,
    bn2: int = 128,
    bk1: int = 64,
    bk2: int = 64,
    gm: int = 1,
    warps: int = 4,
    stages: int = 3,
):
    common = {
        "BLOCK_SIZE_M": bm,
        "GROUP_SIZE_M": gm,
        "num_warps": warps,
        "num_stages": stages,
        "USE_INT32_OFFSETS": False,
    }
    c1 = dict(common, BLOCK_SIZE_N=bn1, BLOCK_SIZE_K=bk1)
    c2 = dict(common, BLOCK_SIZE_N=bn2, BLOCK_SIZE_K=bk2)
    return c1, c2


CANDIDATES = [
    ("bm64_current", *cfg(64)),
    ("bm64_bn2_256", *cfg(64, bn2=256)),
    ("bm64_bk32", *cfg(64, bk1=32, bk2=32)),
    ("bm32", *cfg(32)),
    ("bm32_bn2_256", *cfg(32, bn2=256)),
    ("bm32_bn1_64", *cfg(32, bn1=64)),
    ("bm32_bn1_256", *cfg(32, bn1=256)),
    ("bm32_bk32", *cfg(32, bk1=32, bk2=32)),
    ("bm32_bk128", *cfg(32, bk1=128, bk2=128)),
    ("bm32_gm4", *cfg(32, gm=4)),
    ("bm32_gm8", *cfg(32, gm=8)),
    ("bm16", *cfg(16)),
    ("bm16_bn2_256", *cfg(16, bn2=256)),
    ("bm32_bk1_128", *cfg(32, bk1=128)),
    ("bm32_bk2_128", *cfg(32, bk2=128)),
    ("bm32_bk128_gm4", *cfg(32, bk1=128, bk2=128, gm=4)),
    ("bm32_bk128_gm8", *cfg(32, bk1=128, bk2=128, gm=8)),
    ("bm32_bk128_bn1_256", *cfg(32, bn1=256, bk1=128, bk2=128)),
    ("bm32_bk128_bn2_256", *cfg(32, bn2=256, bk1=128, bk2=128)),
    ("bm32_bk128_stages2", *cfg(32, bk1=128, bk2=128, stages=2)),
    ("bm32_bk128_stages4", *cfg(32, bk1=128, bk2=128, stages=4)),
    ("bm32_bk128_warps8", *cfg(32, bk1=128, bk2=128, warps=8)),
]


def synchronize() -> None:
    torch.cuda.synchronize()


def build_inputs() -> dict[str, object]:
    torch.manual_seed(20260919)
    hidden = torch.randn((M, HIDDEN), device="cuda", dtype=torch.bfloat16)
    w1 = torch.randint(-8, 9, (E, 2 * LOCAL_I, HIDDEN), device="cuda", dtype=torch.int8)
    w2 = torch.randint(-8, 9, (E, HIDDEN, LOCAL_I), device="cuda", dtype=torch.int8)
    topk_ids = torch.randint(0, E, (M, TOPK), device="cuda", dtype=torch.int32)
    topk_weights = torch.rand((M, TOPK), device="cuda", dtype=torch.float32)
    topk_weights /= topk_weights.sum(dim=-1, keepdim=True)
    return {
        "hidden_states": hidden,
        "w1": w1,
        "w2": w2,
        "topk_weights": topk_weights.contiguous(),
        "topk_ids": topk_ids.contiguous(),
        "inplace": False,
        "activation": "silu",
        "apply_router_weight_on_input": False,
        "use_fp8_w8a8": False,
        "use_int8_w8a8": True,
        "use_int8_w8a16": False,
        "use_int4_w4a16": False,
        "per_channel_quant": True,
        "global_num_experts": E,
        "expert_map": None,
        "w1_scale": torch.full((E, 2 * LOCAL_I, 1), 0.01, device="cuda"),
        "w2_scale": torch.full((E, HIDDEN, 1), 0.01, device="cuda"),
        "a1_scale": None,
        "a2_scale": None,
        "block_shape": None,
        "w1_bias": None,
        "w2_bias": None,
    }


def call(kwargs: dict[str, object], c1: dict | None = None, c2: dict | None = None):
    if c1 is None:
        return fm.fused_experts_impl(**kwargs)
    original_get = fm.try_get_optimal_moe_config
    original_dispatch = fm.dispatch_fused_moe_kernel

    def override_get(*args, **call_kwargs):
        result = dict(c1)
        return (result, False) if call_kwargs.get("return_is_embedded", False) else result

    def override_dispatch(
        A, B, C, A_scale, B_scale, B_zp, topk_weights,
        sorted_token_ids, expert_ids, num_tokens_post_padded,
        mul_routed_weight, top_k, config, compute_type, **call_kwargs,
    ):
        chosen = c2 if B.size(1) == HIDDEN else c1
        return original_dispatch(
            A, B, C, A_scale, B_scale, B_zp, topk_weights,
            sorted_token_ids, expert_ids, num_tokens_post_padded,
            mul_routed_weight, top_k, dict(chosen), compute_type, **call_kwargs,
        )

    try:
        fm.try_get_optimal_moe_config = override_get
        fm.dispatch_fused_moe_kernel = override_dispatch
        return fm.fused_experts_impl(**kwargs)
    finally:
        fm.dispatch_fused_moe_kernel = original_dispatch
        fm.try_get_optimal_moe_config = original_get


def measure(kwargs, c1=None, c2=None, warmup=4, iterations=30):
    for _ in range(warmup):
        output = call(kwargs, c1, c2)
    synchronize()
    samples = []
    for _ in range(iterations):
        start = time.perf_counter()
        output = call(kwargs, c1, c2)
        synchronize()
        samples.append((time.perf_counter() - start) * 1000.0)
    return {
        "median_ms": statistics.median(samples),
        "mean_ms": statistics.fmean(samples),
        "min_ms": min(samples),
        "max_ms": max(samples),
    }, output


def padded_rows(topk_ids: torch.Tensor, block_m: int) -> int:
    _, _, count = moe_align_block_size_no_tle(topk_ids, block_m, E, None)
    synchronize()
    return int(count.item())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    kwargs = build_inputs()
    reference = call(kwargs)
    synchronize()
    baseline_before, _ = measure(kwargs, warmup=6, iterations=40)
    rows = []
    for name, c1, c2 in CANDIDATES:
        try:
            timing, output = measure(kwargs, c1, c2)
            diff = (reference.float() - output.float()).abs()
            padded = padded_rows(kwargs["topk_ids"], c1["BLOCK_SIZE_M"])
            row = {
                "name": name,
                "gemm1": c1,
                "gemm2": c2,
                "timing": timing,
                "speedup_vs_baseline_before": baseline_before["median_ms"] / timing["median_ms"],
                "valid_routed_rows": M * TOPK,
                "padded_rows": padded,
                "padding_ratio": padded / (M * TOPK),
                "exact": bool(torch.equal(reference, output)),
                "max_abs_diff": float(diff.max().item()),
            }
        except Exception as exc:
            row = {"name": name, "gemm1": c1, "gemm2": c2, "error": repr(exc)}
        rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
    baseline_after, _ = measure(kwargs, warmup=4, iterations=40)
    report = {
        "shape": {"M": M, "E": E, "hidden": HIDDEN, "local_i": LOCAL_I, "topk": TOPK},
        "baseline_before": baseline_before,
        "baseline_after": baseline_after,
        "candidates": rows,
    }
    with open(args.output, "x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"output": args.output, "baseline_before": baseline_before, "baseline_after": baseline_after}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
