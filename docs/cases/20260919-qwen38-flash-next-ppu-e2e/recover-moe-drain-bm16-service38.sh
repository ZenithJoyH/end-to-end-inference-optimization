#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
expected_container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
source_manifest=${case_root}/transitions/post-prof-004-restored-op008-service-37/post-prof-004-restored-op008-service-37-raw.json
source_config=${case_root}/configs/moe-bm16-decode-only-01
target_config=${case_root}/configs/moe-bm16-decode-drain-02
run_dir=${case_root}/transitions/moe-drain-bm16-service-38
before_process=${run_dir}/before-process.json
failed_after_process=${run_dir}/after-process.json
after_process=${run_dir}/after-process-recovered.json
service_log=${run_dir}/service-8030.live.log
startup_log=${run_dir}/service-8030.startup.log
smoke=${run_dir}/graph-replay-smoke.json
ppu_snapshot=${run_dir}/host-ppu-smi.after-launch.txt
recovery=${run_dir}/recovery-evidence.json
raw_manifest=${run_dir}/moe-drain-bm16-service-38-raw.json

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
test -s "${before_process}"
test -f "${failed_after_process}"
test ! -s "${failed_after_process}"
test -f "${service_log}"
test ! -e "${after_process}"
test ! -e "${raw_manifest}"

docker exec -i "${container}" python3 - "${after_process}" "${target_config}" <<'PY'
import json
import os
import sys
import time

output, target_config = sys.argv[1:]
model = "/mnt/cpfs/models/Qwen3.8-Flash-Next"
expected_launch = [
    "serve", model, "--served-model-name", "Qwen3.8-Flash-Next", "--host", "0.0.0.0",
    "--port", "8030", "--tensor-parallel-size", "8", "--pipeline-parallel-size", "1",
    "--dtype", "bfloat16", "--language-model-only", "--max-model-len", "80000",
    "--max-num-seqs", "64", "--max-num-batched-tokens", "4096",
    "--gpu-memory-utilization", "0.90", "--disable-custom-all-reduce",
    "--reasoning-parser", "qwen3", "--no-enable-prefix-caching", "--compilation-config",
    '{"cudagraph_mode":"FULL_AND_PIECEWISE"}',
]
env_keys = {
    "CUDA_VISIBLE_DEVICES", "VLLM_WORKER_MULTIPROC_METHOD",
    "VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS", "GLOO_SOCKET_IFNAME", "NCCL_IB_HCA",
    "NCCL_IB_GID_INDEX", "NCCL_IB_ADDR_FAMILY", "NCCL_SOCKET_IFNAME",
    "NCCL_SOCKET_FAMILY", "VLLM_FL_FLAGOS_BLACKLIST_APPEND",
    "VLLM_TUNED_CONFIG_FOLDER", "VLLM_FL_QSA_STATIC_SCORE_COLUMNS", "PATH",
    "LD_LIBRARY_PATH",
}

def snap(pid):
    raw = open(f"/proc/{pid}/stat", encoding="utf-8").read()
    tail = raw[raw.rfind(")") + 2:].split()
    args = [value.decode(errors="replace") for value in open(
        f"/proc/{pid}/cmdline", "rb").read().split(b"\0") if value]
    return {"pid": pid, "ppid": int(tail[1]), "start_ticks": int(tail[19]), "args": args}

deadline = time.monotonic() + 120
while True:
    processes = {}
    matches = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            item = snap(int(entry))
        except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
            continue
        processes[item["pid"]] = item
        args = item["args"]
        index = next((i for i, value in enumerate(args) if os.path.basename(value) == "vllm"), None)
        if index is not None and args[index + 1:] == expected_launch:
            matches.append(item)
    if len(matches) == 1:
        service = dict(matches[0])
        break
    if len(matches) > 1:
        raise SystemExit(f"multiple exact candidate services: {matches}")
    if time.monotonic() >= deadline:
        raise SystemExit("candidate service did not appear")
    time.sleep(1)

environment = {}
for item in open(f"/proc/{service['pid']}/environ", "rb").read().split(b"\0"):
    if b"=" in item:
        key, value = item.split(b"=", 1)
        name = key.decode(errors="replace")
        if name in env_keys:
            environment[name] = value.decode(errors="replace")
if environment.get("VLLM_TUNED_CONFIG_FOLDER") != target_config:
    raise SystemExit("recovered service does not use target config")
tree = {service["pid"]}
changed = True
while changed:
    changed = False
    for pid, item in processes.items():
        if pid not in tree and item["ppid"] in tree:
            tree.add(pid)
            changed = True
