#!/usr/bin/env python3
"""Verify the applied HY4 moe_sum dispatch and graph replay."""

from __future__ import annotations

import json
import statistics
import time

import torch
import triton

from flag_gems.fused.moe_sum import moe_sum, moe_sum_kernel
from flag_gems.runtime import torch_device_fn


TOPK, HIDDEN = 8, 6144


def sync() -> None:
    torch_device_fn.synchronize()


def generic(inp: torch.Tensor) -> torch.Tensor:
    m = inp.shape[0]
    out = torch.empty((m, HIDDEN), device=inp.device, dtype=inp.dtype)
    grid = lambda meta: (m, triton.cdiv(HIDDEN, meta["BLOCK_SIZE"]))
    moe_sum_kernel[grid](
        inp, out, m, TOPK, HIDDEN,
        inp.stride(0), inp.stride(1), inp.stride(2),
        out.stride(0), out.stride(1),
    )
    return out


def patched(inp: torch.Tensor) -> torch.Tensor:
    out = torch.empty((inp.shape[0], HIDDEN), device=inp.device, dtype=inp.dtype)
    moe_sum(inp, out)
    return out


def measure(fn) -> tuple[dict[str, float], torch.Tensor]:
    out = fn()
    for _ in range(5):
        out = fn()
    sync()
    samples = []
    for _ in range(80):
        start = time.perf_counter()
        out = fn()
        sync()
        samples.append((time.perf_counter() - start) * 1_000_000)
    return {
        "mean_us": statistics.fmean(samples),
        "median_us": statistics.median(samples),
        "min_us": min(samples),
        "max_us": max(samples),
    }, out


def main() -> None:
    torch.manual_seed(20260916)
    dev = torch.device("cuda")
    results = {}
    graph_input = None
    eager_output = None
    for m in (256, 2048):
        inp = torch.randn((m, TOPK, HIDDEN), device=dev, dtype=torch.bfloat16)
        baseline_timing, reference = measure(lambda: generic(inp))
        candidate_timing, output = measure(lambda: patched(inp))
        results[str(m)] = {
            "generic": baseline_timing,
            "patched": candidate_timing,
            "speedup": baseline_timing["median_us"] / candidate_timing["median_us"],
            "exact": bool(torch.equal(reference, output)),
            "max_abs_diff": float((reference.float() - output.float()).abs().max().item()),
        }
        if m == 2048:
            graph_input, eager_output = inp, output

    for _ in range(3):
        patched(graph_input)
    sync()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        graph_output = patched(graph_input)
    graph.replay()
    sync()
    replay_one = graph_output.clone()
    graph.replay()
    sync()
    replay_two = graph_output.clone()
    results["graph"] = {
        "capture": "passed",
        "replays": 2,
        "replays_exact": bool(torch.equal(replay_one, replay_two)),
        "eager_vs_replay_exact": bool(torch.equal(eager_output, replay_two)),
        "max_abs_diff": float((eager_output.float() - replay_two.float()).abs().max().item()),
    }
    print(json.dumps({"shape": {"topk": TOPK, "hidden": HIDDEN}, "results": results}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
