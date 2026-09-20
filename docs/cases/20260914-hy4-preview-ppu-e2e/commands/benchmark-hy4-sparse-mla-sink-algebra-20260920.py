#!/usr/bin/env python3
"""Benchmark exp2 online softmax for T-Head HQ4 score-selected sparse MLA."""

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
BDP, BK = 256, 32
SCALE = DQK**-0.5
WARMUP, RUNS, REPEATS = 3, 3, 5


@triton.jit
def _hq4_sink_algebra_candidate(
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
    skv,
    SM_SCALE: tl.constexpr,
    HQC: tl.constexpr,
    DVC: tl.constexpr,
    BDPC: tl.constexpr,
    BKC: tl.constexpr,
    USE_EXP2: tl.constexpr,
):
    row = tl.program_id(0)
    offs_h = tl.arange(0, HQC)
    offs_d = tl.arange(0, BDPC)
    offs_t = tl.arange(0, BKC)
    offs_td = tl.arange(0, 64)

    q_base = q + row * stride_qm
    q0 = tl.load(
        q_base + offs_h[:, None] * stride_qh + offs_d[None, :],
        eviction_policy="evict_first",
    )
    q1 = tl.load(
        q_base + offs_h[:, None] * stride_qh + BDPC + offs_d[None, :],
        eviction_policy="evict_first",
    )
    qt = tl.load(
        q_base + offs_h[:, None] * stride_qh + DVC + offs_td[None, :],
        eviction_policy="evict_first",
    )

    max_log = tl.full([HQC], float("-inf"), dtype=tl.float32)
    sum_exp = tl.zeros([HQC], dtype=tl.float32)
    acc0 = tl.zeros([HQC, BDPC], dtype=tl.float32)
    acc1 = tl.zeros([HQC, BDPC], dtype=tl.float32)
    topk_len = tl.load(topk_length + row)
    index_base = indices + row * stride_tm
    num_blocks = tl.cdiv(topk_len, BKC)

    for block_id in range(num_blocks):
        positions = block_id * BKC + offs_t
        position_mask = positions < topk_len
        kv_ids = tl.load(index_base + positions, mask=position_mask, other=-1)
        valid_ids = position_mask & (kv_ids >= 0) & (kv_ids < skv)
        safe_ids = tl.where(valid_ids, kv_ids, 0)
        kv0 = tl.load(
            kv + safe_ids[None, :] * stride_kvn + offs_d[:, None],
            cache_modifier=".cg",
        )
        kv1 = tl.load(
            kv
            + safe_ids[None, :] * stride_kvn
            + BDPC
            + offs_d[:, None],
            cache_modifier=".cg",
        )
        kvt = tl.load(
            kv
            + safe_ids[None, :] * stride_kvn
            + DVC
            + offs_td[:, None],
            cache_modifier=".cg",
        )
        qk = tl.dot(q0, kv0, out_dtype=tl.float32)
        qk = tl.dot(q1, kv1, qk, out_dtype=tl.float32)
        qk = tl.dot(qt, kvt, qk, out_dtype=tl.float32) * SM_SCALE
        qk = tl.where(valid_ids[None, :], qk, float("-inf"))
        new_max = tl.maximum(max_log, tl.max(qk, axis=1))
        if USE_EXP2:
            exp_qk = tl.math.exp2(
                (qk - new_max[:, None]) * 1.4426950408889634
            )
            alpha = tl.math.exp2((max_log - new_max) * 1.4426950408889634)
        else:
            exp_qk = tl.math.exp(qk - new_max[:, None])
            alpha = tl.math.exp(max_log - new_max)
        sum_exp = sum_exp * alpha + tl.sum(exp_qk, axis=1)
        acc0 = tl.dot(
            exp_qk.to(tl.bfloat16),
            kv0.trans(),
            acc0 * alpha[:, None],
            out_dtype=tl.float32,
        )
        acc1 = tl.dot(
            exp_qk.to(tl.bfloat16),
            kv1.trans(),
            acc1 * alpha[:, None],
            out_dtype=tl.float32,
        )
        max_log = new_max

    valid = max_log != float("-inf")
    if USE_EXP2:
        orig_lse = max_log + tl.math.log2(sum_exp) * 0.6931471805599453
    else:
        orig_lse = max_log + tl.math.log(sum_exp)
    sink = tl.load(attn_sink + offs_h)
    if USE_EXP2:
        factor = 1.0 / (
            sum_exp + tl.math.exp2((sink - max_log) * 1.4426950408889634)
        )
    else:
        factor = 1.0 / (sum_exp + tl.math.exp(sink - max_log))
    out0 = tl.where(valid[:, None], acc0 * factor[:, None], 0.0)
    out1 = tl.where(valid[:, None], acc1 * factor[:, None], 0.0)

    out_base = output + row * stride_om + offs_h[:, None] * stride_oh
    tl.store(out_base + offs_d[None, :], out0.to(tl.bfloat16))
    tl.store(out_base + BDPC + offs_d[None, :], out1.to(tl.bfloat16))
    stat_offset = row * stride_mm + offs_h
    tl.store(max_logits + stat_offset, tl.where(valid, max_log, float("-inf")))
    lse_offset = row * stride_lm + offs_h
    tl.store(lse + lse_offset, tl.where(valid, orig_lse, float("inf")))


