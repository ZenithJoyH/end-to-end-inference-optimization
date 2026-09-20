#!/usr/bin/env python3
"""Split a torch-profiler trace by vLLM graph-execution windows.

The report uses graph annotation intervals only for attribution. Device times are
cumulative kernel durations, not critical-path or wall-clock measurements.
"""

from __future__ import annotations

import argparse
import bisect
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path


DEVICE_CATEGORIES = frozenset(("kernel", "gpu_memcpy", "gpu_memset"))
CPU_CATEGORIES = frozenset(
    ("cpu_op", "user_annotation", "python_function", "cuda_runtime", "cuda_driver")
)


def load_events(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    events = payload.get("traceEvents") if isinstance(payload, dict) else payload
    if not isinstance(events, list):
        raise ValueError("traceEvents is not a list")
    return events


def category(event: dict) -> str:
    values = {item.strip() for item in str(event.get("cat", "")).split(",")}
    if values & CPU_CATEGORIES:
        return "cpu"
    if values & DEVICE_CATEGORIES:
        return "device"
    return "unclassified"


def valid_complete(event: dict) -> bool:
    if event.get("ph") != "X":
        return False
    ts = event.get("ts")
    dur = event.get("dur")
    return (
        type(ts) in (int, float)
        and type(dur) in (int, float)
        and math.isfinite(ts)
        and math.isfinite(dur)
        and dur > 0
    )


def marker_phase(name: str) -> str | None:
    if name.startswith("execute_new_0_cached_"):
        return "decode_graph"
    if name.startswith("execute_new_1_cached_") or name.startswith("execute_new_4_cached_"):
        return "prefill_mixed_graph"
    return None


def merge_intervals(markers: list[tuple[float, float, str, str]]) -> list[tuple[float, float, str]]:
    merged: list[tuple[float, float, str]] = []
    for start, end, phase, _ in sorted(markers):
        if merged and phase == merged[-1][2] and start <= merged[-1][1]:
            old_start, old_end, old_phase = merged[-1]
            merged[-1] = (old_start, max(old_end, end), old_phase)
        else:
            merged.append((start, end, phase))
    for previous, current in zip(merged, merged[1:]):
        if current[0] < previous[1] and current[2] != previous[2]:
            raise ValueError(f"overlapping phase windows: {previous!r} and {current!r}")
    return merged


def add_stat(table: dict, name: str, duration: float) -> None:
    row = table[name]
    row["count"] += 1
    row["total_us"] += duration
    row["min_us"] = min(row["min_us"], duration)
    row["max_us"] = max(row["max_us"], duration)


def serializable_stats(table: dict, limit: int = 30) -> list[dict]:
    rows = []
    for name, value in sorted(table.items(), key=lambda item: item[1]["total_us"], reverse=True)[:limit]:
        rows.append(
            {
                "name": name,
                "count": value["count"],
                "total_us": round(value["total_us"], 3),
                "avg_us": round(value["total_us"] / value["count"], 3),
                "min_us": round(value["min_us"], 3),
                "max_us": round(value["max_us"], 3),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    events = load_events(args.trace)
    marker_rows = []
    seen_markers = set()
    marker_names: dict[str, dict] = defaultdict(lambda: {"count": 0, "total_us": 0.0})
    for event in events:
        if not valid_complete(event):
            continue
        name = event.get("name")
        if not isinstance(name, str):
            continue
        # The same compiled-graph name also appears on nested CPU/Python
        # annotations. Only the graph replay annotations are unclassified by
        # the maintained trace parser; mixing the inclusive wrappers creates
        # overlapping windows and invalid phase attribution.
        if category(event) != "unclassified":
            continue
        phase = marker_phase(name)
        if phase is None:
            continue
        key = (event["ts"], event["dur"], name)
        if key in seen_markers:
            continue
        seen_markers.add(key)
        marker_rows.append((float(event["ts"]), float(event["ts"] + event["dur"]), phase, name))
        marker_names[name]["count"] += 1
        marker_names[name]["total_us"] += float(event["dur"])

    if not marker_rows:
        raise ValueError("no execute_new_0/1/4 graph markers found")
    intervals = merge_intervals(marker_rows)
    starts = [row[0] for row in intervals]
    phase_device = defaultdict(
        lambda: defaultdict(lambda: {"count": 0, "total_us": 0.0, "min_us": float("inf"), "max_us": 0.0})
    )
    phase_sync = defaultdict(
        lambda: defaultdict(lambda: {"count": 0, "total_us": 0.0, "min_us": float("inf"), "max_us": 0.0})
    )
    coverage = defaultdict(lambda: {"events": 0, "total_us": 0.0})

    for event in events:
        if not valid_complete(event):
            continue
        event_category = category(event)
        name = event.get("name")
        if not isinstance(name, str):
            continue
        if event_category != "device" and name != "cudaStreamSynchronize":
            continue
        ts = float(event["ts"])
        index = bisect.bisect_right(starts, ts) - 1
        phase = "outside_graph_windows"
        if index >= 0 and ts < intervals[index][1]:
            phase = intervals[index][2]
        duration = float(event["dur"])
        if event_category == "device":
            add_stat(phase_device[phase], name, duration)
            coverage[phase]["events"] += 1
            coverage[phase]["total_us"] += duration
        elif name == "cudaStreamSynchronize":
            add_stat(phase_sync[phase], name, duration)

    report = {
        "schema_version": 1,
        "trace": str(args.trace),
        "event_count": len(events),
        "method": {
            "prefill_mixed_graph": "device-event start timestamp is inside execute_new_4_cached_* annotation",
            "decode_graph": "device-event start timestamp is inside execute_new_0_cached_* annotation",
            "warning": "all durations are cumulative and may overlap; profiler-on results are diagnostic only",
        },
        "markers": {
            name: {"count": value["count"], "total_us": round(value["total_us"], 3)}
            for name, value in sorted(marker_names.items())
        },
        "merged_intervals": [
            {"start_us": start, "end_us": end, "duration_us": end - start, "phase": phase}
            for start, end, phase in intervals
        ],
        "device_coverage": {
            phase: {"events": value["events"], "total_us": round(value["total_us"], 3)}
            for phase, value in sorted(coverage.items())
        },
        "top_device_events": {
            phase: serializable_stats(table) for phase, table in sorted(phase_device.items())
        },
        "stream_synchronize": {
            phase: serializable_stats(table, limit=5) for phase, table in sorted(phase_sync.items())
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"output": str(args.output), "markers": report["markers"], "coverage": report["device_coverage"]}, indent=2))


if __name__ == "__main__":
    main()
