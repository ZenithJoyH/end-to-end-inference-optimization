#!/usr/bin/env python3
"""Sweep Hy4 Indexer scoring block rows at the real P4K scoring shape."""

from __future__ import annotations

import json
import statistics

import torch

from vllm_fl.models import hy_v4


HEADS = 32
HEAD_DIM = 128
TOPK = 2048
KEYS = 4096
MAX_ROWS = 512
BLOCK_ROWS = (64, 128, 256, 512)
WARMUP = 2
RUNS = 2
REPEATS = 5


def synchronize() -> None:
    torch.cuda.synchronize()


def elapsed_us(fn) -> list[float]:
    for _ in range(WARMUP):
        fn()
    synchronize()
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


def run_block(q, weights, keys, row_starts, row_ends, output) -> None:
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


def main() -> None:
    torch.manual_seed(20260916)
    q = torch.randn(
        (MAX_ROWS, HEADS, HEAD_DIM), device="cuda", dtype=torch.bfloat16
    )
    weights = torch.randn(
        (MAX_ROWS, HEADS), device="cuda", dtype=torch.bfloat16
    )
    keys = torch.randn((KEYS, HEAD_DIM), device="cuda", dtype=torch.bfloat16)
    row_starts = torch.zeros(MAX_ROWS, device="cuda", dtype=torch.int32)
    # All rows require real scoring: valid width is strictly greater than TOPK.
    row_ends = torch.linspace(
        TOPK + 1, KEYS, MAX_ROWS, device="cuda"
    ).to(torch.int32)

    # Freeze the active 128-row implementation as the semantic baseline. The
    # shared radix provider is intentionally allowed to differ from dense
    # torch.topk around its selection threshold, so this experiment must prove
    # that changing only the batch partition preserves the active path exactly.
    baseline_output = torch.empty(
        (MAX_ROWS, TOPK), device="cuda", dtype=torch.int32
    )
    for start in range(0, MAX_ROWS, 128):
        end = start + 128
        run_block(
            q[start:end],
            weights[start:end],
            keys,
            row_starts[start:end],
            row_ends[start:end],
            baseline_output[start:end],
        )
    synchronize()

    rows = []
    for block_rows in BLOCK_ROWS:
        output = torch.empty(
            (block_rows, TOPK), device="cuda", dtype=torch.int32
        )

        def run() -> None:
            run_block(
                q[:block_rows],
                weights[:block_rows],
                keys,
                row_starts[:block_rows],
                row_ends[:block_rows],
                output,
            )

        run()
        synchronize()
        sorted_output = output.sort(dim=1).values
        sorted_baseline = baseline_output[:block_rows].sort(dim=1).values
        valid = (
            (sorted_output >= 0)
            & (sorted_output < row_ends[:block_rows].unsqueeze(1))
        )
        if not bool(valid.all().item()):
            raise AssertionError("candidate emitted an out-of-range index")
        if not bool((sorted_output[:, 1:] > sorted_output[:, :-1]).all().item()):
            raise AssertionError("candidate emitted a duplicate index")
        candidate_mask = torch.zeros(
            (block_rows, KEYS), device="cuda", dtype=torch.bool
        )
        baseline_mask = torch.zeros_like(candidate_mask)
        candidate_mask.scatter_(1, output.to(torch.long), True)
        baseline_mask.scatter_(
            1, baseline_output[:block_rows].to(torch.long), True
        )
        intersection_per_row = (candidate_mask & baseline_mask).sum(dim=1)
        overlap_fraction = float(
            intersection_per_row.sum().item() / (block_rows * TOPK)
        )
        minimum_row_overlap_fraction = float(
            intersection_per_row.min().item() / TOPK
        )
        exact_sorted_fraction = float(
            (sorted_output == sorted_baseline).float().mean().item()
        )
        samples = elapsed_us(run)
        median = statistics.median(samples)
        rows.append(
            {
                "block_rows": block_rows,
                "samples_us": samples,
                "median_us": median,
                "us_per_row": median / block_rows,
                "projected_2048_rows_us": median * (2048 / block_rows),
                "selected_set_overlap_fraction_vs_128": overlap_fraction,
                "minimum_row_overlap_fraction_vs_128": minimum_row_overlap_fraction,
                "exact_sorted_fraction_vs_128": exact_sorted_fraction,
                "valid_unique_indices": True,
            }
        )
        print(json.dumps(rows[-1]), flush=True)

    baseline = next(row for row in rows if row["block_rows"] == 128)
    for row in rows:
        row["projected_speedup_vs_128"] = (
            baseline["projected_2048_rows_us"] / row["projected_2048_rows_us"]
        )
    best = min(rows, key=lambda row: row["projected_2048_rows_us"])
    print(
        "SUMMARY="
        + json.dumps(
            {
                "status": "passed",
                "shape": {
                    "heads": HEADS,
                    "head_dim": HEAD_DIM,
                    "topk": TOPK,
                    "keys": KEYS,
                },
                "correctness": (
                    "valid unique indices plus selected-set overlap against "
                    "active 128-row partition; non-identical candidates require "
                    "formal accuracy validation"
                ),
                "baseline_block_rows": 128,
                "best_block_rows": best["block_rows"],
                "best_projected_speedup_vs_128": best[
                    "projected_speedup_vs_128"
                ],
                "rows": rows,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
