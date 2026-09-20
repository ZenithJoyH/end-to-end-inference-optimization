#!/usr/bin/env python3
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path("/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance")
CANDIDATE = ROOT / "p4k-qsa-static-bound8448-mixed-candidate-summary-02.json"
BASELINE = ROOT / "p4k-entry-summary-01.json"
RUN = ROOT / "p4k-qsa-static-bound8448-revert-02" / "run-record.json"
OUTPUT = ROOT / "p4k-qsa-static-bound8448-candidate-revert-summary-01.json"
METRICS = (
    "duration", "completed", "failed", "request_throughput",
    "output_throughput", "total_token_throughput", "median_ttft_ms",
    "p99_ttft_ms", "median_tpot_ms", "p99_tpot_ms", "median_itl_ms",
    "p99_itl_ms", "median_e2el_ms", "p99_e2el_ms",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percent(lhs: dict, rhs: dict) -> dict:
    return {
        metric: (lhs[metric] / rhs[metric] - 1.0) * 100.0
        for metric in lhs.keys() & rhs.keys()
        if rhs[metric] != 0
    }


candidate_doc = json.loads(CANDIDATE.read_text())
candidate = candidate_doc["candidate_medians"]
baseline = json.loads(BASELINE.read_text())["phases"]["mixed"]["medians"]
record = json.loads(RUN.read_text())
if record["status"] != "complete" or record["errors"]:
    raise SystemExit("revert is not a clean complete run")
measured = [row for row in record["rounds"] if row["phase"] == "measured"]
if len(measured) != 3:
    raise SystemExit("expected three measured revert rounds")
raw = [json.loads(Path(row["raw_result"]["path"]).read_text()) for row in measured]
if any(row["completed"] != 128 or row["failed"] != 0 for row in raw):
    raise SystemExit("incomplete revert round")
values = {metric: [row[metric] for row in raw] for metric in METRICS}
revert = {metric: statistics.median(series) for metric, series in values.items()}
candidate_vs_revert = percent(candidate, revert)
revert_vs_baseline = percent(revert, baseline)
warmup_stable = all(
    item.get("status") == "passed" for item in record["warmup_check"].values()
)
checks = {
    "candidate_output_ge_3pct_vs_revert": candidate_vs_revert["output_throughput"] >= 3.0,
    "candidate_total_ge_3pct_vs_revert": candidate_vs_revert["total_token_throughput"] >= 3.0,
    "candidate_p99_ttft_le_5pct_vs_revert": candidate_vs_revert["p99_ttft_ms"] <= 5.0,
    "candidate_p99_tpot_le_5pct_vs_revert": candidate_vs_revert["p99_tpot_ms"] <= 5.0,
    "candidate_p99_itl_le_5pct_vs_revert": candidate_vs_revert["p99_itl_ms"] <= 5.0,
    "candidate_p99_e2el_le_5pct_vs_revert": candidate_vs_revert["p99_e2el_ms"] <= 5.0,
    "revert_output_drift_le_3pct": abs(revert_vs_baseline["output_throughput"]) <= 3.0,
    "revert_total_drift_le_3pct": abs(revert_vs_baseline["total_token_throughput"]) <= 3.0,
    "zero_failures": revert["failed"] == 0,
    "warmup_stable": warmup_stable,
}
payload = {
    "schema_version": 1,
    "scenario_id": "p4096-d1024-c64-n128",
    "experiment_id": "op-006-qsa-static-score-bound8448-service-revert",
    "candidate_summary": {"path": str(CANDIDATE), "sha256": sha(CANDIDATE)},
    "baseline_summary": {"path": str(BASELINE), "sha256": sha(BASELINE)},
    "revert_run_record": {"path": str(RUN), "sha256": sha(RUN)},
    "revert_warmup_check": record["warmup_check"],
    "revert_values": values,
    "candidate_medians": candidate,
    "revert_medians": revert,
    "baseline_medians": baseline,
    "candidate_vs_revert_percent": candidate_vs_revert,
    "revert_vs_baseline_percent": revert_vs_baseline,
    "checks": checks,
    "decision": "pass_retain" if all(checks.values()) else "fail_revert_candidate",
}
if OUTPUT.exists():
    raise SystemExit(f"refusing to overwrite {OUTPUT}")
OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print(OUTPUT)
