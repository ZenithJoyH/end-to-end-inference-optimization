#!/usr/bin/env python3
import csv
import hashlib
import json
import statistics
import sys
from pathlib import Path


run_root = Path(sys.argv[1]).resolve()
history_path = Path(sys.argv[2]).resolve()
native_root = run_root / "runs" / "candidate-01"
metrics = [
    "duration",
    "request_throughput",
    "output_throughput",
    "total_token_throughput",
    "mean_ttft_ms",
    "median_ttft_ms",
    "p99_ttft_ms",
    "mean_tpot_ms",
    "median_tpot_ms",
    "p99_tpot_ms",
    "mean_itl_ms",
    "median_itl_ms",
    "p99_itl_ms",
    "mean_e2el_ms",
    "median_e2el_ms",
    "p99_e2el_ms",
]

rounds = []
for round_id in (1, 2, 3):
    path = native_root / f"p4096-d1024-c64-n128-r{round_id}.json"
    native = json.loads(path.read_text(encoding="utf-8"))
    row = {name: native.get(name) for name in metrics}
    row.update(
        round=round_id,
        phase="warmup" if round_id == 1 else "measured",
        completed=native.get("completed"),
        failed=native.get("failed"),
        total_input_tokens=native.get("total_input_tokens"),
        total_output_tokens=native.get("total_output_tokens"),
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )
    rounds.append(row)

measured = rounds[1:]
measured_median = {
    name: statistics.median(row[name] for row in measured) for name in metrics
}
measured_relative_spread = {
    name: (
        (max(row[name] for row in measured) - min(row[name] for row in measured))
        / measured_median[name]
    )
    for name in metrics
}

with history_path.open(newline="", encoding="utf-8") as handle:
    history_rows = list(csv.DictReader(handle))
history = next(row for row in history_rows if row["Run"] == "SUMMARY")
history_map = {
    "duration": float(history["Benchmark Duration (s)"]),
    "request_throughput": float(history["Req/s"]),
    "output_throughput": float(history["Output tok/s"]),
    "total_token_throughput": float(history["Total tok/s"]),
    "mean_ttft_ms": float(history["Mean TTFT (ms)"]),
    "median_ttft_ms": float(history["Median TTFT (ms)"]),
    "p99_ttft_ms": float(history["P99 TTFT (ms)"]),
    "mean_tpot_ms": float(history["Mean TPOT (ms)"]),
    "median_tpot_ms": float(history["Median TPOT (ms)"]),
    "p99_tpot_ms": float(history["P99 TPOT (ms)"]),
    "mean_itl_ms": float(history["Mean ITL (ms)"]),
    "median_itl_ms": float(history["Median ITL (ms)"]),
    "p99_itl_ms": float(history["P99 ITL (ms)"]),
}

higher_is_better = {
    "request_throughput", "output_throughput", "total_token_throughput"
}
relative_to_history = {}
for name, old in history_map.items():
    new = measured_median[name]
    relative_to_history[name] = (
        new / old - 1 if name in higher_is_better else old / new - 1
    )

run_record_path = native_root / "run-record.json"
run_record = json.loads(run_record_path.read_text(encoding="utf-8"))
summary = {
    "schema_version": 1,
    "mode": "targeted",
    "scope": "performance_only",
    "scenario_id": "p4096-d1024-c64-n128",
    "stage": "mixed",
    "run_record_status": run_record.get("status"),
    "inputs_verified_before": run_record.get("inputs_verified_before"),
    "inputs_verified_after": run_record.get("inputs_verified_after"),
    "rounds": rounds,
    "measured_median": measured_median,
    "measured_relative_spread": measured_relative_spread,
    "historical_context": {
        "path": str(history_path),
        "summary": history_map,
        "relative_improvement": relative_to_history,
        "comparison_status": "context_only_not_same_plan_baseline_revert",
    },
    "run_record": {
        "path": str(run_record_path),
        "sha256": hashlib.sha256(run_record_path.read_bytes()).hexdigest(),
    },
}
output_path = run_root / "summary.json"
with output_path.open("x", encoding="utf-8") as handle:
    json.dump(summary, handle, ensure_ascii=False, indent=2, allow_nan=False)
    handle.write("\n")
print(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False))

