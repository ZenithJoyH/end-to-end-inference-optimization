#!/usr/bin/env python3
"""Compare FlagGems general_mm with the platform-native BF16 mm provider.

The shapes are the rank-local TP=8 projections observed in the post-op008 P4K
trace.  The trace records exact Prefill shapes, while Decode graph replay hides
the CPU-side aten::mm records.  Replacing the Prefill M dimension with the live
Decode graph width (64) gives the finite set screened here.

This is an offline accelerator microbenchmark.  Importing and calling the
FlagGems function directly avoids changing the process-wide ATen registry, so
``torch.mm`` remains the platform-native reference/provider in this process.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Callable

import torch

from flag_gems.ops.mm import mm_out as gems_mm_out


SHAPES = (
    (64, 10240, 4),
    (64, 768, 2560),
    (64, 10240, 320),
    (64, 320, 10240),
    (64, 2560, 12),
    (64, 2560, 2048),
    (64, 2560, 10240),
    (64, 2560, 2560),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--repeat", type=int, default=200)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--seed", type=int, default=84621)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def event_ms(fn: Callable[[], torch.Tensor], warmup: int, repeat: int) -> float:
    for _ in range(warmup):
        fn()
    torch.cuda.synchronize()
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    start.record()
    for _ in range(repeat):
        fn()
    end.record()
    torch.cuda.synchronize()
    return float(start.elapsed_time(end)) / repeat


def capture(fn: Callable[[], torch.Tensor]) -> tuple[torch.cuda.CUDAGraph, torch.Tensor]:
    for _ in range(3):
        output = fn()
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, capture_error_mode="thread_local"):
        output = fn()
    torch.cuda.synchronize()
    graph.replay()
    graph.replay()
    torch.cuda.synchronize()
    return graph, output


def graph_ms(graph: torch.cuda.CUDAGraph, repeat: int) -> float:
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    start.record()
    for _ in range(repeat):
        graph.replay()
    end.record()
    torch.cuda.synchronize()
    return float(start.elapsed_time(end)) / repeat


def error(reference: torch.Tensor, actual: torch.Tensor) -> dict[str, float | bool]:
    ref = reference.float()
    got = actual.float()
    delta = (ref - got).abs()
    denom = ref.norm().clamp_min(1e-12)
    cosine = torch.nn.functional.cosine_similarity(ref.flatten(), got.flatten(), dim=0)
    return {
        "max_abs": float(delta.max().item()),
        "mean_abs": float(delta.mean().item()),
        "relative_l2": float((delta.norm() / denom).item()),
        "cosine": float(cosine.item()),
        "allclose_atol_0p1_rtol_0p02": bool(
            torch.allclose(reference, actual, atol=0.1, rtol=0.02)
        ),
    }


def run_shape(
    shape: tuple[int, int, int],
    warmup: int,
    repeat: int,
    rounds: int,
    seed: int,
    device: torch.device,
) -> dict[str, object]:
    m, k, n = shape
    generator = torch.Generator(device=device)
    generator.manual_seed(seed + m * 13 + k * 17 + n * 19)
    a = torch.randn((m, k), device=device, dtype=torch.bfloat16, generator=generator)
    b = torch.randn((k, n), device=device, dtype=torch.bfloat16, generator=generator)
    native_out = torch.empty((m, n), device=device, dtype=torch.bfloat16)
    gems_out = torch.empty_like(native_out)
    native_fn = lambda: torch.mm(a, b, out=native_out)
    gems_fn = lambda: gems_mm_out(a, b, out=gems_out)

    native = native_fn()
    gems = gems_fn()
    torch.cuda.synchronize()
    correctness = error(native, gems)

    native_graph, native_capture = capture(native_fn)
    gems_graph, gems_capture = capture(gems_fn)
    graph_correctness = error(native_capture, gems_capture)

    eager_samples: dict[str, list[float]] = {"native": [], "flaggems": []}
    graph_samples: dict[str, list[float]] = {"native": [], "flaggems": []}
    for round_index in range(rounds):
        eager_order = (
            (("native", native_fn), ("flaggems", gems_fn))
            if round_index % 2 == 0
            else (("flaggems", gems_fn), ("native", native_fn))
        )
        graph_order = (
            (("flaggems", gems_graph), ("native", native_graph))
            if round_index % 2 == 0
            else (("native", native_graph), ("flaggems", gems_graph))
        )
        for name, fn in eager_order:
            eager_samples[name].append(event_ms(fn, warmup, repeat))
        for name, graph in graph_order:
            graph_samples[name].append(graph_ms(graph, repeat))

    eager_medians = {
        name: statistics.median(values) for name, values in eager_samples.items()
    }
    graph_medians = {
        name: statistics.median(values) for name, values in graph_samples.items()
    }
    graph_native_improvement = (
        (graph_medians["flaggems"] / graph_medians["native"] - 1.0) * 100.0
    )
    eager_native_improvement = (
        (eager_medians["flaggems"] / eager_medians["native"] - 1.0) * 100.0
    )
    return {
        "shape": {"m": m, "k": k, "n": n},
        "correctness": correctness,
        "graph_correctness": graph_correctness,
        "eager_ms": {"samples": eager_samples, "median": eager_medians},
        "graph_ms": {"samples": graph_samples, "median": graph_medians},
        "native_improvement_percent": {
            "eager": eager_native_improvement,
            "graph": graph_native_improvement,
        },
        "native_screen_pass": bool(
            correctness["allclose_atol_0p1_rtol_0p02"]
            and graph_correctness["allclose_atol_0p1_rtol_0p02"]
            and graph_native_improvement >= 5.0
        ),
    }


def main() -> None:
    args = parse_args()
    if args.rounds != 3 or args.warmup < 1 or args.repeat < 1:
        raise ValueError("rounds must remain 3 and warmup/repeat must be positive")
    torch.cuda.set_device(args.device)
    device = torch.device("cuda", args.device)
    results = [
        run_shape(shape, args.warmup, args.repeat, args.rounds, args.seed, device)
        for shape in SHAPES
    ]
    payload = {
        "schema_version": 1,
        "experiment": "op010-p4k-decode-mm-out-native-provider-screen",
        "scope": "screening_only_co_resident_idle_service",
        "dtype": "bfloat16",
        "device": args.device,
        "warmup": args.warmup,
        "repeat": args.repeat,
        "rounds": args.rounds,
        "graph_capture_replays_before_measurement": 2,
        "shape_source": "prof004 exact TP8 projections with live graph M=64",
        "retention_threshold_percent": 5.0,
        "results": results,
        "passing_shapes": [
            item["shape"] for item in results if item["native_screen_pass"]
        ],
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True)
    args.output.parent.mkdir(parents=True, exist_ok=False)
    args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
