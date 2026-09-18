#!/usr/bin/env python3
"""Benchmark removal of HY4 single-row boolean-index synchronization."""

from __future__ import annotations

import json
from pathlib import Path
import statistics
import time

import torch

from vllm_fl.models import hy_v4


OUTPUT = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e/results/operator/"
    "hyv4-single-row-prefix-translate-20260917.json"
)
WIDTH = 2048
CALLS = 42
OFFSET = 4096


def baseline_translate(indices: torch.Tensor, count: int, offset: int) -> None:
    valid = indices >= 0
    indices[valid] += offset


def candidate_translate(indices: torch.Tensor, count: int, offset: int) -> None:
    hy_v4._translate_hyv4_selected_prefix(indices, count, offset)


def synchronize() -> None:
    torch.cuda.synchronize()


def run_chain(fn, buffers: torch.Tensor, count: int) -> None:
    for row in buffers:
        fn(row, count, OFFSET)


def benchmark(fn, template: torch.Tensor, *, warmup: int = 5, repeats: int = 30):
    buffers = template.repeat(CALLS, 1)
    for _ in range(warmup):
        buffers.copy_(template)
        synchronize()
        run_chain(fn, buffers, WIDTH)
        synchronize()
    samples_ms = []
    for _ in range(repeats):
        buffers.copy_(template)
        synchronize()
        start = time.perf_counter()
        run_chain(fn, buffers, WIDTH)
        synchronize()
        samples_ms.append((time.perf_counter() - start) * 1e3)
    return {
        "median_ms": statistics.median(samples_ms),
        "min_ms": min(samples_ms),
        "max_ms": max(samples_ms),
        "samples_ms": samples_ms,
    }


def main() -> None:
    assert torch.cuda.is_available()
    torch.manual_seed(20260917)
    device = torch.device("cuda")
    full = torch.randperm(WIDTH, device=device, dtype=torch.int64).to(torch.int32)

    correctness = []
    for count in (0, 1, 17, 1024, WIDTH):
        template = torch.full((WIDTH,), -1, device=device, dtype=torch.int32)
        if count:
            template[:count].copy_(full[:count])
        expected = template.clone()
        actual = template.clone()
        baseline_translate(expected, count, OFFSET)
        candidate_translate(actual, count, OFFSET)
        synchronize()
        correctness.append({
            "count": count,
            "exact": bool(torch.equal(expected, actual)),
            "invalid_tail_preserved": bool(
                torch.all(actual[count:] == -1).item()
            ),
        })
    assert all(row["exact"] and row["invalid_tail_preserved"] for row in correctness)

    baseline = benchmark(baseline_translate, full)
    candidate = benchmark(candidate_translate, full)

    graph_buffers = full.repeat(CALLS, 1)
    graph = torch.cuda.CUDAGraph()
    synchronize()
    with torch.cuda.graph(graph):
        run_chain(candidate_translate, graph_buffers, WIDTH)
    graph_replays = []
    for replay in range(2):
        graph_buffers.copy_(full)
        graph.replay()
        synchronize()
        expected = full + OFFSET
        graph_replays.append({
            "replay": replay + 1,
            "exact": bool(torch.equal(graph_buffers[0], expected)),
            "all_rows_equal": bool(
                torch.all(graph_buffers == expected.unsqueeze(0)).item()
            ),
        })
    assert all(row["exact"] and row["all_rows_equal"] for row in graph_replays)

    result = {
        "device": torch.cuda.get_device_name(0),
        "dtype": "int32",
        "width": WIDTH,
        "calls_per_chain": CALLS,
        "offset": OFFSET,
        "baseline": "valid=indices>=0; indices[valid]+=offset",
        "candidate": "indices[:count].add_(offset)",
        "correctness": correctness,
        "graph_capture": "passed",
        "graph_replays": graph_replays,
        "baseline_timing": baseline,
        "candidate_timing": candidate,
        "speedup": baseline["median_ms"] / candidate["median_ms"],
        "conclusion_boundary": (
            "single-row request-offset translation only; includes host-visible "
            "synchronization for a 42-call chain and is not an E2E result"
        ),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    OUTPUT.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
