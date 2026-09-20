#!/usr/bin/env python3
import hashlib
import json
import statistics
from pathlib import Path

CASE_ROOT = Path("/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e")
PERF_ROOT = CASE_ROOT / "performance"
RUN_ROOT = PERF_ROOT / "p4k-longprefill2048-mixed-candidate-01"
BASELINE = PERF_ROOT / "p4k-entry-summary-01.json"
STOP_EVIDENCE = CASE_ROOT / "transitions/stop-p4k-longprefill2048-after-warmup-20/before-term.json"
OUTPUT = PERF_ROOT / "p4k-longprefill2048-mixed-candidate-summary-early-stop-01.json"
METRICS = (
    "duration", "completed", "failed", "request_throughput",
    "output_throughput", "total_token_throughput", "median_ttft_ms",
    "p99_ttft_ms", "median_tpot_ms", "p99_tpot_ms", "median_itl_ms",
    "p99_itl_ms", "median_e2el_ms", "p99_e2el_ms",
)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


rows = [
    json.loads((RUN_ROOT / f"p4096-d1024-c64-n128-r{index}.json").read_text(encoding="utf-8"))
    for index in (1, 2, 3)
]
if any(row["completed"] != 128 or row["failed"] != 0 for row in rows):
    raise SystemExit("warmup evidence is incomplete")
values = {metric: [row[metric] for row in rows] for metric in METRICS}
medians = {metric: statistics.median(series) for metric, series in values.items()}
baseline = json.loads(BASELINE.read_text(encoding="utf-8"))["phases"]["mixed"]["medians"]


def pct(new: float, old: float) -> float:
    return (new / old - 1.0) * 100.0


deltas = {
    metric: pct(medians[metric], baseline[metric])
    for metric in medians.keys() & baseline.keys() if baseline[metric] != 0
}
output_spread = (
    max(values["output_throughput"]) / min(values["output_throughput"]) - 1.0
) * 100.0
checks = {
    "p99_itl_improves_at_least_20pct": deltas["p99_itl_ms"] <= -20.0,
    "output_throughput_retains_95pct": deltas["output_throughput"] >= -5.0,
    "total_token_throughput_retains_95pct": deltas["total_token_throughput"] >= -5.0,
    "p99_ttft_le_5pct": deltas["p99_ttft_ms"] <= 5.0,
    "p99_tpot_le_5pct": deltas["p99_tpot_ms"] <= 5.0,
    "p99_e2el_le_5pct": deltas["p99_e2el_ms"] <= 5.0,
    "zero_failures": medians["failed"] == 0,
    "warmup_stable": output_spread <= 2.0,
}
payload = {
    "schema_version": 1,
    "scenario_id": "p4096-d1024-c64-n128",
    "experiment_id": "fw-006-p4k-long-prefill-threshold2048",
    "scope": "three_complete_warmup_rounds_early_stop_before_measured_rounds",
    "baseline_summary": {"path": str(BASELINE), "sha256": sha(BASELINE)},
    "stop_evidence": {"path": str(STOP_EVIDENCE), "sha256": sha(STOP_EVIDENCE)},
    "warmup_rounds": 3,
    "values": values,
    "medians": medians,
    "candidate_vs_baseline_percent": deltas,
    "output_throughput_spread_percent": output_spread,
    "checks": checks,
    "decision": "fail_revert",
    "stop_reason": "The primary P99 ITL recovery threshold failed in all three complete warmup rounds; continuing measured rounds could not establish the pre-frozen mechanism target and would consume unnecessary accelerator time.",
}
if OUTPUT.exists():
    raise SystemExit(f"refusing to overwrite {OUTPUT}")
OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(OUTPUT)
