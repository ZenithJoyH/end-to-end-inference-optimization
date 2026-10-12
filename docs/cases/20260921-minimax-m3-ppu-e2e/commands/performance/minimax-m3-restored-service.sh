#!/usr/bin/env bash
set -eo pipefail

case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
cache_dir=${case_dir}/cache/baseline-no-prefix
log_file=${case_dir}/logs/baseline-no-prefix-restored-after-prof001.log

exec > "${log_file}" 2>&1
source /usr/local/PPU_SDK/envsetup.sh
export PATH="/usr/lib64/openmpi/bin:${PATH}"
export LD_LIBRARY_PATH="/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:${LD_LIBRARY_PATH:-}"
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=1800
export GLOO_SOCKET_IFNAME=eth0
export NCCL_IB_HCA=fic2_soe_bond
export NCCL_IB_GID_INDEX=1
export NCCL_IB_ADDR_FAMILY=6
export NCCL_SOCKET_IFNAME=bond
export NCCL_SOCKET_FAMILY=AF_INET6
export FLAGTREE_AABS=0
export TRITON_CACHE_DIR="${cache_dir}/triton"
export HF_HOME="${cache_dir}/huggingface"
export XDG_CACHE_HOME="${cache_dir}/xdg"
export PYTHONDONTWRITEBYTECODE=1

cd /workspace/vllm-plugin-FL
exec python -m vllm.entrypoints.openai.api_server \
  --model /mnt/cpfs/models/MiniMax-M3 \
  --host 0.0.0.0 \
  --port 8023 \
  --served-model-name MiniMax-M3 \
  --tensor-parallel-size 16 \
  --dtype bfloat16 \
  --block-size 128 \
  --max-model-len 65536 \
  --max-num-seqs 32 \
  --max-num-batched-tokens 8192 \
  --gpu-memory-utilization 0.90 \
  --no-enable-prefix-caching \
  --compilation-config '{"cudagraph_mode":"FULL_DECODE_ONLY","cudagraph_capture_sizes":[1,2,4,8,16,32]}'
