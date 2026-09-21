#!/usr/bin/env python3
import hashlib
import json
import statistics
from pathlib import Path

case_root = Path("/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e")
run_record_path = case_root / "performance/p4k-op008-mixed-candidate-01/run-record.json"
op006_path = case_root / "performance/p4k-qsa-static-bound8448-mixed-candidate-summary-02.json"
entry_path = case_root / "performance/p4k-entry-summary-01.json"
output_path = case_root / "performance/p4k-op008-mixed-vs-op006-summary-01.json"

run = json.loads(run_record_path.read_text())
op006_doc = json.loads(op006_path.read_text())
entry_doc = json.loads(entry_path.read_text())
op006 = op006_doc["candidate_medians"]
entry = entry_doc["phases"]["mixed"]["medians"]
measured = [r for r in run["rounds"] if r["phase"] == "measured"]
rows = [json.loads(Path(r["raw_result"]["path"]).read_text()) for r in measured]
metrics = [
    "completed",
    "failed",
    "duration",
    "request_throughput",
    "output_throughput",
    "total_token_throughput",
    "median_ttft_ms",
    "p99_ttft_ms",
    "median_tpot_ms",
    "p99_tpot_ms",
    "median_itl_ms",
    "p99_itl_ms",
    "median_e2el_ms",
    "p99_e2el_ms",
]
values = {m: [row[m] for row in rows] for m in metrics}
candidate = {m: statistics.median(v) for m, v in values.items()}

def deltas(reference):
    return {m: (candidate[m] / reference[m] - 1.0) * 100.0 for m in metrics if reference.get(m) not in (None, 0)}

vs_op006 = deltas(op006)
vs_entry = deltas(entry)
checks = {
    "three_measured_rounds": len(rows) == 3,
    "zero_failures": all(v == 0 for v in values["failed"]),
    "all_completed": all(v == 128 for v in values["completed"]),
    "warmup_stable": all(v.get("status") == "passed" for v in run["warmup_check"].values()),
    "output_throughput_ge_3pct_vs_op006": vs_op006["output_throughput"] >= 3.0,
    "total_token_throughput_not_down_2pct_vs_op006": vs_op006["total_token_throughput"] >= -2.0,
    "p99_ttft_le_5pct_vs_op006": vs_op006["p99_ttft_ms"] <= 5.0,
    "p99_tpot_le_5pct_vs_op006": vs_op006["p99_tpot_ms"] <= 5.0,
    "p99_itl_le_5pct_vs_op006": vs_op006["p99_itl_ms"] <= 5.0,
    "p99_e2el_le_5pct_vs_op006": vs_op006["p99_e2el_ms"] <= 5.0,
}
doc = {
    "schema_version": 1,
    "experiment_id": "perf-012-op008-p4k-mixed",
    "scenario_id": "p4096-d1024-c64-n128",
    "scope": "performance_only",
    "op006_baseline_identity": "p4k-qsa-static-bound8448-mixed-candidate-01",
    "entry_baseline_identity": "p4k-entry-mixed-baseline-01",
    "candidate_identity": "service-35 op006+op008 cumulative candidate",
    "runtime_score_bound": {"static": 8448, "p4096": 1024, "p5120": 1280},
    "op006_medians": op006,
    "entry_medians": entry,
    "candidate_values": values,
    "candidate_medians": candidate,
    "candidate_vs_op006_percent": vs_op006,
    "candidate_vs_entry_percent": vs_entry,
    "warmup_check": run["warmup_check"],
    "checks": checks,
    "decision": "pass_retain_performance_only" if all(checks.values()) else "fail",
    "boundary": "This is a same-workload checkpoint comparison across archived service processes, not independent-process formal performance acceptance. Formal accuracy remains blocked.",
    "inputs": {
        "run_record": {"path": str(run_record_path), "sha256": hashlib.sha256(run_record_path.read_bytes()).hexdigest()},
        "op006_summary": {"path": str(op006_path), "sha256": hashlib.sha256(op006_path.read_bytes()).hexdigest()},
        "entry_summary": {"path": str(entry_path), "sha256": hashlib.sha256(entry_path.read_bytes()).hexdigest()},
    },
}
output_path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
print(output_path)
print(hashlib.sha256(output_path.read_bytes()).hexdigest())
print(json.dumps({"candidate_medians": candidate, "candidate_vs_op006_percent": vs_op006, "candidate_vs_entry_percent": vs_entry, "checks": checks, "decision": doc["decision"]}, indent=2, sort_keys=True))
