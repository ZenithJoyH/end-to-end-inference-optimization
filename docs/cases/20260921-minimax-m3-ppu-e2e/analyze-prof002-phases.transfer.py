#!/usr/bin/env python3
"""Phase-scope rank0 device events using GPU execute_new annotations."""

from bisect import bisect_right
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path
import re
import sys


if len(sys.argv) != 2:
    raise SystemExit("usage: analyze-prof002-phases.py RANK0_TRACE_GZ")
source = Path(sys.argv[1]).resolve()
with gzip.open(source, "rt", encoding="utf-8") as stream:
    payload = json.load(stream)
events = payload["traceEvents"] if isinstance(payload, dict) else payload
pattern = re.compile(r"execute_new_(\d+)_cached_(\d+)")


def label(new, cached):
    if new and cached:
        return "mixed_prefill_decode"
    if new:
        return "prefill_only"
    if cached:
        return "decode_only"
    return "idle"


annotations = {"cpu_worker": [], "gpu": []}
for event in events:
    match = pattern.fullmatch(str(event.get("name", "")))
    if not match or event.get("ph") != "X":
        continue
    key = "gpu" if event.get("pid") == 0 else "cpu_worker"
    start = event["ts"]
    annotations[key].append({
        "start_us": start,
        "end_us": start + event["dur"],
        "duration_us": event["dur"],
        "new": int(match.group(1)),
        "cached": int(match.group(2)),
        "phase": label(int(match.group(1)), int(match.group(2))),
        "name": event["name"],
    })
for group in annotations.values():
    group.sort(key=lambda row: row["start_us"])
if not annotations["gpu"] or not annotations["cpu_worker"]:
    raise SystemExit("missing GPU or CPU execute_new phase annotations")

gpu = annotations["gpu"]
starts = [row["start_us"] for row in gpu]
phase_durations = defaultdict(Counter)
phase_calls = defaultdict(Counter)
phase_categories = defaultdict(Counter)
phase_event_count = Counter()
phase_duration_us = Counter()
unassigned_samples = []

for event in events:
    if event.get("ph") != "X":
        continue
    categories = {part.strip() for part in str(event.get("cat", "")).split(",")}
    category = next((value for value in ("kernel", "gpu_memcpy", "gpu_memset")
                     if value in categories), None)
    if category is None:
        continue
    mid = event["ts"] + event["dur"] / 2
    position = bisect_right(starts, mid) - 1
    candidates = []
    # Adjacent annotations may overlap; retain that uncertainty explicitly.
    for index in (position - 1, position):
        if index >= 0 and gpu[index]["start_us"] <= mid <= gpu[index]["end_us"]:
            candidates.append(gpu[index])
    if len(candidates) == 1:
        phase = candidates[0]["phase"]
    elif len(candidates) > 1:
        phase = "overlap_ambiguous"
    else:
        phase = "outside_gpu_annotation"
        if len(unassigned_samples) < 5:
            unassigned_samples.append({"name": event["name"], "ts": event["ts"]})
    phase_event_count[phase] += 1
    phase_duration_us[phase] += event["dur"]
    phase_durations[phase][event["name"]] += event["dur"]
    phase_calls[phase][event["name"]] += 1
    phase_categories[phase][category] += event["dur"]

cpu = annotations["cpu_worker"]
cpu_gaps = []
for previous, current in zip(cpu, cpu[1:]):
    cpu_gaps.append({
        "gap_ms": (current["start_us"] - previous["end_us"]) / 1000,
        "previous_phase": previous["phase"],
        "next_phase": current["phase"],
        "previous": previous["name"],
        "next": current["name"],
    })

result = {
    "schema_version": 1,
    "trace": str(source),
    "phase_method": "GPU pid=0 execute_new_<new>_cached_<cached> annotation contains device event midpoint; CPU worker annotations only for host step gaps",
    "scope_warning": "Activity durations can overlap across streams and are not critical-path or wall time; Prefill/Mixed classification uses request-count annotations, not per-token kernel semantics.",
    "annotation_counts": {
        group: dict(Counter(row["phase"] for row in rows))
        for group, rows in annotations.items()
    },
    "gpu_annotation_overlap_pairs": sum(
        left["end_us"] > right["start_us"]
        for left, right in zip(gpu, gpu[1:])
    ),
    "device_event_count": dict(phase_event_count),
    "device_activity_sum_s": {key: value / 1e6 for key, value in phase_duration_us.items()},
    "device_category_sum_s": {
        phase: {key: value / 1e6 for key, value in categories.items()}
        for phase, categories in phase_categories.items()
    },
    "top_kernels_by_phase": {
        phase: [
            {"name": name, "activity_sum_s": duration / 1e6,
             "calls": phase_calls[phase][name]}
            for name, duration in counts.most_common(20)
        ]
        for phase, counts in phase_durations.items()
    },
    "selected_kernels_by_phase": {
        phase: {
            name: {"activity_sum_s": phase_durations[phase][name] / 1e6,
                   "calls": phase_calls[phase][name]}
            for name in ("fused_moe_kernel", "linear_kernel",
                         "_gqa_sparse_fwd_kernel", "_gqa_sparse_decode_kernel")
        }
        for phase in phase_durations
    },
    "outside_annotation_samples": unassigned_samples,
    "cpu_worker_step_counts": dict(Counter(row["phase"] for row in cpu)),
    "cpu_worker_step_duration_s": {
        phase: sum(row["duration_us"] for row in cpu if row["phase"] == phase) / 1e6
        for phase in {row["phase"] for row in cpu}
    },
    "cpu_worker_positive_gap_s": sum(max(row["gap_ms"], 0) for row in cpu_gaps) / 1000,
    "cpu_worker_largest_gaps": sorted(cpu_gaps, key=lambda row: row["gap_ms"], reverse=True)[:10],
}
json.dump(result, sys.stdout, indent=2, sort_keys=True)
sys.stdout.write("\n")