service["launch_args"] = expected_launch
service["selected_environment"] = environment
service["tree"] = [dict(processes[value]) for value in sorted(tree)]
open(output, "w", encoding="utf-8").write(json.dumps(service, indent=2, sort_keys=True) + "\n")
PY

ready=0
for _ in $(seq 1 360); do
  if timeout 5s curl -fsS http://127.0.0.1:8030/v1/models >/dev/null 2>&1; then
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
grep -F "Using configuration from ${target_config}/E=512,N=80,device_name=thead.json for MoE layer." "${service_log}" >/dev/null
cp -- "${service_log}" "${startup_log}"

python3 - "${after_process}" "${source_manifest}" "${source_config}" "${target_config}" "${startup_log}" "${raw_manifest}" "${before_process}" "${failed_after_process}" "${recovery}" <<'PY'
import copy
import hashlib
import json
import sys
from pathlib import Path

(process_path, source_path, source_config, target_config, startup_path,
 output_path, before_path, failed_path, recovery_path) = sys.argv[1:]
source = json.load(open(source_path, encoding="utf-8"))
process = json.load(open(process_path, encoding="utf-8"))
before = json.load(open(before_path, encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

manifest = copy.deepcopy(source)
manifest["service_instance_id"] = f"{source['container_id'][:12]}-8030-{process['pid']}-{process['start_ticks']}"
manifest["runtime_evidence_sha256"] = sha(process_path)
manifest["launch_config"]["selected_environment"] = process["selected_environment"]
manifest["launch_config"]["launch_args"] = process["launch_args"]
manifest["evidence"] = {
    **manifest["evidence"],
    "role": "moe-drain-bm16-service-38",
    "after_process_path": process_path,
    "after_process_sha256": sha(process_path),
    "before_process_path": before_path,
    "before_process_sha256": sha(before_path),
    "startup_log_snapshot_path": startup_path,
    "startup_log_snapshot_sha256": sha(startup_path),
    "recovered_after_evidence_serialization_failure": True,
}
manifest["transition"] = {
    "source_manifest_path": source_path,
    "source_manifest_sha256": sha(source_path),
    "before_pid": before["pid"], "before_start_ticks": before["start_ticks"],
    "after_pid": process["pid"], "after_start_ticks": process["start_ticks"],
    "only_environment_change": {
        "VLLM_TUNED_CONFIG_FOLDER": {"from": source_config, "to": target_config}
    },
    "source_config_sha256": sha(Path(source_config) / "E=512,N=80,device_name=thead.json"),
    "target_config_sha256": sha(Path(target_config) / "E=512,N=80,device_name=thead.json"),
}
Path(output_path).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
recovery = {
    "status": "recovered_without_additional_restart",
    "failure": "after-process JSON construction used the live service dict inside its own tree and raised circular-reference before writing evidence",
    "failed_after_process_path": failed_path,
    "failed_after_process_size": Path(failed_path).stat().st_size,
    "failed_after_process_sha256": sha(failed_path),
    "recovered_after_process_path": process_path,
    "recovered_after_process_sha256": sha(process_path),
    "service_instance_id": manifest["service_instance_id"],
}
Path(recovery_path).write_text(json.dumps(recovery, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

python3 "${case_root}/commands/performance/verify-live-service-manifest.py" \
  "${raw_manifest}" "${container}" 8030 64

python3 - "${smoke}" <<'PY'
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

payload = json.dumps({
    "model": "Qwen3.8-Flash-Next", "prompt": "Return only the integer 42.",
    "max_tokens": 8, "temperature": 0, "seed": 42,
}).encode()
responses = []
for _ in range(2):
    request = urllib.request.Request(
        "http://127.0.0.1:8030/v1/completions", data=payload,
        headers={"Content-Type": "application/json"}, method="POST")
    raw = urllib.request.urlopen(request, timeout=300).read()
    document = json.loads(raw)
    responses.append({
        "sha256": hashlib.sha256(raw).hexdigest(),
        "finish_reason": document["choices"][0]["finish_reason"],
        "text": document["choices"][0]["text"],
    })
Path(sys.argv[1]).write_text(json.dumps({"replays": 2, "responses": responses}, indent=2, sort_keys=True) + "\n")
PY

ppu-smi > "${ppu_snapshot}"
sha256sum \
  "${source_manifest}" "${before_process}" "${failed_after_process}" \
  "${after_process}" "${startup_log}" "${smoke}" "${recovery}" \
  "${ppu_snapshot}" "${raw_manifest}" \
  "${target_config}/E=512,N=80,device_name=thead.json"
