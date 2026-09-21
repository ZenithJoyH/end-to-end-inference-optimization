#!/usr/bin/env python3
"""Attribute P16K sparse-MLA kernel grids to Prefill/Mixed/Decode markers."""

from __future__ import annotations

import argparse
import bisect
import collections
import gzip
import json
import re
from pathlib import Path

PHASE_MARKER = re.compile(r"execute_new_(\d+)_cached_(\d+)")
TARGETS = {
    "triton_flash_mla_sparse_fwd",
    "_flash_mla_sparse_full_prefix_grouped",
    "_flash_mla_sparse_splitk_stage1",
    "_flash_mla_sparse_splitk_stage2",
}


def phase_for(name: str) -> str | None:
    match = PHASE_MARKER.search(name)
    if not match:
        return None
    new, cached = map(int, match.groups())
    if new and not cached:
        return "prefill"
    if new and cached:
        return "mixed"
    if cached and not new:
        return "decode"
    return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")

    markers: list[tuple[float, float, str, str]] = []
    kernels: list[dict] = []
    with gzip.open(args.trace, "rt", encoding="utf-8") as stream:
        payload = json.load(stream)
        for event in payload.get("traceEvents", []):
            if event.get("ph") != "X":
                continue
            name = event.get("name", "")
            if event.get("cat") == "gpu_user_annotation":
                phase = phase_for(name)
                if phase:
                    start = float(event["ts"])
                    markers.append(
                        (start, start + float(event.get("dur", 0.0)), phase, name)
                    )
                continue
            if name not in TARGETS:
                continue
            start = float(event["ts"])
            raw_args = event.get("args") if isinstance(event.get("args"), dict) else {}
            kernels.append(
                {
                    "name": name,
                    "start": start,
                    "midpoint": start + float(event.get("dur", 0.0)) / 2,
                    "duration_us": float(event.get("dur", 0.0)),
                    "grid": list(raw_args.get("grid", [])),
                    "block": list(raw_args.get("block", [])),
                    "stream": raw_args.get("stream"),
                }
            )

    markers.sort()
    starts = [row[0] for row in markers]
    grouped: dict[tuple[str, str, tuple], dict] = collections.defaultdict(
        lambda: {"count": 0, "total_us": 0.0, "min_us": None, "max_us": 0.0}
    )
    unassigned = 0
    for kernel in kernels:
        index = bisect.bisect_right(starts, kernel["midpoint"]) - 1
        phase = "unassigned"
        marker_name = None
        if index >= 0 and kernel["midpoint"] <= markers[index][1]:
            phase = markers[index][2]
            marker_name = markers[index][3]
        else:
            unassigned += 1
        key = (phase, kernel["name"], tuple(kernel["grid"]))
        row = grouped[key]
        row["count"] += 1
        row["total_us"] += kernel["duration_us"]
        row["min_us"] = (
            kernel["duration_us"]
            if row["min_us"] is None
            else min(row["min_us"], kernel["duration_us"])
        )
        row["max_us"] = max(row["max_us"], kernel["duration_us"])
        row["block"] = kernel["block"]
        row["stream"] = kernel["stream"]
        row["example_marker"] = marker_name

    rows = []
    for (phase, name, grid), row in grouped.items():
        item = {"phase": phase, "name": name, "grid": list(grid), **row}
        item["average_us"] = item["total_us"] / item["count"]
        if name in {"triton_flash_mla_sparse_fwd", "_flash_mla_sparse_full_prefix_grouped"} and grid:
            item["inferred_sq"] = grid[0]
        if name == "_flash_mla_sparse_splitk_stage2" and grid:
            item["inferred_sq"] = grid[0] // 8
        rows.append(item)
    rows.sort(key=lambda row: (row["phase"], -row["total_us"], row["name"], row["grid"]))

    result = {
        "schema_version": 1,
        "trace": str(args.trace),
        "marker_count": len(markers),
        "target_kernel_count": len(kernels),
        "unassigned_kernel_count": unassigned,
        "rows": rows,
        "notes": [
            "Generic and grouped kernels launch grid=(SQ,1,1).",
            "Split-K stage2 launches grid=(SQ*HQ*2,1,1), with HQ=4.",
            "Phase assignment uses the kernel midpoint inside execute_new/cached GPU annotations.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
