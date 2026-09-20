#!/usr/bin/env python3
import hashlib
import json
import statistics
import sys
from pathlib import Path


run_root = Path(sys.argv[1]).resolve()
case_id = "p4096-d128-c64-n64"
metrics = [
    "duration",
    "request_throughput",
    "output_throughput",
    "total_token_throughput",
    "mean_ttft_ms",
    "p99_ttft_ms",
    "mean_tpot_ms",
    "p99_tpot_ms",
    "mean_itl_ms",
    "p99_itl_ms",
    "mean_e2el_ms",
    "p99_e2el_ms",
]


def one_config(mbt: int) -> dict:
    native_root = run_root / "runs" / f"mbt-{mbt}"
    record_path = native_root / "run-record.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    rounds = []
    for round_id in (1, 2, 3):
        path = native_root / f"{case_id}-r{round_id}.json"
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
    medians = {
        name: statistics.median(row[name] for row in measured) for name in metrics
    }
    spreads = {
        name: (
            (max(row[name] for row in measured) - min(row[name] for row in measured))
            / medians[name]
        )
        for name in metrics
    }
    return {
        "max_num_batched_tokens": mbt,
        "run_record_status": record.get("status"),
        "inputs_verified_before": record.get("inputs_verified_before"),
        "inputs_verified_after": record.get("inputs_verified_after"),
        "rounds": rounds,
        "measured_median": medians,
        "measured_relative_spread": spreads,
        "run_record": {
            "path": str(record_path),
            "sha256": hashlib.sha256(record_path.read_bytes()).hexdigest(),
        },
    }


configs = {
    str(mbt): one_config(mbt) for mbt in (2048, 2256, 2304, 2560, 3072, 4096)
}
baseline = configs["2048"]["measured_median"]
higher = {"request_throughput", "output_throughput", "total_token_throughput"}
for mbt in (2256, 2304, 2560, 3072, 4096):
    item = configs[str(mbt)]
    median = item["measured_median"]
    item["relative_to_2048"] = {
        name: (
            median[name] / baseline[name] - 1
            if name in higher
            else baseline[name] / median[name] - 1
        )
        for name in metrics
    }
    output_gain = item["relative_to_2048"]["output_throughput"]
    ttft_regression = median["p99_ttft_ms"] / baseline["p99_ttft_ms"] - 1
    tpot_regression = median["p99_tpot_ms"] / baseline["p99_tpot_ms"] - 1
    itl_regression = median["p99_itl_ms"] / baseline["p99_itl_ms"] - 1
    complete = all(
        row["completed"] == 64
        and (row["failed"] in (None, 0))
        and row["total_input_tokens"] == 4096 * 64
        and row["total_output_tokens"] == 128 * 64
        for row in item["rounds"][1:]
    )
    spread_ok = item["measured_relative_spread"]["output_throughput"] <= 0.08
    item["promotion"] = {
        "output_gain": output_gain,
        "p99_ttft_regression": ttft_regression,
        "p99_tpot_regression": tpot_regression,
        "p99_itl_regression": itl_regression,
        "complete": complete,
        "spread_ok": spread_ok,
        "passed": (
            output_gain >= 0.03
            and ttft_regression <= 0.10
            and tpot_regression <= 0.05
            and itl_regression <= 0.05
            and complete
            and spread_ok
        ),
    }

summary = {
    "schema_version": 1,
    "mode": "targeted",
    "scope": "performance_only",
    "parent_scenario_id": "p4096-d1024-c64-n128",
    "scenario_id": case_id,
    "stage": "mixed",
    "cold_start_included_in_conclusion": False,
    "configs": configs,
    "best_by_output_throughput": max(
        configs,
        key=lambda key: configs[key]["measured_median"]["output_throughput"],
    ),
    "conclusion_boundary": (
        "Same-source config milestone only; full D1024/N128 remains required before retention."
    ),
}
output = run_root / "summary.json"
output.write_text(
    json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
    encoding="utf-8",
)
print(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False))
