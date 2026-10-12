#!/usr/bin/env python3
"""Validate T-Head vendor dispatch, fallback, numerics, graph and M32 A/B/A."""

import importlib
import inspect
import json
from pathlib import Path
import statistics
import sys
import time

import torch
import triton.testing
import flag_gems


E, H, I, TOP_K = 128, 6144, 192, 4
M_VALUES = (1, 2, 4, 8, 16, 32)
ATOL, RTOL = 0.12, 0.03


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: op009-vendor-candidate-micro.py OUTPUT_JSON")
    output = Path(sys.argv[1]).resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")
    generic = importlib.import_module("flag_gems.fused.fused_moe").fused_experts_impl
    vendor_module = importlib.import_module("_thead.fused.fused_moe")
    candidate = flag_gems.fused_experts_impl
    if candidate is not vendor_module.fused_experts_impl:
        raise SystemExit("top-level API did not select T-Head vendor wrapper")
    if not inspect.getsourcefile(candidate).endswith("/_thead/fused/fused_moe.py"):
        raise SystemExit("unexpected candidate source")
    if not vendor_module._is_target_device():
        raise SystemExit("wrong target device")

    device = torch.device("cuda:0")
    torch.manual_seed(20260923)
    w1 = torch.randn((E, 2 * I, H), device=device, dtype=torch.bfloat16) * 0.02
    w2 = torch.randn((E, H, I), device=device, dtype=torch.bfloat16) * 0.02
    rows = []
    graph_result = None
    status, failure = "complete", None
    started = time.time()

    def bench(call):
        p50, p20, p80 = triton.testing.do_bench(
            call, warmup=30, rep=150, quantiles=[0.5, 0.2, 0.8]
        )
        return {"p50": float(p50), "p20": float(p20), "p80": float(p80)}

    try:
        for m in M_VALUES:
            hidden = torch.randn((m, H), device=device, dtype=torch.bfloat16) * 0.02
            ids = torch.stack(
                [torch.randperm(E, device=device)[:TOP_K] for _ in range(m)]
            ).to(torch.int64)
            weights = torch.rand((m, TOP_K), device=device, dtype=torch.float32)
            weights = (weights / weights.sum(dim=-1, keepdim=True)).to(torch.bfloat16)

            def common_call():
                return generic(hidden, w1, w2, weights, ids, inplace=False, activation="silu")

            def vendor_call():
                return candidate(hidden, w1, w2, weights, ids, inplace=False, activation="silu")

            reference = common_call()
            baseline = bench(common_call) if m == 32 else None
            before_hits = vendor_module._report_op009_hit.cache_info().misses
            actual = vendor_call()
            torch.cuda.synchronize(device)
            hit_delta = vendor_module._report_op009_hit.cache_info().misses - before_hits
            expected_delta = 1 if m == 32 else 0
            numerical = bool(torch.allclose(actual, reference, atol=ATOL, rtol=RTOL))
            finite = bool(torch.isfinite(actual).all())
            exact = bool(torch.equal(actual, reference))
            diff = (actual.float() - reference.float()).abs()
            if not (numerical and finite and hit_delta == expected_delta):
                raise RuntimeError(f"dispatch/numerical failure at M={m}: hit_delta={hit_delta}")
            if m < 32 and not exact:
                raise RuntimeError(f"fallback not bitwise identical at M={m}")
            candidate_ms = bench(vendor_call) if m == 32 else None
            revert = bench(common_call) if m == 32 else None
            row = {
                "m": m, "allclose": numerical, "finite": finite, "exact": exact,
                "first_call_hit_delta": hit_delta,
                "max_abs": float(diff.max().item()),
                "mean_abs": float(diff.mean().item()),
                "baseline_ms": baseline, "candidate_ms": candidate_ms,
                "revert_ms": revert,
            }
            if m == 32:
                baseline_ref = statistics.median((baseline["p50"], revert["p50"]))
                row["baseline_reference_p50_ms"] = baseline_ref
                row["candidate_improvement_percent"] = 100 * (
                    baseline_ref - candidate_ms["p50"]
                ) / baseline_ref
                vendor_call()
                torch.cuda.synchronize(device)
                graph = torch.cuda.CUDAGraph()
                with torch.cuda.graph(graph):
                    captured = vendor_call()
                graph.replay()
                graph.replay()
                torch.cuda.synchronize(device)
                graph_result = {
                    "capture": True, "replays": 2,
                    "allclose": bool(torch.allclose(captured, reference, atol=ATOL, rtol=RTOL)),
                }
            rows.append(row)
            print(json.dumps(row), flush=True)
    except Exception as exc:
        status, failure = "failed", f"{type(exc).__name__}: {exc}"
    finally:
        m32 = next((r for r in rows if r["m"] == 32), None)
        if status == "complete" and (
            m32 is None or m32["candidate_improvement_percent"] < 10
            or not graph_result or not graph_result["allclose"]
        ):
            status = "rejected_gate"
        payload = {
            "schema_version": 1,
            "experiment_id": "op-009-thead-m32-gemm2-bk64-integration",
            "scope": "single_card_fake_weights_vendor_wrapper_validation",
            "vendor_source": inspect.getsourcefile(candidate),
            "generic_source": inspect.getsourcefile(generic),
            "device": torch.cuda.get_device_name(device),
            "shape_contract": {"M": list(M_VALUES), "E": E, "H": H, "I": I,
                               "top_k": TOP_K, "dtype": "bf16"},
            "protocol": {"timing": "triton.testing.do_bench_full_call",
                         "warmup_ms": 30, "measurement_ms": 150,
                         "aba_bracket": True, "atol": ATOL, "rtol": RTOL,
                         "m32_min_gain_percent": 10},
            "rows": rows, "graph": graph_result,
            "status": status, "failure": failure,
            "elapsed_seconds": time.time() - started,
        }
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"status": status, "failure": failure,
                          "graph": graph_result, "result": str(output)}), flush=True)
    if status != "complete":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
