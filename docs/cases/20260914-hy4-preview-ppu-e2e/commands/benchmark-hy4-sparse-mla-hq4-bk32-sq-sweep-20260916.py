#!/usr/bin/env python3
"""Compare the current generic tile with BK32 across traced Hy4 prefill sizes."""

from __future__ import annotations

import json
import math
import statistics

import torch

from flag_gems.fused.flashmla_sparse import triton_flash_mla_sparse_fwd


HQ, DQK, SKV, TOPK, DV = 4, 576, 8192, 2048, 512
SCALE = DQK**-0.5
BASELINE = (4, 64, 4, 2)
CANDIDATE = (4, 32, 4, 1)
SQS = (128, 256, 512, 1024, 1536, 2048)
PATTERNS = ("ramp", "all")


def launch(q, kv, indices, sink, lengths, outputs, config):
    sq = q.shape[0]
    bh, bk, warps, stages = config
    output, max_logits, lse = outputs
    triton_flash_mla_sparse_fwd.fn[(sq * math.ceil(HQ / bh),)](
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
        BK=bk,
        BH=bh,
        num_warps=warps,
        num_stages=stages,
    )


def make_outputs(sq):
    return (
        torch.empty((sq, HQ, DV), device="cuda", dtype=torch.bfloat16),
        torch.empty((sq, HQ), device="cuda", dtype=torch.float32),
        torch.empty((sq, HQ), device="cuda", dtype=torch.float32),
    )


def measure(fn, sq):
    for _ in range(3):
        fn()
    torch.cuda.synchronize()
    runs = 10 if sq <= 512 else 5
    samples = []
    for _ in range(5):
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        for _ in range(runs):
            fn()
        end.record()
        end.synchronize()
        samples.append(start.elapsed_time(end) * 1000.0 / runs)
    return samples


def main():
    torch.manual_seed(20260916)
    kv = (torch.randn((SKV, 1, DQK), device="cuda") * 0.05).to(torch.bfloat16)
    sink = torch.randn((HQ,), device="cuda", dtype=torch.float32)
    rows = []
    for sq in SQS:
        q = (torch.randn((sq, HQ, DQK), device="cuda") * 0.05).to(torch.bfloat16)
        indices = torch.randint(
            0, SKV, (sq, 1, TOPK), device="cuda", dtype=torch.int32
        )
        for pattern in PATTERNS:
            lengths = (
                torch.linspace(1, TOPK, sq, device="cuda").to(torch.int32)
                if pattern == "ramp"
                else torch.full((sq,), TOPK, device="cuda", dtype=torch.int32)
            )
            results = {}
            reference = None
            for name, config in (("baseline", BASELINE), ("candidate", CANDIDATE)):
                outputs = make_outputs(sq)
                launch(q, kv, indices, sink, lengths, outputs, config)
                torch.cuda.synchronize()
                errors = None
                if reference is None:
                    reference = tuple(item.clone() for item in outputs)
                else:
                    errors = [
                        float((actual.float() - expected.float()).abs().max())
                        for actual, expected in zip(outputs, reference)
                    ]
                    for actual, expected in zip(outputs, reference):
                        torch.testing.assert_close(
                            actual, expected, atol=2e-2, rtol=2e-2
                        )
                samples = measure(
                    lambda: launch(q, kv, indices, sink, lengths, outputs, config),
                    sq,
                )
                results[name] = {
                    "config": config,
                    "samples_us": samples,
                    "median_us": statistics.median(samples),
                    "max_abs_error": errors,
                }
            row = {
                "sq": sq,
                "pattern": pattern,
                **results,
                "speedup": (
                    results["baseline"]["median_us"]
                    / results["candidate"]["median_us"]
                ),
            }
            rows.append(row)
            print(json.dumps(row), flush=True)
    summary = {
        "status": "passed",
        "shape": {"hq": HQ, "dqk": DQK, "skv": SKV, "topk": TOPK, "dv": DV},
        "baseline": BASELINE,
        "candidate": CANDIDATE,
        "min_speedup": min(row["speedup"] for row in rows),
        "rows": rows,
    }
    print("SUMMARY=" + json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
