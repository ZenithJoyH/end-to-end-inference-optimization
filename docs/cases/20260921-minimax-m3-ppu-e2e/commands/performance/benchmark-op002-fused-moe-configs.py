#!/usr/bin/env python3
"""Bounded exact-shape screen of T-Head fused MoE decode configs."""

import importlib
import json
from pathlib import Path
import time

import torch
import triton

import flaggems_vllm


M_VALUES = (1, 2, 4, 8, 16, 32)
E = 128
HIDDEN = 6144
INTERMEDIATE = 192
TOP_K = 4
ATOL = 0.12
RTOL = 0.03

CANDIDATES = {
    "current": {},
    "stages3": {"both": {"num_stages": 3}},
    "stages2": {"both": {"num_stages": 2}},
    "group1": {"both": {"GROUP_SIZE_M": 1}},
    "group16": {"both": {"GROUP_SIZE_M": 16}},
    "gemm1_bn128_bk64": {"gemm1": {"BLOCK_SIZE_N": 128, "BLOCK_SIZE_K": 64}},
    "gemm1_bn128_bk32": {"gemm1": {"BLOCK_SIZE_N": 128, "BLOCK_SIZE_K": 32}},
    "gemm2_bn256_bk32": {"gemm2": {"BLOCK_SIZE_N": 256, "BLOCK_SIZE_K": 32}},
    "gemm2_bn256_bk64": {"gemm2": {"BLOCK_SIZE_N": 256, "BLOCK_SIZE_K": 64}},
}


def error_stats(actual, expected):
    a = actual.float()
    b = expected.float()
    diff = (a - b).abs()
    return {
        "max_abs": float(diff.max().item()),
        "mean_abs": float(diff.mean().item()),
        "allclose": bool(torch.allclose(actual, expected, atol=ATOL, rtol=RTOL)),
    }


def main():
    output = Path(__file__).resolve().parents[2] / "results" / "op002-fused-moe-config-screen.json"
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")
    module = importlib.import_module(
        "flaggems_vllm.runtime.backend._thead.ops.fused_moe"
    )
    original_get_default = module.get_default_config
    device = torch.device("cuda:0")
    torch.manual_seed(20260921)
    w1 = torch.randn(
        (E, INTERMEDIATE * 2, HIDDEN), device=device, dtype=torch.bfloat16
    ) * 0.02
    w2 = torch.randn(
        (E, HIDDEN, INTERMEDIATE), device=device, dtype=torch.bfloat16
    ) * 0.02

    def install(candidate_name):
        overrides = CANDIDATES[candidate_name]

        def wrapped(*args, **kwargs):
            config = original_get_default(*args, **kwargs)
            stage = kwargs.get("gemm_stage", "gemm1")
            config.update(overrides.get("both", {}))
            config.update(overrides.get(stage, {}))
            return config

        module.get_default_config = wrapped

    results = []
    started = time.time()
    for m in M_VALUES:
        hidden = torch.randn((m, HIDDEN), device=device, dtype=torch.bfloat16) * 0.02
        ids = torch.stack(
            [torch.randperm(E, device=device)[:TOP_K] for _ in range(m)]
        ).to(torch.int64)
        weights = torch.rand((m, TOP_K), device=device, dtype=torch.float32)
        weights = (weights / weights.sum(dim=-1, keepdim=True)).to(torch.bfloat16)

        install("current")
        reference = flaggems_vllm.ops_experts_impl(
            hidden, w1, w2, weights, ids, inplace=False, activation="silu"
        )
        torch.cuda.synchronize(device)

        measurements = []
        for name in CANDIDATES:
            install(name)

            def call():
                return flaggems_vllm.ops_experts_impl(
                    hidden, w1, w2, weights, ids, inplace=False, activation="silu"
                )

            actual = call()
            torch.cuda.synchronize(device)
            numerical = error_stats(actual, reference)
            if not numerical["allclose"]:
                raise RuntimeError(f"numerical failure M={m} candidate={name}: {numerical}")
            timing = triton.testing.do_bench(
                call,
                warmup=20,
                rep=100,
                quantiles=[0.5, 0.2, 0.8],
            )
            measurements.append({
                "candidate": name,
                "overrides": CANDIDATES[name],
                "p50_ms": float(timing[0]),
                "p20_ms": float(timing[1]),
                "p80_ms": float(timing[2]),
                "numerical": numerical,
            })
        current_ms = measurements[0]["p50_ms"]
        best = min(measurements, key=lambda item: item["p50_ms"])
        results.append({
            "m": m,
            "measurements": measurements,
            "best": best,
            "best_vs_current_percent": 100.0 * (current_ms - best["p50_ms"]) / current_ms,
        })
        del hidden, ids, weights, reference, actual

    module.get_default_config = original_get_default
    payload = {
        "schema_version": 1,
        "experiment_id": "op-002-fused-moe-decode-stage-config-screen",
        "device": torch.cuda.get_device_name(device),
        "shape_contract": {
            "E": E,
            "hidden": HIDDEN,
            "per_tp_intermediate": INTERMEDIATE,
            "top_k": TOP_K,
            "dtype": "torch.bfloat16",
            "m_values": list(M_VALUES),
            "activation": "silu",
            "bias": False,
        },
        "protocol": {
            "timing": "triton.testing.do_bench",
            "warmup_ms": 20,
            "measurement_ms": 100,
            "quantiles": [0.5, 0.2, 0.8],
            "atol": ATOL,
            "rtol": RTOL,
            "scope": "candidate_search_only",
            "search_and_confirmation_separated": False,
        },
        "candidates": CANDIDATES,
        "elapsed_seconds": time.time() - started,
        "results": results,
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "elapsed_seconds": payload["elapsed_seconds"],
        "best_by_m": [
            {"m": row["m"], "candidate": row["best"]["candidate"], "p50_ms": row["best"]["p50_ms"], "improvement_percent": row["best_vs_current_percent"]}
            for row in results
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
