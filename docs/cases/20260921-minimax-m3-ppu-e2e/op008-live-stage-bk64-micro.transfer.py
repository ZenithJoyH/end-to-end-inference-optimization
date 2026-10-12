#!/usr/bin/env python3
"""Screen GEMM2 BK64 at the actually invoked FlagGems stage boundary."""

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
        raise SystemExit("usage: op008-live-stage-bk64-micro.py OUTPUT_JSON")
    output = Path(sys.argv[1]).resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")
    module = importlib.import_module("flag_gems.fused.fused_moe")
    if inspect.getfile(flag_gems.fused_experts_impl) != module.__file__:
        raise SystemExit("top-level FlagGems fused_experts_impl source mismatch")

    original = module.dispatch_fused_moe_kernel
    enabled = False
    hits = 0
    seen = {}

    def guarded(*args, **kwargs):
        nonlocal hits
        a, b, c = args[:3]
        top_k, config = args[11:13]
        m = c.size(0)
        stage = "gemm2" if tuple(b.shape) == (E, H, I) and top_k == 1 else "other"
        key = (m, stage)
        if key not in seen:
            seen[key] = {
                "a": list(a.shape), "b": list(b.shape), "c": list(c.shape),
                "top_k": top_k, "config": dict(config),
            }
        if enabled and m == 32 and stage == "gemm2":
            if config["BLOCK_SIZE_K"] != 128 or config["BLOCK_SIZE_M"] != 16:
                raise RuntimeError(f"live config unexpected: {config}")
            changed = dict(config)
            changed["BLOCK_SIZE_K"] = 64
            mutable = list(args)
            mutable[12] = changed
            args = tuple(mutable)
            hits += 1
        return original(*args, **kwargs)

    module.dispatch_fused_moe_kernel = guarded
    device = torch.device("cuda:0")
    torch.manual_seed(20260923)
    w1 = torch.randn((E, 2 * I, H), device=device, dtype=torch.bfloat16) * 0.02
    w2 = torch.randn((E, H, I), device=device, dtype=torch.bfloat16) * 0.02
    rows = []
    graph_result = None
    started = time.time()
    status, failure = "complete", None

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

            def call():
                return flag_gems.fused_experts_impl(
                    hidden, w1, w2, weights, ids, inplace=False, activation="silu"
                )

            enabled = False
            reference = call()
            baseline = bench(call) if m == 32 else None
            enabled = True
            hits = 0
            actual = call()
            torch.cuda.synchronize(device)
            first_hits = hits
            numerical = bool(torch.allclose(actual, reference, atol=ATOL, rtol=RTOL))
            finite = bool(torch.isfinite(actual).all())
            diff = (actual.float() - reference.float()).abs()
            if not (numerical and finite and first_hits == (1 if m == 32 else 0)):
                raise RuntimeError(f"numerical or dispatch failure at M={m}: {first_hits}")
            candidate = bench(call) if m == 32 else None
            enabled = False
            revert = bench(call) if m == 32 else None
            row = {
                "m": m, "allclose": numerical, "finite": finite,
                "first_call_candidate_hits": first_hits,
                "max_abs": float(diff.max().item()),
                "mean_abs": float(diff.mean().item()),
                "baseline_ms": baseline, "candidate_ms": candidate,
                "revert_ms": revert,
            }
            if m == 32:
                baseline_ref = statistics.median((baseline["p50"], revert["p50"]))
                row["baseline_reference_p50_ms"] = baseline_ref
                row["candidate_improvement_percent"] = 100 * (
                    baseline_ref - candidate["p50"]
                ) / baseline_ref
                enabled = True
                call()
                torch.cuda.synchronize(device)
                graph = torch.cuda.CUDAGraph()
                with torch.cuda.graph(graph):
                    captured = call()
                graph.replay()
                graph.replay()
                torch.cuda.synchronize(device)
                graph_result = {
                    "capture": True, "replays": 2,
                    "allclose": bool(torch.allclose(captured, reference, atol=ATOL, rtol=RTOL)),
                }
                enabled = False
            rows.append(row)
            print(json.dumps(row), flush=True)
    except Exception as exc:
        status, failure = "failed", f"{type(exc).__name__}: {exc}"
    finally:
        module.dispatch_fused_moe_kernel = original
        m32 = next((r for r in rows if r["m"] == 32), None)
        if status == "complete" and (
            m32 is None or m32["candidate_improvement_percent"] < 10
            or not graph_result or not graph_result["allclose"]
        ):
            status = "rejected_gate"
        payload = {
            "schema_version": 1,
            "experiment_id": "op-008-plugin-cachedop-moe-invoke-shape-proof",
            "scope": "single_card_fake_weights_exact_live_stage_config_only",
            "source_file": module.__file__,
            "device": torch.cuda.get_device_name(device),
            "shape_contract": {"M": list(M_VALUES), "E": E, "H": H, "I": I,
                               "top_k": TOP_K, "dtype": "bf16"},
            "change": "GEMM2 M32 only BLOCK_SIZE_K 128 to 64 at dispatch boundary",
            "protocol": {"timing": "triton.testing.do_bench_full_call",
                         "warmup_ms": 30, "measurement_ms": 150,
                         "aba_bracket": True, "atol": ATOL, "rtol": RTOL,
                         "m32_min_gain_percent": 10},
            "seen_configs": {f"M{m}-{stage}": value for (m, stage), value in seen.items()},
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
