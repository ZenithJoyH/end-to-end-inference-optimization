#!/usr/bin/env python3
"""Measure whether position-ordering sparse MLA indices has a net benefit."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import torch

from flaggems_vllm.runtime.backend._thead.fused.flashmla_sparse import (
    flash_mla_sparse_fwd,
)


HQ, DQK, DV, TOPK, SKV = 4, 576, 512, 2048, 8192
SCALE = DQK**-0.5
WARMUP, RUNS, REPEATS = 3, 3, 5


def elapsed_us(fn):
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


def launch(q, kv, indices, sink, lengths):
    return flash_mla_sparse_fwd(
        q,
        kv,
        indices,
        SCALE,
        d_v=DV,
        attn_sink=sink,
        topk_length=lengths,
    )


def make_unique_score_ordered_indices(sq):
    # Random logits make score rank independent of token position, matching the
    # locality characteristic of a non-local sparse selection while preserving
    # unique token ids per row like a real Top-K provider.
    scores = torch.rand((sq, SKV), device="cuda", dtype=torch.float32)
    return torch.topk(scores, TOPK, dim=-1, sorted=True).indices.to(torch.int32)[:, None]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")

    torch.manual_seed(20260919)
    rows = []
    for sq in (128, 512, 2048):
        q = (torch.randn((sq, HQ, DQK), device="cuda") * 0.05).to(torch.bfloat16)
        kv = (torch.randn((SKV, 1, DQK), device="cuda") * 0.05).to(torch.bfloat16)
        score_ordered = make_unique_score_ordered_indices(sq)
        position_ordered = torch.sort(score_ordered, dim=-1).values
        lengths = torch.full((sq,), TOPK, device="cuda", dtype=torch.int32)
        sink = torch.randn((HQ,), device="cuda", dtype=torch.float32)

        baseline_out = launch(q, kv, score_ordered, sink, lengths)
        ordered_out = launch(q, kv, position_ordered, sink, lengths)
        torch.cuda.synchronize()
        max_abs_error = [
            float((actual.float() - expected.float()).abs().max())
            for actual, expected in zip(ordered_out, baseline_out)
        ]
        for actual, expected in zip(ordered_out, baseline_out):
            torch.testing.assert_close(actual, expected, atol=2e-2, rtol=2e-2)

        baseline_samples = elapsed_us(
            lambda: launch(q, kv, score_ordered, sink, lengths)
        )
        ordered_samples = elapsed_us(
            lambda: launch(q, kv, position_ordered, sink, lengths)
        )
        sort_samples = elapsed_us(lambda: torch.sort(score_ordered, dim=-1).values)
        combined_samples = elapsed_us(
            lambda: launch(
                q,
                kv,
                torch.sort(score_ordered, dim=-1).values,
                sink,
                lengths,
            )
        )

        baseline_median = statistics.median(baseline_samples)
        ordered_median = statistics.median(ordered_samples)
        sort_median = statistics.median(sort_samples)
        combined_median = statistics.median(combined_samples)
        row = {
            "sq": sq,
            "max_abs_error": max_abs_error,
            "baseline_samples_us": baseline_samples,
            "ordered_attention_samples_us": ordered_samples,
            "sort_samples_us": sort_samples,
            "combined_samples_us": combined_samples,
            "baseline_median_us": baseline_median,
            "ordered_attention_median_us": ordered_median,
            "sort_median_us": sort_median,
            "combined_median_us": combined_median,
            "attention_only_speedup": baseline_median / ordered_median,
            "combined_speedup": baseline_median / combined_median,
        }
        rows.append(row)
        print(json.dumps(row), flush=True)

    large = [row for row in rows if row["sq"] in (512, 2048)]
    status = (
        "candidate"
        if all(row["combined_speedup"] >= 1.05 for row in large)
        else "rejected"
    )
    result = {
        "schema_version": 1,
        "status": status,
        "candidate": "position_order_sparse_indices_including_torch_sort_cost",
        "baseline": "score_order_sparse_indices",
        "shapes": {"hq": HQ, "dqk": DQK, "dv": DV, "topk": TOPK, "skv": SKV},
        "threshold": "SQ512 and SQ2048 combined speedup >= 1.05",
        "scope": "operator upper bound with unique random Top-K indices",
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print("SUMMARY=" + json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
