#!/usr/bin/env python3
import hashlib
import json
import statistics
from pathlib import Path

case_root = Path("/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e")
run_record_path = case_root / "performance/p4k-op008-prefill-candidate-01/run-record.json"
baseline_path = case_root / "performance/p4k-entry-summary-01.json"
output_path = case_root / "performance/p4k-op008-prefill-vs-entry-summary-01.json"

run = json.loads(run_record_path.read_text())
baseline_doc = json.loads(baseline_path.read_text())
baseline = baseline_doc["phases"]["prefill"]["medians"]
measured = [r for r in run["rounds"] if r["phase"] == "measured"]
rows = [json.loads(Path(r["raw_result"]["path"]).read_text()) for r in measured]
metrics = [
    "completed",
    "failed",
    "duration",
    "request_throughput",
    "total_token_throughput",
    "median_ttft_ms",
    "p99_ttft_ms",
    "median_e2el_ms",
    "p99_e2el_ms",
]
values = {m: [row[m] for row in rows] for m in metrics}
candidate = {m: statistics.median(v) for m, v in values.items()}

def percent(metric):
    return (candidate[metric] / baseline[metric] - 1.0) * 100.0

deltas = {m: percent(m) for m in metrics if baseline.get(m) not in (None, 0)}
checks = {
    "three_measured_rounds": len(rows) == 3,
    "zero_failures": all(v == 0 for v in values["failed"]),
    "all_completed": all(v == 64 for v in values["completed"]),
    "warmup_stable": all(v.get("status") == "passed" for v in run["warmup_check"].values()),
    "total_token_throughput_ge_3pct": deltas["total_token_throughput"] >= 3.0,
    "p99_ttft_le_5pct": deltas["p99_ttft_ms"] <= 5.0,
    "p99_e2el_le_5pct": deltas["p99_e2el_ms"] <= 5.0,
}
doc = {
    "schema_version": 1,
    "experiment_id": "perf-012-op008-p4k-prefill",
    "scenario_id": "p4096-d1-c32-n64-prefill-entry",
    "scope": "performance_only",
    "baseline_identity": "p4k-entry-prefill-baseline-01; pre-op006 scenario entry",
    "candidate_identity": "service-35 op006+op008 cumulative candidate",
    "runtime_score_bound": {"static": 8448, "p4096": 1024, "p5120": 1280},
    "baseline_medians": baseline,
    "candidate_values": values,
    "candidate_medians": candidate,
    "candidate_vs_baseline_percent": deltas,
    "warmup_check": run["warmup_check"],
    "checks": checks,
    "decision": "pass_cumulative_vs_entry_needs_mixed_for_incremental_op008" if all(checks.values()) else "fail",
    "boundary": "No isolated op006 P4K Prefill service run exists; this comparison is cumulative op006+op008 versus the pre-op006 P4K entry and must not attribute the full delta to op008 alone.",
    "inputs": {
        "run_record": {"path": str(run_record_path), "sha256": hashlib.sha256(run_record_path.read_bytes()).hexdigest()},
        "baseline": {"path": str(baseline_path), "sha256": hashlib.sha256(baseline_path.read_bytes()).hexdigest()},
    },
}
output_path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
print(output_path)
print(hashlib.sha256(output_path.read_bytes()).hexdigest())
print(json.dumps({"candidate_medians": candidate, "candidate_vs_baseline_percent": deltas, "checks": checks, "decision": doc["decision"]}, indent=2, sort_keys=True))
