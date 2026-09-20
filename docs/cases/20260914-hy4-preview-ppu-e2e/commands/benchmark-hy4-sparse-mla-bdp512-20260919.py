#!/usr/bin/env python3
"""Compare the retained HQ4 sparse-MLA kernel with a 512-wide D/V tile."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import torch
import triton
import triton.language as tl

from flaggems_vllm.ops.flashmla_sparse import triton_flash_mla_sparse_fwd


HQ, DQK, DV, TOPK, SKV = 4, 576, 512, 2048, 8192
BK = 32
SCALE = DQK**-0.5
WARMUP, RUNS, REPEATS = 3, 5, 7


@triton.jit
def sparse_mla_hq4_bdp512(
    q,
    kv,
    indices,
    attn_sink,
    topk_length,
    output,
    max_logits,
    lse,
    stride_qm,
    stride_qh,
    stride_kvn,
    stride_tm,
    stride_om,
    stride_oh,
    stride_mm,
    stride_lm,
    sq,
    skv,
    SM_SCALE: tl.constexpr,
    HQC: tl.constexpr,
    DVC: tl.constexpr,
    BKX: tl.constexpr,
):
    row = tl.program_id(0).to(tl.int64)
    offs_h = tl.arange(0, HQC)
    offs_d = tl.arange(0, DVC)
    offs_t = tl.arange(0, BKX)
    offs_tail = tl.arange(0, 64)

    q_base = q + row * stride_qm
    q_main = tl.load(
        q_base + offs_h[:, None] * stride_qh + offs_d[None, :],
        eviction_policy="evict_first",
    )
    q_tail = tl.load(
        q_base + offs_h[:, None] * stride_qh + DVC + offs_tail[None, :],
        eviction_policy="evict_first",
    )
    valid_topk = tl.load(topk_length + row)
    index_base = indices + row * stride_tm

    max_log = tl.full([HQC], float("-inf"), dtype=tl.float32)
    sum_exp = tl.zeros([HQC], dtype=tl.float32)
    acc = tl.zeros([HQC, DVC], dtype=tl.float32)
    num_blocks = tl.cdiv(valid_topk, BKX)
    for block_id in range(num_blocks):
        positions = block_id * BKX + offs_t
        position_mask = positions < valid_topk
        kv_ids = tl.load(index_base + positions, mask=position_mask, other=-1)
        valid_ids = position_mask & (kv_ids >= 0) & (kv_ids < skv)
        safe_ids = tl.where(valid_ids, kv_ids, 0)
        kv_main = tl.load(
            kv + safe_ids[None, :] * stride_kvn + offs_d[:, None],
            cache_modifier=".cg",
        )
        kv_tail = tl.load(
            kv + safe_ids[None, :] * stride_kvn + DVC + offs_tail[:, None],
            cache_modifier=".cg",
        )
        qk = tl.dot(q_main, kv_main, out_dtype=tl.float32)
        qk = tl.dot(q_tail, kv_tail, qk, out_dtype=tl.float32) * SM_SCALE
        qk = tl.where(valid_ids[None, :], qk, float("-inf"))
        new_max = tl.maximum(max_log, tl.max(qk, axis=1))
        exp_qk = tl.where(
            valid_ids[None, :], tl.exp(qk - new_max[:, None]), 0.0
        )
        alpha = tl.where(
            max_log != float("-inf"), tl.exp(max_log - new_max), 0.0
        )
        sum_exp = sum_exp * alpha + tl.sum(exp_qk, axis=1)
        acc = tl.dot(
            exp_qk.to(tl.bfloat16),
            kv_main.trans(),
            acc * alpha[:, None],
            out_dtype=tl.float32,
        )
        max_log = new_max

    valid = max_log != float("-inf")
    original_lse = max_log + tl.log(sum_exp)
    sink = tl.load(attn_sink + offs_h)
    denominator = tl.exp(original_lse) + tl.exp(sink)
    factor = tl.exp(max_log) / denominator
    result = tl.where(valid[:, None], acc * factor[:, None], 0.0)
    tl.store(
        output
        + row * stride_om
        + offs_h[:, None] * stride_oh
        + offs_d[None, :],
        result.to(tl.bfloat16),
    )
    stat = row * stride_mm + offs_h
    tl.store(max_logits + stat, tl.where(valid, max_log, float("-inf")))
    tl.store(
        lse + row * stride_lm + offs_h,
        tl.where(valid, original_lse, float("inf")),
    )


def outputs(sq: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    return (
        torch.empty((sq, HQ, DV), device="cuda", dtype=torch.bfloat16),
        torch.empty((sq, HQ), device="cuda", dtype=torch.float32),
        torch.empty((sq, HQ), device="cuda", dtype=torch.float32),
    )


def launch_baseline(q, kv, indices, sink, lengths, result) -> None:
    sq = q.shape[0]
    output, max_logits, lse = result
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
        BK=BK,
        BH=HQ,
        num_warps=4,
        num_stages=1,
    )


def launch_candidate(q, kv, indices, sink, lengths, result) -> None:
    sq = q.shape[0]
    output, max_logits, lse = result
    sparse_mla_hq4_bdp512[(sq,)](
        q,
        kv,
        indices,
        sink,
        lengths,
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
        HQC=HQ,
        DVC=DV,
        BKX=BK,
        num_warps=4,
        num_stages=1,
    )


def measure(fn) -> list[float]:
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
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")

    torch.manual_seed(20260919)
    kv = (torch.randn((SKV, 1, DQK), device="cuda") * 0.05).to(
        torch.bfloat16
    )
    sink = torch.randn((HQ,), device="cuda", dtype=torch.float32)
    rows = []
    for sq in (64, 128, 512, 2048):
        q = (torch.randn((sq, HQ, DQK), device="cuda") * 0.05).to(
            torch.bfloat16
        )
        indices = torch.randint(
            0, SKV, (sq, 1, TOPK), device="cuda", dtype=torch.int32
        )
        lengths = torch.full(
            (sq,), TOPK, device="cuda", dtype=torch.int32
        )
        baseline = outputs(sq)
        candidate = outputs(sq)
        baseline_fn = lambda: launch_baseline(
            q, kv, indices, sink, lengths, baseline
        )
        candidate_fn = lambda: launch_candidate(
            q, kv, indices, sink, lengths, candidate
        )
        row = {"sq": sq}
        try:
            baseline_fn()
            candidate_fn()
            torch.cuda.synchronize()
            errors = [
                float((actual.float() - expected.float()).abs().max())
                for actual, expected in zip(candidate, baseline)
            ]
            for actual, expected in zip(candidate, baseline):
                torch.testing.assert_close(
                    actual, expected, atol=2e-2, rtol=2e-2
                )
            baseline_samples = measure(baseline_fn)
            candidate_samples = measure(candidate_fn)
            graph_replay(candidate_fn)
            baseline_median = statistics.median(baseline_samples)
            candidate_median = statistics.median(candidate_samples)
            row.update(
                status="passed",
                max_abs_error=errors,
                baseline_samples_us=baseline_samples,
                candidate_samples_us=candidate_samples,
                baseline_median_us=baseline_median,
                candidate_median_us=candidate_median,
                speedup=baseline_median / candidate_median,
                graph_replay="passed",
            )
        except Exception as exc:
            row.update(status="failed", error=repr(exc))
            torch.cuda.synchronize()
        rows.append(row)
        print(json.dumps(row), flush=True)

    passed = [row for row in rows if row["status"] == "passed"]
    large = [row for row in passed if row["sq"] in (512, 2048)]
    status = (
        "candidate"
        if len(large) == 2 and min(row["speedup"] for row in large) >= 1.05
        else "rejected"
    )
    payload = {
        "status": status,
        "hypothesis": "HQ4 can use one 512-wide QK/PV tile instead of the generic 256+256 value path",
        "guard": {
            "hq": HQ,
            "dqk": DQK,
            "dv": DV,
            "topk": TOPK,
            "dtype": "bfloat16",
            "bk": BK,
        },
        "threshold": "SQ512 and SQ2048 both >=1.05x, numerical checks and graph replay pass",
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=False)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "status": status}))
    return 0 if status == "candidate" else 2


if __name__ == "__main__":
    raise SystemExit(main())
