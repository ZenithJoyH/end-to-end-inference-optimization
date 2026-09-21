#!/usr/bin/env bash
set -euo pipefail

mode=${1:?usage: service-op018-qsa-overlap.sh launch|stop PHASE RUN_ID OUTPUT_DIR PATCH_MANIFEST}
phase=${2:?missing phase}
run_id=${3:?missing run id}
output_dir=${4:?missing unique output dir}
patch_manifest=${5:?missing patch manifest}
case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
image_id=sha256:d87b7b26da3623b18863d47fa623135d0dfc3ba3288293be18aa6f928cb9bbe6
run_dir=${case_root}/transitions/${run_id}
service_log=${run_dir}/op018-${phase}-service-8031.live.log

case "${mode}" in launch|stop) ;; *) echo "invalid mode" >&2; exit 2;; esac
case "${phase}" in prefill|mixed) ;; *) echo "invalid phase" >&2; exit 2;; esac
case "${run_id}" in *[!A-Za-z0-9._-]*|'') echo "invalid run id" >&2; exit 2;; esac
test "$(docker inspect --format '{{.Id}}' "${container}")" = "${container_id}"
test "$(docker inspect --format '{{.Image}}' "${container}")" = "${image_id}"
test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test -f "${patch_manifest}"

if [[ "${mode}" == launch ]]; then
  test ! -e "${run_dir}"
  test ! -e "${output_dir}"
  if ss -ltnH 'sport = :8031' | grep -q .; then
    echo "port 8031 is already in use" >&2
    exit 3
  fi
  mkdir -p "${case_root}/transitions"
  mkdir "${run_dir}"
  ppu-smi > "${run_dir}/host-ppu-smi.before-launch.txt"
  docker exec -i "${container}" python3 - "${patch_manifest}" <<'PY' > "${run_dir}/patched-source.json"
import hashlib, json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
digest = lambda path: hashlib.sha256(open(path, "rb").read()).hexdigest()
assert digest(data["qsa_path"]) == data["patched_sha256"]
assert digest(data["helper_path"]) == data["helper_sha256"]
print(json.dumps(data, indent=2, sort_keys=True))
PY

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
    -e VLLM_FL_QSA_OVERLAP_TELEMETRY=1 \
    -e VLLM_FL_QSA_OVERLAP_RANK=0 \
    -e VLLM_FL_QSA_OVERLAP_MIN_ROWS=4096 \
    -e VLLM_FL_QSA_OVERLAP_ARM_FILE=${output_dir}/arm.json \
    -e VLLM_FL_QSA_OVERLAP_OUTPUT_DIR=${output_dir} \
    -e VLLM_FL_QSA_FIXTURE_CAPTURE=1 \
    -e VLLM_FL_QSA_FIXTURE_RANK=0 \
    -e VLLM_FL_QSA_FIXTURE_ARM_FILE=${output_dir}/arm.json \
    -e VLLM_FL_QSA_FIXTURE_OUTPUT_DIR=${output_dir} \
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
  --no-enable-prefix-caching --enforce-eager \\
  > '${service_log}' 2>&1
"

  for _ in $(seq 1 60); do
    if docker exec -i "${container}" python3 - <<'PY' > "${run_dir}/service-process.json"
import json, os
found = []
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        argv = [x.decode(errors="replace") for x in open(f"/proc/{entry}/cmdline", "rb").read().split(b"\0") if x]
        raw = open(f"/proc/{entry}/stat", encoding="utf-8").read()
        tail = raw[raw.rfind(")") + 2:].split()
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    if "serve" in argv and "--port" in argv and argv[argv.index("--port") + 1] == "8031":
        found.append({"pid": int(entry), "ppid": int(tail[1]), "start_ticks": int(tail[19]), "argv": argv})
if len(found) != 1:
    raise SystemExit(1)
print(json.dumps(found[0], indent=2, sort_keys=True))
PY
    then
      break
    fi
    sleep 2
  done
  test -s "${run_dir}/service-process.json"
  for _ in $(seq 1 180); do
    if curl -fsS http://127.0.0.1:8031/health > "${run_dir}/health.ready.json"; then
      ppu-smi > "${run_dir}/host-ppu-smi.ready.txt"
      sha256sum "${patch_manifest}" "${run_dir}/patched-source.json" \
        "${run_dir}/service-process.json" > "${run_dir}/SHA256SUMS"
      printf '%s\n' "${run_dir}"
      exit 0
    fi
    sleep 5
  done
  echo "diagnostic service did not become ready" >&2
  exit 4
fi

test -s "${run_dir}/service-process.json"
docker exec -i "${container}" python3 - "${run_dir}/service-process.json" <<'PY'
import json, os, signal, sys
target = json.load(open(sys.argv[1], encoding="utf-8"))
pid = target["pid"]
raw = open(f"/proc/{pid}/stat", encoding="utf-8").read()
tail = raw[raw.rfind(")") + 2:].split()
argv = [x.decode(errors="replace") for x in open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0") if x]
if int(tail[19]) != target["start_ticks"] or argv != target["argv"]:
    raise SystemExit("service PID identity changed")
os.kill(pid, signal.SIGTERM)
PY
docker exec -i "${container}" python3 - "${run_dir}/service-process.json" <<'PY'
import json, os, sys, time
target = json.load(open(sys.argv[1], encoding="utf-8"))
deadline = time.monotonic() + 300
while True:
    try:
        raw = open(f"/proc/{target['pid']}/stat", encoding="utf-8").read()
        tail = raw[raw.rfind(")") + 2:].split()
        alive = int(tail[19]) == target["start_ticks"]
    except FileNotFoundError:
        alive = False
    if not alive:
        break
    if time.monotonic() >= deadline:
        raise SystemExit("timed out waiting for exact service root")
    time.sleep(2)
PY
for _ in $(seq 1 60); do
  if ! ss -ltnH 'sport = :8031' | grep -q .; then
    ppu-smi > "${run_dir}/host-ppu-smi.after-stop.txt"
    printf '%s\n' "stopped ${run_id}"
    exit 0
  fi
  sleep 2
done
echo "port 8031 remains in use" >&2
exit 5
