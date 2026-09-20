#!/usr/bin/env python3
"""Stream Indexer-contained CPU shapes and device kernels from a large trace."""

from __future__ import annotations

import argparse
import bisect
import gzip
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import ijson


INDEXER = "vllm::hyv4_bf16_sparse_attn_indexer"
PHASE_RE = re.compile(r"execute_new_(\d+)_cached_(\d+)")


def events(path: Path):
    with gzip.open(path, "rb") as stream:
        yield from ijson.items(stream, "traceEvents.item")


def phase_of(name: str) -> str | None:
    match = PHASE_RE.search(name)
    if not match:
        return None
    new, cached = map(int, match.groups())
    if new > 0 and cached == 0:
        return "prefill"
    if new > 0 and cached > 0:
        return "mixed"
    if new == 0 and cached > 0:
        return "decode"
    return "other"


def freeze(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")

    indexer_intervals: dict[tuple[Any, Any], list[tuple[float, float]]] = defaultdict(list)
    phase_intervals: dict[tuple[Any, Any], list[tuple[float, float, str]]] = defaultdict(list)
    for event in events(args.trace):
        if event.get("ph") != "X":
            continue
        name = str(event.get("name") or "")
        ts = float(event.get("ts") or 0.0)
        end = ts + float(event.get("dur") or 0.0)
        key = (event.get("pid"), event.get("tid"))
        if name == INDEXER:
            indexer_intervals[key].append((ts, end))
        phase = phase_of(name)
        if phase is not None:
            phase_intervals[key].append((ts, end, phase))

    indexer_starts = {}
    phase_starts = {}
    for key, rows in indexer_intervals.items():
        rows.sort()
        indexer_starts[key] = [row[0] for row in rows]
    for key, rows in phase_intervals.items():
        rows.sort()
        phase_starts[key] = [row[0] for row in rows]

    def inside_indexer(key, ts, end):
        rows = indexer_intervals.get(key, ())
        starts = indexer_starts.get(key, ())
        pos = bisect.bisect_right(starts, ts) - 1
        return pos >= 0 and end <= rows[pos][1]

    def containing_phase(key, ts, end):
        rows = phase_intervals.get(key, ())
        starts = phase_starts.get(key, ())
        pos = bisect.bisect_right(starts, ts) - 1
        if pos >= 0 and end <= rows[pos][1]:
            return rows[pos][2]
        return "unclassified"

    cpu_rows: dict[str, dict[str, Any]] = {}
    device_rows: dict[str, dict[str, Any]] = {}
    for event in events(args.trace):
        if event.get("ph") != "X":
            continue
        name = str(event.get("name") or "")
        if name == INDEXER or phase_of(name) is not None:
            continue
        ts = float(event.get("ts") or 0.0)
        duration = float(event.get("dur") or 0.0)
        end = ts + duration
        key = (event.get("pid"), event.get("tid"))
        if not inside_indexer(key, ts, end):
            continue
        phase = containing_phase(key, ts, end)
        event_args = event.get("args") or {}
        input_dims = event_args.get("Input Dims")
        if input_dims is not None:
            payload = {
                "phase": phase,
                "name": name,
                "category": event.get("cat"),
                "input_dims": input_dims,
                "input_strides": event_args.get("Input Strides"),
                "input_type": event_args.get("Input type"),
            }
            signature = freeze(payload)
            row = cpu_rows.setdefault(signature, {**payload, "count": 0, "total_us": 0.0})
        else:
            payload = {"phase": phase, "name": name, "category": event.get("cat")}
            signature = freeze(payload)
            row = device_rows.setdefault(signature, {**payload, "count": 0, "total_us": 0.0})
        row["count"] += 1
        row["total_us"] += duration

    def ordered(rows):
        values = list(rows.values())
        for row in values:
            row["average_us"] = row["total_us"] / row["count"]
        return sorted(values, key=lambda row: (-row["total_us"], -row["count"], row["name"]))

    report = {
        "schema_version": 1,
        "trace": str(args.trace),
        "indexer_intervals": sum(len(rows) for rows in indexer_intervals.values()),
        "cpu_signatures": ordered(cpu_rows),
        "device_signatures": ordered(device_rows),
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
