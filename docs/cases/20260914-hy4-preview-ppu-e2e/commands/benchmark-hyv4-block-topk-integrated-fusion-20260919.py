#!/usr/bin/env python3
"""Benchmark the fused translation inside HY4 `_select_topk_block`."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import torch

from vllm_fl.models import hy_v4


WARMUP = 3
RUNS = 3
REPEATS = 7
HEADS = 32
HEAD_DIM = 128
KEYS = 4096
TOPK = 2048


def baseline_translate(
    selected: torch.Tensor,
    row_starts: torch.Tensor,
    request_start: int,
) -> None:
    valid = selected >= 0
    selected.add_((row_starts - request_start).unsqueeze(1))
    selected.masked_fill_(~valid, -1)


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


def timing(samples: list[float]) -> dict[str, object]:
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
    assert hy_v4.current_platform.vendor_name == "thead"

    torch.manual_seed(20260919)
    rows_out = []
    candidate_translate = hy_v4._translate_hyv4_selected_block

    raw_selected = torch.randint(
        -1, KEYS, (128, TOPK), device="cuda", dtype=torch.int32
    )
    raw_selected[:, ::7] = -1
    translation_starts = torch.arange(
        128, device="cuda", dtype=torch.int32
    ).mul_(4096)
    translated_expected = raw_selected.clone()
    translated_actual = raw_selected.clone()
    baseline_translate(translated_expected, translation_starts, 1024)
    candidate_translate(translated_actual, translation_starts, 1024)
    torch.cuda.synchronize()
    translation_exact = bool(
        torch.equal(translated_expected, translated_actual)
    )
    assert translation_exact

    graph_work = raw_selected.clone()
    graph = torch.cuda.CUDAGraph()
    torch.cuda.synchronize()
    with torch.cuda.graph(graph):
        candidate_translate(graph_work, translation_starts, 1024)
    graph_replays = []
    for replay in range(2):
        graph_work.copy_(raw_selected)
        graph.replay()
        torch.cuda.synchronize()
        graph_replays.append(
            {
                "replay": replay + 1,
                "exact": bool(
                    torch.equal(translated_expected, graph_work)
                ),
            }
        )
    assert all(row["exact"] for row in graph_replays)

    for rows in (26, 128):
        q = torch.randn(
            (rows, HEADS, HEAD_DIM), device="cuda", dtype=torch.bfloat16
        )
        weights = torch.randn(
            (rows, HEADS), device="cuda", dtype=torch.bfloat16
        )
        keys = torch.randn(
            (KEYS, HEAD_DIM), device="cuda", dtype=torch.bfloat16
        )
        row_starts = torch.zeros((rows,), device="cuda", dtype=torch.int32)
        row_ends = torch.arange(
            KEYS - rows + 1,
            KEYS + 1,
            device="cuda",
            dtype=torch.int32,
        )
        baseline_output = torch.empty(
            (rows, TOPK), device="cuda", dtype=torch.int32
        )
        candidate_output = torch.empty_like(baseline_output)

        def invoke(output: torch.Tensor) -> None:
            hy_v4._select_topk_block(
                q,
                weights,
                keys,
                row_starts,
                row_ends,
                key_start=0,
                key_end=KEYS,
                request_start=0,
                topk=TOPK,
                output=output,
            )

        hy_v4._translate_hyv4_selected_block = baseline_translate
        invoke(baseline_output)
        torch.cuda.synchronize()
        baseline_samples = elapsed_us(lambda: invoke(baseline_output))

        hy_v4._translate_hyv4_selected_block = candidate_translate
        invoke(candidate_output)
        torch.cuda.synchronize()
        candidate_samples = elapsed_us(lambda: invoke(candidate_output))

        exact = bool(torch.equal(baseline_output, candidate_output))
        set_exact = bool(
            torch.equal(
                baseline_output.sort(dim=1).values,
                candidate_output.sort(dim=1).values,
            )
        )
        baseline_stats = timing(baseline_samples)
        candidate_stats = timing(candidate_samples)
        rows_out.append(
            {
                "rows": rows,
                "keys": KEYS,
                "topk": TOPK,
                "exact": exact,
                "set_exact": set_exact,
                "baseline": baseline_stats,
                "candidate": candidate_stats,
                "speedup": baseline_stats["median_us"]
                / candidate_stats["median_us"],
                "delta_us": baseline_stats["median_us"]
                - candidate_stats["median_us"],
            }
        )

    result = {
        "schema_version": 1,
        "device": torch.cuda.get_device_name(0),
        "vendor": hy_v4.current_platform.vendor_name,
        "dtype": "bfloat16 scores / int32 indices",
        "warmup": WARMUP,
        "runs": RUNS,
        "repeats": REPEATS,
        "translation_exact": translation_exact,
        "graph_capture": "passed",
        "graph_replays": graph_replays,
        "rows": rows_out,
        "conclusion_boundary": (
            "full `_select_topk_block` operator timing at representative "
            "synthetic shapes; the shared Top-K provider may choose different "
            "threshold-adjacent sets across independent calls, while fused "
            "translation correctness is checked on identical raw indices; "
            "not an end-to-end result"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
