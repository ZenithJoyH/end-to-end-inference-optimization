#!/usr/bin/env bash
set -euo pipefail

run_id=${1:?usage: launch-fw008-service57.sh UNIQUE_RUN_ID}
case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
image_id=sha256:d87b7b26da3623b18863d47fa623135d0dfc3ba3288293be18aa6f928cb9bbe6
plugin_root=/workspace/vllm-plugin-FL-qwen38-adaptation
plugin_file=${plugin_root}/vllm_fl/worker/common_slot_mapping.py
patch=${case_root}/commands/patches/fw008-common-slot-host-sync-optout.patch
baseline_sha=811289ae9cbcf2869e506eeae7028818a07b65daf54b10d425c1c2baf60a64d6
run_dir=${case_root}/transitions/${run_id}
service_log=${run_dir}/fw008-service57-8031.live.log

case "${run_id}" in *[!A-Za-z0-9._-]*|'') echo "invalid run_id" >&2; exit 2;; esac
test "$(docker inspect --format '{{.Id}}' "${container}")" = "${container_id}"
test "$(docker inspect --format '{{.Image}}' "${container}")" = "${image_id}"
test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test "$(docker exec "${container}" sha256sum "${plugin_file}" | awk '{print $1}')" = "${baseline_sha}"
test -f "${patch}"
test ! -e "${run_dir}"
if ss -ltnH 'sport = :8031' | grep -q .; then
  echo "port 8031 is already in use" >&2
  exit 3
fi
mkdir "${run_dir}"
ppu-smi > "${run_dir}/host-ppu-smi.before-launch.txt"
docker exec "${container}" bash -lc "cd '${plugin_root}' && git apply --check '${patch}' && git apply '${patch}'"
candidate_sha=$(docker exec "${container}" sha256sum "${plugin_file}" | awk '{print $1}')
test "${candidate_sha}" != "${baseline_sha}"
printf '%s  %s\n' "${candidate_sha}" "${plugin_file}" > "${run_dir}/plugin-file.sha256"

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
  -e VLLM_FL_SKIP_COMMON_SLOT_HOST_SYNC=1 \
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
  if docker exec "${container}" python3 -c '
import os
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        argv=[x.decode(errors="replace") for x in open(f"/proc/{entry}/cmdline","rb").read().split(b"\0") if x]
    except (FileNotFoundError, PermissionError):
        continue
    if "serve" in argv and "--port" in argv and argv[argv.index("--port")+1] == "8031":
        raise SystemExit(0)
raise SystemExit(1)
'; then
    sha256sum "${patch}" "${run_dir}/plugin-file.sha256"
    printf '%s\n' "${run_dir}"
    exit 0
  fi
  sleep 1
done
echo "service process did not appear within 30 seconds" >&2
exit 4
