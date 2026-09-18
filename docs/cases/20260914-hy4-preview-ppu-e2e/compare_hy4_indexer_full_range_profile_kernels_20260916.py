#!/usr/bin/env python3
"""Compare whole-rank0 Indexer-related kernels without phase-marker bias."""

from __future__ import annotations

import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path
import re

import ijson


EXACT_TARGETS = {
    "bmm_kernel",
    "relu_forward_kernel_rank_1",
    "non_tle_top_k_per_row_prefill",
    "non_tle_top_k_per_row_decode",
    "_fill_hyv4_full_range_indices_kernel",
    "_convert_req_index_to_global_index_kernel",
    "triton_flash_mla_sparse_fwd",
    "_flash_mla_sparse_splitk_stage1",
    "_flash_mla_sparse_splitk_stage2",
}


def canonical_name(name: str) -> str | None:
    if name in EXACT_TARGETS:
        return name
    if (
        name.startswith("void at::native::reduce_kernel<512, 1")
        and "sum_functor" in name
    ):
        return "sum_reduce_kernel"
    return None


def rank0_trace(trace_dir: Path) -> Path:
    matches = [
        path
        for path in trace_dir.glob("*.json.gz")
        if re.search(r"_rank0\.", path.name)
    ]
    if len(matches) != 1:
        raise SystemExit(f"expected one rank0 trace in {trace_dir}, found {len(matches)}")
    return matches[0]


def summarize(trace_dir: Path) -> dict:
    trace = rank0_trace(trace_dir)
    totals = defaultdict(
        lambda: {"count": 0, "total_us": 0.0, "min_us": None, "max_us": 0.0}
    )
    sparse_grids = defaultdict(lambda: {"count": 0, "total_us": 0.0})
    with gzip.open(trace, "rb") as stream:
        for event in ijson.items(stream, "traceEvents.item", use_float=True):
            if event.get("ph") != "X":
                continue
            name = canonical_name(str(event.get("name", "")))
            if name is None:
                continue
            args = event.get("args")
            if not isinstance(args, dict) or "grid" not in args:
                continue
            duration = float(event.get("dur", 0.0))
            row = totals[name]
            row["count"] += 1
            row["total_us"] += duration
            row["min_us"] = duration if row["min_us"] is None else min(row["min_us"], duration)
            row["max_us"] = max(row["max_us"], duration)
            if name.startswith("triton_flash_mla") or name.startswith("_flash_mla"):
                grid = tuple(args.get("grid", []))
                grid_row = sparse_grids[(name, grid)]
                grid_row["count"] += 1
                grid_row["total_us"] += duration

    for row in totals.values():
        row["average_us"] = row["total_us"] / row["count"]
    grids = []
    for (name, grid), row in sorted(sparse_grids.items()):
        grids.append(
            {
                "name": name,
                "grid": list(grid),
                **row,
                "average_us": row["total_us"] / row["count"],
            }
        )
    return {"trace": str(trace), "kernels": dict(sorted(totals.items())), "sparse_grids": grids}


def delta(before: dict, after: dict) -> dict:
    result = {}
    for name in sorted(set(before) | set(after)):
        old = before.get(name, {"count": 0, "total_us": 0.0})
        new = after.get(name, {"count": 0, "total_us": 0.0})
        old_us = old["total_us"]
        new_us = new["total_us"]
        result[name] = {
            "count_before": old["count"],
            "count_after": new["count"],
            "count_delta": new["count"] - old["count"],
            "total_us_before": old_us,
            "total_us_after": new_us,
            "total_us_delta": new_us - old_us,
            "total_us_change_fraction": ((new_us / old_us) - 1.0) if old_us else None,
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("before_trace_dir", type=Path)
    parser.add_argument("after_trace_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output already exists: {args.output}")

    before = summarize(args.before_trace_dir)
    after = summarize(args.after_trace_dir)
    result = {
        "schema_version": 1,
        "scope": "whole rank0 trace; events with launch grid; independent of phase markers",
        "before": before,
        "after": after,
        "kernel_delta": delta(before["kernels"], after["kernels"]),
        "notes": [
            "The phase analyzer marker cannot distinguish later chunked-Prefill continuations from true Decode.",
            "Kernel totals here intentionally cover the full rank0 trace.",
            "Profiler-on duration is diagnostic and is not a formal performance result.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(args.output)


if __name__ == "__main__":
    main()
