#!/usr/bin/env bash
set -euo pipefail

target_role=${1:?usage: transition-op014-service8031.sh baseline|candidate RUN_ID}
run_id=${2:?missing RUN_ID}
case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
image_id=sha256:d87b7b26da3623b18863d47fa623135d0dfc3ba3288293be18aa6f928cb9bbe6
plugin_root=/workspace/vllm-plugin-FL-qwen38-adaptation
plugin_file=${plugin_root}/vllm_fl/models/qwen3_8_flash_next.py
patch=${case_root}/commands/patches/op014-repeat-interleave-output-size.patch
baseline_sha=3ae84180f7b5f4d70886c98f1d1afcf2255f8f7223a110397ec4894cf81a9a59
candidate_sha=c1062b5810a1bcfec7cfca7f61e11a0ffd08700cee2b3f6472b7086d195a87e7
run_dir=${case_root}/transitions/${run_id}
service_log=${run_dir}/${target_role}-service-8031.live.log

case "${target_role}" in baseline|candidate) ;; *) echo "invalid target role" >&2; exit 2;; esac
case "${run_id}" in *[!A-Za-z0-9._-]*|'') echo "invalid run_id" >&2; exit 2;; esac
test "$(docker inspect --format '{{.Id}}' "${container}")" = "${container_id}"
test "$(docker inspect --format '{{.Image}}' "${container}")" = "${image_id}"
test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test -f "${patch}"
test ! -e "${run_dir}"
mkdir -p "${case_root}/transitions"
mkdir "${run_dir}"

docker exec -i "${container}" python3 - <<'PY' > "${run_dir}/before-process.json"
import json
import os

model = "/mnt/cpfs/models/Qwen3.8-Flash-Next"
port = "8031"
processes = {}
services = []
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        argv = [item.decode(errors="replace") for item in open(
            f"/proc/{entry}/cmdline", "rb").read().split(b"\0") if item]
        raw = open(f"/proc/{entry}/stat", encoding="utf-8").read()
        tail = raw[raw.rfind(")") + 2:].split()
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    row = {
        "pid": int(entry), "ppid": int(tail[1]), "start_ticks": int(tail[19]),
        "argv": argv,
    }
    processes[row["pid"]] = row
    if "serve" in argv and model in argv and "--port" in argv and argv[argv.index("--port") + 1] == port:
        services.append(row)
if len(services) != 1:
    raise SystemExit(f"expected one service on port {port}, got {len(services)}")
root = dict(services[0])
tree = {root["pid"]}
changed = True
while changed:
    changed = False
    for pid, row in processes.items():
        if pid not in tree and row["ppid"] in tree:
            tree.add(pid)
            changed = True
root["tree"] = [dict(processes[pid]) for pid in sorted(tree)]
print(json.dumps(root, indent=2, sort_keys=True))
PY

docker exec -i "${container}" python3 - "${run_dir}/before-process.json" <<'PY'
import json
import os
import signal
import sys

target = json.load(open(sys.argv[1], encoding="utf-8"))
pid = target["pid"]
raw = open(f"/proc/{pid}/stat", encoding="utf-8").read()
tail = raw[raw.rfind(")") + 2:].split()
argv = [item.decode(errors="replace") for item in open(
    f"/proc/{pid}/cmdline", "rb").read().split(b"\0") if item]
if int(tail[19]) != target["start_ticks"] or argv != target["argv"]:
    raise SystemExit("service PID identity changed")
os.kill(pid, signal.SIGTERM)
PY

docker exec -i "${container}" python3 - "${run_dir}/before-process.json" <<'PY'
import json
import sys
import time

tree = json.load(open(sys.argv[1], encoding="utf-8"))["tree"]
def alive(row):
    try:
        raw = open(f"/proc/{row['pid']}/stat", encoding="utf-8").read()
    except FileNotFoundError:
        return False
    tail = raw[raw.rfind(")") + 2:].split()
    return int(tail[19]) == row["start_ticks"]
