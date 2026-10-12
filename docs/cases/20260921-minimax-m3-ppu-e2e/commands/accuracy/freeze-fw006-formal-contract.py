#!/usr/bin/env python3
"""Freeze the formal GPQA schema-3 contract after provenance capture."""

import hashlib
import json
from pathlib import Path
import sys


if len(sys.argv) != 3:
    raise SystemExit("usage: freeze-fw006-formal-contract.py PROVENANCE_JSON CONTRACT_JSON")
provenance_path = Path(sys.argv[1]).resolve()
contract_path = Path(sys.argv[2]).resolve()
if contract_path.exists():
    raise SystemExit(f"refusing to overwrite {contract_path}")
provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
sha256 = hashlib.sha256(provenance_path.read_bytes()).hexdigest()
contract = {
    "schema_version": 3,
    "task": "gpqa_diamond_generative_cot",
    "metric": "exact_match,strict-match",
    "expected_samples": 198,
    "expected_doc_ids": list(range(198)),
    "dataset_revision": provenance["dataset_revision"],
    "task_provenance": {"path": str(provenance_path), "sha256": sha256},
    "threshold": 0.88,
}
contract_path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
