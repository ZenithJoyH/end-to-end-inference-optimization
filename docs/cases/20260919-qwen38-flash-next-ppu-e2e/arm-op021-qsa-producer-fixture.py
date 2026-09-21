#!/usr/bin/env python3
"""Create a unique, bounded one-shot op-021 capture arm."""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prefill", "mixed"))
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--sample-id")
    parser.add_argument("--expected-qsa-sha256", required=True)
    args = parser.parse_args()
    root = args.output_dir.resolve()
    if root.exists():
        raise SystemExit(f"refusing to reuse output directory: {root}")
    root.mkdir(parents=True)
    minimum, maximum = ((1, 1) if args.phase == "prefill" else (2, 64))
    sample_id = args.sample_id or f"op021-p4k-{args.phase}-producer-001"
    arm = {
        "schema_version": 1,
        "experiment_id": "op-021",
        "sample_id": sample_id,
        "expected_phase": args.phase,
        "expected_rows": 4096,
        "expected_compress_ratio": 4,
        "expected_cache_page_size": 1600,
        "min_request_runs": minimum,
        "max_request_runs": maximum,
        "max_cache_pages": 1250,
        "max_total_bytes": 64 * 1024 * 1024,
        "provenance": {
            "expected_qsa_sha256": args.expected_qsa_sha256,
            "scope": "isolated eager synthetic P4K diagnostic; timing invalid",
        },
    }
    path = root / "arm.json"
    path.write_text(json.dumps(arm, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
