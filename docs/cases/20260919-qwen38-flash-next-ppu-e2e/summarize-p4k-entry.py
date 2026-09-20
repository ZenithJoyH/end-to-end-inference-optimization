#!/usr/bin/env python3
import json
import statistics
from pathlib import Path

CASE_ROOT = Path("/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e")
PERF_ROOT = CASE_ROOT / "performance"
RUNS = {
    "prefill": "p4k-entry-prefill-baseline-01",
    "decode": "p4k-entry-decode-baseline-01",
    "mixed": "p4k-entry-mixed-baseline-01",
}
METRICS = (
    "duration",
    "completed",
    "failed",
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
)

summary = {"schema_version": 1, "scenario_id": "p4096-d1024-c64-n128", "phases": {}}
for phase, run_id in RUNS.items():
    run_path = PERF_ROOT / run_id / "run-record.json"
    record = json.loads(run_path.read_text(encoding="utf-8"))
    if record["status"] != "complete" or record["errors"]:
        raise SystemExit(f"{run_id} is not a clean complete run")
    measured = [row for row in record["rounds"] if row["phase"] == "measured"]
    if len(measured) != 3:
        raise SystemExit(f"{run_id}: expected three measured rounds")
    raw_rows = [
        json.loads(Path(row["raw_result"]["path"]).read_text(encoding="utf-8"))
        for row in measured
    ]
    if any(row["completed"] <= 0 or row["failed"] != 0 for row in raw_rows):
        raise SystemExit(f"{run_id}: incomplete or failed requests")
    values = {
        metric: [row.get(metric) for row in raw_rows]
        for metric in METRICS
        if all(row.get(metric) is not None for row in raw_rows)
    }
    summary["phases"][phase] = {
        "run_id": run_id,
        "run_record": str(run_path),
        "warmup_check": record["warmup_check"],
        "measured_rounds": 3,
        "values": values,
        "medians": {metric: statistics.median(rows) for metric, rows in values.items()},
    }

output = PERF_ROOT / "p4k-entry-summary-01.json"
if output.exists():
    raise SystemExit(f"refusing to overwrite {output}")
output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(output)
