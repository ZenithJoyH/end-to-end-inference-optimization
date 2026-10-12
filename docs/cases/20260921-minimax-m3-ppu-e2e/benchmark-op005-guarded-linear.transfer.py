#!/usr/bin/env python3
"""Verify installed op005 guard hits only its intended shapes and graphs."""

import importlib
import json
from pathlib import Path
import statistics
import time

import flag_gems
import torch
import torch.nn.functional as F
import triton.testing


LINEAR = importlib.import_module("flag_gems.ops.linear")
OUTPUT = Path(
    "/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/"
    "results/op005-guarded-linear-regression.json"
)
SHAPES = ((32, 384, 6144), (32, 1024, 6144), (32, 768, 6144),
          (32, 1536, 6144), (32, 6144, 192), (32, 6144, 512),
          (32, 6144, 768), (32, 12512, 6144), (16, 384, 6144),
          (8, 1024, 6144))
TARGETS = {(32, 384, 6144), (32, 1024, 6144)}


class CountHandle:
    def __init__(self, native):
        self.native = native
        self.count = 0

    def call_boxed(self, *args, **kwargs):
        self.count += 1
        return self.native.call_boxed(*args, **kwargs)


def error(actual, expected):
    delta = (actual.float() - expected.float()).abs()
    return {"allclose": bool(torch.allclose(actual, expected, atol=0.08, rtol=0.02)),
            "max_abs": float(delta.max().item())}


def graph_replays(x, w, expected):
    side = torch.cuda.Stream()
    side.wait_stream(torch.cuda.current_stream())
    with torch.cuda.stream(side):
        for _ in range(3):
            F.linear(x, w)
    torch.cuda.current_stream().wait_stream(side)
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        output = F.linear(x, w)
    results = []
    for _ in range(2):
        graph.replay()
        torch.cuda.synchronize()
        results.append(error(output, expected))
    return results


def main():
    if OUTPUT.exists():
        raise SystemExit(f"refusing to overwrite {OUTPUT}")
    original = LINEAR._NATIVE_MM
    if original is None:
        raise RuntimeError("patched native mm handle is unavailable")
    counter = CountHandle(original)
    torch.manual_seed(20260923)
    started = time.time()
    rows = []
    try:
        for m, n, k in SHAPES:
            x = torch.randn((m, k), device="cuda:0", dtype=torch.bfloat16) * 0.02
            w = torch.randn((n, k), device="cuda:0", dtype=torch.bfloat16) * 0.02
            expected = F.linear(x, w)
            with flag_gems.use_gems(include=["linear"]):
                LINEAR._NATIVE_MM = counter
                before = counter.count
                actual = F.linear(x, w)
                hit = counter.count - before
                wanted = 1 if (m, n, k) in TARGETS else 0
                if hit != wanted:
                    raise RuntimeError(f"unexpected guard hit {(m,n,k)}: {hit}, wanted {wanted}")
                numerical = error(actual, expected)
                if not numerical["allclose"]:
                    raise RuntimeError(f"numerical mismatch {(m,n,k)}: {numerical}")
                timings = {"baseline": [], "candidate": []}
                for order in (("baseline", "candidate"), ("candidate", "baseline")):
                    for name in order:
                        LINEAR._NATIVE_MM = None if name == "baseline" else counter
                        timings[name].append(float(triton.testing.do_bench(
                            lambda: F.linear(x, w), warmup=30, rep=150)))
                LINEAR._NATIVE_MM = counter
                replay = graph_replays(x, w, expected)
                if not all(item["allclose"] for item in replay):
                    raise RuntimeError(f"graph mismatch {(m,n,k)}: {replay}")
            baseline_ms = statistics.median(timings["baseline"])
            candidate_ms = statistics.median(timings["candidate"])
            rows.append({"m": m, "n": n, "k": k, "guard_hits": hit,
                         "numerical": numerical, "graph_replays": replay,
                         "timings_ms": timings, "baseline_p50_ms": baseline_ms,
                         "candidate_p50_ms": candidate_ms,
                         "improvement_percent": 100 * (baseline_ms - candidate_ms) / baseline_ms})
            del x, w, expected, actual
            torch.cuda.empty_cache()
    finally:
        LINEAR._NATIVE_MM = original
    payload = {"schema_version": 1, "experiment_id": "op-005-native-linear-backend-screen",
               "test": "installed_guard_exact_shape_hit_numerical_graph_and_micro",
               "scope": "candidate_confirmation_not_end_to_end",
               "protocol": {"timing": "triton.testing.do_bench", "warmup_ms": 30,
                            "measurement_ms": 150, "rounds_per_variant": 2,
                            "order": ["baseline", "candidate", "candidate", "baseline"],
                            "graph_replays": 2, "atol": 0.08, "rtol": 0.02},
               "elapsed_seconds": time.time() - started, "results": rows}
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUTPUT), "elapsed_seconds": payload["elapsed_seconds"],
                      "results": [{k: row[k] for k in ("m", "n", "k", "guard_hits", "baseline_p50_ms", "candidate_p50_ms", "improvement_percent")} for row in rows]},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
