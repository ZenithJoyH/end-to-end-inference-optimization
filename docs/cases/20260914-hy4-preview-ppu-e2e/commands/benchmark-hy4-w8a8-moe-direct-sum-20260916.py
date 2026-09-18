#!/usr/bin/env python3
"""Compare the current PPU W8A8 MoE path with experimental direct sum."""

from __future__ import annotations

import json
import statistics
import sys
import time

import torch

import flag_gems.fused.fused_moe as fm
from flag_gems.runtime import torch_device_fn


E, HIDDEN, LOCAL_I, TOPK = 256, 6144, 128, 8


def sync() -> None:
    torch_device_fn.synchronize()


def run(kwargs: dict[str, object], direct_sum: bool) -> torch.Tensor:
    old = fm._THEAD_PPU_W8A8_DIRECT_SUM_MIN_TOKENS
    try:
        fm._THEAD_PPU_W8A8_DIRECT_SUM_MIN_TOKENS = 256 if direct_sum else sys.maxsize
        return fm.fused_experts_impl(**kwargs)
    finally:
        fm._THEAD_PPU_W8A8_DIRECT_SUM_MIN_TOKENS = old


def measure(kwargs: dict[str, object], direct_sum: bool) -> tuple[dict[str, float], torch.Tensor]:
    out = run(kwargs, direct_sum)
    for _ in range(3):
        out = run(kwargs, direct_sum)
    sync()
    samples = []
    for _ in range(40):
        start = time.perf_counter()
        out = run(kwargs, direct_sum)
        sync()
        samples.append((time.perf_counter() - start) * 1000)
    return {
        "mean_ms": statistics.fmean(samples),
        "median_ms": statistics.median(samples),
        "min_ms": min(samples),
        "max_ms": max(samples),
    }, out


def main() -> None:
    torch.manual_seed(20260916)
    device = torch.device("cuda")
    results = {}
    for m in (256, 2048):
        hidden = torch.randn((m, HIDDEN), device=device, dtype=torch.bfloat16)
        w1 = torch.randint(-8, 9, (E, 2 * LOCAL_I, HIDDEN), device=device, dtype=torch.int8)
        w2 = torch.randint(-8, 9, (E, HIDDEN, LOCAL_I), device=device, dtype=torch.int8)
        ids = torch.randint(0, E, (m, TOPK), device=device, dtype=torch.int32)
        weights = torch.rand((m, TOPK), device=device, dtype=torch.float32)
        weights /= weights.sum(dim=-1, keepdim=True)
        kwargs = {
            "hidden_states": hidden,
            "w1": w1,
            "w2": w2,
            "topk_weights": weights.contiguous(),
            "topk_ids": ids.contiguous(),
            "inplace": False,
            "activation": "silu",
            "apply_router_weight_on_input": False,
            "use_int8_w8a8": True,
            "per_channel_quant": True,
            "global_num_experts": E,
            "w1_scale": torch.full((E, 2 * LOCAL_I, 1), 0.01, device=device),
            "w2_scale": torch.full((E, HIDDEN, 1), 0.01, device=device),
        }
        baseline, reference = measure(kwargs, False)
        candidate, output = measure(kwargs, True)
        delta = (reference.float() - output.float()).abs()
        repeated = [run(kwargs, True).clone() for _ in range(3)]
        sync()
        results[str(m)] = {
            "baseline": baseline,
            "direct_sum": candidate,
            "speedup": baseline["median_ms"] / candidate["median_ms"],
            "correctness": {
                "exact": bool(torch.equal(reference, output)),
                "max_abs_diff": float(delta.max().item()),
                "mean_abs_diff": float(delta.mean().item()),
                "candidate_repeats_exact": all(torch.equal(repeated[0], x) for x in repeated[1:]),
            },
        }
    print(json.dumps({"results": results}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
