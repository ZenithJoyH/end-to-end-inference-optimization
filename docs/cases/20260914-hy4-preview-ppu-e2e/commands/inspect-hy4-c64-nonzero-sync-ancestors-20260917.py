#!/usr/bin/env python3
"""Recover CPU ancestor chains for HY4 nonzero/sync and long aten::to events."""

from __future__ import annotations

import collections
import gzip
import json
import re
import sys

import ijson


INDEXER_NAME = "vllm::hyv4_bf16_sparse_attn_indexer"
PHASE_RE = re.compile(r"execute_new_(\d+)_cached_(\d+)")
DEVICE_CATEGORIES = {"kernel", "gpu_memcpy", "gpu_memset"}


def interval(event):
    start = float(event.get("ts") or 0.0)
    return start, start + float(event.get("dur") or 0.0)


def phase_from_name(name):
    match = PHASE_RE.search(name)
    if not match:
        return None
    new_tokens, cached_tokens = map(int, match.groups())
    if new_tokens > 0 and cached_tokens == 0:
        return "prefill"
    if new_tokens > 0 and cached_tokens > 0:
        return "mixed"
    if new_tokens == 0 and cached_tokens > 0:
        return "decode"
    return "unknown"


def main(trace_path, output_path):
    markers = []
    indexers = []
    targets = []
    with gzip.open(trace_path, "rb") as stream:
        for event in ijson.items(stream, "traceEvents.item"):
            if event.get("ph") != "X":
                continue
            name = str(event.get("name", ""))
            start, end = interval(event)
            row = {
                "name": name,
                "start": start,
                "end": end,
                "duration_us": end - start,
                "pid": event.get("pid"),
                "tid": event.get("tid"),
            }
            phase = phase_from_name(name)
            if phase and event.get("cat") == "user_annotation":
                markers.append({**row, "phase": phase})
            if name == INDEXER_NAME:
                indexers.append(row)
            if (
                name in {"aten::nonzero", "cudaStreamSynchronize"}
                or (name == "aten::to" and row["duration_us"] >= 10_000.0)
            ):
                args = event.get("args") or {}
                targets.append({
                    **row,
                    "category": str(event.get("cat", "")),
                    "input_dims": args.get("Input Dims"),
                    "input_type": args.get("Input type"),
                    "ancestors": [],
                })

    with gzip.open(trace_path, "rb") as stream:
        for event in ijson.items(stream, "traceEvents.item"):
            if event.get("ph") != "X" or event.get("cat") in DEVICE_CATEGORIES:
                continue
            start, end = interval(event)
            for target in targets:
                if (
                    event.get("pid") == target["pid"]
                    and event.get("tid") == target["tid"]
                    and start <= target["start"]
                    and target["end"] <= end
                    and not (
                        str(event.get("name", "")) == target["name"]
                        and start == target["start"]
                        and end == target["end"]
                    )
                ):
                    args = event.get("args") or {}
                    target["ancestors"].append({
                        "name": str(event.get("name", "")),
                        "category": str(event.get("cat", "")),
                        "start": start,
                        "duration_us": end - start,
                        "input_dims": args.get("Input Dims"),
                        "input_type": args.get("Input type"),
                    })

    nearest_counter = collections.defaultdict(collections.Counter)
    for target in targets:
        target["phase"] = next((
            marker["phase"] for marker in markers
            if marker["pid"] == target["pid"]
            and marker["tid"] == target["tid"]
            and marker["start"] <= target["start"]
            and target["end"] <= marker["end"]
        ), "unassigned")
        target["inside_indexer"] = any(
            item["pid"] == target["pid"]
            and item["tid"] == target["tid"]
            and item["start"] <= target["start"]
            and target["end"] <= item["end"]
            for item in indexers
        )
        target["ancestors"].sort(key=lambda item: (item["duration_us"], -item["start"]))
        seen = set()
        unique = []
        for item in target["ancestors"]:
            key = (item["name"], item["start"], item["duration_us"])
            if key not in seen:
                seen.add(key)
                unique.append(item)
        target["ancestors"] = unique
        nearest = next((
            item["name"] for item in unique
            if item["name"] not in {"aten::to", "aten::_to_copy", "aten::copy_"}
        ), None)
        nearest_counter[target["name"]][nearest] += 1

    result = {
        "schema_version": 1,
        "trace": trace_path,
        "counts": dict(collections.Counter(item["name"] for item in targets)),
        "nearest_non_copy_ancestor_counts": {
            name: dict(counter.most_common())
            for name, counter in nearest_counter.items()
        },
        "targets": sorted(
            targets,
            key=lambda item: (item["name"], -item["duration_us"]),
        ),
    }
    with open(output_path, "x", encoding="utf-8") as output:
        json.dump(result, output, indent=2)
    print(json.dumps({
        "output": output_path,
        "counts": result["counts"],
        "nearest_non_copy_ancestor_counts": result["nearest_non_copy_ancestor_counts"],
        "longest": [
            {
                "name": item["name"],
                "phase": item["phase"],
                "duration_us": item["duration_us"],
                "inside_indexer": item["inside_indexer"],
                "ancestors": [ancestor["name"] for ancestor in item["ancestors"][:12]],
            }
            for item in sorted(targets, key=lambda item: item["duration_us"], reverse=True)[:30]
        ],
    }, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: {sys.argv[0]} TRACE.json.gz OUTPUT.json")
    main(sys.argv[1], sys.argv[2])
