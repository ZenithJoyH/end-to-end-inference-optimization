#!/usr/bin/env python3
"""Verify HY4's T-Head native full-FP32 router MM integration."""

from __future__ import annotations

import json
import statistics
import time

import torch
import torch.nn.functional as F
from torch import nn

import flag_gems
from flag_gems.ops.linear import linear as flaggems_linear
from flag_gems.runtime import torch_device_fn
from vllm_fl.models.hy_v4 import (
    HYV4RouterLinear,
    _can_use_hyv4_native_router_mm,
)
from vllm_fl.utils import get_flag_gems_whitelist_blacklist, use_flaggems_op


K, N, TOP_K = 6144, 256, 8
SHAPES = (1, 16, 64, 256, 1024, 2048)


def sync() -> None:
    torch_device_fn.synchronize()


def measure(fn, warmup: int = 8, repeats: int = 30):
    output = fn()
    for _ in range(warmup):
        output = fn()
    sync()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        output = fn()
        sync()
        samples.append((time.perf_counter() - start) * 1_000_000)
    return {
        "mean_us": statistics.fmean(samples),
        "median_us": statistics.median(samples),
        "min_us": min(samples),
        "max_us": max(samples),
    }, output


def compare(reference: torch.Tensor, candidate: torch.Tensor) -> dict[str, object]:
    delta = (reference - candidate).abs()
    ref_top8 = reference.topk(TOP_K, dim=-1)
    ref_top9 = reference.topk(TOP_K + 1, dim=-1)
    ref_idx = ref_top8.indices
    cand_idx = candidate.topk(TOP_K, dim=-1).indices
    position_equal = (ref_idx == cand_idx).all(dim=-1)
    set_equal = (
        ref_idx.sort(dim=-1).values == cand_idx.sort(dim=-1).values
    ).all(dim=-1)
    changed_details = []
    for row in (~set_equal).nonzero(as_tuple=False).flatten().tolist():
        ref_set = set(ref_idx[row].tolist())
        cand_set = set(cand_idx[row].tolist())
        changed_details.append(
            {
                "row": row,
                "reference_only": sorted(ref_set - cand_set),
                "candidate_only": sorted(cand_set - ref_set),
                "reference_cutoff_margin": float(
                    (
                        ref_top9.values[row, TOP_K - 1]
                        - ref_top9.values[row, TOP_K]
                    ).item()
                ),
                "row_max_abs_diff": float(delta[row].max().item()),
            }
        )
    return {
        "exact_tensor": bool(torch.equal(reference, candidate)),
        "max_abs_diff": float(delta.max().item()),
        "mean_abs_diff": float(delta.mean().item()),
        "position_changed_rows": int((~position_equal).sum().item()),
        "set_changed_rows": int((~set_equal).sum().item()),
        "set_equal_fraction": float(set_equal.float().mean().item()),
        "set_changed_details": changed_details,
    }


def profile_once(fn) -> dict[str, object]:
    try:
        with torch.profiler.profile(
            activities=[
                torch.profiler.ProfilerActivity.CPU,
                torch.profiler.ProfilerActivity.CUDA,
            ]
        ) as prof:
            fn()
            sync()
        rows = []
        for event in prof.key_averages():
            device_time = float(
                getattr(event, "self_device_time_total", 0.0)
                or getattr(event, "self_cuda_time_total", 0.0)
            )
            if device_time > 0 or "mm" in event.key.lower():
                rows.append(
                    {
                        "name": event.key,
                        "self_device_time_us": device_time,
                        "count": int(event.count),
                    }
                )
        rows.sort(key=lambda item: item["self_device_time_us"], reverse=True)
        return {"status": "passed", "top_events": rows[:20]}
    except Exception as exc:
        return {"status": "unsupported", "error": repr(exc)}


def main() -> None:
    torch.manual_seed(20260917)
    whitelist, blacklist = get_flag_gems_whitelist_blacklist()
    if whitelist:
        flag_gems.only_enable(include=whitelist, record=False, once=True)
    elif blacklist:
        flag_gems.enable(unused=blacklist, record=False, once=True)
    else:
        flag_gems.enable(record=False, once=True)

    device = torch.device("cuda")
    native_guard = _can_use_hyv4_native_router_mm(
        input_size=K,
        output_size=N,
        bias=False,
        params_dtype=torch.float32,
        out_dtype=torch.float32,
    )
    # ReplicatedLinear construction requires an initialized TP group.  The
    # operator-only verifier builds the post-init runtime state directly; the
    # focused unit test separately covers __init__ and guard assignment.
    layer = object.__new__(HYV4RouterLinear)
    nn.Module.__init__(layer)
    layer.weight = nn.Parameter(
        torch.randn((N, K), device=device, dtype=torch.float32)
    )
    layer._use_thead_native_router_mm = native_guard

    report: dict[str, object] = {
        "shape": {"K": K, "N": N, "top_k": TOP_K},
        "seed": 20260917,
        "platform_vendor": getattr(
            __import__("vllm.platforms", fromlist=["current_platform"]).current_platform,
            "vendor_name",
            None,
        ),
        "float32_matmul_precision": torch.get_float32_matmul_precision(),
        "allow_tf32": bool(torch.backends.cuda.matmul.allow_tf32),
        "effective_flaggems_mm": use_flaggems_op("mm"),
        "effective_flaggems_linear": use_flaggems_op("linear"),
        "native_guard": bool(native_guard),
        "native_path_enabled": bool(layer._use_thead_native_router_mm),
        "results": {},
    }
    if not layer._use_thead_native_router_mm:
        raise RuntimeError(f"native router MM guard did not enable: {report}")

    graph_input = None
    graph_eager = None
    for m in SHAPES:
        x = torch.randn((m, K), device=device, dtype=torch.bfloat16)
        baseline_timing, baseline = measure(
            lambda: flaggems_linear(x.float(), layer.weight)
        )
        candidate_timing, candidate = measure(lambda: layer(x)[0])
        native_direct = torch.mm(x.float(), layer.weight.T)
        old_flinear = F.linear(x.float(), layer.weight)
        report["results"][str(m)] = {
            "baseline_flaggems_linear": baseline_timing,
            "candidate_native_router": candidate_timing,
            "speedup": baseline_timing["median_us"]
            / candidate_timing["median_us"],
            "baseline_vs_candidate": compare(baseline, candidate),
            "candidate_equals_direct_native_mm": bool(
                torch.equal(candidate, native_direct)
            ),
            "old_flinear_equals_direct_flaggems": bool(
                torch.equal(old_flinear, baseline)
            ),
        }
        if m == 2048:
            graph_input = x
            graph_eager = candidate

    assert graph_input is not None and graph_eager is not None
    for _ in range(3):
        layer(graph_input)
    sync()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        graph_output = layer(graph_input)[0]
    graph.replay()
    sync()
    replay_one = graph_output.clone()
    graph.replay()
    sync()
    replay_two = graph_output.clone()
    report["graph"] = {
        "capture": "passed",
        "replays": 2,
        "replays_exact": bool(torch.equal(replay_one, replay_two)),
        "eager_vs_replay_exact": bool(torch.equal(graph_eager, replay_two)),
    }
    report["profile_m2048"] = profile_once(lambda: layer(graph_input)[0])
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
