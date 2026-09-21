#!/usr/bin/env python3
"""Create a compact, workload-correct summary from the P16K profiler outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def compact_events(events: list[dict], limit: int) -> list[dict]:
    keep = (
        "name",
        "count",
        "total_us",
        "average_us",
        "share_of_bucket_summed_duration",
    )
    return [{key: event[key] for key in keep if key in event} for event in events[:limit]]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()

    sampled = json.loads((args.root / "phase-analysis-sampled.json").read_text())
    cpu = json.loads((args.root / "phase-analysis-rank0-cpu.json").read_text())
    indexer = json.loads((args.root / "indexer-breakdown-rank0.json").read_text())
    rank0 = cpu["ranks"][0]

    phases = {}
    for phase in ("prefill", "mixed", "decode"):
        device = sampled["aggregate"][phase]
        host = rank0["phases"][phase]
        phases[phase] = {
            "sampled_marker_counts_by_rank": device["marker_counts_by_rank"],
            "sampled_device_activity_us_by_rank": device[
                "summed_device_activity_us_by_rank"
            ],
            "sampled_cross_rank_relative_spread": device[
                "cross_rank_relative_spread"
            ],
            "top_device_across_sampled_ranks": compact_events(
                device["top_device_across_ranks"], args.top
            ),
            "rank0_cpu_marker_count": host["cpu_marker_count"],
            "rank0_cpu_marker_summed_us": host["cpu_marker_summed_us"],
            "rank0_top_cpu_inclusive": compact_events(
                host["top_cpu_inclusive"], args.top
            ),
            "rank0_indexer": indexer["phases"].get(phase),
        }

    result = {
        "schema_version": 1,
        "profile_id": "p16k-d128-c16-n16-scenario-entry-20260920-02",
        "actual_scenario_id": "p16384-d128-c16-n16",
        "parent_scenario_id": "p16384-d1024-c64-n128",
        "source_metadata_issue": {
            "present": True,
            "detail": (
                "The reused analyzer retains stale P4K scenario labels; workload, "
                "trace paths, service log, and dry-run prove P16384/D128/C16/N16."
            ),
            "raw_sampled_scenario_id": sampled.get("scenario_id"),
            "raw_sampled_parent_scenario_id": sampled.get("parent_scenario_id"),
        },
        "rank_coverage": sampled["rank_coverage"],
        "rank0_unassigned_device_fraction": rank0[
            "unassigned_device_fraction"
        ],
        "phases": phases,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
