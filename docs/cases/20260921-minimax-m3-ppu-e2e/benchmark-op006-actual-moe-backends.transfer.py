#!/usr/bin/env python3
"""Exact-runtime generic FlagGems versus T-Head full MoE call screen.

Single-card, fake weights, process-local instrumentation only; no source or
service changes. This is a search screen, not end-to-end performance evidence.
"""

import importlib
import inspect
import json
from pathlib import Path
import sys
import time

import torch
import triton.testing
import flag_gems
import flaggems_vllm


M_VALUES = (1, 2, 4, 8, 16, 32)
E, H, I, TOP_K = 128, 6144, 192, 4
ATOL, RTOL = 0.12, 0.03


def error_stats(actual, expected):
    diff = (actual.float() - expected.float()).abs()
    return {
        "allclose": bool(torch.allclose(actual, expected, atol=ATOL, rtol=RTOL)),
        "finite": bool(torch.isfinite(actual).all()),
        "max_abs": float(diff.max().item()),
        "mean_abs": float(diff.mean().item()),
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: benchmark-op006-actual-moe-backends.py OUTPUT_JSON")
    output = Path(sys.argv[1]).resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")

    current_module = importlib.import_module("flag_gems.fused.fused_moe")
    candidate_module = importlib.import_module(
        "flaggems_vllm.runtime.backend._thead.ops.fused_moe"
    )
    current_fn = flag_gems.fused_experts_impl
    candidate_fn = flaggems_vllm.ops_experts_impl
    if inspect.getfile(current_fn) != current_module.__file__:
        raise SystemExit("current function does not resolve to generic FlagGems")
    if inspect.getfile(candidate_fn) != candidate_module.__file__:
        raise SystemExit("candidate function does not resolve to T-Head FlagGems-vllm")

    device = torch.device("cuda:0")
    torch.manual_seed(20260923)
    w1 = torch.randn((E, 2 * I, H), device=device, dtype=torch.bfloat16) * 0.02
    w2 = torch.randn((E, H, I), device=device, dtype=torch.bfloat16) * 0.02
    w1_before = w1.clone()
    w2_before = w2.clone()
    rows = []
    started = time.time()
    status = "complete"
    failure = None

    try:
        for m in M_VALUES:
            hidden = torch.randn((m, H), device=device, dtype=torch.bfloat16) * 0.02
            hidden_before = hidden.clone()
            ids = torch.stack(
                [torch.randperm(E, device=device)[:TOP_K] for _ in range(m)]
            ).to(torch.int64)
            weights = torch.rand((m, TOP_K), device=device, dtype=torch.float32)
            weights = (weights / weights.sum(dim=-1, keepdim=True)).to(torch.bfloat16)
            ids_before = ids.clone()
            weights_before = weights.clone()

            def current():
                return current_fn(hidden, w1, w2, weights, ids, inplace=False,
                                  activation="silu")

            def candidate():
                return candidate_fn(hidden, w1, w2, weights, ids, inplace=False,
                                    activation="silu")

            reference = current()
            actual = candidate()
            torch.cuda.synchronize(device)
            numerical = error_stats(actual, reference)
            immutable = all((
                torch.equal(hidden, hidden_before),
                torch.equal(ids, ids_before),
                torch.equal(weights, weights_before),
                torch.equal(w1, w1_before),
                torch.equal(w2, w2_before),
            ))
            row = {"m": m, "numerical": numerical, "inputs_immutable": immutable}
            rows.append(row)
            if not (numerical["allclose"] and numerical["finite"] and immutable):
                status = "rejected_numerical_or_mutation"
                failure = f"m={m}: {numerical}, inputs_immutable={immutable}"
                break

            current_p50, current_p20, current_p80 = triton.testing.do_bench(
                current, warmup=30, rep=150, quantiles=[0.5, 0.2, 0.8]
            )
            candidate_p50, candidate_p20, candidate_p80 = triton.testing.do_bench(
                candidate, warmup=30, rep=150, quantiles=[0.5, 0.2, 0.8]
            )
            row["current_generic_ms"] = {
                "p50": float(current_p50), "p20": float(current_p20),
                "p80": float(current_p80),
            }
            row["candidate_thead_ms"] = {
                "p50": float(candidate_p50), "p20": float(candidate_p20),
                "p80": float(candidate_p80),
            }
            row["candidate_improvement_percent"] = (
                100 * (current_p50 - candidate_p50) / current_p50
            )
            print(json.dumps({"m": m, "generic_p50_ms": float(current_p50),
                              "thead_p50_ms": float(candidate_p50),
                              "candidate_improvement_percent":
                              row["candidate_improvement_percent"]}), flush=True)
    except Exception as exc:
        status = "failed_exception"
        failure = f"{type(exc).__name__}: {exc}"
    finally:
        payload = {
            "schema_version": 1,
            "experiment_id": "op-006-actual-flag-gems-versus-thead-moe-screen",
            "scope": "single_card_fake_weights_search_only",
            "device": torch.cuda.get_device_name(device),
            "source_files": {
                "current": inspect.getfile(current_fn),
                "candidate": inspect.getfile(candidate_fn),
            },
            "shape_contract": {
                "m_values": list(M_VALUES), "experts": E, "hidden": H,
                "intermediate_per_tp": I, "top_k": TOP_K,
                "dtype": "torch.bfloat16", "activation": "silu", "bias": False,
            },
            "protocol": {
                "timing": "triton.testing.do_bench_complete_call",
                "warmup_ms": 30, "measurement_ms": 150,
                "quantiles": [0.5, 0.2, 0.8],
                "atol": ATOL, "rtol": RTOL,
                "independent_confirmation": False,
            },
            "status": status, "failure": failure,
            "elapsed_seconds": time.time() - started,
            "results": rows,
        }
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"status": status, "failure": failure,
                          "output": str(output), "elapsed_seconds":
                          payload["elapsed_seconds"]}), flush=True)
    if status != "complete":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
