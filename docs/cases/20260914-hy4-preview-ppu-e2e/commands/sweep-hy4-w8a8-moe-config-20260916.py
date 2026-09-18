#!/usr/bin/env python3
"""Finite full-operator tile sweep for the dominant Hy4 W8A8 MoE shape."""

from __future__ import annotations

import json
import statistics
import time

import torch

import flag_gems.fused.fused_moe as fm
from flag_gems.runtime import torch_device_fn


M, E, HIDDEN, LOCAL_I, TOPK = 2048, 256, 6144, 128, 8
BASE1 = {
    "BLOCK_SIZE_M": 64,
    "BLOCK_SIZE_N": 128,
    "BLOCK_SIZE_K": 64,
    "GROUP_SIZE_M": 1,
    "num_warps": 8,
    "num_stages": 3,
}
BASE2 = dict(BASE1)


def sync() -> None:
    torch_device_fn.synchronize()


def config(**updates: int) -> dict[str, int]:
    result = dict(BASE1)
    result.update(updates)
    return result


CANDIDATES: list[tuple[str, dict[str, int], dict[str, int]]] = [
    ("stage2_bn256", BASE1, config(BLOCK_SIZE_N=256)),
    ("both_warps4", config(num_warps=4), config(num_warps=4)),
    ("gemm1_warps4", config(num_warps=4), BASE2),
    ("gemm2_warps4", BASE1, config(num_warps=4)),
    ("both_stages2", config(num_stages=2), config(num_stages=2)),
    ("gemm1_stages2", config(num_stages=2), BASE2),
    ("gemm2_stages2", BASE1, config(num_stages=2)),
    ("both_stages4", config(num_stages=4), config(num_stages=4)),
    ("gemm1_stages4", config(num_stages=4), BASE2),
    ("gemm2_stages4", BASE1, config(num_stages=4)),
    ("both_bm32", config(BLOCK_SIZE_M=32), config(BLOCK_SIZE_M=32)),
    ("gemm1_bm32", config(BLOCK_SIZE_M=32), BASE2),
    ("gemm2_bm32", BASE1, config(BLOCK_SIZE_M=32)),
    ("both_bm128", config(BLOCK_SIZE_M=128), config(BLOCK_SIZE_M=128)),
    ("gemm1_bm128", config(BLOCK_SIZE_M=128), BASE2),
    ("gemm2_bm128", BASE1, config(BLOCK_SIZE_M=128)),
    ("both_bk128", config(BLOCK_SIZE_K=128), config(BLOCK_SIZE_K=128)),
    ("gemm1_bk128", config(BLOCK_SIZE_K=128), BASE2),
    ("gemm2_bk128", BASE1, config(BLOCK_SIZE_K=128)),
    ("gemm1_bn64", config(BLOCK_SIZE_N=64), BASE2),
    ("gemm2_bn64", BASE1, config(BLOCK_SIZE_N=64)),
    ("both_group8", config(GROUP_SIZE_M=8), config(GROUP_SIZE_M=8)),
    ("gemm1_group8", config(GROUP_SIZE_M=8), BASE2),
    ("gemm2_group8", BASE1, config(GROUP_SIZE_M=8)),
]


def build_inputs() -> dict[str, object]:
    torch.manual_seed(20260916)
    device = torch.device("cuda")
    hidden = torch.randn((M, HIDDEN), device=device, dtype=torch.bfloat16)
    w1 = torch.randint(-8, 9, (E, 2 * LOCAL_I, HIDDEN), device=device, dtype=torch.int8)
    w2 = torch.randint(-8, 9, (E, HIDDEN, LOCAL_I), device=device, dtype=torch.int8)
    w1_scale = torch.full((E, 2 * LOCAL_I, 1), 0.01, device=device, dtype=torch.float32)
    w2_scale = torch.full((E, HIDDEN, 1), 0.01, device=device, dtype=torch.float32)
    # Multinomial routing approximates the padding pressure of a live router.
    topk_ids = torch.randint(0, E, (M, TOPK), device=device, dtype=torch.int32)
    topk_weights = torch.rand((M, TOPK), device=device, dtype=torch.float32)
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
        "use_int8_w8a8": True,
        "per_channel_quant": True,
        "global_num_experts": E,
        "w1_scale": w1_scale,
        "w2_scale": w2_scale,
    }


def call(kwargs: dict[str, object], configs: tuple[dict[str, int], dict[str, int]] | None) -> torch.Tensor:
    if configs is None:
        return fm.fused_experts_impl(**kwargs)
    c1, c2 = configs
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


def measure(kwargs: dict[str, object], configs: tuple[dict[str, int], dict[str, int]] | None, warmup: int = 3, iterations: int = 20) -> tuple[dict[str, float], torch.Tensor]:
    output = call(kwargs, configs)
    for _ in range(warmup):
        output = call(kwargs, configs)
    sync()
    samples: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        output = call(kwargs, configs)
        sync()
        samples.append((time.perf_counter() - start) * 1000.0)
    return {
        "mean_ms": statistics.fmean(samples),
        "median_ms": statistics.median(samples),
        "min_ms": min(samples),
        "max_ms": max(samples),
    }, output


def main() -> None:
    kwargs = build_inputs()
    reference = call(kwargs, None)
    sync()
    baseline_before, _ = measure(kwargs, None, warmup=5, iterations=30)
    results: list[dict[str, object]] = []
    for name, c1, c2 in CANDIDATES:
        try:
            timing, output = measure(kwargs, (c1, c2))
            diff = (reference.float() - output.float()).abs()
            row = {
                "name": name,
                "gemm1": c1,
                "gemm2": c2,
                "timing": timing,
                "speedup_vs_baseline_before": baseline_before["median_ms"] / timing["median_ms"],
                "max_abs_diff": float(diff.max().item()),
                "mean_abs_diff": float(diff.mean().item()),
            }
        except Exception as exc:
            row = {"name": name, "error": repr(exc), "gemm1": c1, "gemm2": c2}
        results.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
    baseline_after, _ = measure(kwargs, None, warmup=3, iterations=30)
    payload = {
        "device_name": fm._get_device_name(),
        "shape": {"M": M, "E": E, "hidden": HIDDEN, "local_intermediate": LOCAL_I, "topk": TOPK},
        "baseline_before": baseline_before,
        "baseline_after": baseline_after,
        "results": results,
    }
    print("FINAL_JSON")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
