#!/usr/bin/env python3
"""Summarize Hy4 W8A8 linear shapes and scaled-mm launch signatures from a trace."""

from __future__ import annotations

import argparse
import collections
import gzip
import json
from pathlib import Path
from typing import Any


def freeze(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    opener = gzip.open if args.trace.suffix == ".gz" else open
    with opener(args.trace, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)

    events = payload.get("traceEvents", payload)
    linear_shapes: dict[str, dict[str, Any]] = {}
    kernel_launches: dict[str, dict[str, Any]] = {}
    samples: dict[str, Any] = {}

    for event in events:
        name = event.get("name")
        event_args = event.get("args") or {}
        duration = float(event.get("dur") or 0.0)
        if name == "vllm::fl_w8a8_dynamic_per_token_linear":
            signature_payload = {
                "input_dims": event_args.get("Input Dims"),
                "input_strides": event_args.get("Input Strides"),
                "input_type": event_args.get("Input type"),
            }
            signature = freeze(signature_payload)
            row = linear_shapes.setdefault(
                signature,
                {**signature_payload, "count": 0, "total_us": 0.0},
            )
            row["count"] += 1
            row["total_us"] += duration
            samples.setdefault(name, event_args)
        elif name == "scaled_mm_kernel":
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
            row["count"] += 1
            row["total_us"] += duration
            samples.setdefault(name, event_args)

    def ordered(rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        result = list(rows.values())
        for row in result:
            row["average_us"] = row["total_us"] / row["count"]
        return sorted(result, key=lambda row: (-row["total_us"], -row["count"]))

    report = {
        "schema_version": 1,
        "trace": str(args.trace),
        "linear_shape_count": len(linear_shapes),
        "linear_shapes": ordered(linear_shapes),
        "scaled_mm_launch_signature_count": len(kernel_launches),
        "scaled_mm_launch_signatures": ordered(kernel_launches),
        "sample_args": samples,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
