#!/usr/bin/env python3
"""Compare PPU native sparse MLA with the active FlagGems-vllm T-Head path."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import torch

from flash_mla import flash_mla_sparse_fwd as native_sparse_mla
from flaggems_vllm.runtime.backend._thead.fused.flashmla_sparse import (
    flash_mla_sparse_fwd as flaggems_sparse_mla,
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


def graph_replay(fn):
    for _ in range(3):
        fn()
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        fn()
    graph.replay()
    graph.replay()
    torch.cuda.synchronize()


def score_order_indices(sq: int):
    rows = torch.arange(sq, device="cuda", dtype=torch.int64)[:, None]
    positions = torch.arange(TOPK, device="cuda", dtype=torch.int64)[None, :]
    return ((positions * 4051 + rows * 7919) % SKV).to(torch.int32)[:, None]


def full_prefix_indices(sq: int):
    prefix = torch.arange(TOPK, device="cuda", dtype=torch.int32)
    return prefix.expand(sq, 1, TOPK).contiguous()


def invoke(fn, q, kv, indices, sink, lengths):
    return fn(
        q=q,
        kv=kv,
        indices=indices,
        sm_scale=SCALE,
        d_v=DV,
        attn_sink=sink,
        topk_length=lengths,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")

    torch.manual_seed(20260920)
    kv = (torch.randn((SKV, 1, DQK), device="cuda") * 0.05).to(torch.bfloat16)
    sink = torch.randn((HQ,), device="cuda", dtype=torch.float32)
    rows = []
    for sq in (64, 512, 2029, 2048):
        q = (torch.randn((sq, HQ, DQK), device="cuda") * 0.05).to(torch.bfloat16)
        score_indices = score_order_indices(sq)
        patterns = [
            (
                "score_full_topk",
                score_indices,
                torch.full((sq,), TOPK, device="cuda", dtype=torch.int32),
            ),
            (
                "score_ragged_1024_2048",
                score_indices,
                torch.linspace(1024, TOPK, sq, device="cuda").to(torch.int32),
            ),
        ]
        if sq >= 512:
            patterns.append(
                (
                    "full_prefix",
                    full_prefix_indices(sq),
                    torch.arange(1, sq + 1, device="cuda", dtype=torch.int32).clamp_(
                        max=TOPK
                    ),
                )
            )
        for pattern, indices, lengths in patterns:
            baseline_fn = lambda: invoke(
                flaggems_sparse_mla, q, kv, indices, sink, lengths
            )
            candidate_fn = lambda: invoke(
                native_sparse_mla, q, kv, indices, sink, lengths
            )
            expected = baseline_fn()
            actual = candidate_fn()
            torch.cuda.synchronize()
            output_max_abs_error = float(
                (actual[0].float() - expected[0].float()).abs().max()
            )
            output_cosine = float(
                torch.nn.functional.cosine_similarity(
                    actual[0].float().flatten(),
                    expected[0].float().flatten(),
                    dim=0,
                )
            )
            torch.testing.assert_close(actual[0], expected[0], atol=2e-2, rtol=2e-2)
            baseline_samples = elapsed_us(baseline_fn)
            candidate_samples = elapsed_us(candidate_fn)
            graph_replay(candidate_fn)
            baseline_median = statistics.median(baseline_samples)
            candidate_median = statistics.median(candidate_samples)
            row = {
                "sq": sq,
                "pattern": pattern,
                "baseline_samples_us": baseline_samples,
                "candidate_samples_us": candidate_samples,
                "baseline_median_us": baseline_median,
                "candidate_median_us": candidate_median,
                "speedup": baseline_median / candidate_median,
                "output_max_abs_error": output_max_abs_error,
                "output_cosine": output_cosine,
                "graph_replay": "passed",
            }
            rows.append(row)
            print(json.dumps(row), flush=True)

    dominant_score = [
        row
        for row in rows
        if row["sq"] in (2029, 2048) and row["pattern"].startswith("score_")
    ]
    full_prefix = [
        row
        for row in rows
        if row["sq"] in (512, 2048) and row["pattern"] == "full_prefix"
    ]
    status = (
        "candidate"
        if min(row["speedup"] for row in dominant_score) >= 1.05
        and min(row["speedup"] for row in full_prefix) >= 0.98
        and max(row["output_max_abs_error"] for row in rows) <= 2e-2
        and min(row["output_cosine"] for row in rows) >= 0.9999
        else "rejected"
    )
    result = {
        "schema_version": 1,
        "status": status,
        "candidate": "ppu_native_flash_mla_sparse_fwd",
        "baseline": "flaggems_vllm_thead_sparse_mla",
        "threshold": "SQ2029/SQ2048 score patterns >=1.05x, SQ512/SQ2048 full-prefix >=0.98x, output atol/rtol 2e-2, cosine >=0.9999, graph replay passes",
        "shape": {"hq": HQ, "dqk": DQK, "dv": DV, "topk": TOPK, "skv": SKV},
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("SUMMARY=" + json.dumps(result), flush=True)
    return 0 if status == "candidate" else 2


if __name__ == "__main__":
    raise SystemExit(main())
