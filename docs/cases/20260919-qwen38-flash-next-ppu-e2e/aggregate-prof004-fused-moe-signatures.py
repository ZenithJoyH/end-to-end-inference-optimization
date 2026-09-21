#!/usr/bin/env python3
import bisect
import gzip
import json
from collections import defaultdict
from pathlib import Path

root = Path("/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/prof-004-p4k-post-op008")
trace = next((root / "traces").glob("dp0_pp0_tp0_*rank0.*.pt.trace.json.gz"))
phase_doc = json.loads((root / "summaries/phase-rank0.json").read_text())
intervals = sorted(phase_doc["merged_intervals"], key=lambda item: item["start_us"])
starts = [item["start_us"] for item in intervals]

def classify(timestamp):
    index = bisect.bisect_right(starts, timestamp) - 1
    if index >= 0 and timestamp < intervals[index]["end_us"]:
        return intervals[index]["phase"]
    return "outside_graph_windows"

with gzip.open(trace, "rt", encoding="utf-8") as handle:
    document = json.load(handle)

groups = defaultdict(lambda: {"count": 0, "total_us": 0.0, "min_us": float("inf"), "max_us": 0.0})
for event in document["traceEvents"]:
    if event.get("name") != "fused_moe_kernel":
        continue
    args = event.get("args", {})
    signature = (
        classify(event["ts"]),
        tuple(args.get("grid", [])),
        tuple(args.get("block", [])),
        args.get("registers per thread"),
        args.get("shared memory"),
        args.get("est. achieved occupancy %"),
    )
    row = groups[signature]
    duration = float(event["dur"])
    row["count"] += 1
    row["total_us"] += duration
    row["min_us"] = min(row["min_us"], duration)
    row["max_us"] = max(row["max_us"], duration)

rows = []
for signature, values in groups.items():
    phase, grid, block, registers, shared_memory, occupancy = signature
    rows.append({
        "phase": phase,
        "grid": list(grid),
        "block": list(block),
        "registers_per_thread": registers,
        "shared_memory": shared_memory,
        "estimated_occupancy_percent": occupancy,
        **values,
        "avg_us": values["total_us"] / values["count"],
    })
rows.sort(key=lambda item: item["total_us"], reverse=True)
output = {"trace": str(trace), "kernel": "fused_moe_kernel", "signatures": rows}
output_path = root / "summaries/fused-moe-signatures-by-phase.json"
output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
print(output_path)
print(json.dumps(output, indent=2, sort_keys=True))
