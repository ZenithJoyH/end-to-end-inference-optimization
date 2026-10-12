#!/usr/bin/env python3
"""Process-local generic FlagGems fused-MoE M32 stage-config search."""

import importlib
import inspect
import json
from pathlib import Path
import statistics
import sys
import time

import torch
import triton
import triton.testing
import flag_gems


E, H, I, TOP_K, M = 128, 6144, 192, 4, 32
ATOL, RTOL = 0.12, 0.03
VARIANTS = (
    ("g1_bn128", "gemm1", "BLOCK_SIZE_N", 128),
    ("g1_bn256", "gemm1", "BLOCK_SIZE_N", 256),
    ("g1_bk64", "gemm1", "BLOCK_SIZE_K", 64),
    ("g1_bk32", "gemm1", "BLOCK_SIZE_K", 32),
    ("g2_bn128", "gemm2", "BLOCK_SIZE_N", 128),
    ("g2_bn256", "gemm2", "BLOCK_SIZE_N", 256),
    ("g2_bk64", "gemm2", "BLOCK_SIZE_K", 64),
    ("g2_bk32", "gemm2", "BLOCK_SIZE_K", 32),
)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: benchmark-op007-generic-moe-config.py OUTPUT_JSON")
    output = Path(sys.argv[1]).resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")
    module = importlib.import_module("flag_gems.fused.fused_moe")
    if inspect.getfile(flag_gems.fused_experts_impl) != module.__file__:
        raise SystemExit("FlagGems fused_experts_impl import source mismatch")
    original_config = module.get_default_config
    original_dispatch = module.dispatch_fused_moe_kernel
    signature = inspect.signature(original_dispatch)
    active = None
    records = []
    hits = 0

    def config_wrapper(*args, **kwargs):
        nonlocal hits
        cfg = original_config(*args, **kwargs)
        stage = kwargs.get("gemm_stage", "gemm1")
        if active is not None and stage == active[1]:
            cfg[active[2]] = active[3]
            hits += 1
        return cfg

    def dispatch_wrapper(*args, **kwargs):
        bound = signature.bind(*args, **kwargs).arguments
        A, B, C = (bound[name] for name in ("A", "B", "C"))
        sorted_ids = bound["sorted_token_ids"]
        cfg = dict(bound["config"])
        fused = bool(bound.get("FUSE_SILU", False))
        actual_n = B.size(1) // 2 if fused else B.size(1)
        em = sorted_ids.numel() if sorted_ids is not None else (
            A.size(0) * bound["top_k"] * cfg["BLOCK_SIZE_M"]
        )
        if A.size(0) < cfg["BLOCK_SIZE_M"] and sorted_ids is not None:
            em = min(em, A.size(0) * bound["top_k"] * cfg["BLOCK_SIZE_M"])
        if len(records) < 2:
            records.append({
                "stage": "gemm1" if B.size(2) == H else "gemm2",
                "A_shape": list(A.shape), "B_shape": list(B.shape),
                "C_shape": list(C.shape),
                "sorted_ids_shape": list(sorted_ids.shape) if sorted_ids is not None else None,
                "expert_ids_shape": list(bound["expert_ids"].shape),
                "top_k": bound["top_k"], "fuse_silu": fused,
                "config": cfg, "source_grid_x": (
                    triton.cdiv(em, cfg["BLOCK_SIZE_M"])
                    * triton.cdiv(actual_n, cfg["BLOCK_SIZE_N"])
                ),
            })
        return original_dispatch(*args, **kwargs)

    module.get_default_config = config_wrapper
    module.dispatch_fused_moe_kernel = dispatch_wrapper
    device = torch.device("cuda:0")
    torch.manual_seed(20260923)
    hidden = torch.randn((M, H), device=device, dtype=torch.bfloat16) * 0.02
    w1 = torch.randn((E, 2 * I, H), device=device, dtype=torch.bfloat16) * 0.02
    w2 = torch.randn((E, H, I), device=device, dtype=torch.bfloat16) * 0.02
    ids = torch.stack([torch.randperm(E, device=device)[:TOP_K] for _ in range(M)]).to(torch.int64)
    weights = torch.rand((M, TOP_K), device=device, dtype=torch.float32)
    weights = (weights / weights.sum(dim=-1, keepdim=True)).to(torch.bfloat16)
    originals = [x.clone() for x in (hidden, w1, w2, ids, weights)]
    started = time.time()
    results = []
    status = "complete"
    failure = None

    def call():
        return flag_gems.fused_experts_impl(
            hidden, w1, w2, weights, ids, inplace=False, activation="silu"
        )

    def bench():
        p50, p20, p80 = triton.testing.do_bench(
            call, warmup=30, rep=150, quantiles=[0.5, 0.2, 0.8]
        )
        return {"p50": float(p50), "p20": float(p20), "p80": float(p80)}

    try:
        reference = call()
        torch.cuda.synchronize(device)
        baseline_before = bench()
        print(json.dumps({"baseline_before": baseline_before,
                          "stage_records": records}), flush=True)
        for variant in VARIANTS:
            active = variant
            hits = 0
            row = {"variant": variant[0], "stage": variant[1],
                   "key": variant[2], "value": variant[3]}
            try:
                actual = call()
                torch.cuda.synchronize(device)
                diff = (actual.float() - reference.float()).abs()
                row["numerical"] = {
                    "allclose": bool(torch.allclose(actual, reference, atol=ATOL, rtol=RTOL)),
                    "finite": bool(torch.isfinite(actual).all()),
                    "max_abs": float(diff.max().item()),
                    "mean_abs": float(diff.mean().item()),
                }
                row["config_hits_on_first_call"] = hits
                if row["numerical"]["allclose"] and row["numerical"]["finite"] and hits:
                    row["timing_ms"] = bench()
                    row["status"] = "valid_search"
                else:
                    row["status"] = "invalid_numerical_or_no_config_hit"
            except Exception as exc:
                row["status"] = "failed_exception"
                row["error"] = f"{type(exc).__name__}: {exc}"
            results.append(row)
            print(json.dumps(row), flush=True)
            active = None
        baseline_after = bench()
        baseline_reference = statistics.median((
            baseline_before["p50"], baseline_after["p50"]
        ))
        for row in results:
            if row["status"] == "valid_search":
                row["improvement_percent_vs_bracketed_baseline"] = (
                    100 * (baseline_reference - row["timing_ms"]["p50"])
                    / baseline_reference
                )
        immutable = all(torch.equal(x, y) for x, y in zip(
            (hidden, w1, w2, ids, weights), originals
        ))
        if not immutable:
            status = "rejected_input_mutation"
            failure = "one or more inputs or weights changed"
    except Exception as exc:
        status = "failed_exception"
        failure = f"{type(exc).__name__}: {exc}"
        baseline_before = locals().get("baseline_before")
        baseline_after = locals().get("baseline_after")
        baseline_reference = locals().get("baseline_reference")
        immutable = None
    finally:
        module.get_default_config = original_config
        module.dispatch_fused_moe_kernel = original_dispatch
        payload = {
            "schema_version": 1, "experiment_id": "op-007-generic-flaggems-moe-stage-config-screen",
            "scope": "single_card_fake_weights_m32_search_only",
            "source_file": module.__file__, "device": torch.cuda.get_device_name(device),
            "shape_contract": {"M": M, "E": E, "H": H, "I_per_tp": I,
                               "top_k": TOP_K, "dtype": "bf16", "activation": "silu"},
            "protocol": {"timing": "triton.testing.do_bench_complete_call",
                         "warmup_ms": 30, "measurement_ms": 150,
                         "baseline_bracket": True, "atol": ATOL, "rtol": RTOL},
            "baseline_before_ms": baseline_before,
            "baseline_after_ms": baseline_after,
            "baseline_reference_p50_ms": baseline_reference,
            "stage_records": records,
            "inputs_immutable": immutable,
            "status": status, "failure": failure,
            "elapsed_seconds": time.time() - started,
            "results": results,
        }
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"status": status, "failure": failure,
                          "result": str(output), "best": sorted(
                              ((r.get("improvement_percent_vs_bracketed_baseline", -1e9),
                                r["variant"]) for r in results), reverse=True)[:3]}),
              flush=True)
    if status != "complete":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
