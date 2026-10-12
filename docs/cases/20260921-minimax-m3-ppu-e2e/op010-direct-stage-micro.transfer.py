#!/usr/bin/env python3
"""Compare the actual T-Head top-level MoE stage launcher with its generic path."""

import importlib
import inspect
import json
from pathlib import Path
import statistics
import sys
import time

import torch
import triton.language as tl
import triton.testing
import flag_gems


E, H, I, TOP_K = 128, 6144, 192, 4
CONFIG = {"BLOCK_SIZE_M": 16, "BLOCK_SIZE_N": 64, "BLOCK_SIZE_K": 128,
          "GROUP_SIZE_M": 1, "SPLIT_K": 1, "num_stages": 4, "num_warps": 4}
ATOL, RTOL = 0.12, 0.03


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: op010-direct-stage-micro.py OUTPUT_JSON")
    output = Path(sys.argv[1]).resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")
    generic = importlib.import_module("flag_gems.fused.fused_moe").invoke_fused_moe_triton_kernel
    vendor_module = importlib.import_module("_thead.fused.fused_moe")
    candidate = flag_gems.invoke_fused_moe_triton_kernel
    if candidate is not vendor_module.invoke_fused_moe_triton_kernel:
        raise SystemExit("top-level API did not select T-Head stage wrapper")
    if not inspect.getsourcefile(candidate).endswith("/_thead/fused/fused_moe.py"):
        raise SystemExit("unexpected top-level stage source")
    device = torch.device("cuda:0")
    torch.manual_seed(20260923)
    b = torch.randn((E, H, I), device=device, dtype=torch.bfloat16) * 0.02
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
        for m in (16, 32):
            a = torch.randn((m * TOP_K, I), device=device, dtype=torch.bfloat16) * 0.02
            c0 = torch.zeros((m, TOP_K, H), device=device, dtype=torch.bfloat16)
            c1 = torch.zeros_like(c0)
            ids = torch.stack(
                [torch.randperm(E, device=device)[:TOP_K] for _ in range(m)]
            ).to(torch.int64)
            weights = torch.rand((m, TOP_K), device=device, dtype=torch.float32)
            weights = (weights / weights.sum(dim=-1, keepdim=True)).to(torch.bfloat16)
            sorted_ids, expert_ids, post_pad = importlib.import_module(
                "flag_gems.fused.moe_align_block_size"
            ).moe_align_block_size(ids, 16, E)
            def call(fn, out):
                return fn(a, b, out, None, None, weights, sorted_ids,
                          expert_ids, post_pad, True, 1, CONFIG, tl.bfloat16,
                          False, False, False, False, False,
                          block_shape=None, B_bias=None)

            reference = call(generic, c0)
            torch.cuda.synchronize(device)
            baseline = bench(lambda: call(generic, c0)) if m == 32 else None
            before_hits = vendor_module._report_op010_hit.cache_info().misses
            actual = call(candidate, c1)
            torch.cuda.synchronize(device)
            hit_delta = vendor_module._report_op010_hit.cache_info().misses - before_hits
            numerical = bool(torch.allclose(c0, c1, atol=ATOL, rtol=RTOL))
            finite = bool(torch.isfinite(c1).all())
            exact = bool(torch.equal(c0, c1))
            diff = (c0.float() - c1.float()).abs()
            if not (numerical and finite and hit_delta == (1 if m == 32 else 0)):
                raise RuntimeError(f"dispatch/numerical failure at M={m}: hit_delta={hit_delta}")
            if m == 16 and not exact:
                raise RuntimeError("fallback M16 not bitwise identical")
            candidate_ms = bench(lambda: call(candidate, c1)) if m == 32 else None
            revert = bench(lambda: call(generic, c0)) if m == 32 else None
            row = {
                "m": m, "allclose": numerical, "finite": finite, "exact": exact,
                "first_call_hit_delta": hit_delta,
                "sorted_len": sorted_ids.numel(), "expert_len": expert_ids.numel(),
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
                call(candidate, c1)
                torch.cuda.synchronize(device)
                graph = torch.cuda.CUDAGraph()
                with torch.cuda.graph(graph):
                    call(candidate, c1)
                graph.replay()
                graph.replay()
                torch.cuda.synchronize(device)
                graph_result = {"capture": True, "replays": 2,
                                "allclose": bool(torch.allclose(c0, c1, atol=ATOL, rtol=RTOL))}
            rows.append(row)
            print(json.dumps(row), flush=True)
    except Exception as exc:
        status, failure = "failed", f"{type(exc).__name__}: {exc}"
    finally:
        m32 = next((r for r in rows if r["m"] == 32), None)
        if status == "complete" and (
            m32 is None or m32["candidate_improvement_percent"] < 5
            or not graph_result or not graph_result["allclose"]
        ):
            status = "rejected_gate"
        payload = {
            "schema_version": 1,
            "experiment_id": "op-010-thead-invoke-m32-gemm2-bk64",
            "scope": "single_card_exact_live_stage4_direct_invoke",
            "vendor_source": inspect.getsourcefile(candidate),
            "generic_source": inspect.getsourcefile(generic),
            "device": torch.cuda.get_device_name(device),
            "shape_contract": {"M": [16, 32], "E": E, "H": H, "I": I,
                               "top_k": TOP_K, "dtype": "bf16", "config": CONFIG},
            "protocol": {"timing": "triton.testing.do_bench_stage",
                         "warmup_ms": 30, "measurement_ms": 150,
                         "aba_bracket": True, "atol": ATOL, "rtol": RTOL,
                         "m32_min_gain_percent": 5},
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
