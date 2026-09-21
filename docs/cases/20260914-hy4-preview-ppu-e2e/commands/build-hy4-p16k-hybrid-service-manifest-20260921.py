#!/usr/bin/env python3
"""Bind the cached-prefill sparse-MLA toggle to a fresh service manifest."""

import argparse
import hashlib
import json
from pathlib import Path


ENV_NAME = "VLLM_FL_THEAD_CACHED_PREFILL_SPARSE_MLA_HYBRID"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence(path: Path) -> dict[str, str]:
    return dict(
        line.split("=", 1)
        for line in path.read_text(encoding="utf-8").splitlines()
        if "=" in line
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--runtime-evidence", type=Path, required=True)
    parser.add_argument("--plugin-sha256", required=True)
    parser.add_argument("--flaggems-vllm-sha256", required=True)
    parser.add_argument("--flaggems-sha256", required=True)
    parser.add_argument("--hybrid-enabled", choices=("0", "1"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    runtime = evidence(args.runtime_evidence)
    keys = ("container_id", "container_api_pid", "api_starttime_ticks")
    if any(not runtime.get(key) for key in keys):
        raise RuntimeError("runtime evidence is incomplete")

    data = json.loads(args.base.read_text(encoding="utf-8"))
    data["service_instance_id"] = ":".join(runtime[key] for key in keys)
    data["runtime_evidence_sha256"] = file_sha256(args.runtime_evidence)
    data["plugin_sha256"] = args.plugin_sha256
    data["flaggems_vllm_sha256"] = args.flaggems_vllm_sha256
    data["flaggems_sha256"] = args.flaggems_sha256

    launch = data["launch_config"]
    launch["max_num_batched_tokens"] = 2048
    launch["max_num_partial_prefills"] = 1
    launch["max_long_partial_prefills"] = 1
    launch["long_prefill_token_threshold"] = 0
    launch["environment"] = {ENV_NAME: args.hybrid_enabled}
    launch["launch_args"] = [
        "--served-model-name=hy4",
        "--port=8010",
        "--trust-remote-code",
        "--reasoning-parser=hy_v4",
        "--tensor-parallel-size=16",
        "--max-model-len=100000",
        "--max-num-batched-tokens=2048",
        "--max-num-partial-prefills=1",
        "--max-long-partial-prefills=1",
        "--long-prefill-token-threshold=0",
        "--no-enable-prefix-caching",
        '--compilation-config={"cudagraph_mode":"FULL_DECODE_ONLY"}',
    ]
    data["performance_context"]["device_ids"] = [str(index) for index in range(16)]
    data["performance_context"]["cache_preparation"] = (
        "Prefix caching is disabled; one warmup round is excluded for each "
        "isolated service instance."
    )
    args.output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
