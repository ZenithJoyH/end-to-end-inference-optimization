#!/usr/bin/env python3
"""Compare steady P4K benchmark summaries without folding in cold Run1."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


METRICS = (
    "Benchmark Duration (s)",
    "Output tok/s",
    "Total tok/s",
    "Mean TTFT (ms)",
    "Median TTFT (ms)",
    "P99 TTFT (ms)",
    "Mean TPOT (ms)",
    "Median TPOT (ms)",
    "P99 TPOT (ms)",
    "Mean ITL (ms)",
    "Median ITL (ms)",
    "P99 ITL (ms)",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def read_csv(path: Path) -> tuple[dict[str, float], dict[str, float], str]:
    raw = path.read_bytes()
    rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    summary = next(row for row in rows if row["Run"] == "SUMMARY")
    run1 = next(row for row in rows if row["Run"].startswith("Run1"))
    return (
        {metric: float(summary[metric]) for metric in METRICS},
        {metric: float(run1[metric]) for metric in METRICS},
        hashlib.sha256(raw).hexdigest(),
    )


def main() -> int:
    args = parse_args()
    baseline, baseline_run1, baseline_sha = read_csv(args.baseline)
    candidate, candidate_run1, candidate_sha = read_csv(args.candidate)
    higher_is_better = {"Output tok/s", "Total tok/s"}
    changes = {}
    for metric in METRICS:
        raw_ratio = candidate[metric] / baseline[metric] - 1.0
        changes[metric] = {
            "baseline": baseline[metric],
            "candidate": candidate[metric],
            "relative_change": raw_ratio,
            "improvement": raw_ratio if metric in higher_is_better else -raw_ratio,
        }
    report = {
        "schema_version": 1,
        "baseline": str(args.baseline),
        "baseline_sha256": baseline_sha,
        "candidate": str(args.candidate),
        "candidate_sha256": candidate_sha,
        "workload": "P4096/D1024/C64/N128",
        "comparison_scope": "CSV SUMMARY (steady Run2/Run3); Run1 reported separately",
        "changes": changes,
        "cold_run1": {
            "baseline_duration_s": baseline_run1["Benchmark Duration (s)"],
            "candidate_duration_s": candidate_run1["Benchmark Duration (s)"],
            "candidate_vs_baseline_improvement": 1.0
            - candidate_run1["Benchmark Duration (s)"]
            / baseline_run1["Benchmark Duration (s)"],
            "candidate_vs_steady_duration_ratio": candidate_run1[
                "Benchmark Duration (s)"
            ]
            / candidate["Benchmark Duration (s)"],
        },
        "conclusion_boundary": (
            "checkpoint comparison only; no same-run baseline/candidate/revert identity proof"
        ),
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
