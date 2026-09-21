#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
result_root="${case_root}/results/operator/pccl-allreduce-sweep-20260920-03"
test ! -e "$result_root"
mkdir -p "$result_root"

run_one() {
  local name=$1
  local algo=$2
  local proto=$3
  docker exec \
    -e SWEEP_ALGO="$algo" \
    -e SWEEP_PROTO="$proto" \
    hy4-opt-20260914 bash -lc '
      set -eo pipefail
      source /usr/local/PPU_SDK/envsetup.sh
      set -u
      export PATH="/usr/lib64/openmpi/bin:${PATH}"
      export LD_LIBRARY_PATH="/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:${LD_LIBRARY_PATH:-}"
      export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
      export GLOO_SOCKET_IFNAME=eth0
      export NCCL_IB_HCA=fic2_soe_bond
      export NCCL_IB_GID_INDEX=1
      export NCCL_IB_ADDR_FAMILY=6
      export NCCL_SOCKET_IFNAME=bond
      export NCCL_SOCKET_FAMILY=AF_INET6
      if [[ "$SWEEP_ALGO" != default ]]; then export NCCL_ALGO="$SWEEP_ALGO"; fi
      if [[ "$SWEEP_PROTO" != default ]]; then export NCCL_PROTO="$SWEEP_PROTO"; fi
      torchrun --nnodes=1 --nproc-per-node=16 --node-rank=0 \
        --master-addr=127.0.0.1 --master-port=29620 \
        /mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/commands/benchmark-hy4-pccl-allreduce-20260920.py
    ' >"${result_root}/${name}.stdout" 2>"${result_root}/${name}.stderr"
}

run_one default default default
run_one simple_ll default Simple,LL
run_one ll_simple default LL,Simple
sha256sum "${result_root}"/* >"${result_root}/artifacts.sha256"
for output in "${result_root}"/*.stdout; do
  printf '=== %s ===\n' "$output"
  grep 'SUMMARY=' "$output"
done
