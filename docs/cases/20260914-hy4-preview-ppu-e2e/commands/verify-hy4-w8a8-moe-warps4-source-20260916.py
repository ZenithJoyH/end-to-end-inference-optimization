#!/usr/bin/env python3
"""Verify the applied PPU W8A8 MoE config and graph replay at Hy4 M=2048."""

from __future__ import annotations

import json
import statistics
import time

import torch

import flag_gems.fused.fused_moe as fm
from flag_gems.runtime import torch_device_fn


M, E, HIDDEN, LOCAL_I, TOPK = 2048, 256, 6144, 128, 8


def sync() -> None:
    torch_device_fn.synchronize()


def run(kwargs: dict[str, object], generic_baseline: bool) -> torch.Tensor:
    if not generic_baseline:
        return fm.fused_experts_impl(**kwargs)
    original = fm._get_device_name
    try:
        fm._get_device_name = lambda: "generic_device"
        return fm.fused_experts_impl(**kwargs)
    finally:
        fm._get_device_name = original


def sample(kwargs: dict[str, object], generic_baseline: bool) -> list[float]:
    for _ in range(3):
        run(kwargs, generic_baseline)
    sync()
    samples: list[float] = []
    for _ in range(20):
        start = time.perf_counter()
        run(kwargs, generic_baseline)
        sync()
        samples.append((time.perf_counter() - start) * 1000)
    return samples


def summarize(samples: list[float]) -> dict[str, float]:
    return {
        "mean_ms": statistics.fmean(samples),
        "median_ms": statistics.median(samples),
        "min_ms": min(samples),
        "max_ms": max(samples),
    }


def main() -> None:
    torch.manual_seed(20260916)
    device = torch.device("cuda")
    hidden = torch.randn((M, HIDDEN), device=device, dtype=torch.bfloat16)
    w1 = torch.randint(-8, 9, (E, 2 * LOCAL_I, HIDDEN), device=device, dtype=torch.int8)
    w2 = torch.randint(-8, 9, (E, HIDDEN, LOCAL_I), device=device, dtype=torch.int8)
    ids = torch.randint(0, E, (M, TOPK), device=device, dtype=torch.int32)
    weights = torch.rand((M, TOPK), device=device, dtype=torch.float32)
    weights /= weights.sum(dim=-1, keepdim=True)
    kwargs: dict[str, object] = {
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
    baseline_output = run(kwargs, True)
    candidate_output = run(kwargs, False)
    sync()
    eager_diff = (baseline_output.float() - candidate_output.float()).abs()

    baseline_samples: list[float] = []
    candidate_samples: list[float] = []
    for round_index in range(6):
        order = (True, False) if round_index % 2 == 0 else (False, True)
        for generic_baseline in order:
            target = baseline_samples if generic_baseline else candidate_samples
            target.extend(sample(kwargs, generic_baseline))

    # The production service uses graph mode. Capture the patched real entry
    # point and require two successful replays with identical output.
    for _ in range(3):
        run(kwargs, False)
    sync()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        graph_output = run(kwargs, False)
    graph.replay()
    sync()
    replay_one = graph_output.clone()
    graph.replay()
    sync()
    replay_two = graph_output.clone()
    graph_diff = (candidate_output.float() - replay_two.float()).abs()

    baseline = summarize(baseline_samples)
    candidate = summarize(candidate_samples)
    config = fm.get_default_config(M, E, 2 * LOCAL_I, HIDDEN, TOPK, "int8_w8a8")
    print(json.dumps({
        "shape": {"M": M, "E": E, "hidden": HIDDEN, "local_intermediate": LOCAL_I, "topk": TOPK},
        "device_name": fm._get_device_name(),
        "applied_config": config,
        "generic_baseline": baseline,
        "patched_candidate": candidate,
        "speedup_mean": baseline["mean_ms"] / candidate["mean_ms"],
        "speedup_median": baseline["median_ms"] / candidate["median_ms"],
        "eager_correctness": {
            "exact": bool(torch.equal(baseline_output, candidate_output)),
            "max_abs_diff": float(eager_diff.max().item()),
            "mean_abs_diff": float(eager_diff.mean().item()),
        },
        "graph": {
            "capture": "passed",
            "replays": 2,
            "replays_exact": bool(torch.equal(replay_one, replay_two)),
            "eager_vs_replay_exact": bool(torch.equal(candidate_output, replay_two)),
            "eager_vs_replay_max_abs_diff": float(graph_diff.max().item()),
        },
        "samples_per_variant": len(baseline_samples),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
