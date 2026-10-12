#!/usr/bin/env python3
"""Process-local exact-shape MoE dispatch probe; does not modify source."""

import importlib
import inspect
import json
from pathlib import Path
import sys

import torch
import triton
import flaggems_vllm


if len(sys.argv) != 2:
    raise SystemExit("usage: prof002-moe-stage-shape-probe.py OUTPUT_JSON")
output = Path(sys.argv[1]).resolve()
if output.exists():
    raise SystemExit(f"refusing to overwrite {output}")

module = importlib.import_module("flaggems_vllm.runtime.backend._thead.ops.fused_moe")
original = module.dispatch_fused_moe_kernel
signature = inspect.signature(original)
rows = []


def probe(*args, **kwargs):
    bound = signature.bind_partial(*args, **kwargs).arguments
    A, B, C = (bound[name] for name in ("A", "B", "C"))
    sorted_ids = bound["sorted_token_ids"]
    config = bound["config"].copy()
    top_k = bound["top_k"]
    fuse_silu = bool(bound.get("FUSE_SILU", False))
    em = (sorted_ids.numel() if sorted_ids is not None
          else A.size(0) * top_k * config["BLOCK_SIZE_M"])
    actual_n = B.size(1) // 2 if fuse_silu else B.size(1)
    grid = triton.cdiv(em, config["BLOCK_SIZE_M"]) * triton.cdiv(
        actual_n, config["BLOCK_SIZE_N"]
    )
    rows.append({
        "stage": "gemm1" if B.size(2) == 6144 else "gemm2",
        "A_shape": list(A.shape),
        "B_shape": list(B.shape),
        "C_shape": list(C.shape),
        "sorted_ids_shape": list(sorted_ids.shape) if sorted_ids is not None else None,
        "expert_ids_shape": list(bound["expert_ids"].shape),
        "top_k": top_k,
        "fuse_silu": fuse_silu,
        "config": config,
        "effective_em_capacity": em,
        "grid_programs_from_source": grid,
    })
    return original(*args, **kwargs)


M, E, H, I, TOP_K = 32, 128, 6144, 192, 4
device = torch.device("cuda:0")
torch.manual_seed(20260923)
hidden = torch.randn((M, H), device=device, dtype=torch.bfloat16) * 0.02
w1 = torch.randn((E, 2 * I, H), device=device, dtype=torch.bfloat16) * 0.02
w2 = torch.randn((E, H, I), device=device, dtype=torch.bfloat16) * 0.02
ids = torch.stack([torch.randperm(E, device=device)[:TOP_K] for _ in range(M)])
weights = torch.rand((M, TOP_K), device=device, dtype=torch.float32)
weights = (weights / weights.sum(dim=-1, keepdim=True)).to(torch.bfloat16)

module.dispatch_fused_moe_kernel = probe
try:
    result = flaggems_vllm.ops_experts_impl(
        hidden, w1, w2, weights, ids, inplace=False, activation="silu"
    )
    torch.cuda.synchronize(device)
finally:
    module.dispatch_fused_moe_kernel = original

if len(rows) != 2 or not torch.isfinite(result).all():
    raise SystemExit(f"unexpected dispatch stages or nonfinite output: {rows}")
payload = {
    "schema_version": 1,
    "scope": "independent_single_card_fake_weights_not_live_model_dispatch",
    "device": torch.cuda.get_device_name(device),
    "module_file": module.__file__,
    "shape_contract": {"M": M, "E": E, "hidden": H, "local_intermediate": I, "top_k": TOP_K},
    "rows": rows,
}
output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print(json.dumps(payload, indent=2, sort_keys=True))
