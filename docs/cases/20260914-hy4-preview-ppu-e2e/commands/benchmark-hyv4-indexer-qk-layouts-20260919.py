#!/usr/bin/env python3
"""Falsify alternative Indexer QK layouts before changing live code."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import torch

from vllm_fl.models import hy_v4


WARMUP = 3
RUNS = 5
REPEATS = 7
HEADS = 32
HEAD_DIM = 128


def baseline(keys: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
    return torch.matmul(keys.unsqueeze(0), q.transpose(1, 2))


def explicit_bmm(keys: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
    return torch.bmm(
        keys.unsqueeze(0).expand(q.shape[0], -1, -1),
        q.transpose(1, 2),
    )


def q_first(keys: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
    return torch.matmul(q, keys.transpose(0, 1)).transpose(1, 2).contiguous()


def einsum(keys: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
    return torch.einsum("kd,rhd->rkh", keys, q)


def elapsed_us(fn) -> list[float]:
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


def stats(samples: list[float]) -> dict:
    return {
        "median_us": statistics.median(samples),
        "min_us": min(samples),
        "max_us": max(samples),
        "samples_us": samples,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")
    assert torch.cuda.is_available()
    torch.manual_seed(20260919)

    rows_out = []
    variants = {
        "baseline": baseline,
        "explicit_bmm": explicit_bmm,
        "q_first_transpose_contiguous": q_first,
        "einsum": einsum,
    }
    for rows, keys_count in ((26, 4096), (128, 2048), (128, 4096)):
        keys = torch.randn(
            (keys_count, HEAD_DIM), device="cuda", dtype=torch.bfloat16
        )
        q = torch.randn(
            (rows, HEADS, HEAD_DIM), device="cuda", dtype=torch.bfloat16
        )
        weights = torch.randn(
            (rows, HEADS), device="cuda", dtype=torch.bfloat16
        )
        expected = baseline(keys, q)
        expected_logits = hy_v4._hyv4_weighted_relu_reduce(
            expected.clone(), weights
        )
        torch.cuda.synchronize()
        timings = {}
        for name, variant in variants.items():
            actual = variant(keys, q)
            logits = hy_v4._hyv4_weighted_relu_reduce(
                actual.clone(), weights
            )
            torch.cuda.synchronize()
            qk_exact = bool(torch.equal(expected, actual))
            logits_exact = bool(torch.equal(expected_logits, logits))
            qk_stats = stats(elapsed_us(lambda: variant(keys, q)))
            chain_stats = stats(
                elapsed_us(
                    lambda: hy_v4._hyv4_weighted_relu_reduce(
                        variant(keys, q), weights
                    )
                )
            )
            timings[name] = {
                "qk_exact": qk_exact,
                "logits_exact": logits_exact,
                "qk": qk_stats,
                "chain": chain_stats,
            }
        baseline_qk = timings["baseline"]["qk"]["median_us"]
        baseline_chain = timings["baseline"]["chain"]["median_us"]
        for item in timings.values():
            item["qk_speedup"] = baseline_qk / item["qk"]["median_us"]
            item["chain_speedup"] = (
                baseline_chain / item["chain"]["median_us"]
            )
        rows_out.append(
            {
                "rows": rows,
                "keys": keys_count,
                "heads": HEADS,
                "head_dim": HEAD_DIM,
                "variants": timings,
            }
        )

    result = {
        "schema_version": 1,
        "device": torch.cuda.get_device_name(0),
        "vendor": hy_v4.current_platform.vendor_name,
        "shapes": rows_out,
        "conclusion_boundary": (
            "synthetic QK and exact pointwise/reduction timings only; no "
            "service or end-to-end claim"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
