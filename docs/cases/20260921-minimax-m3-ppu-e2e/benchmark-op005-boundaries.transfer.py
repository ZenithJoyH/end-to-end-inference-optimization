#!/usr/bin/env python3
"""Target/boundary/fallback numerical and dispatch checks for op005."""

import importlib
import json
from pathlib import Path
import time

import flag_gems
import torch
import torch.nn.functional as F


LINEAR = importlib.import_module("flag_gems.ops.linear")
OUTPUT = Path(
    "/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/"
    "results/op005-linear-boundary-regression.json"
)


class CountHandle:
    def __init__(self, native):
        self.native = native
        self.count = 0

    def call_boxed(self, *args, **kwargs):
        self.count += 1
        return self.native.call_boxed(*args, **kwargs)


def compare(actual, expected, atol, rtol):
    delta = (actual.float() - expected.float()).abs()
    return {
        "shape": list(actual.shape),
        "allclose": bool(torch.allclose(actual, expected, atol=atol, rtol=rtol)),
        "max_abs": float(delta.max().item()) if delta.numel() else 0.0,
    }


def tensors(m, n, k, dtype, input_layout, weight_layout, bias):
    if input_layout == "contiguous":
        x = torch.randn((m, k), device="cuda:0", dtype=dtype) * 0.02
    else:
        x = (torch.randn((k, m), device="cuda:0", dtype=dtype) * 0.02).t()
    if weight_layout == "contiguous":
        w = torch.randn((n, k), device="cuda:0", dtype=dtype) * 0.02
    else:
        w = (torch.randn((k, n), device="cuda:0", dtype=dtype) * 0.02).t()
    b = torch.randn((n,), device="cuda:0", dtype=dtype) * 0.02 if bias else None
    return x, w, b


def main():
    if OUTPUT.exists():
        raise SystemExit(f"refusing to overwrite {OUTPUT}")
    original = LINEAR._NATIVE_MM
    if original is None:
        raise RuntimeError("op005 native handle unavailable")
    counter = CountHandle(original)
    torch.manual_seed(20260923)
    cases = (
        ("target_n384", 32, 384, 6144, torch.bfloat16, "contiguous", "contiguous", False, 1),
        ("target_n1024", 32, 1024, 6144, torch.bfloat16, "contiguous", "contiguous", False, 1),
        ("m31", 31, 384, 6144, torch.bfloat16, "contiguous", "contiguous", False, 0),
        ("m33", 33, 384, 6144, torch.bfloat16, "contiguous", "contiguous", False, 0),
        ("n383", 32, 383, 6144, torch.bfloat16, "contiguous", "contiguous", False, 0),
        ("k6145", 32, 384, 6145, torch.bfloat16, "contiguous", "contiguous", False, 0),
        ("bias", 32, 384, 6144, torch.bfloat16, "contiguous", "contiguous", True, 0),
        ("float16", 32, 384, 6144, torch.float16, "contiguous", "contiguous", False, 0),
        ("float32", 32, 384, 6144, torch.float32, "contiguous", "contiguous", False, 0),
        ("input_noncontiguous", 32, 384, 6144, torch.bfloat16, "transposed", "contiguous", False, 0),
        ("weight_noncontiguous", 32, 384, 6144, torch.bfloat16, "contiguous", "transposed", False, 0),
        ("empty_batch", 0, 384, 6144, torch.bfloat16, "contiguous", "contiguous", False, 0),
    )
    started = time.time()
    rows = []
    try:
        for name, m, n, k, dtype, x_layout, w_layout, has_bias, expected_hits in cases:
            x, w, b = tensors(m, n, k, dtype, x_layout, w_layout, has_bias)
            expected = F.linear(x, w, b)
            with flag_gems.use_gems(include=["linear"]):
                LINEAR._NATIVE_MM = counter
                before = counter.count
                actual = F.linear(x, w, b)
                hits = counter.count - before
                if hits != expected_hits:
                    raise RuntimeError(f"{name} hit {hits}, expected {expected_hits}")
                numerical = compare(actual, expected, 0.08, 0.02)
                if not numerical["allclose"]:
                    raise RuntimeError(f"{name} numerical mismatch: {numerical}")
                LINEAR._NATIVE_MM = None
                fallback = F.linear(x, w, b)
                fallback_numerical = compare(fallback, expected, 0.08, 0.02)
                if not fallback_numerical["allclose"]:
                    raise RuntimeError(f"{name} baseline mismatch: {fallback_numerical}")
            rows.append({"case": name, "m": m, "n": n, "k": k,
                         "dtype": str(dtype), "input_layout": x_layout,
                         "weight_layout": w_layout, "bias": has_bias,
                         "guard_hits": hits, "numerical": numerical,
                         "fallback_numerical": fallback_numerical})
            del x, w, b, expected, actual, fallback
    finally:
        LINEAR._NATIVE_MM = original
    payload = {"schema_version": 1, "experiment_id": "op-005-native-linear-backend-screen",
               "scope": "source_level_boundary_correctness_not_full_accuracy",
               "atol": 0.08, "rtol": 0.02,
               "elapsed_seconds": time.time() - started, "results": rows}
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUTPUT), "elapsed_seconds": payload["elapsed_seconds"],
                      "checks": [{"case": x["case"], "guard_hits": x["guard_hits"],
                                  "max_abs": x["numerical"]["max_abs"]} for x in rows]},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
