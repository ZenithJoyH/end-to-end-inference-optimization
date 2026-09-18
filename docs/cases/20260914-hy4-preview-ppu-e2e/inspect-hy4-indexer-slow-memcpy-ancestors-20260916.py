#!/usr/bin/env python3
"""Find CPU ancestor chains for long cudaMemcpyAsync calls inside Hy4 Indexer."""

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


def main(trace_path, output_path, threshold_us=50_000.0):
    indexers = []
    phase_markers = []
    targets = []
    with gzip.open(trace_path, "rb") as stream:
        for event in ijson.items(stream, "traceEvents.item"):
            if event.get("ph") != "X":
                continue
            name = str(event.get("name", ""))
            start, end = interval(event)
            if name == INDEXER_NAME:
                indexers.append({
                    "start": start,
                    "end": end,
                    "pid": event.get("pid"),
                    "tid": event.get("tid"),
                })
            phase = phase_from_name(name)
            if phase and event.get("cat") == "user_annotation":
                phase_markers.append({
                    "start": start,
                    "end": end,
                    "pid": event.get("pid"),
                    "tid": event.get("tid"),
                    "phase": phase,
                    "name": name,
                })
            if name == "cudaMemcpyAsync" and end - start >= threshold_us:
                targets.append({
                    "start": start,
                    "end": end,
                    "duration_us": end - start,
                    "pid": event.get("pid"),
                    "tid": event.get("tid"),
                    "args": event.get("args") or {},
                    "ancestors": [],
                })

    targets = [
        target
        for target in targets
        if any(
            item["pid"] == target["pid"]
            and item["tid"] == target["tid"]
            and item["start"] <= target["start"]
            and target["end"] <= item["end"]
            for item in indexers
        )
    ]

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

    for target in targets:
        containing_marker = next(
            (
                marker
                for marker in phase_markers
                if marker["pid"] == target["pid"]
                and marker["tid"] == target["tid"]
                and marker["start"] <= target["start"]
                and target["end"] <= marker["end"]
            ),
            None,
        )
        target["phase"] = containing_marker["phase"] if containing_marker else "unassigned"
        target["phase_marker"] = containing_marker["name"] if containing_marker else None
        target["ancestors"].sort(key=lambda item: (item["duration_us"], -item["start"]))
        seen = set()
        unique = []
        for item in target["ancestors"]:
            key = (item["name"], item["start"], item["duration_us"])
            if key not in seen:
                seen.add(key)
                unique.append(item)
        target["ancestors"] = unique

    result = {
        "schema_version": 1,
        "trace": trace_path,
        "threshold_us": threshold_us,
        "target_count": len(targets),
        "targets": sorted(targets, key=lambda item: item["duration_us"], reverse=True),
    }
    with open(output_path, "x", encoding="utf-8") as output:
        json.dump(result, output, indent=2)
    print(json.dumps({
        "output": output_path,
        "target_count": len(targets),
        "summary": [
            {
                "phase": target["phase"],
                "duration_us": target["duration_us"],
                "nearest_ancestors": [item["name"] for item in target["ancestors"][:12]],
            }
            for target in sorted(targets, key=lambda item: item["duration_us"], reverse=True)
        ],
    }, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: {sys.argv[0]} TRACE.json.gz OUTPUT.json")
    main(sys.argv[1], sys.argv[2])
