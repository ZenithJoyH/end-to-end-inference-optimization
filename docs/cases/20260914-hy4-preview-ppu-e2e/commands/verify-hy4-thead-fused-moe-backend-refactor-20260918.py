#!/usr/bin/env python3
"""Verify the T-Head fused-MoE backend wrapper after specialization relocation."""

from __future__ import annotations

import json
import statistics
import time

import torch

import flag_gems
from flag_gems.fused import fused_moe as generic_fused_moe
from flag_gems.runtime import torch_device_fn
from flag_gems.runtime.backend._thead.fused import fused_moe as thead_fused_moe


M, E, HIDDEN, LOCAL_I, TOPK = 2048, 256, 6144, 128, 8


def sync() -> None:
    torch_device_fn.synchronize()


def summarize(samples: list[float]) -> dict[str, float]:
    return {
        "mean_ms": statistics.fmean(samples),
        "median_ms": statistics.median(samples),
        "min_ms": min(samples),
        "max_ms": max(samples),
    }


def sample(fn, samples: list[float]) -> torch.Tensor:
    output = fn()
    for _ in range(3):
        output = fn()
    sync()
    for _ in range(20):
        start = time.perf_counter()
        output = fn()
        sync()
        samples.append((time.perf_counter() - start) * 1000)
    return output


def main() -> None:
    assert flag_gems.vendor_name == "thead"
    assert flag_gems.fused_experts_impl.__module__.endswith(
        "_thead.fused.fused_moe"
    )
    assert flag_gems.moe_sum.__module__.endswith("_thead.fused.moe_sum")

    torch.manual_seed(20260918)
    device = torch.device("cuda")
    hidden = torch.randn((M, HIDDEN), device=device, dtype=torch.bfloat16)
    w1 = torch.randint(
        -8, 9, (E, 2 * LOCAL_I, HIDDEN), device=device, dtype=torch.int8
    )
    w2 = torch.randint(
        -8, 9, (E, HIDDEN, LOCAL_I), device=device, dtype=torch.int8
    )
    ids = torch.randint(0, E, (M, TOPK), device=device, dtype=torch.int32)
    weights = torch.rand((M, TOPK), device=device, dtype=torch.float32)
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

    baseline_samples: list[float] = []
    candidate_samples: list[float] = []
    baseline_output = None
    candidate_output = None
    for round_index in range(4):
        if round_index % 2 == 0:
            baseline_output = sample(
                lambda: generic_fused_moe.fused_experts_impl(**kwargs),
                baseline_samples,
            )
            candidate_output = sample(
                lambda: flag_gems.fused_experts_impl(**kwargs),
                candidate_samples,
            )
        else:
            candidate_output = sample(
                lambda: flag_gems.fused_experts_impl(**kwargs),
                candidate_samples,
            )
            baseline_output = sample(
                lambda: generic_fused_moe.fused_experts_impl(**kwargs),
                baseline_samples,
            )
    assert baseline_output is not None
    assert candidate_output is not None
    sync()

    for _ in range(3):
        flag_gems.fused_experts_impl(**kwargs)
    sync()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        graph_output = flag_gems.fused_experts_impl(**kwargs)
    graph.replay()
    sync()
    replay_one = graph_output.clone()
    graph.replay()
    sync()
    replay_two = graph_output.clone()

    baseline = summarize(baseline_samples)
    candidate = summarize(candidate_samples)
    difference = (baseline_output.float() - candidate_output.float()).abs()
    replay_difference = (candidate_output.float() - replay_two.float()).abs()
    candidate_config = thead_fused_moe._thead_get_default_config(
        M, E, 2 * LOCAL_I, HIDDEN, TOPK, "int8_w8a8"
    )
    result = {
        "dispatch": {
            "fused_experts_impl": flag_gems.fused_experts_impl.__module__,
            "moe_sum": flag_gems.moe_sum.__module__,
        },
        "shape": {
            "M": M,
            "E": E,
            "hidden": HIDDEN,
            "local_intermediate": LOCAL_I,
            "topk": TOPK,
        },
        "candidate_config": candidate_config,
        "generic_baseline": baseline,
        "thead_backend_candidate": candidate,
        "speedup_median": baseline["median_ms"] / candidate["median_ms"],
        "eager_correctness": {
            "exact": bool(torch.equal(baseline_output, candidate_output)),
            "max_abs_diff": float(difference.max().item()),
        },
        "graph": {
            "capture": "passed",
            "replays": 2,
            "replays_exact": bool(torch.equal(replay_one, replay_two)),
            "eager_vs_replay_exact": bool(
                torch.equal(candidate_output, replay_two)
            ),
            "eager_vs_replay_max_abs_diff": float(
                replay_difference.max().item()
            ),
        },
        "samples_per_variant": len(baseline_samples),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
