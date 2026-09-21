#!/usr/bin/env python3
"""Confirm the boundary SQ2048 result with interleaved random Top-K inputs."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import torch

from flaggems_vllm.runtime.backend._thead.fused import flashmla_sparse as thead


HQ, DQK, DV, TOPK, SKV, SQ = 4, 576, 512, 2048, 16384, 2048
SCALE = DQK**-0.5
RUNS, REPEATS = 3, 9


def elapsed_us(fn):
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    start.record()
    for _ in range(RUNS):
        fn()
    end.record()
    end.synchronize()
    return start.elapsed_time(end) * 1000.0 / RUNS


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")

    rows = []
    for seed in (20260921, 20260922, 20260923):
        torch.manual_seed(seed)
        q = (torch.randn((SQ, HQ, DQK), device="cuda") * 0.05).to(torch.bfloat16)
        kv = (torch.randn((SKV, 1, DQK), device="cuda") * 0.05).to(torch.bfloat16)
        sink = torch.randn((HQ,), device="cuda", dtype=torch.float32)
        # Random score ranking over unique token ids without materializing a
        # SQ x SKV score matrix: every row is an independent affine permutation.
        positions = torch.arange(TOPK, device="cuda", dtype=torch.int64)[None, :]
        row = torch.arange(SQ, device="cuda", dtype=torch.int64)[:, None]
        multipliers = torch.tensor(
            [8191, 12289, 16381], device="cuda", dtype=torch.int64
        )
        multiplier = multipliers[seed - 20260921]
        indices = ((positions * multiplier + row * 7919) % SKV).to(torch.int32)
        indices = indices[:, None]
        lengths = torch.full((SQ,), TOPK, device="cuda", dtype=torch.int32)

        baseline = lambda: thead.flash_mla_sparse_fwd(
            q,
            kv,
            indices,
            SCALE,
            d_v=DV,
            attn_sink=sink,
            topk_length=lengths,
        )
        candidate = lambda: thead.flash_mla_sparse_cached_prefill_fwd(
            q,
            kv,
            indices,
            SCALE,
            d_v=DV,
            attn_sink=sink,
            topk_length=lengths,
        )
        expected = baseline()
        actual = candidate()
        torch.cuda.synchronize()
        torch.testing.assert_close(actual[0], expected[0], atol=2e-2, rtol=2e-2)
        max_abs_error = float((actual[0].float() - expected[0].float()).abs().max())
        cosine = float(
            torch.nn.functional.cosine_similarity(
                actual[0].float().flatten(), expected[0].float().flatten(), dim=0
            )
        )
        for _ in range(3):
            baseline()
            candidate()
        torch.cuda.synchronize()

        pairs = []
        for repeat in range(REPEATS):
            if repeat % 2 == 0:
                baseline_us = elapsed_us(baseline)
                candidate_us = elapsed_us(candidate)
            else:
                candidate_us = elapsed_us(candidate)
                baseline_us = elapsed_us(baseline)
            pairs.append(
                {
                    "baseline_us": baseline_us,
                    "candidate_us": candidate_us,
                    "speedup": baseline_us / candidate_us,
                }
            )
        speedups = [pair["speedup"] for pair in pairs]
        item = {
            "seed": seed,
            "pairs": pairs,
            "median_speedup": statistics.median(speedups),
            "minimum_speedup": min(speedups),
            "max_abs_error": max_abs_error,
            "cosine": cosine,
        }
        rows.append(item)
        print(json.dumps(item), flush=True)

    seed_medians = [row["median_speedup"] for row in rows]
    aggregate_median = statistics.median(seed_medians)
    status = (
        "candidate"
        if aggregate_median >= 1.08
        and min(seed_medians) >= 1.05
        and max(row["max_abs_error"] for row in rows) <= 2e-2
        and min(row["cosine"] for row in rows) >= 0.9999
        else "rejected"
    )
    result = {
        "schema_version": 1,
        "status": status,
        "shape": {"sq": SQ, "skv": SKV, "hq": HQ, "dqk": DQK, "dv": DV, "topk": TOPK},
        "method": "three deterministic unique score-order distributions; nine interleaved baseline/candidate pairs per distribution; three launches per event timing",
        "threshold": "median of per-seed medians >=1.08x and every seed median >=1.05x",
        "aggregate_median_speedup": aggregate_median,
        "minimum_seed_median_speedup": min(seed_medians),
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("SUMMARY=" + json.dumps(result), flush=True)
    return 0 if status == "candidate" else 2


if __name__ == "__main__":
    raise SystemExit(main())
