#!/usr/bin/env python3
"""Estimate exposed collective device time from a validated rank trace."""

from __future__ import annotations

import argparse
import bisect
import collections
import gzip
import json
import re
from pathlib import Path


PHASE_MARKER = re.compile(r"execute_new_(\d+)_cached_(\d+)")


def union(intervals):
    merged = []
    for start, end in sorted(intervals):
        if end <= start:
            continue
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return merged


def length(intervals):
    return sum(end - start for start, end in union(intervals))


def classify_marker(name):
    match = PHASE_MARKER.search(name)
    if not match:
        return None
    new, cached = map(int, match.groups())
    if new > 0 and cached == 0:
        return "prefill"
    if new > 0 and cached > 0:
        return "mixed"
    if new == 0 and cached > 0:
        return "decode"
    return "unknown"


def is_collective(name):
    lowered = name.lower()
    return "allreduce" in lowered or "all_reduce" in lowered


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")

    with gzip.open(args.trace, "rt", encoding="utf-8") as stream:
        payload = json.load(stream)
    events = payload.get("traceEvents", [])
    categories = collections.Counter(
        event.get("cat", "") for event in events if event.get("ph") == "X"
    )
    markers = []
    for event in events:
        if event.get("ph") != "X" or event.get("cat") != "gpu_user_annotation":
            continue
        phase = classify_marker(event.get("name", ""))
        if phase is not None:
            markers.append(
                {
                    "phase": phase,
                    "name": event["name"],
                    "start": float(event["ts"]),
                    "end": float(event["ts"] + event.get("dur", 0)),
                }
            )

    device = []
    for event in events:
        if event.get("ph") != "X" or "dur" not in event:
            continue
        category = event.get("cat", "")
        event_args = event.get("args") or {}
        has_device_identity = any(
            key in event_args for key in ("device", "stream", "context")
        )
        if category not in ("kernel", "gpu_memcpy", "gpu_memset") and not has_device_identity:
            continue
        start = float(event["ts"])
        end = start + float(event["dur"])
        device.append(
            {
                "start": start,
                "end": end,
                "name": event.get("name", ""),
                "category": category,
                "stream": event_args.get("stream"),
                "midpoint": (start + end) / 2,
            }
        )
    device.sort(key=lambda event: event["midpoint"])
    device_midpoints = [event["midpoint"] for event in device]

    aggregate = {
        phase: {
            "marker_count": 0,
            "marker_duration_us": 0.0,
            "collective_activity_us": 0.0,
            "collective_union_us": 0.0,
            "noncollective_union_us": 0.0,
            "all_device_union_us": 0.0,
            "exposed_collective_union_us": 0.0,
            "collective_event_count": 0,
            "collective_streams": set(),
        }
        for phase in ("prefill", "mixed", "decode", "unknown")
    }
    for marker in markers:
        phase = marker["phase"]
        current = aggregate[phase]
        current["marker_count"] += 1
        current["marker_duration_us"] += marker["end"] - marker["start"]
        collective = []
        noncollective = []
        first = bisect.bisect_left(device_midpoints, marker["start"])
        last = bisect.bisect_right(device_midpoints, marker["end"])
        for event in device[first:last]:
            clipped = (
                max(marker["start"], event["start"]),
                min(marker["end"], event["end"]),
            )
            if is_collective(event["name"]):
                collective.append(clipped)
                current["collective_activity_us"] += clipped[1] - clipped[0]
                current["collective_event_count"] += 1
                if event["stream"] is not None:
                    current["collective_streams"].add(str(event["stream"]))
            else:
                noncollective.append(clipped)
        collective_union = length(collective)
        noncollective_union = length(noncollective)
        all_union = length(collective + noncollective)
        current["collective_union_us"] += collective_union
        current["noncollective_union_us"] += noncollective_union
        current["all_device_union_us"] += all_union
        current["exposed_collective_union_us"] += (
            all_union - noncollective_union
        )

    for values in aggregate.values():
        values["collective_streams"] = sorted(values["collective_streams"])
        collective_union = values["collective_union_us"]
        exposed = values["exposed_collective_union_us"]
        values["overlapped_collective_union_us"] = max(
            0.0, collective_union - exposed
        )
        values["exposed_fraction_of_collective_union"] = (
            exposed / collective_union if collective_union else 0.0
        )
        marker_duration = values["marker_duration_us"]
        values["exposed_collective_fraction_of_marker"] = (
            exposed / marker_duration if marker_duration else 0.0
        )

    result = {
        "schema_version": 1,
        "trace": str(args.trace),
        "method": (
            "Within each GPU execute_new/cached marker, compute interval unions for "
            "collective and non-collective device events. Exposed collective time is "
            "union(all device events) minus union(non-collective events)."
        ),
        "event_count": len(events),
        "complete_event_categories": categories.most_common(),
        "device_event_count": len(device),
        "marker_count": len(markers),
        "phases": aggregate,
        "limitations": [
            "Interval-union attribution is a critical-path upper-bound proxy, not a dependency DAG.",
            "Events are assigned by midpoint to the enclosing GPU phase marker.",
            "Only rank0 is deeply analyzed; cross-rank balance comes from the existing sampled report.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
