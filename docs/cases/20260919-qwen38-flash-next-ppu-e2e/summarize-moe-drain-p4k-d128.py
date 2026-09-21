#!/usr/bin/env python3
"""Summarize the same-process P4K/D128 MoE drain milestone."""

from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path


ROOT = Path(
    "/mnt/nfs/users/jinghao/qwen3.8-flash/"
    "20260919-qwen38-flash-next-ppu-e2e/performance"
)
OUTPUT = ROOT / "p4k-d128-mm-native-abr-summary-01.json"
METRICS = (
    "output_throughput", "total_token_throughput", "duration",
    "median_ttft_ms", "p99_ttft_ms", "median_tpot_ms", "p99_tpot_ms",
    "median_itl_ms", "p99_itl_ms", "median_e2el_ms", "p99_e2el_ms",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(role: str) -> dict[str, object]:
    directory = (
        ROOT / "p4k-d128-moe-drain-baseline-01"
        if role == "baseline"
        else ROOT / f"p4k-d128-mm-native-{role}-01"
    )
    record_path = directory / "run-record.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    measured = [row for row in record["rounds"] if row["phase"] == "measured"]
    documents = [
        json.loads(Path(row["raw_result"]["path"]).read_text(encoding="utf-8"))
        for row in measured
    ]
    medians = {key: statistics.median(item[key] for item in documents) for key in METRICS}
    output_values = [item["output_throughput"] for item in documents]
    return {
        "run_record": str(record_path),
        "run_record_sha256": sha(record_path),
        "status": record["status"],
        "warmup_check": record["warmup_check"],
        "rounds": [
            {
                "output_throughput": item["output_throughput"],
                "duration": item["duration"],
                "completed": item["completed"],
                "failed": item["failed"],
            }
            for item in documents
        ],
        "measured_output_relative_spread": max(output_values) / min(output_values) - 1.0,
        "medians": medians,
    }


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit(f"output already exists: {OUTPUT}")
    baseline = collect("baseline")
    candidate = collect("candidate")
    revert = collect("revert")
    base = baseline["medians"]
    cand = candidate["medians"]
    rev = revert["medians"]
    deltas = {key: (cand[key] / base[key] - 1.0) * 100.0 for key in METRICS}
    candidate_vs_revert = {
        key: (cand[key] / rev[key] - 1.0) * 100.0 for key in METRICS
    }
    revert_vs_baseline = {
        key: (rev[key] / base[key] - 1.0) * 100.0 for key in METRICS
    }
    checks = {
        "baseline_complete": baseline["status"] == "complete",
        "candidate_complete": candidate["status"] == "complete",
        "revert_complete": revert["status"] == "complete",
        "baseline_warmup_passed": all(
            value["status"] == "passed" for value in baseline["warmup_check"].values()
        ),
        "candidate_warmup_passed": all(
            value["status"] == "passed" for value in candidate["warmup_check"].values()
        ),
        "revert_warmup_passed": all(
            value["status"] == "passed" for value in revert["warmup_check"].values()
        ),
        "both_measured_spreads_le_8pct": max(
            baseline["measured_output_relative_spread"],
            candidate["measured_output_relative_spread"],
            revert["measured_output_relative_spread"],
        ) <= 0.08,
        "output_throughput_ge_1pct": deltas["output_throughput"] >= 1.0,
        "total_token_throughput_regression_le_2pct": deltas["total_token_throughput"] >= -2.0,
        "candidate_vs_revert_output_throughput_ge_1pct": (
            candidate_vs_revert["output_throughput"] >= 1.0
        ),
        "revert_vs_baseline_output_drift_le_5pct": (
            abs(revert_vs_baseline["output_throughput"]) <= 5.0
        ),
    }
    for key in (
        "p99_ttft_ms", "p99_tpot_ms", "p99_itl_ms", "p99_e2el_ms"
    ):
        checks[f"{key}_regression_le_3pct"] = deltas[key] <= 3.0
    passed = all(checks.values())
    payload = {
        "schema_version": 1,
        "status": "passed_screen" if passed else "failed_screen",
        "workload": "P4096/D128/C64/N64 finite batch",
        "baseline": baseline,
        "candidate": candidate,
        "revert": revert,
        "candidate_vs_baseline_percent": deltas,
        "candidate_vs_revert_percent": candidate_vs_revert,
        "revert_vs_baseline_percent": revert_vs_baseline,
        "checks": checks,
        "decision": "retain_for_correctly_bound_checkpoint" if passed else "revert_candidate",
        "boundary": (
            "Independent service instances were used for candidate and revert, but the run records "
            "were bound to the preceding MoE tuned-config comparison contract rather than a blacklist "
            "variable contract. This is valid screening evidence only; remeasure under the correct "
            "contract before a formal performance claim. It does not resolve the formal accuracy blocker."
        ),
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
