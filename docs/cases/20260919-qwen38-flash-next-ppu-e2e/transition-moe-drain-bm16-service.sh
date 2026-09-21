#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
expected_container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
expected_image_id=sha256:d87b7b26da3623b18863d47fa623135d0dfc3ba3288293be18aa6f928cb9bbe6
source_manifest=${SOURCE_MANIFEST:-${case_root}/transitions/mm-native-provider-service-40/mm-native-provider-service-40-raw.json}
source_process=${SOURCE_PROCESS:-${case_root}/transitions/mm-native-provider-service-40/after-process.json}
source_config=${SOURCE_CONFIG:-${case_root}/configs/moe-bm16-decode-only-01}
target_config=${TARGET_CONFIG:-${case_root}/configs/moe-bm16-decode-only-01}
source_blacklist=${SOURCE_BLACKLIST:-_conv_depthwise2d,index,normal_,mm,mm.out}
target_blacklist=${TARGET_BLACKLIST:-_conv_depthwise2d,index,normal_,mm,mm_out}
run_id=${RUN_ID:-mm-native-provider-service-41}
run_dir=${case_root}/transitions/${run_id}
before_process=${run_dir}/before-process.json
after_process=${run_dir}/after-process.json
service_log=${run_dir}/service-8030.live.log
startup_log=${run_dir}/service-8030.startup.log
smoke=${run_dir}/graph-replay-smoke.json
ppu_snapshot=${run_dir}/host-ppu-smi.after-launch.txt
raw_manifest=${run_dir}/${run_id}-raw.json

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
test "$(docker inspect --format '{{.Image}}' "${container}")" = "${expected_image_id}"
test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test -f "${source_manifest}"
test -f "${source_process}"
test -f "${source_config}/E=512,N=80,device_name=thead.json"
test -f "${target_config}/E=512,N=80,device_name=thead.json"
test ! -e "${run_dir}"
mkdir "${run_dir}"

docker exec -i "${container}" python3 - \
  "${source_manifest}" "${source_process}" "${before_process}" \
  "${expected_container_id}" "${source_config}" "${source_blacklist}" <<'PY'
import json
import os
import signal
import sys

manifest_path, process_path, output_path, container_id, source_config, source_blacklist = sys.argv[1:]
manifest = json.load(open(manifest_path, encoding="utf-8"))
expected = json.load(open(process_path, encoding="utf-8"))
pid = expected["pid"]

def snapshot(target):
    raw = open(f"/proc/{target}/stat", encoding="utf-8").read()
    tail = raw[raw.rfind(")") + 2:].split()
    args = [value.decode(errors="replace") for value in open(
        f"/proc/{target}/cmdline", "rb").read().split(b"\0") if value]
    return {"pid": target, "ppid": int(tail[1]), "start_ticks": int(tail[19]), "args": args}

live = snapshot(pid)
if live["start_ticks"] != expected["start_ticks"] or live["args"] != expected["args"]:
    raise SystemExit("source PID identity changed; refusing to signal")
instance = f"{container_id[:12]}-8030-{pid}-{live['start_ticks']}"
if manifest.get("service_instance_id") != instance:
    raise SystemExit("source manifest does not identify live service")
environment = {}
for item in open(f"/proc/{pid}/environ", "rb").read().split(b"\0"):
    if b"=" in item:
        key, value = item.split(b"=", 1)
        environment[key.decode(errors="replace")] = value.decode(errors="replace")
if environment.get("VLLM_TUNED_CONFIG_FOLDER") != source_config:
    raise SystemExit("live source tuned config differs from frozen source")
if environment.get("VLLM_FL_FLAGOS_BLACKLIST_APPEND") != source_blacklist:
    raise SystemExit("live source FlagGems blacklist differs from frozen source")

processes = {}
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        item = snapshot(int(entry))
    except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
        continue
    processes[item["pid"]] = item
tree = {pid}
changed = True
while changed:
    changed = False
    for child, item in processes.items():
        if child not in tree and item["ppid"] in tree:
            tree.add(child)
            changed = True
