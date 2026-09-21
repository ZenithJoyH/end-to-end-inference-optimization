#!/usr/bin/env python3
"""Summarize the op014 cross-device-group P4K milestone."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import median


METRICS = (
    "output_throughput",
    "total_token_throughput",
    "p99_ttft_ms",
    "p99_tpot_ms",
    "p99_itl_ms",
    "p99_e2el_ms",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_record(path: Path) -> tuple[dict, dict[str, list[float]]]:
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("status") != "complete" or record.get("errors"):
        raise SystemExit(f"incomplete run record: {path}")
    values = {key: [] for key in METRICS}
    measured = [row for row in record["rounds"] if row["phase"] == "measured"]
    if len(measured) != 2:
        raise SystemExit(f"expected two measured rounds: {path}")
    for row in measured:
        validation = json.loads(Path(row["validation"]["path"]).read_text(encoding="utf-8"))
        raw = json.loads(Path(row["raw_result"]["path"]).read_text(encoding="utf-8"))
        if not validation.get("valid") or raw.get("completed") != 128 or raw.get("failed") != 0:
            raise SystemExit(f"invalid measured round: {row}")
        for key in METRICS:
            value = raw.get(key)
            if not isinstance(value, (int, float)):
                raise SystemExit(f"missing {key}: {row}")
            values[key].append(float(value))
    return record, values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite {args.output}")
    baseline_record, baseline = load_record(args.baseline)
    candidate_record, candidate = load_record(args.candidate)
    rows = {}
    issues = []
    for metric in METRICS:
        base = median(baseline[metric])
        cand = median(candidate[metric])
        throughput = metric.endswith("throughput")
        improvement = ((cand / base) - 1 if throughput else 1 - (cand / base)) * 100
        rows[metric] = {
            "baseline_values": baseline[metric],
            "candidate_values": candidate[metric],
            "baseline_median": base,
            "candidate_median": cand,
            "improvement_percent": improvement,
        }
    if rows["output_throughput"]["improvement_percent"] < 1.0:
        issues.append("output throughput improvement is below the 1% promotion gate")
    if rows["total_token_throughput"]["improvement_percent"] < -2.0:
        issues.append("total token throughput regressed more than 2%")
    for metric in ("p99_ttft_ms", "p99_tpot_ms", "p99_itl_ms", "p99_e2el_ms"):
        if rows[metric]["improvement_percent"] < -3.0:
            issues.append(f"{metric} regressed more than 3%")
    payload = {
        "schema_version": 1,
        "experiment": "op014-repeat-interleave-output-size-dual-service-screen",
        "scope": "cross-device-group milestone; not formal performance",
        "scenario_id": "p4096-d1024-c64-n128",
        "baseline": {
            "service": "service50",
            "devices": list(range(8, 16)),
            "run_record": str(args.baseline),
            "sha256": sha256(args.baseline),
        },
        "candidate": {
            "service": "service51",
            "devices": list(range(8)),
            "run_record": str(args.candidate),
            "sha256": sha256(args.candidate),
        },
        "metrics": rows,
        "issues": issues,
        "decision": "promote_to_same_device_abr" if not issues else "reject_or_remeasure",
        "boundary": (
            "The roles ran on different PPU groups. This result can promote a same-device "
            "A/B/R but cannot retain op014 or establish an exact speedup by itself."
        ),
        "run_ids": [baseline_record["run_id"], candidate_record["run_id"]],
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
