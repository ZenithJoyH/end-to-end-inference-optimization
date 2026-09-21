#!/usr/bin/env python3
"""Aggregate corrected prof005 phase reports across TP ranks."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import statistics


PHASES = ("prefill_graph", "mixed_graph", "decode_graph", "outside_graph_windows")


def numeric_stats(values: list[float]) -> dict:
    minimum = min(values)
    maximum = max(values)
    return {
        "min": round(minimum, 3),
        "max": round(maximum, 3),
        "mean": round(statistics.fmean(values), 3),
        "median": round(statistics.median(values), 3),
        "max_over_min": round(maximum / minimum, 6) if minimum else None,
        "rank_at_min": values.index(minimum),
        "rank_at_max": values.index(maximum),
        "by_rank": [round(value, 3) for value in values],
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("summary_dir", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)

    completeness_path = args.summary_dir / "phase-completeness.json"
    completeness = json.loads(completeness_path.read_text(encoding="utf-8"))
    if completeness.get("status") != "complete":
        raise SystemExit("corrected phase completeness is not complete")
    reports = []
    inputs = {str(completeness_path): sha256(completeness_path)}
    for rank in range(8):
        path = args.summary_dir / f"phase-rank{rank}.json"
        reports.append(json.loads(path.read_text(encoding="utf-8")))
        inputs[str(path)] = sha256(path)

    phases = {}
    for phase in PHASES:
        coverage = [report.get("device_coverage", {}).get(phase, {}) for report in reports]
        device_total = [float(row.get("total_us", 0)) for row in coverage]
        event_count = [int(row.get("events", 0)) for row in coverage]
        marker_duration = []
        marker_count = []
        sync_total = []
        event_rows = defaultdict(lambda: [{"count": 0, "total_us": 0.0} for _ in range(8)])
        for rank, report in enumerate(reports):
            intervals = [
                row for row in report.get("merged_intervals", []) if row.get("phase") == phase
            ]
            marker_duration.append(sum(float(row["duration_us"]) for row in intervals))
            marker_count.append(len(intervals))
            sync_rows = report.get("stream_synchronize", {}).get(phase, [])
            sync_total.append(sum(float(row.get("total_us", 0)) for row in sync_rows))
            for row in report.get("top_device_events", {}).get(phase, []):
                event_rows[row["name"]][rank] = {
                    "count": int(row["count"]),
                    "total_us": float(row["total_us"]),
                }
        top_events = []
        for name, by_rank in event_rows.items():
            totals = [row["total_us"] for row in by_rank]
            counts = [row["count"] for row in by_rank]
            shares = [
                total / phase_total if phase_total else 0.0
                for total, phase_total in zip(totals, device_total)
            ]
            top_events.append(
                {
                    "name": name,
                    "total_us": numeric_stats(totals),
                    "count": numeric_stats([float(value) for value in counts]),
                    "median_fraction_of_phase_device_sum": round(statistics.median(shares), 6),
                }
            )
        top_events.sort(key=lambda row: row["total_us"]["median"], reverse=True)
        phases[phase] = {
            "device_total_us": numeric_stats(device_total),
            "device_event_count": numeric_stats([float(value) for value in event_count]),
            "marker_wall_duration_us": numeric_stats(marker_duration) if any(marker_duration) else None,
            "marker_count": numeric_stats([float(value) for value in marker_count]) if any(marker_count) else None,
            "cuda_stream_synchronize_total_us": numeric_stats(sync_total),
            "top_device_events_by_median_total_us": top_events[:20],
        }

    names = {
        row["name"]
        for phase in phases.values()
        for row in phase["top_device_events_by_median_total_us"]
    }
    payload = {
        "schema_version": 1,
        "status": "complete",
        "scenario_id": "p4096-d128-c64-n64-post-op010-profile",
        "rank_count": 8,
        "phase_semantics": completeness["phase_boundary_method"],
        "phases": phases,
        "checks": {
            "mm_kernel_general_absent_from_top20_all_phases": "mm_kernel_general" not in names,
            "all_rank_phase_checks_passed": all(
                all(checks.values()) for checks in completeness["rank_checks"].values()
            ),
        },
        "inputs_sha256": inputs,
        "boundary": (
            "Profiler-on cumulative activity may overlap and is not critical-path, utilization, "
            "or no-profiler speedup evidence. Cross-rank differences are diagnostic only."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "checks": payload["checks"]}, indent=2))


if __name__ == "__main__":
    main()
