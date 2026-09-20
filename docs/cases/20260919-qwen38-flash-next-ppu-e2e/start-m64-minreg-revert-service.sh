#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-20260919
expected_container_id=2eafbddebde1b14c691173de29d1965bc48064829a86ee4150056ef1fc5297f7
source_manifest=${case_root}/manifests/candidate-maxseq64-bt4096-moe-bm16-service-comparison-10.json
config_dir=${case_root}/configs/moe-bm16-decode-only-01
service_label=${1:-m64-minreg-revert-service-11}
manifest_name=${2:-baseline-maxseq64-bt4096-m64-minreg-revert-service-11.json}
use_tuned_config=${3:-0}
case "${use_tuned_config}" in 0|1) ;; *) echo "invalid tuned config flag" >&2; exit 2;; esac
run_dir=${case_root}/transitions/${service_label}
service_log=${run_dir}/${service_label}-8020.live.log
startup_log=${run_dir}/${service_label}-8020.startup.log
after_process=${run_dir}/after-process.json
manifest=${case_root}/manifests/${manifest_name}
expected_tracked=${case_root}/transitions/m64-minreg-revert-service-11/qwen3.8-flash-opt-20260919.tracked-imports.sha256

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test -f "${source_manifest}"
test -f "${expected_tracked}"
test -f "${config_dir}/E=512,N=80,device_name=thead.json"
test ! -e "${run_dir}"
test ! -e "${manifest}"
if ss -ltnH 'sport = :8020' | grep -q .; then
  echo "port 8020 is already in use" >&2
  exit 3
fi
if docker exec "${container}" pgrep -f 'vllm serve /mnt/cpfs/models/Qwen3.8-Flash-Next' >/dev/null 2>&1; then
  echo "revert container already has a model service" >&2
  exit 4
fi
mkdir "${run_dir}"

docker exec -i "${container}" python3 - "${run_dir}/${container}.tracked-imports.sha256" <<'PY'
import hashlib
import os
import subprocess
import sys
from pathlib import Path

output = Path(sys.argv[1])
roots = (
    "/workspace/vllm-plugin-FL-qwen38-adaptation",
    "/workspace/FlagGems-vllm",
    "/workspace/FlagGems",
)
digest = hashlib.sha256()
for root in roots:
    tracked = subprocess.check_output(["git", "-C", root, "ls-files", "-c", "-z"])
    for rel in sorted(value for value in tracked.split(b"\0") if value):
        digest.update(root.encode() + b"\0" + rel + b"\0")
        digest.update(hashlib.sha256((Path(root) / os.fsdecode(rel)).read_bytes()).digest())
output.write_text(digest.hexdigest() + "\n", encoding="utf-8")
PY
cmp "${run_dir}/${container}.tracked-imports.sha256" "${expected_tracked}"

moe_env_args=()
if test "${use_tuned_config}" -eq 1; then
  moe_env_args=(-e "VLLM_TUNED_CONFIG_FOLDER=${config_dir}")
fi

docker exec -d \
  "${moe_env_args[@]}" \
  -e CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
  -e VLLM_WORKER_MULTIPROC_METHOD=spawn \
  -e VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=1800 \
  -e GLOO_SOCKET_IFNAME=eth0 \
  -e NCCL_IB_HCA=fic2_soe_bond \
  -e NCCL_IB_GID_INDEX=1 \
  -e NCCL_IB_ADDR_FAMILY=6 \
  -e NCCL_SOCKET_IFNAME=bond \
  -e NCCL_SOCKET_FAMILY=AF_INET6 \
  -e VLLM_FL_FLAGOS_BLACKLIST_APPEND=_conv_depthwise2d,index,normal_ \
  -w "${case_root}" \
  "${container}" bash -lc "
set -e
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:\${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}
exec vllm serve /mnt/cpfs/models/Qwen3.8-Flash-Next \
  --served-model-name Qwen3.8-Flash-Next \
  --host 0.0.0.0 \
  --port 8020 \
  --tensor-parallel-size 8 \
  --pipeline-parallel-size 1 \
  --dtype bfloat16 \
  --language-model-only \
  --max-model-len 80000 \
  --max-num-seqs 64 \
  --max-num-batched-tokens 4096 \
  --gpu-memory-utilization 0.90 \
  --disable-custom-all-reduce \
  --reasoning-parser qwen3 \
  --no-enable-prefix-caching \
  --compilation-config '{\"cudagraph_mode\":\"FULL_AND_PIECEWISE\"}' \
  > '${service_log}' 2>&1
"

docker exec -i "${container}" python3 - "${after_process}" "${use_tuned_config}" "${config_dir}" <<'PY'
import json
import os
import sys
import time
from pathlib import Path

output = sys.argv[1]
use_tuned_config = bool(int(sys.argv[2]))
config_dir = sys.argv[3]
model = "/mnt/cpfs/models/Qwen3.8-Flash-Next"
expected_launch = [
    "serve", model, "--served-model-name", "Qwen3.8-Flash-Next",
    "--host", "0.0.0.0", "--port", "8020", "--tensor-parallel-size", "8",
    "--pipeline-parallel-size", "1", "--dtype", "bfloat16",
    "--language-model-only", "--max-model-len", "80000", "--max-num-seqs", "64",
    "--max-num-batched-tokens", "4096", "--gpu-memory-utilization", "0.90",
    "--disable-custom-all-reduce", "--reasoning-parser", "qwen3",
    "--no-enable-prefix-caching", "--compilation-config",
    '{"cudagraph_mode":"FULL_AND_PIECEWISE"}',
]
env_keys = (
    "CUDA_VISIBLE_DEVICES", "VLLM_WORKER_MULTIPROC_METHOD",
    "VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS", "GLOO_SOCKET_IFNAME", "NCCL_IB_HCA",
    "NCCL_IB_GID_INDEX", "NCCL_IB_ADDR_FAMILY", "NCCL_SOCKET_IFNAME",
    "NCCL_SOCKET_FAMILY", "VLLM_FL_FLAGOS_BLACKLIST_APPEND",
    "VLLM_TUNED_CONFIG_FOLDER",
)

