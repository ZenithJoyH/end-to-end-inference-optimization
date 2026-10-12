#!/usr/bin/env bash
set -euo pipefail

root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
case_dir=${root}/accuracy/acc-008-full-gpqa-dual-service-current-candidate-20260922
diag_dir=${case_dir}/diagnostics/accdiag-001-qsa-bound-long-gpqa-20260922
container=qwen3.8-flash-opt-candidate-20260919
container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
config_dir=${root}/configs/moe-bm16-decode-only-01

mkdir -p "${diag_dir}/service-8000" "${diag_dir}/evidence" "${diag_dir}/results"
test "$(docker inspect --format '{{.Id}}' "${container}")" = "${container_id}"
curl -fsS http://127.0.0.1:8010/v1/models > "${diag_dir}/evidence/service-8010.before.json"

docker top "${container}" -eo pid,ppid,lstart,stat,args > "${diag_dir}/evidence/processes.before.txt"
ppu-smi > "${diag_dir}/evidence/ppu-smi.before.txt"

mapfile -t service_pids < <(docker exec "${container}" pgrep -f '^/usr/local/bin/python3.12 /usr/local/bin/vllm serve /mnt/cpfs/models/Qwen3.8-Flash-Next .*--port 8000 ')
test "${#service_pids[@]}" -eq 1
old_pid=${service_pids[0]}
docker exec "${container}" sh -c "tr '\0' '\n' < /proc/${old_pid}/environ" > "${diag_dir}/evidence/service-8000.before.env"
docker exec "${container}" sh -c "cat /proc/${old_pid}/stat" > "${diag_dir}/evidence/service-8000.before.stat"
grep -Fx 'VLLM_FL_QSA_STATIC_SCORE_COLUMNS=8448' "${diag_dir}/evidence/service-8000.before.env"

docker exec "${container}" kill -TERM "${old_pid}"
for _ in $(seq 1 120); do
  if ! docker exec "${container}" test -d "/proc/${old_pid}"; then
    break
  fi
  sleep 1
done
test ! -d "/proc/${old_pid}"

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
  -e VLLM_TUNED_CONFIG_FOLDER="${config_dir}" \
  -w "${root}" \
  "${container}" bash -lc "
set -e
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:\${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}
unset VLLM_FL_QSA_STATIC_SCORE_COLUMNS
exec vllm serve /mnt/cpfs/models/Qwen3.8-Flash-Next \\
  --served-model-name Qwen3.8-Flash-Next --host 0.0.0.0 --port 8000 \\
  --tensor-parallel-size 8 --pipeline-parallel-size 1 --dtype bfloat16 \\
  --language-model-only --max-model-len 80000 --max-num-seqs 64 \\
  --max-num-batched-tokens 4096 --gpu-memory-utilization 0.90 \\
  --disable-custom-all-reduce --reasoning-parser qwen3 \\
  --no-enable-prefix-caching \\
  --compilation-config '{\"cudagraph_mode\":\"FULL_AND_PIECEWISE\"}' \\
  > '${diag_dir}/service-8000/service-8000.log' 2>&1
"

ready=0
for _ in $(seq 1 900); do
  if curl -fsS http://127.0.0.1:8000/v1/models > "${diag_dir}/evidence/service-8000.ready.json.tmp" 2>/dev/null; then
    mv "${diag_dir}/evidence/service-8000.ready.json.tmp" "${diag_dir}/evidence/service-8000.ready.json"
    ready=1
    break
  fi
  sleep 2
done
test "${ready}" -eq 1

mapfile -t new_pids < <(docker exec "${container}" pgrep -f '^/usr/local/bin/python3.12 /usr/local/bin/vllm serve /mnt/cpfs/models/Qwen3.8-Flash-Next .*--port 8000 ')
test "${#new_pids[@]}" -eq 1
new_pid=${new_pids[0]}
docker exec "${container}" sh -c "tr '\0' '\n' < /proc/${new_pid}/environ" > "${diag_dir}/evidence/service-8000.after.env"
docker exec "${container}" sh -c "cat /proc/${new_pid}/stat" > "${diag_dir}/evidence/service-8000.after.stat"
if grep -q '^VLLM_FL_QSA_STATIC_SCORE_COLUMNS=' "${diag_dir}/evidence/service-8000.after.env"; then
  echo 'QSA static bound unexpectedly present in control service' >&2
  exit 4
fi
docker top "${container}" -eo pid,ppid,lstart,stat,args > "${diag_dir}/evidence/processes.after.txt"
ppu-smi > "${diag_dir}/evidence/ppu-smi.after.txt"
date -Iseconds > "${diag_dir}/evidence/service-8000.ready-at.txt"
