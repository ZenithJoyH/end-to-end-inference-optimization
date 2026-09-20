#!/usr/bin/env python3
"""Benchmark fusing HY4 block Top-K request-offset postprocessing."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import torch
import triton
import triton.language as tl


WARMUP = 10
RUNS = 100
REPEATS = 9
WIDTH = 2048


@triton.jit
def _translate_valid_topk_kernel(
    selected,
    row_offsets,
    stride_selected_row,
    count: tl.constexpr,
    BLOCK: tl.constexpr,
):
    row = tl.program_id(0)
    cols = tl.program_id(1) * BLOCK + tl.arange(0, BLOCK)
    mask = cols < count
    values = tl.load(selected + row * stride_selected_row + cols, mask=mask)
    offset = tl.load(row_offsets + row)
    translated = tl.where(values >= 0, values + offset, -1)
    tl.store(selected + row * stride_selected_row + cols, translated, mask=mask)


def baseline(selected: torch.Tensor, row_offsets: torch.Tensor) -> None:
    valid = selected >= 0
    selected.add_(row_offsets.unsqueeze(1))
    selected.masked_fill_(~valid, -1)


def candidate(
    selected: torch.Tensor,
    row_offsets: torch.Tensor,
    *,
    block: int,
    num_warps: int,
) -> None:
    rows, count = selected.shape
    _translate_valid_topk_kernel[(rows, triton.cdiv(count, block))](
        selected,
        row_offsets,
        selected.stride(0),
        count=count,
        BLOCK=block,
        num_warps=num_warps,
        num_stages=1,
    )


def elapsed_us(fn) -> list[float]:
    for _ in range(WARMUP):
        fn()
    torch.cuda.synchronize()
    samples = []
    for _ in range(REPEATS):
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        for _ in range(RUNS):
            fn()
        end.record()
        end.synchronize()
        samples.append(start.elapsed_time(end) * 1000.0 / RUNS)
    return samples


def stats(samples: list[float]) -> dict[str, object]:
    return {
        "median_us": statistics.median(samples),
        "min_us": min(samples),
        "max_us": max(samples),
        "samples_us": samples,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")

    assert torch.cuda.is_available()
    torch.manual_seed(20260919)
    rows_out = []
    configurations = ((256, 4), (512, 4), (1024, 4), (1024, 8))
    for rows in (1, 7, 26, 64, 120, 128):
        source = torch.randint(
            -1,
            4096,
            (rows, WIDTH),
            device="cuda",
            dtype=torch.int32,
        )
        source[:, ::7] = -1
        row_offsets = torch.arange(
            rows, device="cuda", dtype=torch.int32
        ).mul_(4096)

        expected = source.clone()
        baseline(expected, row_offsets)
        baseline_work = source.clone()
        baseline_samples = elapsed_us(
            lambda: baseline(baseline_work, row_offsets)
        )
        baseline_stats = stats(baseline_samples)

        candidates = []
        for block, num_warps in configurations:
            actual = source.clone()
            candidate(
                actual,
                row_offsets,
                block=block,
                num_warps=num_warps,
            )
            torch.cuda.synchronize()
            exact = bool(torch.equal(expected, actual))
            assert exact
            candidate_work = source.clone()
            samples = elapsed_us(
                lambda block=block, num_warps=num_warps: candidate(
                    candidate_work,
                    row_offsets,
                    block=block,
                    num_warps=num_warps,
                )
            )
            candidate_stats = stats(samples)
            candidates.append(
                {
                    "block": block,
                    "num_warps": num_warps,
                    "exact": exact,
                    "timing": candidate_stats,
                    "speedup": baseline_stats["median_us"]
                    / candidate_stats["median_us"],
                }
            )
        rows_out.append(
            {
                "rows": rows,
                "count": WIDTH,
                "baseline": baseline_stats,
                "candidates": candidates,
            }
        )

    # Validate strided prefixes and graph replay independently of the timed
    # full-width dominant shape.
    correctness = []
    for rows, count in ((1, 17), (7, 1024), (128, 1537), (128, WIDTH)):
        backing = torch.randint(
            -1,
            4096,
            (rows, WIDTH),
            device="cuda",
            dtype=torch.int32,
        )
        backing[:, ::5] = -1
        row_offsets = torch.arange(
            rows, device="cuda", dtype=torch.int32
        ).mul_(3072)
        expected = backing.clone()
        actual = backing.clone()
        baseline(expected[:, :count], row_offsets)
        candidate(actual[:, :count], row_offsets, block=1024, num_warps=4)
        torch.cuda.synchronize()
        row = {
            "rows": rows,
            "count": count,
            "exact": bool(torch.equal(expected, actual)),
            "tail_preserved": bool(
                torch.equal(expected[:, count:], actual[:, count:])
            ),
        }
        correctness.append(row)
        assert row["exact"] and row["tail_preserved"]

    source = torch.randint(
        -1, 4096, (128, WIDTH), device="cuda", dtype=torch.int32
    )
    source[:, ::11] = -1
    row_offsets = torch.arange(
        128, device="cuda", dtype=torch.int32
    ).mul_(4096)
    graph_work = source.clone()
    graph = torch.cuda.CUDAGraph()
    torch.cuda.synchronize()
    with torch.cuda.graph(graph):
        candidate(graph_work, row_offsets, block=1024, num_warps=4)
    graph_replays = []
    expected = source.clone()
    baseline(expected, row_offsets)
    for replay in range(2):
        graph_work.copy_(source)
        graph.replay()
        torch.cuda.synchronize()
        graph_replays.append(
            {
                "replay": replay + 1,
                "exact": bool(torch.equal(expected, graph_work)),
            }
        )
    assert all(row["exact"] for row in graph_replays)

    result = {
        "schema_version": 1,
        "device": torch.cuda.get_device_name(0),
        "dtype": "int32",
        "width": WIDTH,
        "warmup": WARMUP,
        "runs": RUNS,
        "repeats": REPEATS,
        "baseline": "ge + add_ + bitwise_not + masked_fill_",
        "candidate": "single strided in-place Triton translate-valid kernel",
        "rows": rows_out,
        "correctness": correctness,
        "graph_capture": "passed",
        "graph_replays": graph_replays,
        "conclusion_boundary": (
            "transform-only operator timing; excludes Top-K and is not an "
            "Indexer or end-to-end result"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
