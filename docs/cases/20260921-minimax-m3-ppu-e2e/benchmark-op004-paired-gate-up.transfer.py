#!/usr/bin/env python3
"""Single-variable screen of the existing T-Head paired Gate/Up dot path.

This process does not edit installed source. It measures the complete
flaggems_vllm.ops_experts_impl call, including routing, GEMM1, GEMM2 and sum.
"""

import importlib
import json
from pathlib import Path
import time

import torch
import triton.testing

import flaggems_vllm


M_VALUES = (1, 2, 4, 8, 16, 32)
E = 128
HIDDEN = 6144
INTERMEDIATE = 192
TOP_K = 4
ATOL = 0.12
RTOL = 0.03
OUTPUT = Path(
    "/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/"
    "results/op004-paired-gate-up-search.json"
)


def error_stats(actual: torch.Tensor, expected: torch.Tensor) -> dict:
    diff = (actual.float() - expected.float()).abs()
    return {
        "allclose": bool(torch.allclose(actual, expected, atol=ATOL, rtol=RTOL)),
        "max_abs": float(diff.max().item()),
        "mean_abs": float(diff.mean().item()),
    }


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit(f"refusing to overwrite {OUTPUT}")

    module = importlib.import_module(
        "flaggems_vllm.runtime.backend._thead.ops.fused_moe"
    )
    original_get_default = module.get_default_config
    device = torch.device("cuda:0")
    torch.manual_seed(20260923)
    w1 = torch.randn(
        (E, INTERMEDIATE * 2, HIDDEN), device=device, dtype=torch.bfloat16
    ) * 0.02
    w2 = torch.randn(
        (E, HIDDEN, INTERMEDIATE), device=device, dtype=torch.bfloat16
    ) * 0.02

    def install(paired: bool) -> dict:
        hits = {"gemm1_fast_path": 0, "gemm2_fast_path": 0}

        def wrapped(*args, **kwargs):
            config = original_get_default(*args, **kwargs)
            stage = kwargs.get("gemm_stage", "gemm1")
            if kwargs.get("enable_gemm_fast_path", False):
                hits[f"{stage}_fast_path"] += 1
                if paired and stage == "gemm1":
                    config["PAIR_GATE_UP_DOT"] = True
            return config

        module.get_default_config = wrapped
        return hits

    rows = []
    started = time.time()
    try:
        for m in M_VALUES:
            hidden = (
                torch.randn((m, HIDDEN), device=device, dtype=torch.bfloat16)
                * 0.02
            )
            ids = torch.stack(
                [torch.randperm(E, device=device)[:TOP_K] for _ in range(m)]
            ).to(torch.int64)
            weights = torch.rand((m, TOP_K), device=device, dtype=torch.float32)
            weights = (weights / weights.sum(dim=-1, keepdim=True)).to(
                torch.bfloat16
            )

            def call():
                return flaggems_vllm.ops_experts_impl(
                    hidden, w1, w2, weights, ids, inplace=False, activation="silu"
                )

            install(False)
            reference = call()
            torch.cuda.synchronize(device)
            measurements = []
            for name, paired in (("current", False), ("paired_gate_up", True)):
                hits = install(paired)
                actual = call()
                torch.cuda.synchronize(device)
                numerical = error_stats(actual, reference)
                if not numerical["allclose"]:
                    raise RuntimeError(
                        f"numerical failure m={m} candidate={name}: {numerical}"
                    )
                if m >= 16 and hits["gemm1_fast_path"] == 0:
                    raise RuntimeError(f"expected GEMM1 fast path did not run for m={m}")
                if m < 16 and hits["gemm1_fast_path"] != 0:
                    raise RuntimeError(f"unexpected GEMM1 fast path for m={m}")
                p50, p20, p80 = triton.testing.do_bench(
                    call, warmup=30, rep=150, quantiles=[0.5, 0.2, 0.8]
                )
                measurements.append(
                    {
                        "candidate": name,
                        "paired_gate_up": paired,
                        "p50_ms": float(p50),
                        "p20_ms": float(p20),
                        "p80_ms": float(p80),
                        "numerical": numerical,
                        "first_call_config_hits": hits,
                    }
                )
            current_ms = measurements[0]["p50_ms"]
            paired_ms = measurements[1]["p50_ms"]
            rows.append(
                {
                    "m": m,
                    "measurements": measurements,
                    "paired_improvement_percent": 100 * (current_ms - paired_ms) / current_ms,
                }
            )
            del hidden, ids, weights, reference, actual
    finally:
        module.get_default_config = original_get_default

    payload = {
        "schema_version": 1,
        "experiment_id": "op-004-fused-moe-m32-paired-gate-up",
        "device": torch.cuda.get_device_name(device),
        "shape_contract": {
            "m_values": list(M_VALUES),
            "experts": E,
            "hidden": HIDDEN,
            "intermediate_per_tp": INTERMEDIATE,
            "top_k": TOP_K,
            "dtype": "torch.bfloat16",
            "activation": "silu",
            "bias": False,
        },
        "protocol": {
            "scope": "candidate_search_only",
            "timing": "triton.testing.do_bench",
            "warmup_ms": 30,
            "measurement_ms": 150,
            "quantiles": [0.5, 0.2, 0.8],
            "atol": ATOL,
            "rtol": RTOL,
            "search_and_confirmation_separated": False,
            "complete_call": True,
        },
        "elapsed_seconds": time.time() - started,
        "results": rows,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "elapsed_seconds": payload["elapsed_seconds"],
                "by_m": [
                    {
                        "m": row["m"],
                        "current_ms": row["measurements"][0]["p50_ms"],
                        "paired_ms": row["measurements"][1]["p50_ms"],
                        "improvement_percent": row["paired_improvement_percent"],
                    }
                    for row in rows
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
