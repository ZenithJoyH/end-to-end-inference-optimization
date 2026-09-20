#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
script=${case_root}/commands/133-qsa-row-range-topk-microbench.py
base_script=${case_root}/commands/46-qsa-column-bound-microbench.py
result_root=${case_root}/microbench/qsa-row-range-topk-003
console_log=${case_root}/microbench/qsa-row-range-topk-003.console.log

test -f "${script}"
test -f "${base_script}"
test ! -e "${result_root}"
test ! -e "${console_log}"
if docker exec "${container}" sh -lc "ps -ef | grep '[v]llm serve' | grep -- '--port 8030'"; then
  echo "candidate task service is still live" >&2
  exit 3
fi
ppu-smi > "${case_root}/microbench/ppu-smi.before-qsa-row-range-003.txt"
docker exec \
  -e CUDA_VISIBLE_DEVICES=8 \
  -w "${case_root}" \
  "${container}" \
  bash -lc "
set -e
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:\${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}
python3 '${script}' \
  --base-script '${base_script}' \
  --rows 1,64,4096 --capacity 20000 --warmup 5 --repeat 20 \
  --output '${result_root}'
" > "${console_log}" 2>&1
ppu-smi > "${case_root}/microbench/ppu-smi.after-qsa-row-range-003.txt"
sha256sum "${script}" "${base_script}" "${result_root}/result.json" "${console_log}"
