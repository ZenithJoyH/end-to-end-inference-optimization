#!/usr/bin/env python3
"""Compare the installed FlagGems-vllm paths with the validated FlagGems paths."""

from __future__ import annotations

import json
import statistics
import time

import torch

import flag_gems
import flaggems_vllm


def sync() -> None:
    torch.cuda.synchronize()


def measure(fn, warmup: int = 5, samples: int = 30) -> tuple[torch.Tensor, dict]:
    output = fn()
    for _ in range(warmup):
        output = fn()
    sync()
    timings = []
    for _ in range(samples):
        start = time.perf_counter()
        output = fn()
        sync()
        timings.append((time.perf_counter() - start) * 1000)
    return output, {
        "median_ms": statistics.median(timings),
        "mean_ms": statistics.fmean(timings),
        "min_ms": min(timings),
        "max_ms": max(timings),
    }


def main() -> None:
    torch.manual_seed(20260918)
    m, experts, hidden, local_i, topk = 2048, 256, 6144, 128, 8
    hidden_states = torch.randn((m, hidden), device="cuda", dtype=torch.bfloat16)
    w1 = torch.randint(
        -8, 9, (experts, 2 * local_i, hidden), device="cuda", dtype=torch.int8
    )
    w2 = torch.randint(
        -8, 9, (experts, hidden, local_i), device="cuda", dtype=torch.int8
    )
    topk_ids = torch.randint(
        0, experts, (m, topk), device="cuda", dtype=torch.int32
    )
    topk_weights = torch.rand((m, topk), device="cuda", dtype=torch.float32)
    topk_weights /= topk_weights.sum(dim=-1, keepdim=True)
    kwargs = {
        "hidden_states": hidden_states,
        "w1": w1,
        "w2": w2,
        "topk_weights": topk_weights.contiguous(),
        "topk_ids": topk_ids.contiguous(),
        "inplace": False,
        "activation": "silu",
        "apply_router_weight_on_input": False,
        "use_int8_w8a8": True,
        "per_channel_quant": True,
        "global_num_experts": experts,
        "w1_scale": torch.full((experts, 2 * local_i, 1), 0.01, device="cuda"),
        "w2_scale": torch.full((experts, hidden, 1), 0.01, device="cuda"),
    }

    fg_output, fg_metrics = measure(lambda: flag_gems.fused_experts_impl(**kwargs))
    fgv_output, fgv_metrics = measure(
        lambda: flaggems_vllm.fused_experts_impl(**kwargs)
    )
    difference = (fg_output.float() - fgv_output.float()).abs()

    moe_input = torch.randn(
        (m, topk, hidden), device="cuda", dtype=torch.bfloat16
    )
    fg_moe_output = torch.empty((m, hidden), device="cuda", dtype=torch.bfloat16)
    fgv_moe_output = torch.empty_like(fg_moe_output)
    _, fg_moe_metrics = measure(lambda: flag_gems.moe_sum(moe_input, fg_moe_output))
    _, fgv_moe_metrics = measure(
        lambda: flaggems_vllm.moe_sum(moe_input, fgv_moe_output)
    )
    moe_difference = (fg_moe_output.float() - fgv_moe_output.float()).abs()

    print(
        json.dumps(
            {
                "revision": {
                    "flaggems_vllm_fused": flaggems_vllm.fused_experts_impl.__module__,
                    "flaggems_vllm_moe_sum": flaggems_vllm.moe_sum.__module__,
                    "flaggems_fused": flag_gems.fused_experts_impl.__module__,
                },
                "fused_moe": {
                    "flaggems": fg_metrics,
                    "flaggems_vllm": fgv_metrics,
                    "flaggems_vllm_vs_flaggems": (
                        fg_metrics["median_ms"] / fgv_metrics["median_ms"]
                    ),
                    "exact": bool(torch.equal(fg_output, fgv_output)),
                    "max_abs_diff": float(difference.max().item()),
                },
                "moe_sum": {
                    "flaggems": fg_moe_metrics,
                    "flaggems_vllm": fgv_moe_metrics,
                    "flaggems_vllm_vs_flaggems": (
                        fg_moe_metrics["median_ms"] / fgv_moe_metrics["median_ms"]
                    ),
                    "exact": bool(torch.equal(fg_moe_output, fgv_moe_output)),
                    "max_abs_diff": float(moe_difference.max().item()),
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
