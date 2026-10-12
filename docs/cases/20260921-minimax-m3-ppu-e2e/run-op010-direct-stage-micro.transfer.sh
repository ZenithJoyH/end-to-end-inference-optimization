#!/usr/bin/env bash
set -euo pipefail
case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
script_path=${case_dir}/commands/performance/op010-direct-stage-micro.py
result_path=${case_dir}/results/op010-direct-stage-micro.json
log_path=${case_dir}/logs/op010-direct-stage-micro.log
test ! -e "${result_path}"
test ! -e "${log_path}"
test "$(sha256sum "${script_path}" | cut -d ' ' -f 1)" = 27b5539c073901b23ced240e3d1775f36f3a42810247e715d26c8a536e2ab1d1
test "$(docker exec "${container}" sha256sum /workspace/FlagGems/src/flag_gems/runtime/backend/_thead/fused/fused_moe.py | cut -d ' ' -f 1)" = 0791a4715ec671e7eb6b55d747e4a5e0ce97e46b83380aea6023cb0333c2fc2d
test -z "$(ppu-smi --query-compute-apps=pid --format=csv,noheader,nounits)"
if ss -ltnp | grep -qE ':8023\b'; then exit 3; fi
docker exec --env CUDA_VISIBLE_DEVICES=0 --env PYTHONDONTWRITEBYTECODE=1 "${container}" \
  bash -lc "source /usr/local/PPU_SDK/envsetup.sh && python '${script_path}' '${result_path}'" \
  > "${log_path}" 2>&1
sha256sum "${script_path}" "${result_path}" "${log_path}"
