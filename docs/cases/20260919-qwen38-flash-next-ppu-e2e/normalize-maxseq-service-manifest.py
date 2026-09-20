#!/usr/bin/env python3
"""Create a comparison-safe service manifest for the max-num-seqs experiment."""

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
    "runtime_evidence_sha256",
    "image_lineage",
    "mount_parity",
    "tokenizer_path",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("max_num_seqs", type=int, choices=(32, 48, 64))
    parser.add_argument(
        "max_num_batched_tokens", type=int, choices=(2048, 4096), nargs="?", default=4096
    )
    args = parser.parse_args()

    source = json.loads(args.source.read_text(encoding="utf-8"))
    missing = [key for key in STABLE_KEYS if key not in source]
    if missing:
        raise SystemExit(f"source manifest missing keys: {missing}")
    launch = source.get("launch_config")
    if not isinstance(launch, dict) or not isinstance(launch.get("launch_args"), list):
        raise SystemExit("source manifest has no launch_config.launch_args")
    launch_args = list(launch["launch_args"])
    if launch_args.count("--max-num-seqs") != 1:
        raise SystemExit("expected one --max-num-seqs argument")
    index = launch_args.index("--max-num-seqs")
    if index != 17:
        raise SystemExit(f"unexpected --max-num-seqs position: {index}")
    if index + 1 >= len(launch_args) or launch_args[index + 1] != str(args.max_num_seqs):
        raise SystemExit("max-num-seqs argument differs from requested normalization")
    if launch_args.count("--max-num-batched-tokens") != 1:
        raise SystemExit("expected one --max-num-batched-tokens argument")
    batched_index = launch_args.index("--max-num-batched-tokens")
    max_num_batched_tokens = int(launch_args[batched_index + 1])
    if max_num_batched_tokens != args.max_num_batched_tokens:
        raise SystemExit("max-num-batched-tokens differs from requested normalization")
    if launch_args.count("--no-enable-prefix-caching") != 1:
        raise SystemExit("prefix caching is not explicitly disabled")
    if "--enable-prefix-caching" in launch_args:
        raise SystemExit("conflicting prefix-cache enable flag is present")

    context = source.get("performance_context")
    if not isinstance(context, dict) or not isinstance(context.get("device_ids"), list):
        raise SystemExit("source manifest has no performance_context.device_ids")
    normalized_context = dict(context)
    normalized_context["device_ids"] = [str(item) for item in context["device_ids"]]
    if normalized_context["device_ids"] != [str(item) for item in range(8, 16)]:
        raise SystemExit("comparison service must use exactly PPU 8-15")

    normalized = {key: source[key] for key in STABLE_KEYS}
    normalized["launch_config"] = {
        "enable_prefix_caching": False,
        "max_num_seqs": args.max_num_seqs,
        "max_num_batched_tokens": max_num_batched_tokens,
        "launch_args": launch_args,
    }
    normalized["performance_context"] = normalized_context
    if args.destination.exists():
        raise SystemExit(f"refusing to overwrite {args.destination}")
    args.destination.write_text(
        json.dumps(normalized, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