evidence = {**live, "tree": [processes[value] for value in sorted(tree)]}
open(output_path, "w", encoding="utf-8").write(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
os.kill(pid, signal.SIGTERM)
PY

docker exec -i "${container}" python3 - "${before_process}" <<'PY'
import json
import sys
import time

tree = json.load(open(sys.argv[1], encoding="utf-8"))["tree"]
def same(item):
    try:
        raw = open(f"/proc/{item['pid']}/stat", encoding="utf-8").read()
    except FileNotFoundError:
        return False
    return int(raw[raw.rfind(")") + 2:].split()[19]) == item["start_ticks"]

deadline = time.monotonic() + 240
while True:
    remaining = [item for item in tree if same(item)]
    if not remaining:
        break
    if time.monotonic() >= deadline:
        raise SystemExit(f"timed out waiting for exact service tree: {remaining}")
    time.sleep(2)
PY

if ss -ltnH 'sport = :8030' | grep -q .; then
  echo "port 8030 is still in use" >&2
  exit 3
fi

docker exec -d \
  -e CUDA_VISIBLE_DEVICES=8,9,10,11,12,13,14,15 \
  -e VLLM_WORKER_MULTIPROC_METHOD=spawn \
  -e VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=1800 \
  -e GLOO_SOCKET_IFNAME=eth0 \
  -e NCCL_IB_HCA=fic2_soe_bond \
  -e NCCL_IB_GID_INDEX=1 \
  -e NCCL_IB_ADDR_FAMILY=6 \
  -e NCCL_SOCKET_IFNAME=bond \
  -e NCCL_SOCKET_FAMILY=AF_INET6 \
  -e VLLM_FL_FLAGOS_BLACKLIST_APPEND="${target_blacklist}" \
  -e VLLM_TUNED_CONFIG_FOLDER="${target_config}" \
  -e VLLM_FL_QSA_STATIC_SCORE_COLUMNS=8448 \
  -w "${case_root}" \
  "${container}" bash -lc "
set -e
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:\${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}
exec vllm serve /mnt/cpfs/models/Qwen3.8-Flash-Next \
  --served-model-name Qwen3.8-Flash-Next \
  --host 0.0.0.0 --port 8030 \
  --tensor-parallel-size 8 --pipeline-parallel-size 1 \
  --dtype bfloat16 --language-model-only --max-model-len 80000 \
  --max-num-seqs 64 --max-num-batched-tokens 4096 \
  --gpu-memory-utilization 0.90 --disable-custom-all-reduce \
  --reasoning-parser qwen3 --no-enable-prefix-caching \
  --compilation-config '{\"cudagraph_mode\":\"FULL_AND_PIECEWISE\"}' \
  > '${service_log}' 2>&1
"

docker exec -i "${container}" python3 - "${after_process}" "${target_config}" "${target_blacklist}" <<'PY'
import json
import os
import sys
import time

output, target_config, target_blacklist = sys.argv[1:]
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
        service = matches[0]
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
    raise SystemExit("candidate service did not load target config environment")
if environment.get("VLLM_FL_FLAGOS_BLACKLIST_APPEND") != target_blacklist:
    raise SystemExit("candidate service did not load target FlagGems blacklist")
tree = {service["pid"]}
changed = True
while changed:
    changed = False
    for pid, item in processes.items():
        if pid not in tree and item["ppid"] in tree:
            tree.add(pid)
            changed = True
tree_evidence = [dict(processes[value]) for value in sorted(tree)]
service = dict(service)
service["launch_args"] = expected_launch
service["selected_environment"] = environment
service["tree"] = tree_evidence
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

python3 - "${after_process}" "${source_manifest}" "${source_config}" "${target_config}" "${source_blacklist}" "${target_blacklist}" "${startup_log}" "${raw_manifest}" "${before_process}" "${run_id}" <<'PY'
import copy
import hashlib
import json
import sys
from pathlib import Path

process_path, source_path, source_config, target_config, source_blacklist, target_blacklist, startup_path, output_path, before_path, run_id = sys.argv[1:]
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
    "role": run_id,
    "after_process_path": process_path,
    "after_process_sha256": sha(process_path),
    "before_process_path": before_path,
    "before_process_sha256": sha(before_path),
    "startup_log_snapshot_path": startup_path,
    "startup_log_snapshot_sha256": sha(startup_path),
}
environment_changes = {}
if source_config != target_config:
    environment_changes["VLLM_TUNED_CONFIG_FOLDER"] = {
        "from": source_config, "to": target_config,
    }
if source_blacklist != target_blacklist:
    environment_changes["VLLM_FL_FLAGOS_BLACKLIST_APPEND"] = {
        "from": source_blacklist, "to": target_blacklist,
    }
manifest["transition"] = {
    "source_manifest_path": source_path,
    "source_manifest_sha256": sha(source_path),
    "before_pid": before["pid"],
    "before_start_ticks": before["start_ticks"],
    "after_pid": process["pid"],
    "after_start_ticks": process["start_ticks"],
    "only_environment_change": environment_changes,
    "source_config_sha256": sha(Path(source_config) / "E=512,N=80,device_name=thead.json"),
    "target_config_sha256": sha(Path(target_config) / "E=512,N=80,device_name=thead.json"),
}
Path(output_path).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
  "${source_manifest}" "${before_process}" "${after_process}" \
  "${startup_log}" "${smoke}" "${ppu_snapshot}" "${raw_manifest}" \
  "${target_config}/E=512,N=80,device_name=thead.json"
