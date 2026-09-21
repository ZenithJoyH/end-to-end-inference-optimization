#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
result_root="${case_root}/results/operator/scaled-mm-int32-offsets-20260920-01"
test ! -e "$result_root"
mkdir -p "$result_root"
docker exec hy4-opt-20260914 bash -lc '
  set -eo pipefail
  source /usr/local/PPU_SDK/envsetup.sh
  set -u
  export PATH="/usr/lib64/openmpi/bin:${PATH}"
  export LD_LIBRARY_PATH="/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:${LD_LIBRARY_PATH:-}"
  export CUDA_VISIBLE_DEVICES=0
  python3 /mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/commands/benchmark-hy4-scaled-mm-int32-offsets-20260920.py \
    --output /mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/operator/scaled-mm-int32-offsets-20260920-01/summary.json
' >"${result_root}/stdout.log" 2>"${result_root}/stderr.log" || status=$?
sha256sum \
  "${case_root}/commands/benchmark-hy4-scaled-mm-int32-offsets-20260920.py" \
  "${result_root}/stdout.log" \
  "${result_root}/stderr.log" \
  >"${result_root}/artifacts.sha256"
cat "${result_root}/stdout.log"
cat "${result_root}/stderr.log" >&2
exit "${status:-0}"
