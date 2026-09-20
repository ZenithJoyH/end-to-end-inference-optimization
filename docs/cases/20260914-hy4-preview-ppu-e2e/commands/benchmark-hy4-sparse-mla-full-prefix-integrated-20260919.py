#!/usr/bin/env python3
"""Benchmark integrated T-Head full-prefix grouping and fallback overhead."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import torch

from flaggems_vllm.ops.flashmla_sparse import (
    triton_flash_mla_sparse_fwd,
)
from flaggems_vllm.runtime.backend._thead.fused.flashmla_sparse import (
    flash_mla_sparse_fwd as candidate_flash_mla_sparse_fwd,
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


def invoke(fn, q, kv, indices, sink, lengths):
    return fn(
        q,
        kv,
        indices,
        SCALE,
        d_v=DV,
        attn_sink=sink,
        topk_length=lengths,
    )


def legacy_hq4(q, kv, indices, scale, d_v, attn_sink, topk_length):
    del d_v
    sq = q.shape[0]
    output = torch.empty((sq, HQ, DV), device=q.device, dtype=q.dtype)
    max_logits = torch.empty((sq, HQ), device=q.device, dtype=torch.float32)
    lse = torch.empty_like(max_logits)
    triton_flash_mla_sparse_fwd.fn[(sq,)](
        q,
        kv,
        indices,
        attn_sink,
        topk_length,
        scale,
        output,
        max_logits,
        lse,
        q.stride(1),
        q.stride(0),
        kv.stride(1),
        kv.stride(0),
        indices.stride(1),
        indices.stride(0),
        output.stride(1),
        output.stride(0),
        max_logits.stride(0),
        lse.stride(0),
        sq,
        HQ,
        DQK,
        kv.shape[0],
        TOPK,
        True,
        True,
        BK=32,
        BH=HQ,
        num_warps=4,
        num_stages=1,
    )
    return output, max_logits, lse


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
        sink = torch.randn((HQ,), device="cuda", dtype=torch.float32)
        prefix = torch.arange(TOPK, device="cuda", dtype=torch.int32)
        full_indices = prefix.expand(sq, 1, TOPK).contiguous()
        full_lengths = torch.clamp(
            torch.arange(1, sq + 1, device="cuda", dtype=torch.int32), max=TOPK
        )
        random_scores = torch.rand((sq, SKV), device="cuda", dtype=torch.float32)
        random_indices = torch.topk(
            random_scores, TOPK, dim=-1, sorted=True
        ).indices.to(torch.int32)[:, None]
        random_lengths = torch.full(
            (sq,), TOPK, device="cuda", dtype=torch.int32
        )
        for pattern, indices, lengths in (
            ("full_prefix", full_indices, full_lengths),
            ("random_topk", random_indices, random_lengths),
        ):
            baseline = lambda: invoke(
                legacy_hq4, q, kv, indices, sink, lengths
            )
            candidate = lambda: invoke(
                candidate_flash_mla_sparse_fwd, q, kv, indices, sink, lengths
            )
            expected = baseline()
            actual = candidate()
            torch.cuda.synchronize()
            errors = [
                float((a.float() - e.float()).abs().max())
                for a, e in zip(actual, expected)
            ]
            for a, e in zip(actual, expected):
                torch.testing.assert_close(a, e, atol=2e-2, rtol=2e-2)
            baseline_samples = elapsed_us(baseline)
            candidate_samples = elapsed_us(candidate)
            baseline_median = statistics.median(baseline_samples)
            candidate_median = statistics.median(candidate_samples)
            row = {
                "sq": sq,
                "pattern": pattern,
                "max_abs_error": errors,
                "baseline_samples_us": baseline_samples,
                "candidate_samples_us": candidate_samples,
                "baseline_median_us": baseline_median,
                "candidate_median_us": candidate_median,
                "speedup": baseline_median / candidate_median,
            }
            rows.append(row)
            print(json.dumps(row), flush=True)
    full_large = [
        row
        for row in rows
        if row["pattern"] == "full_prefix" and row["sq"] in (512, 2048)
    ]
    fallback = [row for row in rows if row["pattern"] == "random_topk"]
    status = (
        "candidate"
        if all(row["speedup"] >= 1.10 for row in full_large)
        and all(row["speedup"] >= 0.95 for row in fallback)
        else "rejected"
    )
    result = {
        "schema_version": 1,
        "status": status,
        "candidate": "integrated_thead_full_prefix_bq4_grouping",
        "baseline": "legacy_hq4_bh4_bk32_w4_s1",
        "threshold": "full-prefix SQ512/SQ2048 >=1.10x; fallback >=0.95x",
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print("SUMMARY=" + json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
