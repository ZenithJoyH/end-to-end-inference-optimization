#!/usr/bin/env python3
"""Analyze normal-path phase annotations and rank spread for prof-001."""

from collections import Counter
import gzip
import json
from pathlib import Path
import re
import statistics
import sys


root = Path(sys.argv[1]).resolve()
trace_paths = sorted(root.glob("dp0_pp0_tp*_rank*.json.gz"))
if len(trace_paths) != 16:
    raise SystemExit(f"expected 16 rank traces, got {len(trace_paths)}")

rank_rows = []
timeline = None
for path in trace_paths:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        payload = json.load(stream)
    events = payload["traceEvents"] if isinstance(payload, dict) else payload
    device = [
        event for event in events
        if event.get("ph") == "X"
        and any(part.strip() in {"kernel", "gpu_memcpy", "gpu_memset"}
                for part in str(event.get("cat", "")).split(","))
    ]
    kernel_totals = Counter()
    for event in device:
        kernel_totals[event["name"]] += event["dur"]
    rank_match = re.search(r"rank(\d+)\.", path.name)
    rank = int(rank_match.group(1))
    collectives = sum(
        duration for name, duration in kernel_totals.items()
        if "pccl" in name.lower() or "nccl" in name.lower()
    )
    rank_rows.append(
        {
            "rank": rank,
            "trace": path.name,
            "device_sum_s": sum(kernel_totals.values()) / 1e6,
            "fused_moe_s": kernel_totals["fused_moe_kernel"] / 1e6,
            "linear_s": kernel_totals["linear_kernel"] / 1e6,
            "sparse_prefill_s": kernel_totals["_gqa_sparse_fwd_kernel"] / 1e6,
            "sparse_decode_s": kernel_totals["_gqa_sparse_decode_kernel"] / 1e6,
            "collective_s": collectives / 1e6,
        }
    )
    if rank == 0:
        annotated = [
            event for event in events
            if event.get("ph") == "X"
            and isinstance(event.get("name"), str)
            and event["name"].startswith("execute_new_")
            and "user_annotation" in str(event.get("cat", ""))
        ]
        annotated.sort(key=lambda event: event["ts"])
        timeline = []
        previous_end = None
        for event in annotated:
            match = re.fullmatch(r"execute_new_(\d+)_cached_(\d+)", event["name"])
            if not match:
                continue
            start = event["ts"]
            end = start + event["dur"]
            timeline.append(
                {
                    "name": event["name"],
                    "new_requests": int(match.group(1)),
                    "cached_requests": int(match.group(2)),
                    "start_from_first_ms": None,
                    "duration_ms": event["dur"] / 1000,
                    "gap_from_previous_ms": None if previous_end is None else (start - previous_end) / 1000,
                }
            )
            previous_end = end
        if timeline:
            first_start = annotated[0]["ts"]
            for row, event in zip(timeline, annotated):
                row["start_from_first_ms"] = (event["ts"] - first_start) / 1000

rank_rows.sort(key=lambda row: row["rank"])
if timeline is None:
    raise SystemExit("rank0 phase annotations not found")
prefill = [row for row in timeline if row["new_requests"] > 0]
decode = [row for row in timeline if row["new_requests"] == 0]
result = {
    "schema_version": 1,
    "trace_root": str(root),
    "rank_coverage": [row["rank"] for row in rank_rows],
    "rank_metrics": rank_rows,
    "rank_spread": {},
    "phase_boundary": {
        "method": "rank0 user annotations execute_new_<new>_cached_<cached>",
        "prefill_or_mixed_event_count": len(prefill),
        "decode_only_event_count": len(decode),
        "prefill_or_mixed_duration_s": sum(row["duration_ms"] for row in prefill) / 1000,
        "decode_only_duration_s": sum(row["duration_ms"] for row in decode) / 1000,
        "max_inter_event_gap_ms": max(
            (row["gap_from_previous_ms"] for row in timeline if row["gap_from_previous_ms"] is not None),
            default=None,
        ),
        "timeline": timeline,
    },
}
for key in ("device_sum_s", "fused_moe_s", "linear_s", "sparse_prefill_s", "sparse_decode_s", "collective_s"):
    values = [row[key] for row in rank_rows]
    center = statistics.median(values)
    result["rank_spread"][key] = {
        "min": min(values),
        "median": center,
        "max": max(values),
        "relative_spread": (max(values) - min(values)) / center if center else None,
    }
json.dump(result, sys.stdout, indent=2, sort_keys=True)
sys.stdout.write("\n")
