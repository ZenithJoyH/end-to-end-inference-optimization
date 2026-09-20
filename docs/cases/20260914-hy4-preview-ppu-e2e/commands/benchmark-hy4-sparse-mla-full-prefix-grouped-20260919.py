#!/usr/bin/env python3
"""Upper-bound prototype: reuse full-prefix KV tiles across adjacent queries."""

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
def grouped_full_prefix_kernel(
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
    SQ,
    SKV,
    SM_SCALE: tl.constexpr,
    HQC: tl.constexpr,
    DVX: tl.constexpr,
    BDPX: tl.constexpr,
    BKX: tl.constexpr,
    BQ: tl.constexpr,
    BH: tl.constexpr,
):
    group_id = tl.program_id(0)
    first_row = group_id * BQ
    last_row = tl.minimum(first_row + BQ - 1, SQ - 1)
    offs_bh = tl.arange(0, BH)
    row_offset = offs_bh // HQC
    head = offs_bh % HQC
    row = first_row + row_offset
    valid_row = row < SQ
    offs_d = tl.arange(0, BDPX)
    offs_t = tl.arange(0, BKX)
    offs_td = tl.arange(0, 64)

    q_base = q + row[:, None] * stride_qm + head[:, None] * stride_qh
    q0 = tl.load(q_base + offs_d[None, :], mask=valid_row[:, None], other=0.0)
    q1 = tl.load(
        q_base + BDPX + offs_d[None, :], mask=valid_row[:, None], other=0.0
    )
    qt = tl.load(
        q_base + DVX + offs_td[None, :], mask=valid_row[:, None], other=0.0
    )
    row_lengths = tl.load(topk_length + row, mask=valid_row, other=0)
    max_length = tl.load(topk_length + last_row)
    index_base = indices + last_row * stride_tm

    max_log = tl.full([BH], float("-inf"), dtype=tl.float32)
    sum_exp = tl.zeros([BH], dtype=tl.float32)
    acc0 = tl.zeros([BH, BDPX], dtype=tl.float32)
    acc1 = tl.zeros([BH, BDPX], dtype=tl.float32)
    num_blocks = tl.cdiv(max_length, BKX)
    for block_id in range(num_blocks):
        positions = block_id * BKX + offs_t
        union_mask = positions < max_length
        kv_ids = tl.load(index_base + positions, mask=union_mask, other=-1)
        valid_ids = union_mask & (kv_ids >= 0) & (kv_ids < SKV)
        safe_ids = tl.where(valid_ids, kv_ids, 0)
        kv0 = tl.load(
            kv + safe_ids[None, :] * stride_kvn + offs_d[:, None],
            cache_modifier=".cg",
        )
        kv1 = tl.load(
            kv + safe_ids[None, :] * stride_kvn + BDPX + offs_d[:, None],
            cache_modifier=".cg",
        )
        kvt = tl.load(
            kv + safe_ids[None, :] * stride_kvn + DVX + offs_td[:, None],
            cache_modifier=".cg",
        )
        qk = tl.dot(q0, kv0, out_dtype=tl.float32)
        qk = tl.dot(q1, kv1, qk, out_dtype=tl.float32)
        qk = tl.dot(qt, kvt, qk, out_dtype=tl.float32) * SM_SCALE
        row_key_mask = valid_row[:, None] & valid_ids[None, :] & (
            positions[None, :] < row_lengths[:, None]
        )
        qk = tl.where(row_key_mask, qk, float("-inf"))
        new_max = tl.maximum(max_log, tl.max(qk, axis=1))
        exp_qk = tl.where(row_key_mask, tl.exp(qk - new_max[:, None]), 0.0)
        alpha = tl.where(
            max_log != float("-inf"), tl.exp(max_log - new_max), 0.0
        )
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

    valid = valid_row & (max_log != float("-inf"))
    orig_lse = max_log + tl.log(sum_exp)
    sink = tl.load(attn_sink + head, mask=valid_row, other=0.0)
    denominator = tl.exp(orig_lse) + tl.exp(sink)
    factor = tl.exp(max_log) / denominator
    out0 = tl.where(valid[:, None], acc0 * factor[:, None], 0.0)
    out1 = tl.where(valid[:, None], acc1 * factor[:, None], 0.0)
    out_base = output + row[:, None] * stride_om + head[:, None] * stride_oh
    tl.store(
        out_base + offs_d[None, :],
        out0.to(tl.bfloat16),
        mask=valid_row[:, None],
    )
    tl.store(
        out_base + BDPX + offs_d[None, :],
        out1.to(tl.bfloat16),
        mask=valid_row[:, None],
    )
    stat_offset = row * stride_mm + head
    tl.store(
        max_logits + stat_offset,
        tl.where(valid, max_log, float("-inf")),
        mask=valid_row,
    )
    lse_offset = row * stride_lm + head
    tl.store(
        lse + lse_offset,
        tl.where(valid, orig_lse, float("inf")),
        mask=valid_row,
    )


