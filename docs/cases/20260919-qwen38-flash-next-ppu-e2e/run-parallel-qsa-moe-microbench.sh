#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
qsa_root=${case_root}/microbench/qsa-column-bound-001
moe_root=${case_root}/microbench/fused-moe-block-m-001
qsa_script=${case_root}/commands/46-qsa-column-bound-microbench.py
moe_script=${case_root}/commands/47-fused-moe-block-m-microbench.py

test -f "${qsa_script}"
test -f "${moe_script}"
test ! -e "${qsa_root}"
test ! -e "${moe_root}"
mkdir -p "${qsa_root}" "${moe_root}"
ppu-smi > "${case_root}/microbench/ppu-smi.before-parallel-001.txt"

for spec in \
  'qwen3.8-flash-opt-20260919 8020' \
  'qwen3.8-flash-opt-candidate-20260919 8030'; do
  set -- ${spec}
  if docker exec "$1" sh -lc "ps -ef | grep '[v]llm serve' | grep -- '--port $2'"; then
    echo "task service is still live in $1 on port $2" >&2
    exit 3
  fi
done

docker exec \
  -e CUDA_VISIBLE_DEVICES=0 \
  -w "${case_root}" \
  qwen3.8-flash-opt-20260919 \
  bash -lc "
set -e
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:\${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}
python3 '${qsa_script}' \
  --rows 1,8,64,4096 --capacity 20000 --warmup 5 --repeat 20 \
  --output '${qsa_root}/result.json'
" > "${qsa_root}/console.log" 2>&1 &
qsa_pid=$!

docker exec \
  -e CUDA_VISIBLE_DEVICES=8 \
  -w "${case_root}" \
  qwen3.8-flash-opt-candidate-20260919 \
  bash -lc "
set -e
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:\${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}
python3 '${moe_script}' \
  --cases decode,prefill,prefill_guard \
  --warmup 20 --repeat 100 --rounds 3 --device 0 \
  --output '${moe_root}/result.json'
" > "${moe_root}/console.log" 2>&1 &
moe_pid=$!

qsa_rc=0
moe_rc=0
wait "${qsa_pid}" || qsa_rc=$?
wait "${moe_pid}" || moe_rc=$?
printf 'qsa_rc=%s\nmoe_rc=%s\n' "${qsa_rc}" "${moe_rc}" | tee "${case_root}/microbench/parallel-001-status.txt"
test "${qsa_rc}" -eq 0
test "${moe_rc}" -eq 0

ppu-smi > "${case_root}/microbench/ppu-smi.after-parallel-001.txt"
sha256sum \
  "${qsa_script}" "${qsa_root}/result.json" \
  "${moe_script}" "${moe_root}/result.json" \
  "${case_root}/microbench/parallel-001-status.txt"
