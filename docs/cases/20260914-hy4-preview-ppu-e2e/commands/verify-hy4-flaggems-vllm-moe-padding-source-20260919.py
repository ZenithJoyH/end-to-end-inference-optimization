#!/usr/bin/env python3
"""Validate applied T-Head W8A8 MoE stage configs, performance, and graph replay."""

from __future__ import annotations

import argparse
import json
import statistics
import time

import torch

from flaggems_vllm.ops.moe_align_block_size import moe_align_block_size_no_tle
from flaggems_vllm.runtime.backend._thead.ops import fused_moe as fm


M, E, HIDDEN, LOCAL_I, TOPK = 2048, 256, 6144, 128, 8
OLD_CONFIG = {
    "BLOCK_SIZE_M": 64,
    "BLOCK_SIZE_N": 128,
    "BLOCK_SIZE_K": 64,
    "GROUP_SIZE_M": 1,
    "num_warps": 4,
    "num_stages": 3,
    "USE_INT32_OFFSETS": False,
}


def sync() -> None:
    torch.cuda.synchronize()


def inputs() -> dict[str, object]:
    torch.manual_seed(20260919)
    hidden = torch.randn((M, HIDDEN), device="cuda", dtype=torch.bfloat16)
    w1 = torch.randint(-8, 9, (E, 2 * LOCAL_I, HIDDEN), device="cuda", dtype=torch.int8)
    w2 = torch.randint(-8, 9, (E, HIDDEN, LOCAL_I), device="cuda", dtype=torch.int8)
    ids = torch.randint(0, E, (M, TOPK), device="cuda", dtype=torch.int32)
    weights = torch.rand((M, TOPK), device="cuda", dtype=torch.float32)
    weights /= weights.sum(dim=-1, keepdim=True)
    return {
        "hidden_states": hidden,
        "w1": w1,
        "w2": w2,
        "topk_weights": weights.contiguous(),
        "topk_ids": ids.contiguous(),
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


def call(kwargs: dict[str, object], mode: str = "current"):
    original_get = fm.try_get_optimal_moe_config
    original_can_fuse = fm._can_fuse_silu_mul_int8_quant

    def old_get(*args, **call_kwargs):
        result = dict(OLD_CONFIG)
        return (result, False) if call_kwargs.get("return_is_embedded", False) else result

    try:
        if mode == "original":
            fm.try_get_optimal_moe_config = old_get
        if mode in ("original", "padding_only"):
            fm._can_fuse_silu_mul_int8_quant = lambda *args, **kwargs: False
        return fm.fused_experts_impl(**kwargs)
    finally:
        fm._can_fuse_silu_mul_int8_quant = original_can_fuse
        fm.try_get_optimal_moe_config = original_get


def sample(kwargs, mode: str) -> float:
    start = time.perf_counter()
    call(kwargs, mode=mode)
    sync()
    return (time.perf_counter() - start) * 1000.0


def stats(values: list[float]) -> dict[str, float]:
    return {
        "median_ms": statistics.median(values),
        "mean_ms": statistics.fmean(values),
        "min_ms": min(values),
        "max_ms": max(values),
    }


def padded_rows(ids: torch.Tensor, block_m: int) -> int:
    _, _, count = moe_align_block_size_no_tle(ids, block_m, E, None)
    sync()
    return int(count.item())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    kwargs = inputs()
    for _ in range(6):
        call(kwargs, mode="original")
        call(kwargs, mode="padding_only")
        call(kwargs)
    sync()

    old_output = call(kwargs, mode="original")
    padding_output = call(kwargs, mode="padding_only")
    new_output = call(kwargs)
    sync()
    old_samples, padding_samples, new_samples = [], [], []
    for index in range(100):
        order = ["original", "padding_only", "current"]
        if index % 2:
            order.reverse()
        buckets = {
            "original": old_samples,
            "padding_only": padding_samples,
            "current": new_samples,
        }
        for mode in order:
            buckets[mode].append(sample(kwargs, mode))

    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        captured = call(kwargs)
    graph.replay()
    sync()
    replay1 = captured.clone()
    graph.replay()
    sync()
    replay2 = captured.clone()

    old_timing = stats(old_samples)
    padding_timing = stats(padding_samples)
    new_timing = stats(new_samples)
    gemm1_config = fm.get_default_config(2048, 256, 256, 6144, 8, "int8_w8a8")
    gemm2_config = fm.get_default_config(
        2048, 256, 6144, 128, 8, "int8_w8a8", gemm_stage="gemm2"
    )
    report = {
        "shape": "M2048/E256/TopK8/H6144/localI128",
        "old_config": OLD_CONFIG,
        "gemm1_config": gemm1_config,
        "gemm2_config": gemm2_config,
        "old_timing": old_timing,
        "padding_only_timing": padding_timing,
        "new_timing": new_timing,
        "speedup_median": old_timing["median_ms"] / new_timing["median_ms"],
        "fusion_incremental_speedup_median": padding_timing["median_ms"] / new_timing["median_ms"],
        "old_vs_new_exact": bool(torch.equal(old_output, new_output)),
        "padding_vs_new_exact": bool(torch.equal(padding_output, new_output)),
        "old_vs_new_max_abs_diff": float((old_output.float() - new_output.float()).abs().max().item()),
        "graph_capture": "passed",
        "graph_replays": 2,
        "eager_vs_replay1_exact": bool(torch.equal(new_output, replay1)),
        "replay1_vs_replay2_exact": bool(torch.equal(replay1, replay2)),
        "bm64_padded_rows": padded_rows(kwargs["topk_ids"], 64),
        "bm32_padded_rows": padded_rows(kwargs["topk_ids"], 32),
        "valid_routed_rows": M * TOPK,
    }
    with open(args.output, "x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
