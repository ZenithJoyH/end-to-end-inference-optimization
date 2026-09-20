#!/usr/bin/env python3
import hashlib
import json
import statistics
from pathlib import Path

CASE_ROOT = Path("/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e")
PERF_ROOT = CASE_ROOT / "performance"
BASELINE_SUMMARY = PERF_ROOT / "p4k-entry-summary-01.json"
CANDIDATE_RUN = PERF_ROOT / "p4k-maxbt6144-mixed-candidate-01" / "run-record.json"
OUTPUT = PERF_ROOT / "p4k-maxbt6144-mixed-candidate-summary-01.json"
METRICS = (
    "duration", "completed", "failed", "request_throughput",
    "output_throughput", "total_token_throughput", "median_ttft_ms",
    "p99_ttft_ms", "median_tpot_ms", "p99_tpot_ms", "median_itl_ms",
    "p99_itl_ms", "median_e2el_ms", "p99_e2el_ms",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


record = json.loads(CANDIDATE_RUN.read_text(encoding="utf-8"))
if record["status"] != "complete" or record["errors"]:
    raise SystemExit("candidate is not a clean complete run")
measured = [row for row in record["rounds"] if row["phase"] == "measured"]
if len(measured) != 3:
    raise SystemExit("expected three candidate measured rounds")
raw_rows = [json.loads(Path(row["raw_result"]["path"]).read_text(encoding="utf-8")) for row in measured]
if any(row["completed"] != 128 or row["failed"] != 0 for row in raw_rows):
    raise SystemExit("candidate has incomplete or failed requests")
values = {
    metric: [row.get(metric) for row in raw_rows]
    for metric in METRICS if all(row.get(metric) is not None for row in raw_rows)
}
candidate = {metric: statistics.median(rows) for metric, rows in values.items()}
baseline_doc = json.loads(BASELINE_SUMMARY.read_text(encoding="utf-8"))
baseline = baseline_doc["phases"]["mixed"]["medians"]


def pct(new: float, old: float) -> float:
    return (new / old - 1.0) * 100.0


deltas = {
    metric: pct(candidate[metric], baseline[metric])
    for metric in candidate.keys() & baseline.keys() if baseline[metric] != 0
}
checks = {
    "output_throughput_ge_3pct": deltas["output_throughput"] >= 3.0,
    "total_token_throughput_ge_minus_2pct": deltas["total_token_throughput"] >= -2.0,
    "p99_ttft_le_5pct": deltas["p99_ttft_ms"] <= 5.0,
    "p99_tpot_le_5pct": deltas["p99_tpot_ms"] <= 5.0,
    "p99_itl_le_5pct": deltas["p99_itl_ms"] <= 5.0,
    "p99_e2el_le_5pct": deltas["p99_e2el_ms"] <= 5.0,
    "zero_failures": candidate["failed"] == 0,
    "warmup_stable": bool(record["warmup_check"].get("passed")),
}
summary = {
    "schema_version": 1,
    "scenario_id": "p4096-d1024-c64-n128",
    "experiment_id": "fw-005-p4k-max-batched-tokens6144",
    "baseline_summary": {"path": str(BASELINE_SUMMARY), "sha256": sha256(BASELINE_SUMMARY)},
    "candidate_run_record": {"path": str(CANDIDATE_RUN), "sha256": sha256(CANDIDATE_RUN)},
    "warmup_check": record["warmup_check"],
    "measured_rounds": 3,
    "candidate_values": values,
    "baseline_medians": baseline,
    "candidate_medians": candidate,
    "candidate_vs_baseline_percent": deltas,
    "checks": checks,
    "decision": "provisional_pass_requires_revert" if all(checks.values()) else "fail_revert",
}
if OUTPUT.exists():
    raise SystemExit(f"refusing to overwrite {OUTPUT}")
OUTPUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(OUTPUT)
