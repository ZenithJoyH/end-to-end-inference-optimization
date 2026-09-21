#!/usr/bin/env python3
"""Create a comparison-safe service manifest for the mm provider experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


STABLE_KEYS = (
    "host",
    "optimization_container_name",
    "service_instance_id",
    "model_name",
    "base_url",
    "mode",
    "model_sha256",
    "tokenizer_sha256",
    "engine_sha256",
    "plugin_sha256",
    "flaggems_sha256",
    "flaggems_vllm_sha256",
    "runtime_evidence_sha256",
    "image_lineage",
    "mount_parity",
    "tokenizer_path",
)
ENVIRONMENT_KEYS = (
    "CUDA_VISIBLE_DEVICES",
    "VLLM_WORKER_MULTIPROC_METHOD",
    "VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS",
    "GLOO_SOCKET_IFNAME",
    "NCCL_IB_HCA",
    "NCCL_IB_GID_INDEX",
    "NCCL_IB_ADDR_FAMILY",
    "NCCL_SOCKET_IFNAME",
    "NCCL_SOCKET_FAMILY",
    "VLLM_FL_FLAGOS_BLACKLIST_APPEND",
    "VLLM_TUNED_CONFIG_FOLDER",
    "VLLM_FL_QSA_STATIC_SCORE_COLUMNS",
    "PATH",
    "LD_LIBRARY_PATH",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("expected_blacklist")
    args = parser.parse_args()

    source = json.loads(args.source.read_text(encoding="utf-8"))
    missing = [key for key in STABLE_KEYS if key not in source]
    if missing:
        raise SystemExit(f"source manifest missing keys: {missing}")
    launch = source.get("launch_config")
    if not isinstance(launch, dict) or not isinstance(launch.get("launch_args"), list):
        raise SystemExit("source manifest has no launch_config.launch_args")
    launch_args = list(launch["launch_args"])
    required = {
        "--max-num-seqs": "64",
        "--max-num-batched-tokens": "4096",
    }
    for option, value in required.items():
        if launch_args.count(option) != 1 or launch_args[launch_args.index(option) + 1] != value:
            raise SystemExit(f"unexpected launch argument: {option}")
    if launch_args.count("--no-enable-prefix-caching") != 1:
        raise SystemExit("prefix caching is not explicitly disabled")

    environment = launch.get("selected_environment")
    if not isinstance(environment, dict):
        raise SystemExit("source manifest has no selected_environment")
    if set(environment) != set(ENVIRONMENT_KEYS):
        raise SystemExit(
            "selected_environment key drift: "
            f"missing={sorted(set(ENVIRONMENT_KEYS) - set(environment))} "
            f"extra={sorted(set(environment) - set(ENVIRONMENT_KEYS))}"
        )
    if environment["VLLM_FL_FLAGOS_BLACKLIST_APPEND"] != args.expected_blacklist:
        raise SystemExit("source manifest has unexpected FlagGems blacklist")

    context = source.get("performance_context")
    if not isinstance(context, dict) or context.get("device_ids") != [
        str(item) for item in range(8, 16)
    ]:
        raise SystemExit("comparison service must use exactly PPU 8-15")

    normalized = {key: source[key] for key in STABLE_KEYS}
    normalized["launch_config"] = {
        "enable_prefix_caching": False,
        "max_num_seqs": 64,
        "max_num_batched_tokens": 4096,
        "qsa_static_score_columns": 8448,
        "selected_environment": {
            key: environment[key] for key in ENVIRONMENT_KEYS
        },
        "launch_args": launch_args,
    }
    normalized["performance_context"] = context
    if args.destination.exists():
        raise SystemExit(f"refusing to overwrite {args.destination}")
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    args.destination.write_text(
        json.dumps(normalized, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
