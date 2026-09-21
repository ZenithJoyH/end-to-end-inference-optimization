#!/usr/bin/env python3
"""Summarize the op010 exact P4K/D1024 checkpoint screen."""

from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path


ROOT = Path(
    "/mnt/nfs/users/jinghao/qwen3.8-flash/"
    "20260919-qwen38-flash-next-ppu-e2e/performance"
)
OUTPUT = ROOT / "p4k-d1024-mm-native-screen-summary-01.json"
RUNS = {
    "baseline": ROOT / "p4k-op008-mixed-candidate-01" / "run-record.json",
    "candidate": ROOT / "p4k-d1024-mm-native-contract-candidate-01" / "run-record.json",
}
METRICS = (
    "output_throughput",
    "total_token_throughput",
    "duration",
    "median_ttft_ms",
    "p99_ttft_ms",
    "median_tpot_ms",
    "p99_tpot_ms",
    "median_itl_ms",
    "p99_itl_ms",
    "median_e2el_ms",
    "p99_e2el_ms",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(path: Path) -> dict[str, object]:
    record = json.loads(path.read_text(encoding="utf-8"))
    measured_rows = [row for row in record["rounds"] if row["phase"] == "measured"]
    documents = [
        json.loads(Path(row["raw_result"]["path"]).read_text(encoding="utf-8"))
        for row in measured_rows
    ]
    outputs = [document["output_throughput"] for document in documents]
    return {
        "run_record": str(path),
        "run_record_sha256": sha256(path),
        "status": record["status"],
        "warmup_check": record["warmup_check"],
        "measured_round_count": len(documents),
        "measured_output_throughput": outputs,
        "measured_output_relative_spread": max(outputs) / min(outputs) - 1.0,
        "medians": {
            metric: statistics.median(document[metric] for document in documents)
            for metric in METRICS
        },
    }


def warmup_passed(run: dict[str, object]) -> bool:
    return all(item["status"] == "passed" for item in run["warmup_check"].values())


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit(f"output already exists: {OUTPUT}")
    baseline = collect(RUNS["baseline"])
    candidate = collect(RUNS["candidate"])
    base = baseline["medians"]
    cand = candidate["medians"]
    deltas = {
        metric: (cand[metric] / base[metric] - 1.0) * 100.0
        for metric in METRICS
    }
    checks = {
        "baseline_complete": baseline["status"] == "complete",
        "candidate_complete": candidate["status"] == "complete",
        "baseline_warmup_passed": warmup_passed(baseline),
        "candidate_warmup_passed": warmup_passed(candidate),
        "measured_spreads_le_8pct": max(
            baseline["measured_output_relative_spread"],
            candidate["measured_output_relative_spread"],
        ) <= 0.08,
        "output_throughput_ge_1pct": deltas["output_throughput"] >= 1.0,
        "total_token_throughput_regression_le_2pct": (
            deltas["total_token_throughput"] >= -2.0
        ),
    }
    for metric in ("p99_ttft_ms", "p99_tpot_ms", "p99_itl_ms", "p99_e2el_ms"):
        checks[f"{metric}_regression_le_3pct"] = deltas[metric] <= 3.0
    passed = all(checks.values())
    payload = {
        "schema_version": 1,
        "status": "passed_checkpoint_screen" if passed else "failed_checkpoint_screen",
        "workload": "P4096/D1024/C64/N128 finite batch",
        "baseline": baseline,
        "candidate": candidate,
        "candidate_vs_baseline_percent": deltas,
        "checks": checks,
        "decision": (
            "retain_native_mm_provider_pending_independent_revert"
            if passed
            else "revert_native_mm_provider"
        ),
        "boundary": (
            "The candidate is bound to the op010 blacklist comparison contract, while the exact-workload "
            "baseline is the previously retained op008 run record. The workload and all non-provider "
            "settings match, but there is no fresh independent-process revert under the op010 D1024 "
            "contract. This is checkpoint screening evidence, not a formal A/B/R result. It does not "
            "resolve the inherited formal accuracy blocker."
        ),
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