def buffers(sq: int, device: torch.device):
    output = torch.empty((sq, HQ, DV), device=device, dtype=torch.bfloat16)
    max_logits = torch.empty((sq, HQ), device=device, dtype=torch.float32)
    return output, max_logits, torch.empty_like(max_logits)


def launch_baseline(q, kv, indices, sink, lengths, out):
    output, max_logits, lse = out
    sq = q.shape[0]
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
    return out


def launch_candidate(q, kv, indices, sink, lengths, out):
    output, max_logits, lse = out
    _hq4_sink_algebra_candidate[(q.shape[0],)](
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
        kv.shape[0],
        SM_SCALE=SCALE,
        HQC=HQ,
        DVC=DV,
        BDPC=BDP,
        BKC=BK,
        USE_EXP2=True,
        num_warps=4,
        num_stages=1,
    )
    return out


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
    # An odd multiplier is a permutation modulo the power-of-two SKV.
    return ((positions * 4051 + rows * 7919) % SKV).to(torch.int32)[:, None]


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
        indices = score_order_indices(sq)
        for pattern, lengths in (
            (
                "full_topk",
                torch.full((sq,), TOPK, device="cuda", dtype=torch.int32),
            ),
            (
                "ragged_1024_2048",
                torch.linspace(1024, TOPK, sq, device="cuda").to(torch.int32),
            ),
        ):
            baseline_out = buffers(sq, q.device)
            candidate_out = buffers(sq, q.device)
            baseline_fn = lambda: launch_baseline(
                q, kv, indices, sink, lengths, baseline_out
            )
            candidate_fn = lambda: launch_candidate(
                q, kv, indices, sink, lengths, candidate_out
            )
            baseline_fn()
            candidate_fn()
            torch.cuda.synchronize()
            max_abs_error = [
                float((actual.float() - expected.float()).abs().max())
                for actual, expected in zip(candidate_out, baseline_out)
            ]
            bitwise_equal = [
                bool(torch.equal(actual, expected))
                for actual, expected in zip(candidate_out, baseline_out)
            ]
            for actual, expected in zip(candidate_out, baseline_out):
                torch.testing.assert_close(actual, expected, atol=2e-2, rtol=2e-2)
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
                "max_abs_error": max_abs_error,
                "bitwise_equal": bitwise_equal,
                "graph_replay": "passed",
            }
            rows.append(row)
            print(json.dumps(row), flush=True)

    dominant = [row for row in rows if row["sq"] in (2029, 2048)]
    status = (
        "candidate"
        if min(row["speedup"] for row in dominant) >= 1.05
        and all(max(row["max_abs_error"]) <= 2e-2 for row in dominant)
        else "rejected"
    )
    result = {
        "schema_version": 1,
        "status": status,
        "candidate": "thead_hq4_sparse_mla_exp2_online_softmax",
        "baseline": "generic_hq4_bk32_bh4_w4_s1",
        "threshold": "all SQ2029/SQ2048 patterns >=1.05x, max abs error <=2e-2, graph replay passes",
        "shape": {"hq": HQ, "dqk": DQK, "dv": DV, "topk": TOPK, "skv": SKV},
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("SUMMARY=" + json.dumps(result), flush=True)
    return 0 if status == "candidate" else 2


if __name__ == "__main__":
    raise SystemExit(main())
