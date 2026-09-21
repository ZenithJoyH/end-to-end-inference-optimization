#!/usr/bin/env python3
"""Screen BLOCK_SIZE_M=16 for the live Decode batch-drain shapes.

The implementation reuses the previously frozen full-pair MoE microbenchmark
and changes only its case table.  The four token counts come directly from the
post-op008 P4K rank-0 trace; the current tuned table uses BM32 for all four and
uses BM16 only at M=64 (and M<=32).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


CURRENT = {
    "BLOCK_SIZE_M": 32,
    "BLOCK_SIZE_N": 64,
    "BLOCK_SIZE_K": 128,
    "GROUP_SIZE_M": 1,
    "SPLIT_K": 1,
    "num_warps": 4,
    "num_stages": 3,
}

TRACE_GRIDS = {
    40: {"gemm1": 960, "gemm2": 12800},
    48: {"gemm1": 1200, "gemm2": 16000},
    56: {"gemm1": 1440, "gemm2": 19200},
    63: {"gemm1": 1542, "gemm2": 20560},
}


def load_base(path: Path):
    spec = importlib.util.spec_from_file_location("frozen_moe_microbench", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import frozen base microbenchmark: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--tokens", default="40,48,56,63")
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--repeat", type=int, default=100)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--seed", type=int, default=74284)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--atol", type=float, default=0.02)
    parser.add_argument("--rtol", type=float, default=0.02)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tokens = [int(value) for value in args.tokens.split(",") if value]
    if tokens != [40, 48, 56, 63]:
        raise ValueError("the frozen screen must remain M=40,48,56,63")
    if args.rounds != 3 or args.warmup < 1 or args.repeat < 1:
        raise ValueError("rounds must remain 3 and warmup/repeat must be positive")

    base = load_base(args.base)
    base.CASES = {
        f"m{value}": {
            "tokens": value,
            "baseline": dict(CURRENT),
            "candidate_block_m": 16,
        }
        for value in tokens
    }
    base.torch.cuda.set_device(args.device)
    device = base.torch.device("cuda", args.device)
    results = []
    for value in tokens:
        result = base.run_case(
            f"m{value}",
            args.warmup,
            args.repeat,
            args.rounds,
            args.seed,
            args.atol,
            args.rtol,
            device,
        )
        result["prof004_rank0_trace_grid"] = TRACE_GRIDS[value]
        result["screen_pass"] = bool(
            result["correctness"]["passed"]
            and result["graph"]["baseline"]["capture_ok"]
            and result["graph"]["candidate"]["capture_ok"]
            and result["pair_improvement_percent"] >= 5.0
        )
        results.append(result)

    payload = {
        "schema_version": 1,
        "experiment": "fused-moe-p4k-decode-batch-drain-block-m-screen",
        "scope": "screening_only_co_resident_idle_service",
        "dtype": "bfloat16",
        "device": args.device,
        "warmup": args.warmup,
        "iterations": args.repeat,
        "rounds": args.rounds,
        "graph_capture_replays": 2,
        "changed_fields": ["BLOCK_SIZE_M"],
        "retention_threshold_percent": 5.0,
        "results": results,
        "all_cases_pass": all(item["screen_pass"] for item in results),
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True)
    args.output.parent.mkdir(parents=True, exist_ok=False)
    args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
