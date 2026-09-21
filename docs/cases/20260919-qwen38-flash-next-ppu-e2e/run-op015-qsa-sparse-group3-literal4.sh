#!/usr/bin/env bash
set -euo pipefail

phase=${1:?usage: run-op015-qsa-sparse-group3-literal4.sh smoke|full}
case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
script=${case_root}/commands/op015-qsa-sparse-group3-literal4-microbench.py

case "${phase}" in
  smoke)
    rows=1
    modes=valid
    warmup=1
    repeat=2
    samples=1
    run_id=op015-qsa-sparse-group3-literal4-smoke-001
    ;;
  full)
    rows=1,64,4096
    modes=valid,invalid_noncontiguous
    warmup=5
    repeat=20
    samples=5
    run_id=op015-qsa-sparse-group3-literal4-001
    ;;
  *)
    echo "unknown phase: ${phase}" >&2
    exit 2
    ;;
esac

result_root=${case_root}/microbench/${run_id}
result=${result_root}/result.json
console=${result_root}/console.log

test -f "${script}"
test ! -e "${result_root}"
mkdir -p "${result_root}"
ppu-smi > "${result_root}/ppu-smi.before.txt"

docker exec \
  -e CUDA_VISIBLE_DEVICES=0 \
  -w "${case_root}" \
  "${container}" \
  bash -lc "
set -e
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:\${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}
python3 '${script}' \
  --rows '${rows}' --modes '${modes}' \
  --warmup '${warmup}' --repeat '${repeat}' --samples '${samples}' \
  --output '${result}'
" > "${console}" 2>&1

ppu-smi > "${result_root}/ppu-smi.after.txt"
sha256sum "${script}" "${result}" "${console}"