def empty_outputs(sq):
    return (
        torch.empty((sq, HQ, DV), device="cuda", dtype=torch.bfloat16),
        torch.empty((sq, HQ), device="cuda", dtype=torch.float32),
        torch.empty((sq, HQ), device="cuda", dtype=torch.float32),
    )


def baseline_launch(q, kv, indices, sink, lengths, outputs):
    sq = q.shape[0]
    output, max_logits, lse = outputs
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
        SKV,
        TOPK,
        True,
        True,
        BK=BK,
        BH=HQ,
        num_warps=4,
        num_stages=1,
    )


def grouped_launch(q, kv, indices, sink, lengths, outputs, bq):
    sq = q.shape[0]
    output, max_logits, lse = outputs
    grouped_full_prefix_kernel[(triton.cdiv(sq, bq),)](
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
        SKV,
        SM_SCALE=SCALE,
        HQC=HQ,
        DVX=DV,
        BDPX=BDP,
        BKX=BK,
        BQ=bq,
        BH=bq * HQ,
        num_warps=4,
        num_stages=1,
    )


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
        prefix = torch.arange(TOPK, device="cuda", dtype=torch.int32)
        indices = prefix.expand(sq, 1, TOPK).contiguous()
        lengths = torch.clamp(
            torch.arange(1, sq + 1, device="cuda", dtype=torch.int32), max=TOPK
        )
        sink = torch.randn((HQ,), device="cuda", dtype=torch.float32)
        baseline = empty_outputs(sq)
        baseline_fn = lambda: baseline_launch(q, kv, indices, sink, lengths, baseline)
        baseline_fn()
        baseline_samples = elapsed_us(baseline_fn)
        baseline_median = statistics.median(baseline_samples)
        for bq in (2, 4):
            candidate = empty_outputs(sq)
            candidate_fn = lambda bq=bq, candidate=candidate: grouped_launch(
                q, kv, indices, sink, lengths, candidate, bq
            )
            row = {"sq": sq, "bq": bq}
            try:
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
                samples = elapsed_us(candidate_fn)
                median = statistics.median(samples)
                row.update(
                    status="passed",
                    max_abs_error=errors,
                    baseline_samples_us=baseline_samples,
                    candidate_samples_us=samples,
                    baseline_median_us=baseline_median,
                    candidate_median_us=median,
                    speedup=baseline_median / median,
                )
            except Exception as exc:
                row.update(status="failed", error=repr(exc))
                torch.cuda.synchronize()
            rows.append(row)
            print(json.dumps(row), flush=True)

    passed = [row for row in rows if row["status"] == "passed"]
    best_large = {
        sq: max((row["speedup"] for row in passed if row["sq"] == sq), default=0.0)
        for sq in (512, 2048)
    }
    status = (
        "candidate"
        if all(speedup >= 1.10 for speedup in best_large.values())
        else "rejected"
    )
    result = {
        "schema_version": 1,
        "status": status,
        "candidate": "group_adjacent_full_prefix_queries_and_reuse_kv_tiles",
        "baseline": "legacy_hq4_bh4_bk32_w4_s1",
        "shapes": {"hq": HQ, "dqk": DQK, "dv": DV, "topk": TOPK},
        "threshold": "best BQ at SQ512 and SQ2048 speedup >= 1.10",
        "scope": "full-range prefix rows only; ideal same-request grouping",
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print("SUMMARY=" + json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
