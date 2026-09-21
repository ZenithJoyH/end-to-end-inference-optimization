#!/usr/bin/env python3
"""Bind one P16K scheduler configuration to a fresh Hy4 service manifest."""

import argparse
import hashlib
import json
from pathlib import Path


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
    parser.add_argument("--max-num-batched-tokens", type=int, required=True)
    parser.add_argument("--max-num-partial-prefills", type=int, required=True)
    parser.add_argument("--max-long-partial-prefills", type=int, required=True)
    parser.add_argument("--long-prefill-token-threshold", type=int, required=True)
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
    launch["max_num_batched_tokens"] = args.max_num_batched_tokens
    launch["max_num_partial_prefills"] = args.max_num_partial_prefills
    launch["max_long_partial_prefills"] = args.max_long_partial_prefills
    launch["long_prefill_token_threshold"] = args.long_prefill_token_threshold
    launch["launch_args"] = [
        "--served-model-name=hy4",
        "--port=8010",
        "--trust-remote-code",
        "--reasoning-parser=hy_v4",
        "--tensor-parallel-size=16",
        "--max-model-len=100000",
        f"--max-num-batched-tokens={args.max_num_batched_tokens}",
        f"--max-num-partial-prefills={args.max_num_partial_prefills}",
        f"--max-long-partial-prefills={args.max_long_partial_prefills}",
        f"--long-prefill-token-threshold={args.long_prefill_token_threshold}",
        "--no-enable-prefix-caching",
        '--compilation-config={"cudagraph_mode":"FULL_DECODE_ONLY"}',
    ]
    data["performance_context"]["device_ids"] = list(range(16))
    data["performance_context"]["cache_preparation"] = (
        "Prefix caching is disabled in exact process arguments and startup log; "
        "one warmup round is excluded for this scheduler configuration."
    )
    args.output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
