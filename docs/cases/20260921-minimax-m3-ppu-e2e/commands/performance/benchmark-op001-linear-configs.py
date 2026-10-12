#!/usr/bin/env python3
"""Benchmark cached and current FlagGems linear configs on MiniMax-M3 decode shapes."""

import json
import math
from pathlib import Path
import time

import torch
import torch.nn.functional as F

from flag_gems.ops.linear import linear, linear_kernel


SHAPES = (
    (32, 384, 6144),
    (32, 768, 6144),
    (32, 1024, 6144),
    (32, 1536, 6144),
    (32, 6144, 192),
    (32, 6144, 512),
    (32, 6144, 768),
    (32, 12512, 6144),
)
ATOL = 0.08
RTOL = 0.02


def config_dict(config):
    return {key: value for key, value in config.all_kwargs().items()}


def error_stats(actual, expected):
    actual_f = actual.float()
    expected_f = expected.float()
    diff = (actual_f - expected_f).abs()
    denom = expected_f.abs().clamp_min(1e-6)
    return {
        "max_abs": float(diff.max().item()),
        "mean_abs": float(diff.mean().item()),
        "max_rel": float((diff / denom).max().item()),
        "allclose": bool(torch.allclose(actual, expected, atol=ATOL, rtol=RTOL)),
    }


def main():
    output = Path(__file__).resolve().parents[2] / "results" / "op001-linear-config-microbenchmark.json"
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")
    torch.manual_seed(1234)
    device = torch.device("cuda:0")
    tuner = linear_kernel.fn
    results = []
    started = time.time()
    for m, n, k in SHAPES:
        x = torch.randn((m, k), device=device, dtype=torch.bfloat16) * 0.02
        weight = torch.randn((n, k), device=device, dtype=torch.bfloat16) * 0.02
        actual = linear(x, weight)
        torch.cuda.synchronize(device)
        cached = tuner.best_config
        reference = F.linear(x, weight)
        torch.cuda.synchronize(device)
        baseline_error = error_stats(actual, reference)
        if not baseline_error["allclose"]:
            raise RuntimeError(f"cached config numerical failure for {(m, n, k)}: {baseline_error}")

        configs = [("cached", cached)]
        seen = {tuple(sorted(config_dict(cached).items()))}
        for index, config in enumerate(tuner.configs):
            identity = tuple(sorted(config_dict(config).items()))
            if identity not in seen:
                configs.append((f"current_{index}", config))
                seen.add(identity)

        measurements = []
        for label, config in configs:
            timing = tuner.benchmark_config(
                config,
                warmup=20,
                rep=100,
                benchmark_mode="event",
            )
            torch.cuda.synchronize(device)
            numerical = error_stats(actual, reference)
            if not numerical["allclose"]:
                raise RuntimeError(
                    f"config numerical failure for {(m, n, k)} {label}: {numerical}"
                )
            measurements.append({
                "label": label,
                "config": config_dict(config),
                "p50_ms": float(timing[0]),
                "p20_ms": float(timing[1]),
                "p80_ms": float(timing[2]),
                "numerical": numerical,
            })
        cached_ms = measurements[0]["p50_ms"]
        best = min(measurements, key=lambda item: item["p50_ms"])
        results.append({
            "shape": {"m": m, "n": n, "k": k, "dtype": "torch.bfloat16", "bias": False},
            "cached_config": config_dict(cached),
            "cached_reference_numerical": baseline_error,
            "measurements": measurements,
            "best": best,
            "best_vs_cached_percent": 100.0 * (cached_ms - best["p50_ms"]) / cached_ms,
        })
        del x, weight, actual, reference
        torch.cuda.empty_cache()

    payload = {
        "schema_version": 1,
        "experiment_id": "op-001-linear-decode-cache-config",
        "device": torch.cuda.get_device_name(device),
        "protocol": {
            "benchmark_mode": "event",
            "warmup_ms": 20,
            "measurement_ms": 100,
            "timing_order": ["p50", "p20", "p80"],
            "atol": ATOL,
            "rtol": RTOL,
            "search_and_confirmation_separated": False,
            "scope": "candidate_search_only",
        },
        "elapsed_seconds": time.time() - started,
        "results": results,
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "elapsed_seconds": payload["elapsed_seconds"],
        "best_vs_cached_percent": [
            {**item["shape"], "improvement": item["best_vs_cached_percent"], "best": item["best"]["config"]}
            for item in results
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
