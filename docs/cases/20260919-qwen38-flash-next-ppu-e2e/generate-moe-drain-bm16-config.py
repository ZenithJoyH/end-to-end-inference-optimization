#!/usr/bin/env python3
"""Create an exact four-key MoE config derived from the retained M64 table."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


CASE_ROOT = Path(
    "/mnt/nfs/users/jinghao/qwen3.8-flash/"
    "20260919-qwen38-flash-next-ppu-e2e"
)
SOURCE = CASE_ROOT / "configs/moe-bm16-decode-only-01/E=512,N=80,device_name=thead.json"
TARGET_DIR = CASE_ROOT / "configs/moe-bm16-decode-drain-02"
TARGET = TARGET_DIR / SOURCE.name
SUMMARY = TARGET_DIR / "config-summary.json"
EXPECTED_SOURCE_SHA256 = "c695793cb283b8d48782d2b0bf5aa6ff54c03c4b8d9251f776bcfdb8833c3e18"
KEYS = (40, 48, 56, 63)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if sha256(SOURCE) != EXPECTED_SOURCE_SHA256:
        raise SystemExit("source config hash changed")
    if TARGET_DIR.exists():
        raise SystemExit(f"target already exists: {TARGET_DIR}")
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    candidate = json.loads(json.dumps(source))
    changes = []
    for value in KEYS:
        key = str(value)
        before = dict(candidate[key])
        if before["BLOCK_SIZE_M"] != 32:
            raise SystemExit(f"unexpected source BLOCK_SIZE_M for M={value}: {before}")
        after = dict(before)
        after["BLOCK_SIZE_M"] = 16
        candidate[key] = after
        changed = sorted(name for name in before if before[name] != after[name])
        if changed != ["BLOCK_SIZE_M"]:
            raise SystemExit(f"unexpected change set for M={value}: {changed}")
        changes.append({"M": value, "before": before, "after": after})

    if candidate["64"] != source["64"] or candidate["32"] != source["32"]:
        raise SystemExit("existing M64/M32 retained configs changed")
    observed = [
        key
        for key in source
        if source[key] != candidate[key]
    ]
    if observed != [str(value) for value in KEYS]:
        raise SystemExit(f"unexpected changed keys: {observed}")

    TARGET_DIR.mkdir(parents=True, exist_ok=False)
    TARGET.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload = {
        "schema_version": 1,
        "parent_path": str(SOURCE),
        "parent_sha256": EXPECTED_SOURCE_SHA256,
        "candidate_path": str(TARGET),
        "candidate_sha256": sha256(TARGET),
        "changed_keys": list(KEYS),
        "changed_fields": ["BLOCK_SIZE_M"],
        "changes": changes,
        "microbench_evidence": str(
            CASE_ROOT / "microbench/fused-moe-drain-batch-002/result.json"
        ),
    }
    SUMMARY.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
