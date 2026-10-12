#!/usr/bin/env python3
"""Independent one-card M1..32 guard and graph proof for op-007 GEMM2 BK64."""

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
        raise SystemExit("usage: confirm-op007-generic-moe-bk64.py OUTPUT_JSON")
    output = Path(sys.argv[1]).resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")
    module = importlib.import_module("flag_gems.fused.fused_moe")
    if inspect.getfile(flag_gems.fused_experts_impl) != module.__file__:
        raise SystemExit("current FlagGems import source mismatch")
    original = module.get_default_config
    enabled = False
    hits = 0

    def guarded(*args, **kwargs):
        nonlocal hits
        cfg = original(*args, **kwargs)
        stage = kwargs.get("gemm_stage", "gemm1")
        if (enabled and stage == "gemm2" and args[0] in M_VALUES
                and args[1] == E and args[2] == H and args[3] == I
                and args[4] == TOP_K and args[5] == "bf16"):
            cfg["BLOCK_SIZE_K"] = 64
            hits += 1
        return cfg

    module.get_default_config = guarded
    device = torch.device("cuda:0")
    torch.manual_seed(20260924)
    w1 = torch.randn((E, 2 * I, H), device=device, dtype=torch.bfloat16) * 0.02
    w2 = torch.randn((E, H, I), device=device, dtype=torch.bfloat16) * 0.02
    w1_before, w2_before = w1.clone(), w2.clone()
    rows = []
    graph_result = None
    started = time.time()
    status = "complete"
    failure = None

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
            hidden_before, ids_before, weights_before = (
                hidden.clone(), ids.clone(), weights.clone()
            )

            def call():
                return flag_gems.fused_experts_impl(
                    hidden, w1, w2, weights, ids, inplace=False,
                    activation="silu"
                )

            enabled = False
            reference = call()
            baseline = bench(call)
            enabled = True
            hits = 0
            actual = call()
            torch.cuda.synchronize(device)
            numerical = bool(torch.allclose(actual, reference, atol=ATOL, rtol=RTOL))
            finite = bool(torch.isfinite(actual).all())
            diff = (actual.float() - reference.float()).abs()
            first_hits = hits
            if not (numerical and finite and first_hits > 0):
                row = {"m": m, "status": "rejected_numerical_or_miss",
                       "allclose": numerical, "finite": finite,
                       "first_call_config_hits": first_hits,
                       "max_abs": float(diff.max().item())}
                rows.append(row)
                status = "rejected_numerical_or_miss"
                failure = f"m={m}"
                break
            candidate = bench(call)
            enabled = False
            revert = bench(call)
            baseline_ref = statistics.median((baseline["p50"], revert["p50"]))
            immutable = all((
                torch.equal(hidden, hidden_before), torch.equal(ids, ids_before),
                torch.equal(weights, weights_before),
                torch.equal(w1, w1_before), torch.equal(w2, w2_before),
            ))
            row = {
                "m": m, "status": "complete", "allclose": numerical,
                "finite": finite, "inputs_immutable": immutable,
                "max_abs": float(diff.max().item()),
                "mean_abs": float(diff.mean().item()),
                "first_call_config_hits": first_hits,
                "baseline_ms": baseline, "candidate_ms": candidate,
                "revert_ms": revert, "baseline_reference_p50_ms": baseline_ref,
                "candidate_improvement_percent": 100 * (
                    baseline_ref - candidate["p50"]
                ) / baseline_ref,
            }
            rows.append(row)
            print(json.dumps(row), flush=True)
            if not immutable:
                status = "rejected_input_mutation"
                failure = f"m={m}"
                break

            if m == 32 and all(
                r.get("candidate_improvement_percent", -1e9) >= -5
                for r in rows if r["m"] != 32
            ) and row["candidate_improvement_percent"] >= 10:
                try:
                    enabled = True
                    call()
                    torch.cuda.synchronize(device)
                    graph = torch.cuda.CUDAGraph()
                    with torch.cuda.graph(graph):
                        captured = call()
                    graph.replay()
                    graph.replay()
                    torch.cuda.synchronize(device)
                    graph_numerical = bool(torch.allclose(
                        captured, reference, atol=ATOL, rtol=RTOL
                    ))
                    graph_result = {
                        "capture": True, "replays": 2,
                        "allclose": graph_numerical,
                    }
                except Exception as exc:
                    graph_result = {"capture": False, "replays": 0,
                                    "error": f"{type(exc).__name__}: {exc}"}
                finally:
                    enabled = False
    except Exception as exc:
        status = "failed_exception"
        failure = f"{type(exc).__name__}: {exc}"
    finally:
        module.get_default_config = original
        if status == "complete" and rows:
            m32 = next((r for r in rows if r["m"] == 32), None)
            if m32 is None or m32["candidate_improvement_percent"] < 10:
                status = "rejected_m32_gate"
            elif any(r["candidate_improvement_percent"] < -5 for r in rows):
                status = "rejected_small_m_guard"
            elif not graph_result or not (graph_result.get("capture") and
                                         graph_result.get("allclose")):
                status = "rejected_graph_guard"
            else:
                status = "passed_single_card_confirmation_only"
        payload = {
            "schema_version": 1,
            "experiment_id": "op-007-generic-flaggems-moe-stage-config-screen",
            "scope": "independent_single_card_fake_weights_confirmation_only",
            "source_file": module.__file__, "device": torch.cuda.get_device_name(device),
            "shape_contract": {"m_values": list(M_VALUES), "E": E, "H": H,
                               "I_per_tp": I, "top_k": TOP_K,
                               "dtype": "bf16", "activation": "silu"},
            "change": {"stage": "gemm2", "key": "BLOCK_SIZE_K", "value": 64,
                       "guard": "exact_E_H_I_topk_bf16_and_M1_to_32"},
            "protocol": {"timing": "triton.testing.do_bench_complete_call",
                         "warmup_ms": 30, "measurement_ms": 150,
                         "aba_bracket": True, "atol": ATOL, "rtol": RTOL,
                         "m32_min_gain_percent": 10,
                         "other_m_max_regression_percent": 5},
            "rows": rows, "graph": graph_result,
            "status": status, "failure": failure,
            "elapsed_seconds": time.time() - started,
        }
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"status": status, "failure": failure,
                          "graph": graph_result, "result": str(output)}), flush=True)
    if status != "passed_single_card_confirmation_only":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
