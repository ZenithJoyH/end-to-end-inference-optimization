#!/usr/bin/env python3
"""Benchmark native score-selected rows plus FlagGems full-prefix groups."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import torch
import triton

from flash_mla import flash_mla_sparse_fwd as native_sparse_mla
from flaggems_vllm.runtime.backend._thead.fused import flashmla_sparse as thead


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


def full_prefix_inputs(sq: int):
    prefix = torch.arange(TOPK, device="cuda", dtype=torch.int32)
    indices = prefix.expand(sq, 1, TOPK).contiguous()
    lengths = torch.arange(1, sq + 1, device="cuda", dtype=torch.int32).clamp_(
        max=TOPK
    )
    return indices, lengths


def mixed_inputs(sq: int):
    prefix_indices, prefix_lengths = full_prefix_inputs(sq)
    score_indices = score_order_indices(sq)
    indices = score_indices.clone()
    lengths = torch.full((sq,), TOPK, device="cuda", dtype=torch.int32)
    groups = torch.arange(sq, device="cuda") // thead._FULL_PREFIX_GROUP_SIZE
    prefix_rows = (groups % 2) == 0
    indices[prefix_rows] = prefix_indices[prefix_rows]
    lengths[prefix_rows] = prefix_lengths[prefix_rows]
    return indices, lengths


def hybrid(q, kv, indices, sink, lengths):
    sq = q.shape[0]
    num_groups = triton.cdiv(sq, thead._FULL_PREFIX_GROUP_SIZE)
    group_flags = torch.empty((num_groups,), device=q.device, dtype=torch.int32)
    legacy_lengths = torch.empty_like(lengths)
    thead._classify_full_prefix_groups[(num_groups,)](
        indices,
        lengths,
        group_flags,
        legacy_lengths,
        indices.stride(0),
        sq,
        TOPK=TOPK,
        GROUP_SIZE=thead._FULL_PREFIX_GROUP_SIZE,
        BLOCK=thead._FULL_PREFIX_CLASSIFY_BLOCK,
        num_warps=4,
        num_stages=1,
    )
    output, max_logits, lse = native_sparse_mla(
        q=q,
        kv=kv,
        indices=indices,
        sm_scale=SCALE,
        d_v=DV,
        attn_sink=sink,
        topk_length=legacy_lengths,
    )
    thead._flash_mla_sparse_full_prefix_grouped[(num_groups,)](
        q,
        kv,
        indices,
        sink,
        lengths,
        group_flags,
        output,
        max_logits,
        lse,
        q.stride(0),
        q.stride(1),
        kv.stride(0),
        indices.stride(0),
        output.stride(0),
        output.stride(1),
        max_logits.stride(0),
        lse.stride(0),
        sq,
        kv.shape[0],
        SM_SCALE=SCALE,
        HQ=HQ,
        DV=DV,
        BDP=thead._SPLITK_BDP,
        BK=32,
        GROUP_SIZE=thead._FULL_PREFIX_GROUP_SIZE,
        BH=thead._FULL_PREFIX_GROUP_SIZE * HQ,
        num_warps=4,
        num_stages=1,
    )
    return output, max_logits, lse


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
    for sq in (512, 2029, 2048):
        q = (torch.randn((sq, HQ, DQK), device="cuda") * 0.05).to(torch.bfloat16)
        score_indices = score_order_indices(sq)
        patterns = [
            (
                "score_full_topk",
                score_indices,
                torch.full((sq,), TOPK, device="cuda", dtype=torch.int32),
            ),
            ("full_prefix", *full_prefix_inputs(sq)),
            ("alternating_prefix_score_groups", *mixed_inputs(sq)),
        ]
        for pattern, indices, lengths in patterns:
            baseline_fn = lambda: thead.flash_mla_sparse_fwd(
                q,
                kv,
                indices,
                SCALE,
                d_v=DV,
                attn_sink=sink,
                topk_length=lengths,
            )
            candidate_fn = lambda: hybrid(q, kv, indices, sink, lengths)
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

    dominant = [row for row in rows if row["sq"] in (2029, 2048)]
    score = [row for row in dominant if row["pattern"] == "score_full_topk"]
    prefix = [row for row in dominant if row["pattern"] == "full_prefix"]
    mixed = [
        row
        for row in dominant
        if row["pattern"] == "alternating_prefix_score_groups"
    ]
    status = (
        "candidate"
        if min(row["speedup"] for row in score) >= 1.05
        and min(row["speedup"] for row in prefix) >= 0.98
        and min(row["speedup"] for row in mixed) >= 1.03
        and max(row["output_max_abs_error"] for row in rows) <= 2e-2
        and min(row["output_cosine"] for row in rows) >= 0.9999
        else "rejected"
    )
    result = {
        "schema_version": 1,
        "status": status,
        "candidate": "native_score_selected_plus_flaggems_full_prefix_groups",
        "baseline": "flaggems_vllm_thead_sparse_mla",
        "threshold": "dominant score >=1.05x, full-prefix >=0.98x, alternating mixed >=1.03x, output atol/rtol 2e-2, cosine >=0.9999, graph replay passes",
        "shape": {"hq": HQ, "dqk": DQK, "dv": DV, "topk": TOPK, "skv": SKV},
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("SUMMARY=" + json.dumps(result), flush=True)
    return 0 if status == "candidate" else 2


if __name__ == "__main__":
    raise SystemExit(main())
