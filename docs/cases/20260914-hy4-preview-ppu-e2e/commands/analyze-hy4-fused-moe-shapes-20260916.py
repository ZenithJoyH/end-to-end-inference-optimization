#!/usr/bin/env python3
"""Extract fused-MoE CPU tensor shapes and kernel launch signatures."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
from typing import Any


def freeze(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    opener = gzip.open if args.trace.suffix == ".gz" else open
    with opener(args.trace, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)

    events = payload.get("traceEvents", payload)
    cpu_events: dict[str, dict[str, Any]] = {}
    kernel_launches: dict[str, dict[str, Any]] = {}
    for event in events:
        name = str(event.get("name") or "")
        if "moe" not in name.lower():
            continue
        event_args = event.get("args") or {}
        duration = float(event.get("dur") or 0.0)
        if name == "fused_moe_kernel":
            signature_payload = {
                key: event_args.get(key)
                for key in sorted(event_args)
                if key.lower()
                in {
                    "grid",
                    "block",
                    "blocks per sm",
                    "registers per thread",
                    "shared memory",
                }
            }
            signature = freeze(signature_payload)
            row = kernel_launches.setdefault(
                signature,
                {**signature_payload, "count": 0, "total_us": 0.0},
            )
        else:
            shape_payload = {
                "name": name,
                "category": event.get("cat"),
                "input_dims": event_args.get("Input Dims"),
                "input_strides": event_args.get("Input Strides"),
                "input_type": event_args.get("Input type"),
            }
            signature = freeze(shape_payload)
            row = cpu_events.setdefault(
                signature,
                {
                    **shape_payload,
                    "sample_args": event_args,
                    "count": 0,
                    "total_us": 0.0,
                },
            )
        row["count"] += 1
        row["total_us"] += duration

    def ordered(rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        result = list(rows.values())
        for row in result:
            row["average_us"] = row["total_us"] / row["count"]
        return sorted(result, key=lambda row: (-row["total_us"], -row["count"]))

    report = {
        "schema_version": 1,
        "trace": str(args.trace),
        "cpu_event_signatures": ordered(cpu_events),
        "kernel_launch_signatures": ordered(kernel_launches),
    }
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