def proc_args(pid):
    return [value.decode(errors="replace") for value in open(
        f"/proc/{pid}/cmdline", "rb").read().split(b"\0") if value]

def start_ticks(pid):
    raw = open(f"/proc/{pid}/stat", encoding="utf-8").read()
    return int(raw[raw.rfind(")") + 2:].split()[19])

deadline = time.monotonic() + 120
while True:
    matches = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            argv = proc_args(entry)
            ticks = start_ticks(entry)
        except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
            continue
        index = next((i for i, value in enumerate(argv) if os.path.basename(value) == "vllm"), None)
        if index is not None and argv[index + 1:] == expected_launch:
            matches.append({"pid": int(entry), "args": argv, "start_ticks": ticks})
    if len(matches) == 1:
        service = matches[0]
        break
    if len(matches) > 1:
        raise SystemExit(f"multiple exact services found: {matches}")
    if time.monotonic() >= deadline:
        raise SystemExit("exact revert service did not appear")
    time.sleep(1)

environment = {}
for item in open(f"/proc/{service['pid']}/environ", "rb").read().split(b"\0"):
    if b"=" not in item:
        continue
    key, value = item.split(b"=", 1)
    name = key.decode(errors="replace")
    if name in env_keys:
        environment[name] = value.decode(errors="replace")
service["selected_environment"] = environment
service["launch_args"] = expected_launch
expected_config = config_dir if use_tuned_config else None
if environment.get("VLLM_TUNED_CONFIG_FOLDER") != expected_config:
    raise SystemExit("revert MoE tuned-config environment does not match request")
Path(output).write_text(json.dumps(service, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

ready=0
for _ in $(seq 1 360); do
  if timeout 5s curl -fsS http://127.0.0.1:8020/v1/models >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 5
done
test "${ready}" -eq 1
grep -F 'enable_prefix_caching=False' "${service_log}" >/dev/null
grep -F 'Asynchronous scheduling is enabled.' "${service_log}" >/dev/null
grep -F 'Capturing CUDA graphs (decode, FULL): 100%' "${service_log}" >/dev/null
grep -F 'Application startup complete' "${service_log}" >/dev/null
if test "${use_tuned_config}" -eq 1; then
  grep -F "Using configuration from ${config_dir}/E=512,N=80,device_name=thead.json for MoE layer." "${service_log}" >/dev/null
else
  if grep -F 'Using configuration from' "${service_log}" | grep -F 'E=512,N=80,device_name=thead.json' >/dev/null; then
    echo "revert service unexpectedly loaded an external MoE config" >&2
    exit 5
  fi
fi
cp -- "${service_log}" "${startup_log}"

python3 - "${source_manifest}" "${after_process}" "${startup_log}" "${manifest}" "${use_tuned_config}" "${config_dir}" "${service_label}" <<'PY'
import hashlib
import json
import subprocess
import sys
from pathlib import Path

source_path, process_path, startup_path, output_path, use_tuned_config, config_dir, service_label = sys.argv[1:]
use_tuned_config = bool(int(use_tuned_config))
source = json.load(open(source_path, encoding="utf-8"))
process = json.load(open(process_path, encoding="utf-8"))
container = json.loads(subprocess.check_output(
    ["docker", "inspect", "qwen3.8-flash-opt-20260919"], text=True))[0]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

instance_id = f"{container['Id'][:12]}-8020-{process['pid']}-{process['start_ticks']}"
manifest = {
    key: source[key]
    for key in (
        "host", "model_name", "mode", "model_sha256", "tokenizer_sha256",
        "engine_sha256", "image_lineage", "mount_parity", "tokenizer_path",
    )
}
manifest.update({
    "schema_version": 1,
    "optimization_container_name": "qwen3.8-flash-opt-20260919",
    "base_url": "http://127.0.0.1:8020/v1/completions",
    "service_instance_id": instance_id,
    "runtime_evidence_sha256": sha(process_path),
    "plugin_sha256": source["plugin_sha256"],
    "flaggems_vllm_sha256": source["flaggems_vllm_sha256"],
    "flaggems_sha256": source["flaggems_sha256"],
    "launch_config": {
        "enable_prefix_caching": False,
        "max_num_seqs": 64,
        "max_num_batched_tokens": 4096,
        "moe_tuned_config_folder": config_dir if use_tuned_config else None,
        "launch_args": process["launch_args"],
    },
    "performance_context": {
        **source["performance_context"],
        "device_ids": [str(value) for value in range(8)],
    },
    "evidence": {
        "role": service_label,
        "process_path": process_path,
        "startup_log_path": startup_path,
        "startup_log_sha256": sha(startup_path),
        "tracked_imports_parity_path": str(Path(process_path).parent / "qwen3.8-flash-opt-20260919.tracked-imports.sha256"),
    },
})
Path(output_path).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

python3 "${case_root}/commands/performance/verify-live-service-manifest.py" \
  "${manifest}" "${container}" 8020 64
sha256sum "${run_dir}"/*.sha256 "${after_process}" "${startup_log}" "${manifest}"
