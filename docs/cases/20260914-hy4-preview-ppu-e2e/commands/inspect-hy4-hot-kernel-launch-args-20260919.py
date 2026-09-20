#!/usr/bin/env python3
"""Inspect launch metadata for the current dominant device kernels."""

from __future__ import annotations

import argparse
import gzip
import json
from collections import defaultdict
from pathlib import Path

import ijson


TARGETS = {
    "triton_flash_mla_sparse_fwd",
    "_flash_mla_sparse_full_prefix_grouped",
    "fused_moe_kernel",
    "scaled_mm_kernel",
    "_moe_sum_general_kernel",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")

    rows: dict[str, dict[str, dict]] = defaultdict(dict)
    with gzip.open(args.trace, "rb") as stream:
        for event in ijson.items(stream, "traceEvents.item"):
            if event.get("ph") != "X":
                continue
            name = str(event.get("name") or "")
            if name not in TARGETS:
                continue
            event_args = event.get("args") or {}
            signature_payload = {
                key: event_args.get(key)
                for key in sorted(event_args)
                if key not in {"External id", "correlation", "stream"}
            }
            signature = json.dumps(
                signature_payload, sort_keys=True, default=str, separators=(",", ":")
            )
            row = rows[name].setdefault(
                signature,
                {
                    "args": signature_payload,
                    "count": 0,
                    "total_us": 0.0,
                    "min_us": None,
                    "max_us": None,
                },
            )
            duration = float(event.get("dur") or 0.0)
            row["count"] += 1
            row["total_us"] += duration
            row["min_us"] = duration if row["min_us"] is None else min(row["min_us"], duration)
            row["max_us"] = duration if row["max_us"] is None else max(row["max_us"], duration)

    output = {}
    for name, signatures in rows.items():
        ordered = sorted(
            signatures.values(), key=lambda row: (-row["total_us"], -row["count"])
        )
        for row in ordered:
            row["average_us"] = row["total_us"] / row["count"]
        output[name] = ordered
    report = {"trace": str(args.trace), "kernels": output}
    args.output.write_text(json.dumps(report, indent=2, default=str) + "\n")
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
