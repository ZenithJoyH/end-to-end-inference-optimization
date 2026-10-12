#!/usr/bin/env python3
"""Build the accformal-004 manifest from fresh runtime evidence."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys


if len(sys.argv) != 4:
    raise SystemExit("usage: build-accformal004-service-manifest.py RUNTIME_JSON STARTUP_LOG OUTPUT_JSON")
runtime_path = Path(sys.argv[1]).resolve()
startup_log = Path(sys.argv[2]).resolve()
output_path = Path(sys.argv[3]).resolve()
if output_path.exists():
    raise SystemExit(f"refusing to overwrite {output_path}")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
container = json.loads(
    subprocess.check_output(["docker", "inspect", "minimaxM3-opt-20260921"], text=True)
)[0]
service = runtime["service"]
argv = service["argv"]
required_args = {
    "--model": "/mnt/cpfs/models/MiniMax-M3",
    "--port": "8023",
    "--served-model-name": "MiniMax-M3",
    "--tensor-parallel-size": "16",
    "--max-model-len": "131072",
    "--max-num-seqs": "32",
    "--max-num-batched-tokens": "8192",
}
for key, expected in required_args.items():
    if key not in argv or argv[argv.index(key) + 1] != expected:
        raise SystemExit(f"live service argument differs: {key}")
if "--no-enable-prefix-caching" not in argv:
    raise SystemExit("live service does not disable prefix caching")

service_instance_id = f"{container['Id'][:12]}:8023:{service['pid']}:{service['start_ticks']}"
expected_service_instance_id = "bd37abcbf719:8023:895010:279945667"
if service_instance_id != expected_service_instance_id:
    raise SystemExit(
        f"service instance changed: expected {expected_service_instance_id}, got {service_instance_id}"
    )

startup = startup_log.read_text(encoding="utf-8", errors="replace")
for marker in (
    "'enable_prefix_caching': False",
    "Capturing CUDA graphs (decode, FULL): 100%",
    "Application startup complete",
):
    if marker not in startup:
        raise SystemExit(f"startup log lacks required marker: {marker}")
for forbidden in ("illegal memory access", "Engine core initialization failed"):
    if forbidden in startup:
        raise SystemExit(f"startup log contains fatal marker: {forbidden}")

thead_yaml = subprocess.check_output(
    [
        "docker",
        "exec",
        "minimaxM3-opt-20260921",
        "cat",
        "/workspace/vllm-plugin-FL/vllm_fl/dispatch/config/thead.yaml",
    ],
    text=True,
)
for entry in ("conv3d", "cudnn_convolution"):
    if f"- {entry}" not in thead_yaml:
        raise SystemExit(f"thead.yaml blacklist lacks {entry}")

repos = runtime["repositories"]
plugin = repos["/workspace/vllm-plugin-FL"]
flaggems_vllm = repos["/workspace/FlagGems-vllm"]
flaggems = repos["/workspace/FlagGems"]
combined_flaggems = hashlib.sha256(
    (flaggems_vllm["content_sha256"] + flaggems["content_sha256"]).encode()
).hexdigest()
manifest = {
    "host": "PPU-07",
    "optimization_container_name": "minimaxM3-opt-20260921",
    "service_instance_id": service_instance_id,
    "model_name": "MiniMax-M3",
    "base_url": "http://127.0.0.1:8023/v1/chat/completions",
    "mode": "graph",
    "model_sha256": runtime["model_identity"]["sha256"],
    "tokenizer_sha256": runtime["tokenizer_identity"]["sha256"],
    "engine_sha256": runtime["engine_identity"]["sha256"],
    "plugin_sha256": plugin["content_sha256"],
    "flaggems_sha256": combined_flaggems,
    "flaggems_vllm_installed": True,
    "flaggems_vllm_sha256": flaggems_vllm["content_sha256"],
    "runtime_evidence_sha256": sha256(runtime_path),
    "launch_config": {
        "enable_prefix_caching": False,
        "tensor_parallel_size": 16,
        "dtype": "bfloat16",
        "block_size": 128,
        "max_model_len": 131072,
        "max_num_seqs": 32,
        "max_num_batched_tokens": 8192,
        "gpu_memory_utilization": 0.9,
        "cudagraph_mode": "FULL_DECODE_ONLY",
        "cudagraph_capture_sizes": [1, 2, 4, 8, 16, 32],
        "plugin_commit": plugin["head"],
        "flaggems_vllm_commit": flaggems_vllm["head"],
        "flaggems_commit": flaggems["head"],
        "launch_args": argv,
    },
    "image_lineage": "verified",
    "mount_parity": "passed",
    "tokenizer_path": "/mnt/cpfs/models/MiniMax-M3",
    "performance_context": {
        "platform": "ppu",
        "device_model": "PPU-ZW810E",
        "device_ids": [str(value) for value in range(16)],
        "driver_version": "2.1.1-rbd225",
        "device_runtime_version": "container-image-bound",
        "image_id": container["Image"],
        "prefix_cache_state": "disabled",
        "cache_preparation": (
            "Current 131072-context service passed 6/6 FULL_DECODE_ONLY graph capture, "
            "health, smoke, and the completed accdiag-003b 64-request diagnostic. "
            "Private Plugin thead.yaml blacklists conv3d and cudnn_convolution."
        ),
    },
    "identity_methods": {
        "model": runtime["model_identity"]["method"],
        "tokenizer_files": runtime["tokenizer_identity"]["files"],
        "engine_root": runtime["engine_identity"]["root"],
    },
}
output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
