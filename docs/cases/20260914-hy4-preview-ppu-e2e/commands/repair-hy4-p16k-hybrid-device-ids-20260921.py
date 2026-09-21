#!/usr/bin/env python3
"""Derive comparator-valid records without overwriting measured P16K evidence."""

import copy
import hashlib
import json
from pathlib import Path


RUN_ROOT = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e/results/performance/"
    "20260921-p16k-d128-c16-n16-cached-prefill-hybrid-01"
)
LABELS = ("baseline", "candidate", "revert")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path: Path, payload: dict) -> None:
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    expected_ids = list(range(16))
    repaired_ids = [str(index) for index in expected_ids]
    for label in LABELS:
        run_dir = RUN_ROOT / "runs" / f"{label}-01"
        source_record_path = run_dir / "run-record.json"
        source_record = json.loads(source_record_path.read_text(encoding="utf-8"))
        service_ref = source_record["artifacts"]["service"]
        source_service_path = Path(service_ref["path"])
        if sha256(source_service_path) != service_ref["sha256"]:
            raise RuntimeError(f"source service hash mismatch: {label}")

        service = json.loads(source_service_path.read_text(encoding="utf-8"))
        if service["performance_context"]["device_ids"] != expected_ids:
            raise RuntimeError(f"unexpected source device IDs: {label}")
        repaired_service = copy.deepcopy(service)
        repaired_service["performance_context"]["device_ids"] = repaired_ids
        repaired_service_path = run_dir / "service-device-id-repaired.json"
        write_new(repaired_service_path, repaired_service)

        repaired_record = copy.deepcopy(source_record)
        repaired_record["artifacts"]["service"] = {
            "path": str(repaired_service_path),
            "sha256": sha256(repaired_service_path),
        }
        repaired_record["metadata_repair"] = {
            "field": "/performance_context/device_ids",
            "operation": "lossless integer-to-decimal-string conversion",
            "source_run_record": {
                "path": str(source_record_path),
                "sha256": sha256(source_record_path),
            },
            "source_service": {
                "path": str(source_service_path),
                "sha256": sha256(source_service_path),
            },
        }
        repaired_record_path = run_dir / "run-record-device-id-repaired.json"
        write_new(repaired_record_path, repaired_record)
        print(repaired_record_path)


if __name__ == "__main__":
    main()
