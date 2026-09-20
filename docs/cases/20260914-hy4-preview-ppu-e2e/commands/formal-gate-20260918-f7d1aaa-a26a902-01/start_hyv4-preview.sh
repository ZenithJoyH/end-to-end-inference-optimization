#!/usr/bin/env bash
set -e

# Run inside hy4-opt-20260914.
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

nohup vllm serve /mnt/cpfs/models/Hy4-preview-W8A8-linear-moe/ \
  --served-model-name hy4 \
  --host 0.0.0.0 \
  --port 8010 \
  --trust-remote-code \
  --reasoning-parser hy_v4 \
  --tensor-parallel-size 16 \
  --max-model-len 100000 \
  --max-num-batched-tokens 2048 \
  --no-enable-prefix-caching \
  --compilation-config '{"cudagraph_mode":"FULL_DECODE_ONLY"}' \
  > ./service.log 2>&1 &
