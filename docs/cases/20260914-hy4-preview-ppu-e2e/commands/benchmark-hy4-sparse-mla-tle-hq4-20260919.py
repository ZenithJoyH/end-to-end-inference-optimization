#!/usr/bin/env python3
"""Falsify reusing the existing TLE producer/two-consumer pipeline for HQ4."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import torch
from triton.tools.tensor_descriptor import TensorDescriptor

import flaggems_vllm.ops.flashmla_sparse as generic


HQ, DQK, DV, TOPK, SKV = 4, 576, 512, 2048, 8192
BH, BK = 4, 64
SCALE = DQK**-0.5
WARMUP, RUNS, REPEATS = 3, 3, 5


def empty_outputs(sq):
    return (
        torch.empty((sq, HQ, DV), device="cuda", dtype=torch.bfloat16),
        torch.empty((sq, HQ), device="cuda", dtype=torch.float32),
        torch.empty((sq, HQ), device="cuda", dtype=torch.float32),
    )


def make_tle_launch(q, kv, indices, sink, lengths, outputs):
    sq = q.shape[0]
    output, max_logits, lse = outputs
    generic._set_triton_descriptor_allocator(q.device)
    q_desc = TensorDescriptor(
        q, shape=[sq * HQ, DQK], strides=[DQK, 1], block_shape=[BH, 256]
    )
    tq_desc = TensorDescriptor(
        q, shape=[sq * HQ, DQK], strides=[DQK, 1], block_shape=[BH, 64]
    )
    output_desc = TensorDescriptor(
        output, shape=[sq * HQ, DV], strides=[DV, 1], block_shape=[BH, 256]
    )

    def launch():
        generic._tle_flashmla_prefill_fwd[(sq,)](
            q_desc,
            tq_desc,
            output_desc,
            kv,
            indices,
            sink,
            lengths,
            SCALE,
            output,
            max_logits,
            lse,
            sq,
            HQ,
            DQK,
            SKV,
            TOPK,
            True,
            True,
            DV,
            DQK - DV,
            DV,
            64,
            HQ,
            1,
            1,
            True,
            BK,
            BH,
            generic.TLE_FLASHMLA_PREFILL_PAIR_BLOCKS,
            num_warps=generic.TLE_FLASHMLA_PREFILL_WORKER_NUM_WARPS,
            num_stages=1,
        )

    return launch


def make_baseline_launch(q, kv, indices, sink, lengths, outputs):
    sq = q.shape[0]
    output, max_logits, lse = outputs

    def launch():
        generic.triton_flash_mla_sparse_fwd.fn[(sq,)](
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
            BK=32,
            BH=HQ,
            num_warps=4,
            num_stages=1,
        )

    return launch


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


def lengths_for(sq, pattern):
    if pattern == "ramp":
        return torch.clamp(
            torch.arange(1, sq + 1, device="cuda", dtype=torch.int32),
            max=TOPK,
        )
    return torch.full((sq,), TOPK, device="cuda", dtype=torch.int32)


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
        indices = torch.randint(
            0, SKV, (sq, 1, TOPK), device="cuda", dtype=torch.int32
        )
        sink = torch.randn((HQ,), device="cuda", dtype=torch.float32)
        for pattern in ("ramp", "all_2048"):
            lengths = lengths_for(sq, pattern)
            baseline = empty_outputs(sq)
            candidate = empty_outputs(sq)
            base_launch = make_baseline_launch(
                q, kv, indices, sink, lengths, baseline
            )
            row = {"sq": sq, "pattern": pattern}
            try:
                candidate_launch = make_tle_launch(
                    q, kv, indices, sink, lengths, candidate
                )
                base_launch()
                candidate_launch()
                torch.cuda.synchronize()
                errors = [
                    float((actual.float() - expected.float()).abs().max())
                    for actual, expected in zip(candidate, baseline)
                ]
                for actual, expected in zip(candidate, baseline):
                    torch.testing.assert_close(
                        actual, expected, atol=2e-2, rtol=2e-2
                    )
                baseline_samples = elapsed_us(base_launch)
                candidate_samples = elapsed_us(candidate_launch)
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
        if len(passed) == len(rows)
        and all(row["speedup"] >= 1.05 for row in large)
        else "rejected"
    )
    result = {
        "schema_version": 1,
        "status": status,
        "candidate": "existing_tle_producer_two_consumer_pipeline_bh4_bk64",
        "baseline": "legacy_hq4_bh4_bk32_w4_s1",
        "shapes": {"hq": HQ, "dqk": DQK, "dv": DV, "topk": TOPK},
        "threshold": "all rows correct and SQ512/SQ2048 speedup >= 1.05",
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print("SUMMARY=" + json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
