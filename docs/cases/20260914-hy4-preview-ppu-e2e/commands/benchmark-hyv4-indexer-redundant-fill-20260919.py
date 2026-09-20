#!/usr/bin/env python3
"""Verify and time removal of the redundant block-output fill."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import torch

from vllm_fl.models import hy_v4


WARMUP = 3
RUNS = 5
REPEATS = 9
HEADS = 32
HEAD_DIM = 128
TOPK = 2048
SENTINEL = 123456789


def candidate(
    q: torch.Tensor,
    weights: torch.Tensor,
    keys: torch.Tensor,
    row_starts: torch.Tensor,
    row_ends: torch.Tensor,
    output: torch.Tensor,
) -> None:
    key_start = 0
    key_end = keys.shape[0]
    scores = torch.matmul(keys.unsqueeze(0), q.transpose(1, 2))
    logits = hy_v4._hyv4_weighted_relu_reduce(scores, weights)
    local_starts = row_starts - key_start
    local_ends = row_ends - key_start
    selected = output[:, :TOPK]
    hy_v4._top_k_per_row_prefill(
        logits,
        local_starts.contiguous(),
        local_ends.contiguous(),
        selected,
    )
    hy_v4._translate_hyv4_selected_block(selected, row_starts, 0)


def baseline(
    q: torch.Tensor,
    weights: torch.Tensor,
    keys: torch.Tensor,
    row_starts: torch.Tensor,
    row_ends: torch.Tensor,
    output: torch.Tensor,
) -> None:
    hy_v4._select_topk_block(
        q,
        weights,
        keys,
        row_starts,
        row_ends,
        key_start=0,
        key_end=keys.shape[0],
        request_start=0,
        topk=TOPK,
        output=output,
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


def timing(samples: list[float]) -> dict:
    return {
        "median_us": statistics.median(samples),
        "min_us": min(samples),
        "max_us": max(samples),
        "samples_us": samples,
    }


def score_multisets(
    output: torch.Tensor,
    logits: torch.Tensor,
    row_starts: torch.Tensor,
) -> list[torch.Tensor]:
    rows = []
    for row in range(output.shape[0]):
        selected = output[row]
        valid = selected >= 0
        local = selected[valid] - row_starts[row]
        rows.append(torch.sort(logits[row, local.long()]).values)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")
    assert torch.cuda.is_available()
    torch.manual_seed(20260919)

    results = []
    for rows, keys_count in ((26, 4096), (128, 2048), (128, 4096)):
        q = torch.randn(
            (rows, HEADS, HEAD_DIM), device="cuda", dtype=torch.bfloat16
        )
        keys = torch.randn(
            (keys_count, HEAD_DIM), device="cuda", dtype=torch.bfloat16
        )
        weights = torch.randn(
            (rows, HEADS), device="cuda", dtype=torch.bfloat16
        )
        row_starts = torch.zeros((rows,), device="cuda", dtype=torch.int32)
        lower = max(1, keys_count - rows + 1)
        row_ends = torch.arange(
            lower, lower + rows, device="cuda", dtype=torch.int32
        ).clamp_max_(keys_count)
        baseline_output = torch.empty(
            (rows, TOPK), device="cuda", dtype=torch.int32
        )
        candidate_output = torch.full_like(baseline_output, SENTINEL)
        baseline(q, weights, keys, row_starts, row_ends, baseline_output)
        candidate(q, weights, keys, row_starts, row_ends, candidate_output)
        scores = torch.matmul(keys.unsqueeze(0), q.transpose(1, 2))
        logits = hy_v4._hyv4_weighted_relu_reduce(scores, weights)
        torch.cuda.synchronize()
        sentinel_remaining = int((candidate_output == SENTINEL).sum().item())
        expected_counts = torch.minimum(
            row_ends - row_starts,
            torch.full_like(row_ends, TOPK),
        )
        candidate_counts = (candidate_output >= 0).sum(dim=1)
        valid_counts_exact = bool(torch.equal(expected_counts, candidate_counts))
        baseline_scores = score_multisets(
            baseline_output, logits, row_starts
        )
        candidate_scores = score_multisets(
            candidate_output, logits, row_starts
        )
        selected_score_multisets_exact = all(
            torch.equal(expected, actual)
            for expected, actual in zip(baseline_scores, candidate_scores)
        )
        assert sentinel_remaining == 0
        assert valid_counts_exact
        assert selected_score_multisets_exact

        baseline_stats = timing(
            elapsed_us(
                lambda: baseline(
                    q,
                    weights,
                    keys,
                    row_starts,
                    row_ends,
                    baseline_output,
                )
            )
        )
        candidate_stats = timing(
            elapsed_us(
                lambda: candidate(
                    q,
                    weights,
                    keys,
                    row_starts,
                    row_ends,
                    candidate_output,
                )
            )
        )
        results.append(
            {
                "rows": rows,
                "keys": keys_count,
                "topk": TOPK,
                "sentinel_remaining": sentinel_remaining,
                "valid_counts_exact": valid_counts_exact,
                "selected_score_multisets_exact": selected_score_multisets_exact,
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
        "shapes": results,
        "conclusion_boundary": (
            "synthetic complete Indexer block only; provider overwrite and "
            "selected-score multisets verified, no service claim"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
