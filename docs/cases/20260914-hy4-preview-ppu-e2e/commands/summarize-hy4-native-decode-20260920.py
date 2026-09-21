#!/usr/bin/env python3
"""Write the diagnostic A/B summary for the rejected native Decode candidate."""

from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path


ROOT = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e/results/performance/"
    "20260920-p4k-d128-c64-n64-native-decode-03"
)
METRICS = (
    "duration",
    "output_throughput",
    "total_token_throughput",
    "p99_ttft_ms",
    "mean_tpot_ms",
    "p99_tpot_ms",
    "median_itl_ms",
    "p99_itl_ms",
    "mean_e2el_ms",
    "p99_e2el_ms",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def measured(role: str) -> tuple[dict[str, float], list[dict]]:
    directory = ROOT / "runs" / role
    rounds = [
        json.loads((directory / f"p4096-d128-c64-n64-r{index}.json").read_text())
        for index in (2, 3)
    ]
    values = {
        metric: statistics.median([row[metric] for row in rounds])
        for metric in METRICS
    }
    values["output_throughput_relative_spread"] = (
        max(row["output_throughput"] for row in rounds)
        - min(row["output_throughput"] for row in rounds)
    ) / values["output_throughput"]
    return values, rounds


baseline, baseline_rounds = measured("native-decode-0")
candidate, candidate_rounds = measured("native-decode-1")
changes = {
    metric: candidate[metric] / baseline[metric] - 1.0 for metric in METRICS
}
receipt = ROOT / "comparison-receipt.json"
summary = {
    "schema_version": 1,
    "status": "rejected",
    "scope": "diagnostic_milestone_only",
    "scenario_id": "p4096-d128-c64-n64",
    "parent_scenario_id": "p4096-d1024-c64-n128",
    "cold_start_policy": "excluded_by_user_request",
    "baseline": baseline,
    "candidate": candidate,
    "candidate_relative_change": changes,
    "completed_requests": {
        "baseline": [row["completed"] for row in baseline_rounds],
        "candidate": [row["completed"] for row in candidate_rounds],
    },
    "failed_requests": {
        "baseline": [row["failed"] for row in baseline_rounds],
        "candidate": [row["failed"] for row in candidate_rounds],
    },
    "promotion_threshold": {"output_throughput_min_improvement": 0.02},
    "decision": (
        "Reject and revert: output throughput improved only 0.196%, below the "
        "pre-frozen 2% milestone threshold."
    ),
    "path_evidence": (
        "Candidate service log contains the one-time T-Head pure Decode native "
        "flash_mla hit record."
    ),
    "standard_comparison_receipt": {
        "path": str(receipt),
        "sha256": sha256(receipt),
        "status": "incomplete",
        "issue": "base service manifest lacks explicit unique device identifiers",
    },
    "conclusion_boundary": (
        "Diagnostic medians from validated R2/R3 only. The standard receipt is "
        "incomplete, so this is not a formal performance pass."
    ),
}
output = ROOT / "diagnostic-comparison.json"
output.write_text(json.dumps(summary, indent=2) + "\n")
print(output)

