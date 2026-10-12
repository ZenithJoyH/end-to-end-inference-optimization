#!/usr/bin/env python3
"""Existing-implementation linear screen at MiniMax-M3 production M32 shapes."""

import importlib.util
import json
from pathlib import Path
import statistics
import time

import torch
import torch.nn.functional as F
import triton.testing

from flag_gems.ops.linear import linear as flaggems_linear


SHAPES = (
    (32, 384, 6144),
    (32, 768, 6144),
    (32, 1024, 6144),
    (32, 1536, 6144),
    (32, 6144, 192),
    (32, 6144, 512),
    (32, 6144, 768),
    (32, 12512, 6144),
)
ATOL = 0.08
RTOL = 0.02
OUTPUT = Path(
    "/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/"
    "results/op005-native-linear-backend-search.json"
)


def error_stats(actual: torch.Tensor, expected: torch.Tensor) -> dict:
    diff = (actual.float() - expected.float()).abs()
    return {
        "allclose": bool(torch.allclose(actual, expected, atol=ATOL, rtol=RTOL)),
        "max_abs": float(diff.max().item()),
        "mean_abs": float(diff.mean().item()),
    }


def bench(call) -> dict:
    p50, p20, p80 = triton.testing.do_bench(
        call, warmup=30, rep=150, quantiles=[0.5, 0.2, 0.8]
    )
    return {"p50_ms": float(p50), "p20_ms": float(p20), "p80_ms": float(p80)}


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit(f"refusing to overwrite {OUTPUT}")

    torch.manual_seed(20260923)
    device = torch.device("cuda:0")
    rows = []
    started = time.time()
    for m, n, k in SHAPES:
        x = torch.randn((m, k), device=device, dtype=torch.bfloat16) * 0.02
        weight = torch.randn((n, k), device=device, dtype=torch.bfloat16) * 0.02

        def current():
            return flaggems_linear(x, weight)

        def native():
            return F.linear(x, weight)

        current_output = current()
        native_output = native()
        torch.cuda.synchronize(device)
        numerical = error_stats(current_output, native_output)
        if not numerical["allclose"]:
            raise RuntimeError(f"numerical mismatch m={m} n={n} k={k}: {numerical}")

        # Reverse the second pass to expose simple temporal/order drift.
        timings = {"flaggems": [], "native": []}
        for names in (("flaggems", "native"), ("native", "flaggems")):
            for name in names:
                timings[name].append(bench(current if name == "flaggems" else native))

        current_ms = statistics.median(t["p50_ms"] for t in timings["flaggems"])
        native_ms = statistics.median(t["p50_ms"] for t in timings["native"])
        rows.append(
            {
                "shape": {"m": m, "n": n, "k": k, "dtype": "torch.bfloat16", "bias": False},
                "numerical": numerical,
                "measurements": timings,
                "flaggems_p50_median_ms": current_ms,
                "native_p50_median_ms": native_ms,
                "native_improvement_percent": 100 * (current_ms - native_ms) / current_ms,
            }
        )
        del x, weight, current_output, native_output
        torch.cuda.empty_cache()

    payload = {
        "schema_version": 1,
        "experiment_id": "op-005-native-linear-backend-screen",
        "device": torch.cuda.get_device_name(device),
        "torch_version": torch.__version__,
        "flaggems_module": importlib.util.find_spec("flag_gems").origin,
        "protocol": {
            "scope": "candidate_search_only",
            "complete_call": True,
            "timing": "triton.testing.do_bench",
            "warmup_ms": 30,
            "measurement_ms": 150,
            "rounds_per_implementation": 2,
            "order": ["flaggems", "native", "native", "flaggems"],
            "quantiles": [0.5, 0.2, 0.8],
            "atol": ATOL,
            "rtol": RTOL,
            "search_and_confirmation_separated": False,
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
                "by_shape": [
                    {
                        **row["shape"],
                        "flaggems_ms": row["flaggems_p50_median_ms"],
                        "native_ms": row["native_p50_median_ms"],
                        "native_improvement_percent": row["native_improvement_percent"],
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
