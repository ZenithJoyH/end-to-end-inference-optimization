#!/usr/bin/env python3
"""Bind the P16K performance manifest to the freshly started Hy4 service."""

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def parse_evidence(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator:
            values[key] = value
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--runtime-evidence", type=Path, required=True)
    parser.add_argument("--plugin-sha256", required=True)
    parser.add_argument("--flaggems-vllm-sha256", required=True)
    parser.add_argument("--flaggems-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    evidence = parse_evidence(args.runtime_evidence)
    required = ("container_id", "container_api_pid", "api_starttime_ticks")
    missing = [key for key in required if not evidence.get(key)]
    if missing:
        raise RuntimeError(f"runtime evidence missing: {missing}")

    data = json.loads(args.base.read_text(encoding="utf-8"))
    data["service_instance_id"] = ":".join(evidence[key] for key in required)
    data["runtime_evidence_sha256"] = sha256(args.runtime_evidence)
    data["plugin_sha256"] = args.plugin_sha256
    data["flaggems_vllm_sha256"] = args.flaggems_vllm_sha256
    data["flaggems_sha256"] = args.flaggems_sha256
    data["performance_context"]["device_ids"] = list(range(16))
    data["performance_context"]["cache_preparation"] = (
        "Prefix caching is disabled in the exact service process arguments and "
        "startup log; one maintained-runner warmup round is excluded."
    )
    args.output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
