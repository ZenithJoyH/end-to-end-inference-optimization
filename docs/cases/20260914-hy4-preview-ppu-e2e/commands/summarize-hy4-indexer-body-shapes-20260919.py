#!/usr/bin/env python3
"""Print a compact summary of the Indexer shape-attribution report."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


CPU_NAMES = {
    "aten::masked_fill_",
    "aten::add_",
    "aten::ge",
    "aten::bitwise_not",
    "aten::bmm",
    "aten::topk",
    "aten::sum",
    "aten::empty",
    "aten::empty_like",
    "aten::empty_strided",
    "aten::contiguous",
    "aten::clone",
    "aten::sub",
    "aten::index_select",
    "aten::reshape",
    "aten::view",
}
DEVICE_RE = re.compile(
    r"masked|fill|bitwise|add|top.?k|bmm|gemm|mm_|reduce|index|scatter",
    re.IGNORECASE,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())

    print(f"indexer_intervals={report['indexer_intervals']}")
    selected_cpu = [
        row for row in report["cpu_signatures"] if row["name"] in CPU_NAMES
    ]
    totals = {}
    for row in selected_cpu:
        key = (row["phase"], row["name"])
        total = totals.setdefault(key, {"count": 0, "total_us": 0.0})
        total["count"] += row["count"]
        total["total_us"] += row["total_us"]
    print("CPU_NAME_TOTALS")
    for (phase, name), total in sorted(
        totals.items(), key=lambda item: -item[1]["total_us"]
    ):
        print(
            json.dumps(
                {"phase": phase, "name": name, **total},
                ensure_ascii=False,
                sort_keys=True,
            )
        )

    print("CPU_TOP_SIGNATURES")
    emitted = {}
    for row in selected_cpu:
        key = (row["phase"], row["name"])
        if emitted.get(key, 0) >= 3:
            continue
        emitted[key] = emitted.get(key, 0) + 1
        print(json.dumps(row, ensure_ascii=False, sort_keys=True))

    print("DEVICE_SIGNATURES")
    matched = [
        row for row in report["device_signatures"] if DEVICE_RE.search(row["name"])
    ]
    for row in matched[:80]:
        print(json.dumps(row, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