deadline = time.monotonic() + 240
while True:
    live = [row for row in tree if alive(row)]
    if not live:
        break
    if time.monotonic() >= deadline:
        raise SystemExit(f"timed out waiting for exact service tree: {live}")
    time.sleep(2)
PY

if ss -ltnH 'sport = :8031' | grep -q .; then
  echo "port 8031 remains in use" >&2
  exit 3
fi

if test "${target_role}" = baseline; then
  test "$(docker exec "${container}" sha256sum "${plugin_file}" | awk '{print $1}')" = "${candidate_sha}"
  docker exec "${container}" bash -lc "cd '${plugin_root}' && git apply -R --check '${patch}' && git apply -R '${patch}'"
  target_sha=${baseline_sha}
else
  test "$(docker exec "${container}" sha256sum "${plugin_file}" | awk '{print $1}')" = "${baseline_sha}"
  docker exec "${container}" bash -lc "cd '${plugin_root}' && git apply --check '${patch}' && git apply '${patch}'"
  target_sha=${candidate_sha}
fi
test "$(docker exec "${container}" sha256sum "${plugin_file}" | awk '{print $1}')" = "${target_sha}"

docker exec -d \
  -e CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
  -e VLLM_WORKER_MULTIPROC_METHOD=spawn \
  -e VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=1800 \
  -e GLOO_SOCKET_IFNAME=eth0 \
  -e NCCL_IB_HCA=fic2_soe_bond \
  -e NCCL_IB_GID_INDEX=1 \
  -e NCCL_IB_ADDR_FAMILY=6 \
  -e NCCL_SOCKET_IFNAME=bond \
  -e NCCL_SOCKET_FAMILY=AF_INET6 \
  -e VLLM_FL_FLAGOS_BLACKLIST_APPEND=_conv_depthwise2d,index,normal_,mm,mm_out \
  -e VLLM_TUNED_CONFIG_FOLDER=${case_root}/configs/moe-bm16-decode-only-01 \
  -e VLLM_FL_QSA_STATIC_SCORE_COLUMNS=8448 \
  -w "${case_root}" \
  "${container}" bash -lc "
set -e
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:\${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}
exec vllm serve /mnt/cpfs/models/Qwen3.8-Flash-Next \\
  --served-model-name Qwen3.8-Flash-Next --host 0.0.0.0 --port 8031 \\
  --tensor-parallel-size 8 --pipeline-parallel-size 1 --dtype bfloat16 \\
  --language-model-only --max-model-len 80000 --max-num-seqs 64 \\
  --max-num-batched-tokens 4096 --gpu-memory-utilization 0.90 \\
  --disable-custom-all-reduce --reasoning-parser qwen3 \\
  --no-enable-prefix-caching \\
  --compilation-config '{\"cudagraph_mode\":\"FULL_AND_PIECEWISE\"}' \\
  > '${service_log}' 2>&1
"

for _ in $(seq 1 30); do
  if docker exec -i "${container}" python3 - <<'PY' > "${run_dir}/after-process.json"
import json
import os

found = []
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        argv = [item.decode(errors="replace") for item in open(
            f"/proc/{entry}/cmdline", "rb").read().split(b"\0") if item]
        raw = open(f"/proc/{entry}/stat", encoding="utf-8").read()
        tail = raw[raw.rfind(")") + 2:].split()
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    if "serve" in argv and "--port" in argv and argv[argv.index("--port") + 1] == "8031":
        found.append({"pid": int(entry), "start_ticks": int(tail[19]), "argv": argv})
if len(found) != 1:
    raise SystemExit(1)
print(json.dumps(found[0], indent=2, sort_keys=True))
PY
  then
    docker exec "${container}" sha256sum "${plugin_file}" > "${run_dir}/plugin-file.sha256"
    sha256sum "${patch}" "${run_dir}/before-process.json" \
      "${run_dir}/after-process.json" "${run_dir}/plugin-file.sha256"
    printf '%s\n' "${run_dir}"
    exit 0
  fi
  sleep 1
done
echo "new service process did not appear" >&2
exit 4
