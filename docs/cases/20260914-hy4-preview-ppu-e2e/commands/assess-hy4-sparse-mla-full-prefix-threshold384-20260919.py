#!/usr/bin/env python3
"""Apply the threshold-aware acceptance rule to the SQ384 sweep."""

import json
from pathlib import Path


ROOT = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e/results/operator/"
    "sparse-mla-full-prefix-threshold384-20260919-06"
)
SOURCE = ROOT / "summary.json"
OUTPUT = ROOT / "assessment.json"


def main() -> None:
    assert SOURCE.is_file(), SOURCE
    assert not OUTPUT.exists(), OUTPUT
    source = json.loads(SOURCE.read_text())
    rows = source["rows"]
    grouped = [row for row in rows if row["pattern"] == "full_prefix" and row["sq"] >= 384]
    legacy = [row for row in rows if row["pattern"] == "full_prefix" and row["sq"] < 384]
    fallback = [row for row in rows if row["pattern"] == "random_topk"]
    checks = {
        "grouped_sq384_plus_ge_1_10x": all(row["speedup"] >= 1.10 for row in grouped),
        "legacy_sq_below_384_ge_0_95x": all(row["speedup"] >= 0.95 for row in legacy),
        "random_topk_ge_0_95x": all(row["speedup"] >= 0.95 for row in fallback),
        "max_abs_error_zero": all(max(row["max_abs_error"]) == 0.0 for row in rows),
    }
    result = {
        "schema_version": 1,
        "status": "candidate" if all(checks.values()) else "rejected",
        "candidate": "lower_full_prefix_grouping_threshold_to_sq384",
        "checks": checks,
        "grouped_speedup": {str(row["sq"]): row["speedup"] for row in grouped},
        "legacy_speedup": {str(row["sq"]): row["speedup"] for row in legacy},
        "random_topk_speedup": {str(row["sq"]): row["speedup"] for row in fallback},
        "source": str(SOURCE),
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
