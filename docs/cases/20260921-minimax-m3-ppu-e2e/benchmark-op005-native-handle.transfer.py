#!/usr/bin/env python3
"""Check a saved native mm handle inside the FlagGems linear registration."""

import importlib.util
import json
from pathlib import Path
import statistics
import time

import torch
import torch.nn.functional as F
import triton.testing

import flag_gems
from flag_gems.ops.linear import linear as flaggems_linear


OUTPUT = Path(
    "/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/"
    "results/op005-native-handle-registration-graph.json"
)
SHAPES = ((32, 384, 6144), (32, 768, 6144), (32, 1024, 6144),
          (32, 1536, 6144), (32, 6144, 192), (32, 6144, 512),
          (32, 6144, 768), (32, 12512, 6144))
ATOL = 0.08
RTOL = 0.02
KEYSET = torch._C.DispatchKeySet(torch._C.DispatchKey.CUDA)
NATIVE_MM = torch.library.get_kernel(torch.ops.aten.mm.default, "CUDA")


def compare(actual, expected):
    delta = (actual.float() - expected.float()).abs()
    return {
        "allclose": bool(torch.allclose(actual, expected, atol=ATOL, rtol=RTOL)),
        "max_abs": float(delta.max().item()),
        "mean_abs": float(delta.mean().item()),
    }


def p50_ms(fn):
    return float(triton.testing.do_bench(fn, warmup=30, rep=150))


def graph_two_replays(fn, x, w, expected):
    # A private graph per implementation tests capture/replay independently.
    side = torch.cuda.Stream()
    side.wait_stream(torch.cuda.current_stream())
    with torch.cuda.stream(side):
        for _ in range(3):
            fn(x, w)
    torch.cuda.current_stream().wait_stream(side)
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        captured = fn(x, w)
    outcomes = []
    for _ in range(2):
        graph.replay()
        torch.cuda.synchronize()
        outcomes.append(compare(captured, expected))
    return outcomes


def main():
    if OUTPUT.exists():
        raise SystemExit(f"refusing to overwrite {OUTPUT}")
    torch.manual_seed(20260923)
    started = time.time()
    results = []
    for m, n, k in SHAPES:
        x = torch.randn((m, k), device="cuda:0", dtype=torch.bfloat16) * 0.02
        w = torch.randn((n, k), device="cuda:0", dtype=torch.bfloat16) * 0.02
        expected = F.linear(x, w)

        def saved_native(a, b):
            return NATIVE_MM.call_boxed(KEYSET, a, b.t())

        with flag_gems.use_gems(include=["linear"]):
            def registered(a, b):
                return F.linear(a, b)

            registered_out = registered(x, w)
            native_out = saved_native(x, w)
            registration_check = compare(registered_out, flaggems_linear(x, w))
            native_check = compare(native_out, expected)
            if not registration_check["allclose"] or not native_check["allclose"]:
                raise RuntimeError(f"numerical mismatch {(m,n,k)}: {registration_check} {native_check}")
            timings = {"registered": [], "saved_native": []}
            for order in (("registered", "saved_native"), ("saved_native", "registered")):
                for name in order:
                    fn = registered if name == "registered" else saved_native
                    timings[name].append(p50_ms(lambda: fn(x, w)))
            graphs = {
                "registered": graph_two_replays(registered, x, w, expected),
                "saved_native": graph_two_replays(saved_native, x, w, expected),
            }
        reg_ms = statistics.median(timings["registered"])
        native_ms = statistics.median(timings["saved_native"])
        results.append({
            "m": m, "n": n, "k": k,
            "registration_check": registration_check,
            "native_check": native_check,
            "registered_p50_ms": reg_ms,
            "saved_native_p50_ms": native_ms,
            "saved_native_improvement_percent": 100 * (reg_ms - native_ms) / reg_ms,
            "timings_ms": timings,
            "graph_replays": graphs,
        })
        del x, w, expected, registered_out, native_out
        torch.cuda.empty_cache()
    payload = {
        "schema_version": 1,
        "experiment_id": "op-005-native-linear-backend-screen",
        "test": "saved_native_mm_under_flaggems_linear_registration",
        "torch_version": torch.__version__,
        "flaggems_module": importlib.util.find_spec("flag_gems").origin,
        "device": torch.cuda.get_device_name(0),
        "protocol": {
            "complete_call": True,
            "timing": "triton.testing.do_bench",
            "warmup_ms": 30,
            "measurement_ms": 150,
            "rounds_per_implementation": 2,
            "order": ["registered", "saved_native", "saved_native", "registered"],
            "atol": ATOL, "rtol": RTOL,
            "graph_replays_per_implementation": 2,
            "scope": "candidate_confirmation_not_end_to_end",
        },
        "elapsed_seconds": time.time() - started,
        "results": results,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUTPUT), "elapsed_seconds": payload["elapsed_seconds"],
                      "results": [{k: v for k, v in row.items() if k not in
                                   ("registration_check", "native_check", "timings_ms", "graph_replays")}
                                  for row in results]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
