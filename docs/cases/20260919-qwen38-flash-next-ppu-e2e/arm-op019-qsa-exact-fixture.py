#!/usr/bin/env python3
"""Create one unique Prefill or Mixed arm for op-019 exact fixture capture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prefill", "mixed"))
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--sample-id")
    parser.add_argument("--op018-summary-sha256", required=True)
    parser.add_argument("--flag-gems-revision", default="record-at-runtime")
    parser.add_argument("--plugin-revision", default="record-at-runtime")
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        raise SystemExit(f"refusing to reuse output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    sample_id = args.sample_id or f"op019-p4k-{args.phase}-fixture-001"
    if args.phase == "prefill":
        minimum, maximum = 1, 1
    else:
        minimum, maximum = 2, 64
    arm = {
        "schema_version": 1,
        "experiment_id": "op-019",
        "sample_id": sample_id,
        "expected_phase": args.phase,
        "expected_rows": 4096,
        "expected_width": 2051,
        "min_request_runs": minimum,
        "max_request_runs": maximum,
        "provenance": {
            "op018_summary_sha256": args.op018_summary_sha256,
            "flag_gems_revision": args.flag_gems_revision,
            "plugin_revision": args.plugin_revision,
            "scope": "diagnostic-only; all client timing is invalid",
        },
    }
    arm_path = output_dir / "arm.json"
    arm_path.write_text(
        json.dumps(arm, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(arm_path)


if __name__ == "__main__":
    main()

