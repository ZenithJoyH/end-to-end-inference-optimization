#!/usr/bin/env python3
"""Validate prof006a event-only vs event+host-ring evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control-diagnostic", required=True, type=Path)
    parser.add_argument("--event-probe", required=True, type=Path)
    parser.add_argument("--event-diagnostic", required=True, type=Path)
    parser.add_argument("--event-host-probe", required=True, type=Path)
    parser.add_argument("--event-host-diagnostic", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def load_one(root: Path, pattern: str) -> dict[str, Any]:
    paths = sorted(root.glob(pattern))
    if len(paths) != 1:
        raise ValueError(f"expected one {pattern} under {root}, got {len(paths)}")
    return json.loads(paths[0].read_text(encoding="utf-8"))


def load_workers(root: Path, arm: str) -> list[dict[str, Any]]:
    workers = [load_one(root, f"worker-rank{rank}-pid*.result.json") for rank in range(8)]
    for rank, worker in enumerate(workers):
        if worker.get("schema") != "prof006a-worker-v1":
            raise ValueError(f"rank{rank} schema mismatch")
        if worker.get("rank") != rank or worker.get("arm") != arm:
            raise ValueError(f"rank{rank} identity/arm mismatch")
        if worker.get("dropped") != 0:
            raise ValueError(f"rank{rank} ring overflow")
    counts = {worker.get("count") for worker in workers}
    if len(counts) != 1 or not counts or next(iter(counts)) <= 0:
        raise ValueError(f"worker count mismatch: {counts}")
    for worker in workers:
        if len(worker.get("rows", [])) != worker.get("count"):
            raise ValueError(f"{worker.get('role')} rows/count mismatch")
        if [row.get("step") for row in worker["rows"]] != list(
            range(worker["count"])
        ):
            raise ValueError(f"{worker.get('role')} non-contiguous steps")
    tags = [
        [
            (row["num_new"], row["num_cached"], row["total_tokens"])
            for row in worker["rows"]
        ]
        for worker in workers
    ]
    if any(value != tags[0] for value in tags[1:]):
        raise ValueError("TP rank step tags are not identical")
    return workers


def load_engine(root: Path, expected_tags: list[tuple[int, int, int]]) -> dict[str, Any]:
    engine = load_one(root, "engine-pid*.result.json")
    if engine.get("schema") != "prof006a-engine-v1" or engine.get("arm") != "event_host":
        raise ValueError("event_host engine schema/arm mismatch")
    if engine.get("dropped") != 0 or engine.get("count") != len(engine.get("rows", [])):
        raise ValueError("engine ring count/overflow mismatch")
    if [row.get("step") for row in engine["rows"]] != list(range(engine["count"])):
        raise ValueError("engine non-contiguous steps")
    active_rows = [row for row in engine["rows"] if row["total_tokens"] > 0]
    empty_rows = [row for row in engine["rows"] if row["total_tokens"] == 0]
    if any(row["num_new"] != 0 or row["num_cached"] != 0 for row in empty_rows):
        raise ValueError("zero-token engine row carried requests")
    tags = [
        (row["num_new"], row["num_cached"], row["total_tokens"])
        for row in active_rows
    ]
    if tags != expected_tags:
        raise ValueError("engine/worker step tags do not align")
    for row in engine["rows"]:
        if not (
            row["schedule_start_ns"] <= row["schedule_end_ns"]
            <= row["dispatch_start_ns"] <= row["dispatch_return_ns"]
        ):
            raise ValueError(f"invalid engine timestamp order at step {row['step']}")
    engine["active_rows"] = active_rows
    engine["empty_schedule_rows"] = len(empty_rows)
    return engine


def measured_rows(path: Path) -> list[dict[str, Any]]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("status") != "complete" or report.get("errors"):
        raise ValueError(f"invalid diagnostic: {path}")
    values = []
    for row in report.get("rounds", []):
        if row.get("phase") != "measured" or not row.get("valid"):
            continue
        metrics = row.get("metrics", {})
        if row.get("case") != [4096, 128, 64, 64]:
            raise ValueError(f"workload drift in {path}")
        expected = {
            "successful_requests": 64,
            "total_input_tokens": 4096 * 64,
            "total_output_tokens": 128 * 64,
        }
        if any(metrics.get(key) != value for key, value in expected.items()):
            raise ValueError(f"request/token evidence drift in {path}")
        value = metrics.get("benchmark_duration")
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(f"missing benchmark_duration in {path}")
        values.append({"wall_s": float(value), "signature": expected})
    if len(values) != 3:
        raise ValueError(f"expected three measured walls in {path}, got {len(values)}")
    return values


def mad_ratio(values: list[float]) -> float:
    center = median(values)
    return median(abs(value - center) for value in values) / center


def round_ranges(tags: list[tuple[int, int, int]]) -> list[tuple[int, int]]:
    starts = [index for index, tag in enumerate(tags) if tag[0] > 0 and tag[1] == 0]
    if len(starts) != 3 or starts[0] != 0:
        raise ValueError(f"expected three pure-prefill round starts, got {starts}")
    return [(start, starts[i + 1] if i + 1 < len(starts) else len(tags)) for i, start in enumerate(starts)]


def summarize_arm(
    workers: list[dict[str, Any]], walls: list[float], host: bool
) -> list[dict[str, Any]]:
    rows = [worker["rows"] for worker in workers]
    tags = [
        (row["num_new"], row["num_cached"], row["total_tokens"])
        for row in rows[0]
    ]
    summaries = []
    for round_index, (start, end) in enumerate(round_ranges(tags)):
        mixed_steps = [
            step for step in range(start, end)
            if tags[step][0] > 0 and tags[step][1] > 0
        ]
        if len(mixed_steps) != 63:
            raise ValueError(
                f"round{round_index + 1} expected 63 Mixed steps, got {len(mixed_steps)}"
            )
        common_idle = 0.0
        causal_preprocess = 0.0
        causal_steps = 0
        for step in mixed_steps:
            idle = min(float(rank_rows[step]["inter_graph_idle_us"]) for rank_rows in rows)
            if idle < 0:
                raise ValueError(f"negative device idle at step {step}")
            common_idle += idle
            if host:
                complete = all(
                    rank_rows[step]["previous_graph_complete_at_entry"]
                    for rank_rows in rows
                )
                if complete:
                    prep = min(
                        max(
                            0.0,
                            (
                                float(rank_rows[step]["graph_enqueue_ns"])
                                - float(rank_rows[step]["worker_entry_ns"])
                            )
                            / 1000.0,
                        )
                        for rank_rows in rows
                    )
                    causal_preprocess += min(idle, prep)
                    causal_steps += 1
        summaries.append(
            {
                "round": round_index + 1,
                "wall_s": walls[round_index],
                "mixed_steps": len(mixed_steps),
                "common_device_idle_us": common_idle,
                "common_device_idle_fraction": common_idle / (walls[round_index] * 1e6),
                "causal_plugin_preprocess_us": causal_preprocess if host else None,
                "causal_plugin_preprocess_fraction": (
                    causal_preprocess / (walls[round_index] * 1e6) if host else None
                ),
                "causal_steps": causal_steps if host else None,
            }
        )
    return summaries


def main() -> int:
    args = parse_args()
    event_workers = load_workers(args.event_probe, "event")
    host_workers = load_workers(args.event_host_probe, "event_host")
    host_tags = [
        (row["num_new"], row["num_cached"], row["total_tokens"])
        for row in host_workers[0]["rows"]
    ]
    host_engine = load_engine(args.event_host_probe, host_tags)
    control_measured = measured_rows(args.control_diagnostic)
    event_measured = measured_rows(args.event_diagnostic)
    host_measured = measured_rows(args.event_host_diagnostic)
    control_walls = [row["wall_s"] for row in control_measured]
    event_walls = [row["wall_s"] for row in event_measured]
    host_walls = [row["wall_s"] for row in host_measured]
    event_tags = [
        (row["num_new"], row["num_cached"], row["total_tokens"])
        for row in event_workers[0]["rows"]
    ]
    if host_tags != event_tags:
        raise ValueError("event/event_host step tags do not align")
    event_rows = summarize_arm(event_workers, event_walls, host=False)
    host_rows = summarize_arm(host_workers, host_walls, host=True)

    event_overhead = median(event_walls) / median(control_walls) - 1.0
    host_overhead = median(host_walls) / median(event_walls) - 1.0
    event_idle_fraction = median(row["common_device_idle_fraction"] for row in event_rows)
    causal_fraction = median(row["causal_plugin_preprocess_fraction"] for row in host_rows)
    mixed_engine_rows = [
        row for row in host_engine["active_rows"]
        if row["num_new"] > 0 and row["num_cached"] > 0
    ]
    schedule_us = [
        (row["schedule_end_ns"] - row["schedule_start_ns"]) / 1000.0
        for row in mixed_engine_rows
    ]
    dispatch_us = [
        (row["dispatch_return_ns"] - row["dispatch_start_ns"]) / 1000.0
        for row in mixed_engine_rows
    ]
    checks = {
        "three_valid_rounds_each_arm": (
            len(control_walls) == len(event_rows) == len(host_rows) == 3
        ),
        "event_wall_abs_overhead_le_0_5pct": abs(event_overhead) <= 0.005,
        "host_ring_wall_abs_overhead_le_0_5pct": abs(host_overhead) <= 0.005,
        "all_arm_wall_mad_over_median_le_3pct": all(
            mad_ratio(values) <= 0.03
            for values in (control_walls, event_walls, host_walls)
        ),
        "event_only_common_idle_strictly_gt_1pct": event_idle_fraction > 0.01,
        "causal_plugin_preprocess_strictly_gt_1pct": causal_fraction > 0.01,
        "all_host_rounds_have_causal_steps": all(row["causal_steps"] > 0 for row in host_rows),
    }
    passed = all(checks.values())
    result = {
        "schema": "prof006a-analysis-v1",
        "status": "passed_unlock_fw012" if passed else "no_go_or_inconclusive",
        "checks": checks,
        "event_only_rounds": event_rows,
        "event_host_rounds": host_rows,
        "medians": {
            "control_wall_s": median(control_walls),
            "event_wall_s": median(event_walls),
            "event_host_wall_s": median(host_walls),
            "event_wall_overhead_vs_control_fraction": event_overhead,
            "event_host_wall_overhead_vs_event_fraction": host_overhead,
            "control_wall_mad_over_median": mad_ratio(control_walls),
            "event_wall_mad_over_median": mad_ratio(event_walls),
            "event_host_wall_mad_over_median": mad_ratio(host_walls),
            "event_only_common_idle_fraction": event_idle_fraction,
            "causal_plugin_preprocess_fraction": causal_fraction,
            "context_only_mixed_schedule_us": median(schedule_us),
            "context_only_mixed_dispatch_return_us": median(dispatch_us),
            "context_only_empty_schedule_rows": host_engine["empty_schedule_rows"],
        },
        "boundary": (
            "Only worker-entry to graph-enqueue is causal: every counted step proved "
            "the previous device graph complete via Event.query on all TP ranks. "
            "Schedule/dispatch timestamps are contextual and are not counted as causal gain."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())
