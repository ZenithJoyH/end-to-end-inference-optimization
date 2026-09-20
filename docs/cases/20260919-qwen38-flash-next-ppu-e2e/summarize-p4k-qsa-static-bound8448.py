#!/usr/bin/env python3
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path("/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance")
BASELINE = ROOT / "p4k-entry-summary-01.json"
RUN = ROOT / "p4k-qsa-static-bound8448-mixed-candidate-01" / "run-record.json"
OUTPUT = ROOT / "p4k-qsa-static-bound8448-mixed-candidate-summary-02.json"
METRICS = (
    "duration", "completed", "failed", "request_throughput",
    "output_throughput", "total_token_throughput", "median_ttft_ms",
    "p99_ttft_ms", "median_tpot_ms", "p99_tpot_ms", "median_itl_ms",
    "p99_itl_ms", "median_e2el_ms", "p99_e2el_ms",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


record = json.loads(RUN.read_text(encoding="utf-8"))
if record["status"] != "complete" or record["errors"]:
    raise SystemExit("candidate is not a clean complete run")
measured = [row for row in record["rounds"] if row["phase"] == "measured"]
if len(measured) != 3:
    raise SystemExit("expected three measured rounds")
raw = [json.loads(Path(row["raw_result"]["path"]).read_text()) for row in measured]
if any(row["completed"] != 128 or row["failed"] != 0 for row in raw):
    raise SystemExit("incomplete candidate round")
values = {metric: [row[metric] for row in raw] for metric in METRICS}
candidate = {metric: statistics.median(series) for metric, series in values.items()}
baseline = json.loads(BASELINE.read_text())["phases"]["mixed"]["medians"]
deltas = {
    metric: (candidate[metric] / baseline[metric] - 1.0) * 100.0
    for metric in candidate.keys() & baseline.keys() if baseline[metric] != 0
}
warmup_stable = all(
    item.get("status") == "passed" for item in record["warmup_check"].values()
)
checks = {
    "output_throughput_ge_3pct": deltas["output_throughput"] >= 3.0,
    "total_token_throughput_ge_3pct": deltas["total_token_throughput"] >= 3.0,
    "p99_ttft_le_5pct": deltas["p99_ttft_ms"] <= 5.0,
    "p99_tpot_le_5pct": deltas["p99_tpot_ms"] <= 5.0,
    "p99_itl_le_5pct": deltas["p99_itl_ms"] <= 5.0,
    "p99_e2el_le_5pct": deltas["p99_e2el_ms"] <= 5.0,
    "zero_failures": candidate["failed"] == 0,
    "warmup_stable": warmup_stable,
}
payload = {
    "schema_version": 2,
    "supersedes": str(
        ROOT / "p4k-qsa-static-bound8448-mixed-candidate-summary-01.json"
    ),
    "correction": "warmup_check is keyed by scenario_id; aggregate nested status fields",
    "scenario_id": "p4096-d1024-c64-n128",
    "experiment_id": "op-006-qsa-static-score-bound8448-service",
    "baseline_summary": {"path": str(BASELINE), "sha256": sha(BASELINE)},
    "candidate_run_record": {"path": str(RUN), "sha256": sha(RUN)},
    "warmup_check": record["warmup_check"],
    "candidate_values": values,
    "baseline_medians": baseline,
    "candidate_medians": candidate,
    "candidate_vs_baseline_percent": deltas,
    "checks": checks,
    "decision": "provisional_pass_requires_revert" if all(checks.values()) else "fail_revert",
}
if OUTPUT.exists():
    raise SystemExit(f"refusing to overwrite {OUTPUT}")
OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print(OUTPUT)
