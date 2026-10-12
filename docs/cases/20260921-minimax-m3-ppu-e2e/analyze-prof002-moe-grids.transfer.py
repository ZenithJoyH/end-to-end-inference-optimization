#!/usr/bin/env python3
"""Group rank0 fused MoE device kernels by launch grid and phase."""

from bisect import bisect_right
from collections import defaultdict
import gzip
import json
from pathlib import Path
import re
import statistics
import sys


if len(sys.argv) != 2:
    raise SystemExit("usage: analyze-prof002-moe-grids.py RANK0_TRACE_GZ")
source = Path(sys.argv[1]).resolve()
with gzip.open(source, "rt", encoding="utf-8") as stream:
    payload = json.load(stream)
events = payload["traceEvents"] if isinstance(payload, dict) else payload
pattern = re.compile(r"execute_new_(\d+)_cached_(\d+)")
markers = []
for event in events:
    match = pattern.fullmatch(str(event.get("name", "")))
    if match and event.get("ph") == "X" and event.get("pid") == 0:
        new, cached = map(int, match.groups())
        phase = ("mixed" if cached else "prefill_only") if new else (
            "decode_only" if cached else "idle")
        markers.append((event["ts"], event["ts"] + event["dur"], phase))
markers.sort()
starts = [row[0] for row in markers]
groups = defaultdict(list)

for event in events:
    if event.get("name") != "fused_moe_kernel" or event.get("ph") != "X":
        continue
    if "kernel" not in {part.strip() for part in str(event.get("cat", "")).split(",")}:
        continue
    mid = event["ts"] + event["dur"] / 2
    index = bisect_right(starts, mid) - 1
    phase = markers[index][2] if index >= 0 and mid <= markers[index][1] else "outside"
    args = event.get("args", {})
    grid = tuple(args.get("grid", ()))
    groups[(phase, grid, args.get("registers per thread"), args.get("shared memory"))].append(
        event["dur"]
    )

rows = []
for (phase, grid, registers, shared_memory), durations in groups.items():
    rows.append({
        "phase": phase,
        "grid": list(grid),
        "registers_per_thread": registers,
        "shared_memory_bytes": shared_memory,
        "calls": len(durations),
        "activity_sum_s": sum(durations) / 1e6,
        "p50_us": statistics.median(durations),
        "p95_us": sorted(durations)[int(0.95 * (len(durations) - 1))],
    })
rows.sort(key=lambda row: row["activity_sum_s"], reverse=True)
json.dump({
    "schema_version": 1,
    "trace": str(source),
    "warning": "Grid to GEMM stage requires independent live source/config mapping; kernel activity sums may overlap and are not wall time.",
    "groups": rows,
}, sys.stdout, indent=2, sort_keys=True)
sys.stdout.write("\n")
