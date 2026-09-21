#!/usr/bin/env bash
set -euo pipefail

phase=${1:?usage: run-fw010-tp8-collective.sh smoke-default|smoke-simple|full-default|full-simple}
case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
script=${case_root}/commands/fw010-tp8-collective-microbench.py
root=${case_root}/microbench/fw010-tp8-collective-002

case "${phase}" in
  smoke-default)
    rows=64; calls=2; warmup=2; repeats=5; proto=default; port=29631 ;;
  smoke-simple)
    rows=64; calls=2; warmup=2; repeats=5; proto=Simple; port=29632 ;;
  full-default)
    rows=1,64,4096; calls=96; warmup=3; repeats=7; proto=default; port=29633 ;;
  full-simple)
    rows=1,64,4096; calls=96; warmup=3; repeats=7; proto=Simple; port=29634 ;;
  *) echo "unknown phase: ${phase}" >&2; exit 2 ;;
esac

run_root=${root}/${phase}
result=${run_root}/result.json
console=${run_root}/console.log
test -f "${script}"
test ! -e "${run_root}"
mkdir -p "${run_root}"
docker exec "${container}" curl -fsS http://127.0.0.1:8030/health >/dev/null
ppu-smi > "${run_root}/ppu-smi.before.txt"
grep -E -i 'backend=nccl|pynccl.py|PCCL version|Using network' \
  "${case_root}/transitions/post-prof-005-restored-native-service-50/maxseq64-service-8030.live.log" \
  > "${run_root}/service50.collective-backend.txt"

docker_args=(
  exec
  -e CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
  -e GLOO_SOCKET_IFNAME=eth0
  -e NCCL_IB_HCA=fic2_soe_bond
  -e NCCL_IB_GID_INDEX=1
  -e NCCL_IB_ADDR_FAMILY=6
  -e NCCL_SOCKET_IFNAME=bond
  -e NCCL_SOCKET_FAMILY=AF_INET6
  -e NCCL_DEBUG=INFO
)
if [[ "${proto}" != default ]]; then
  docker_args+=(-e "NCCL_PROTO=${proto}")
fi

timeout --signal=TERM --kill-after=15s 300s \
  docker "${docker_args[@]}" -w "${case_root}" "${container}" bash -lc "
set -e
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:\${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}
unset NCCL_ALGO
if [[ '${proto}' == default ]]; then unset NCCL_PROTO; fi
torchrun --nnodes=1 --nproc-per-node=8 --node-rank=0 \
  --master-addr=127.0.0.1 --master-port='${port}' \
  '${script}' --rows '${rows}' --hidden-size 2560 \
  --calls-per-chain '${calls}' --warmup '${warmup}' --repeats '${repeats}' \
  --output '${result}'
" > "${console}" 2>&1

test -s "${result}"
ppu-smi > "${run_root}/ppu-smi.after.txt"
docker exec "${container}" curl -fsS http://127.0.0.1:8030/health >/dev/null
sha256sum "${script}" "${result}" "${console}" \
  "${run_root}/service50.collective-backend.txt"
