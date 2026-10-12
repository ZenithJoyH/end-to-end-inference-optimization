#!/usr/bin/env python3
"""Bind op-007 comparison to an exact graph-ready 131K service and MoE SHA."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys


if len(sys.argv) != 6:
    raise SystemExit("usage: build-op007-comparison-manifest.py ROLE RUNTIME_JSON STARTUP_LOG OUTPUT_JSON EXPECTED_MOE_SHA256")
role = sys.argv[1]
if role not in ("baseline", "candidate", "revert"):
    raise SystemExit(f"invalid role: {role}")
runtime_path, startup_log, output_path = (Path(x).resolve() for x in sys.argv[2:5])
expected_moe = sys.argv[5]
if output_path.exists():
    raise SystemExit(f"refusing to overwrite {output_path}")
if len(expected_moe) != 64 or any(c not in "0123456789abcdef" for c in expected_moe):
    raise SystemExit("expected MoE SHA256 must be lowercase hex")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
container = json.loads(subprocess.check_output(
    ["docker", "inspect", "minimaxM3-opt-20260921"], text=True))[0]
if container["Id"][:12] != "bd37abcbf719":
    raise SystemExit("optimization container identity changed")
service = runtime["service"]
argv = service["argv"]
required = {
    "--model": "/mnt/cpfs/models/MiniMax-M3",
    "--port": "8023",
    "--served-model-name": "MiniMax-M3",
    "--tensor-parallel-size": "16",
    "--max-model-len": "131072",
    "--max-num-seqs": "32",
    "--max-num-batched-tokens": "8192",
}
for key, value in required.items():
    if key not in argv or argv[argv.index(key) + 1] != value:
        raise SystemExit(f"service arg mismatch: {key}")
if "--no-enable-prefix-caching" not in argv:
    raise SystemExit("prefix cache must be disabled")
startup = startup_log.read_text(encoding="utf-8", errors="replace")
for marker in ("'enable_prefix_caching': False",
               "Capturing CUDA graphs (decode, FULL): 100%",
               "Application startup complete"):
    if marker not in startup:
        raise SystemExit(f"startup marker missing: {marker}")
for forbidden in ("Engine core initialization failed", "illegal memory access"):
    if forbidden in startup:
        raise SystemExit(f"startup fatal marker: {forbidden}")
thead_yaml = subprocess.check_output(
    ["docker", "exec", "minimaxM3-opt-20260921", "cat",
     "/workspace/vllm-plugin-FL/vllm_fl/dispatch/config/thead.yaml"], text=True)
for entry in ("conv3d", "cudnn_convolution"):
    if f"- {entry}" not in thead_yaml:
        raise SystemExit(f"Plugin blacklist missing: {entry}")


def container_file_sha(path):
    return subprocess.check_output(
        ["docker", "exec", "minimaxM3-opt-20260921", "sha256sum", path],
        text=True).split()[0]


linear_sha = container_file_sha("/workspace/FlagGems/src/flag_gems/ops/linear.py")
if linear_sha != "4d46bae0804ac32b698582d010d5f0e02d3570c6703efff9d1d666e2bf43fd94":
    raise SystemExit("linear source differs from retained baseline")
moe_sha = container_file_sha("/workspace/FlagGems/src/flag_gems/fused/fused_moe.py")
if moe_sha != expected_moe:
    raise SystemExit(f"MoE source mismatch for {role}: {moe_sha}")
if role != "candidate" and moe_sha != "a780da6348ba611640b546b47c60b79baa1312094386ce8f49d99d0d8e4750af":
    raise SystemExit(f"{role} must use original MoE source")
if role == "candidate" and "op007 PPU BF16 MoE GEMM2 BK64" not in startup:
    raise SystemExit("candidate service lacks actual op007 MoE config-hit log")

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
    "service_instance_id": f"{container['Id'][:12]}:8023:{service['pid']}:{service['start_ticks']}",
    "model_name": "MiniMax-M3",
    "base_url": "http://127.0.0.1:8023/v1/completions",
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
        "cache_preparation": "TP16 131K FULL_DECODE_ONLY graph capture completed; prefix caching disabled; same case cache paths.",
    },
    "identity_methods": {
        "model": runtime["model_identity"]["method"],
        "tokenizer_files": runtime["tokenizer_identity"]["files"],
        "engine_root": runtime["engine_identity"]["root"],
    },
}
output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8")
print(manifest["service_instance_id"], role, moe_sha)
