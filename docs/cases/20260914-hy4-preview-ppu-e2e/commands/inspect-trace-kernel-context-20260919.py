#!/usr/bin/env python3
"""Resolve representative device kernels back to nearby CPU/runtime trace events."""

from __future__ import annotations

import argparse
import gzip
import json
from collections import defaultdict
from pathlib import Path

import ijson


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--kernel", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--samples", type=int, default=2)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")

    targets = []
    with gzip.open(args.trace, "rb") as stream:
        for event in ijson.items(stream, "traceEvents.item"):
            if event.get("ph") != "X" or event.get("name") != args.kernel:
                continue
            targets.append(
                {
                    "ts": float(event.get("ts") or 0.0),
                    "dur": float(event.get("dur") or 0.0),
                    "external_id": (event.get("args") or {}).get("External id"),
                    "correlation": (event.get("args") or {}).get("correlation"),
                    "args": event.get("args") or {},
                }
            )
            if len(targets) >= args.samples:
                break

    external_ids = {row["external_id"] for row in targets if row["external_id"] is not None}
    correlations = {row["correlation"] for row in targets if row["correlation"] is not None}
    # Device kernels usually only carry a correlation id. Resolve the matching
    # runtime/driver launch first, then use its External id to find the owning
    # CPU op or graph annotation.
    with gzip.open(args.trace, "rb") as stream:
        for event in ijson.items(stream, "traceEvents.item"):
            event_args = event.get("args") or {}
            if event_args.get("correlation") not in correlations:
                continue
            event_external_id = event_args.get("External id")
            if event_external_id is not None:
                external_ids.add(event_external_id)
    related = defaultdict(list)
    nearby = defaultdict(list)
    with gzip.open(args.trace, "rb") as stream:
        for event in ijson.items(stream, "traceEvents.item"):
            event_args = event.get("args") or {}
            event_external_id = event_args.get("External id")
            event_correlation = event_args.get("correlation")
            for index, target in enumerate(targets):
                if (
                    event_external_id in external_ids
                    or event_correlation in correlations
                ):
                    related[index].append(event)
                event_ts = float(event.get("ts") or 0.0)
                if abs(event_ts - target["ts"]) <= 1000.0:
                    nearby[index].append(event)

    def compact(event: dict) -> dict:
        event_args = event.get("args") or {}
        return {
            "name": event.get("name"),
            "cat": event.get("cat"),
            "ph": event.get("ph"),
            "ts": event.get("ts"),
            "dur": event.get("dur"),
            "pid": event.get("pid"),
            "tid": event.get("tid"),
            "args": event_args,
        }

    report = {
        "trace": str(args.trace),
        "kernel": args.kernel,
        "samples": [
            {
                "target": target,
                "related": [compact(event) for event in related[index]],
                "nearby": [compact(event) for event in nearby[index]][:200],
            }
            for index, target in enumerate(targets)
        ],
    }
    args.output.write_text(json.dumps(report, indent=2, default=str) + "\n")
    print(json.dumps({
        "output": str(args.output),
        "sample_count": len(targets),
        "related_counts": {str(k): len(v) for k, v in related.items()},
        "nearby_counts": {str(k): len(v) for k, v in nearby.items()},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
