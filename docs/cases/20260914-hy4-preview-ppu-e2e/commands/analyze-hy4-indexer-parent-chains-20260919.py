#!/usr/bin/env python3
"""Attribute selected Indexer CPU ops to their immediate parent chains."""

from __future__ import annotations

import argparse
import gzip
import json
from collections import defaultdict
from pathlib import Path

import ijson


INDEXER = "vllm::hyv4_bf16_sparse_attn_indexer"
TARGETS = {
    "aten::contiguous",
    "aten::clone",
    "aten::sub",
    "aten::empty_like",
    "aten::empty",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")

    stacks = defaultdict(list)
    rows = {}
    with gzip.open(args.trace, "rb") as stream:
        for event in ijson.items(stream, "traceEvents.item"):
            if event.get("ph") != "X":
                continue
            ts = float(event.get("ts") or 0.0)
            duration = float(event.get("dur") or 0.0)
            end = ts + duration
            key = (event.get("pid"), event.get("tid"))
            stack = stacks[key]
            while stack and stack[-1][0] <= ts:
                stack.pop()
            name = str(event.get("name") or "")
            in_indexer = any(item[1] == INDEXER for item in stack)
            if in_indexer and name in TARGETS:
                event_args = event.get("args") or {}
                input_dims = event_args.get("Input Dims")
                chain = [item[1] for item in stack[-4:]]
                signature = json.dumps(
                    {
                        "name": name,
                        "input_dims": input_dims,
                        "parent_chain": chain,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                row = rows.setdefault(
                    signature,
                    {
                        "name": name,
                        "input_dims": input_dims,
                        "parent_chain": chain,
                        "count": 0,
                        "total_us": 0.0,
                    },
                )
                row["count"] += 1
                row["total_us"] += duration
            if duration > 0:
                stack.append((end, name))

    ordered = sorted(
        rows.values(), key=lambda row: (-row["total_us"], -row["count"])
    )
    report = {"trace": str(args.trace), "rows": ordered}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    for row in ordered[:80]:
        print(json.dumps(row, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
