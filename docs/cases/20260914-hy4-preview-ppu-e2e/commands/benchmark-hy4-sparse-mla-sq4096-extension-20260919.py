#!/usr/bin/env python3
"""Validate extending the T-Head HQ4 sparse-MLA path above SQ2048."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import torch

from flaggems_vllm.ops.flashmla_sparse import triton_flash_mla_sparse_fwd
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


def legacy_hq4(q, kv, indices, sink, lengths):
    sq = q.shape[0]
    output = torch.empty((sq, HQ, DV), device=q.device, dtype=q.dtype)
    max_logits = torch.empty((sq, HQ), device=q.device, dtype=torch.float32)
    lse = torch.empty_like(max_logits)
    triton_flash_mla_sparse_fwd.fn[(sq,)](
        q,
        kv,
        indices,
        sink,
        lengths,
        SCALE,
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


def candidate(q, kv, indices, sink, lengths):
    return thead.flash_mla_sparse_fwd(
        q,
        kv,
        indices,
        SCALE,
        d_v=DV,
        attn_sink=sink,
        topk_length=lengths,
    )


def graph_replay(fn) -> None:
    for _ in range(3):
        fn()
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        fn()
    graph.replay()
    graph.replay()
    torch.cuda.synchronize()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")

    original_max = thead._HQ4_PREFILL_MAX_SQ
    thead._HQ4_PREFILL_MAX_SQ = 4096
    torch.manual_seed(20260919)
    kv = (torch.randn((SKV, 1, DQK), device="cuda") * 0.05).to(
        torch.bfloat16
    )
    sink = torch.randn((HQ,), device="cuda", dtype=torch.float32)
    rows = []
    try:
        for sq in (2560, 3072, 4096):
            q = (torch.randn((sq, HQ, DQK), device="cuda") * 0.05).to(
                torch.bfloat16
            )
            prefix = torch.arange(TOPK, device="cuda", dtype=torch.int32)
            full_indices = prefix.expand(sq, 1, TOPK).contiguous()
            full_lengths = torch.clamp(
                torch.arange(1, sq + 1, device="cuda", dtype=torch.int32),
                max=TOPK,
            )
            random_indices = torch.randint(
                0,
                SKV,
                (sq, 1, TOPK),
                device="cuda",
                dtype=torch.int32,
            )
            random_lengths = torch.full(
                (sq,), TOPK, device="cuda", dtype=torch.int32
            )
            for pattern, indices, lengths in (
                ("prefix_then_capped", full_indices, full_lengths),
                ("random_topk", random_indices, random_lengths),
            ):
                baseline_fn = lambda: legacy_hq4(
                    q, kv, indices, sink, lengths
                )
                candidate_fn = lambda: candidate(
                    q, kv, indices, sink, lengths
                )
                expected = baseline_fn()
                actual = candidate_fn()
                torch.cuda.synchronize()
                errors = [
                    float((a.float() - e.float()).abs().max())
                    for a, e in zip(actual, expected)
                ]
                for a, e in zip(actual, expected):
                    torch.testing.assert_close(
                        a, e, atol=2e-2, rtol=2e-2
                    )
                baseline_samples = elapsed_us(baseline_fn)
                candidate_samples = elapsed_us(candidate_fn)
                graph_replay(candidate_fn)
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
                    "graph_replay": "passed",
                }
                rows.append(row)
                print(json.dumps(row), flush=True)
    finally:
        thead._HQ4_PREFILL_MAX_SQ = original_max

    random_rows = [row for row in rows if row["pattern"] == "random_topk"]
    status = (
        "candidate"
        if len(random_rows) == 3
        and min(row["speedup"] for row in random_rows) >= 0.98
        else "rejected"
    )
    payload = {
        "schema_version": 1,
        "status": status,
        "candidate": "extend_thead_hq4_prefill_max_sq_2048_to_4096",
        "baseline": "legacy_hq4_bh4_bk32_w4_s1",
        "threshold": "random TopK >=0.98x at SQ2560/3072/4096; numerical and graph replay pass",
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=False)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "status": status}))
    return 0 if status == "candidate" else 2


if __name__ == "__main__":
    raise SystemExit(main())
