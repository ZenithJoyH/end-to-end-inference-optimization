#!/usr/bin/env python3
"""Compare the same bounded Indexer profile before and after body optimizations."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


CASE_ROOT = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
OLD_ID = "p4k-d16-c16-n16-full-prefix-hit-profile-20260919-11"
NEW_ID = "p4k-d16-c16-n16-indexer-body-reprofile-20260919-12"
TARGET_NAMES = {
    "aten::ge",
    "aten::bitwise_not",
    "aten::add_",
    "aten::masked_fill_",
    "aten::index_select",
    "aten::contiguous",
    "aten::clone",
    "aten::sub",
    "aten::empty",
    "aten::empty_like",
    "aten::bmm",
    "aten::sum",
    "aten::topk",
}


def load(profile_id: str, name: str) -> dict:
    path = CASE_ROOT / "results/profiling" / profile_id / name
    return json.loads(path.read_text())


def cpu_name_totals(report: dict) -> dict[tuple[str, str], dict]:
    totals: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"count": 0, "total_us": 0.0}
    )
    for row in report["cpu_signatures"]:
        if row["name"] not in TARGET_NAMES:
            continue
        item = totals[(row["phase"], row["name"])]
        item["count"] += row["count"]
        item["total_us"] += row["total_us"]
    return totals


def selected_signatures(report: dict) -> list[dict]:
    rows = []
    for row in report["cpu_signatures"]:
        dims = row.get("input_dims")
        if row["name"] in TARGET_NAMES and (
            dims in ([[128, 2048]], [[424960, 128]], [[128, 424960]])
            or row["name"] in {"aten::index_select", "aten::contiguous", "aten::clone"}
        ):
            rows.append(row)
    return rows


def main() -> None:
    old_breakdown = load(OLD_ID, "indexer-breakdown-rank0.json")
    new_breakdown = load(NEW_ID, "indexer-breakdown-rank0.json")
    old_shapes = load(OLD_ID, "indexer-body-shapes-rank0.json")
    new_shapes = load(NEW_ID, "indexer-body-shapes-rank0.json")
    comparison = {
        "profiles": {"baseline": OLD_ID, "candidate": NEW_ID},
        "indexer_breakdown": {},
        "cpu_name_totals": {},
        "selected_signatures": {
            "baseline": selected_signatures(old_shapes),
            "candidate": selected_signatures(new_shapes),
        },
    }
    for phase in ("prefill", "mixed", "decode"):
        old = old_breakdown["phases"][phase]
        new = new_breakdown["phases"][phase]
        metrics = {}
        for key in (
            "indexer_calls",
            "indexer_total_us",
            "copy_conversion_wrapper_only_us",
            "memcpy_api_wait_us",
            "explicit_sync_us",
            "indexer_body_excluding_copy_sync_us",
            "device_kernel_total_us_inside_indexer_wall",
            "device_copy_total_us_inside_indexer_wall",
        ):
            old_value = old[key]
            new_value = new[key]
            metrics[key] = {
                "baseline": old_value,
                "candidate": new_value,
                "delta": new_value - old_value,
                "candidate_over_baseline": (
                    new_value / old_value if old_value else None
                ),
            }
        comparison["indexer_breakdown"][phase] = metrics

    old_totals = cpu_name_totals(old_shapes)
    new_totals = cpu_name_totals(new_shapes)
    for key in sorted(set(old_totals) | set(new_totals)):
        old = old_totals.get(key, {"count": 0, "total_us": 0.0})
        new = new_totals.get(key, {"count": 0, "total_us": 0.0})
        comparison["cpu_name_totals"]["/".join(key)] = {
            "baseline": old,
            "candidate": new,
            "delta_total_us": new["total_us"] - old["total_us"],
        }

    output = (
        CASE_ROOT
        / "results/profiling"
        / NEW_ID
        / "indexer-body-before-after-comparison.json"
    )
    if output.exists():
        raise SystemExit(f"output exists: {output}")
    output.write_text(json.dumps(comparison, indent=2) + "\n")
    print(json.dumps(comparison, indent=2))


if __name__ == "__main__":
    main()
