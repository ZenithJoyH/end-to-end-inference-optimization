#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
script_path=${case_dir}/commands/performance/op009-vendor-candidate-micro.py
result_path=${case_dir}/results/op009-vendor-candidate-micro.json
log_path=${case_dir}/logs/op009-vendor-candidate-micro.log
test ! -e "${result_path}"
test ! -e "${log_path}"
test "$(sha256sum "${script_path}" | cut -d ' ' -f 1)" = 61404f9504140459fed6b9ae72882a7afdc5803e910677cb740b2b2f787c6613
test "$(docker exec "${container}" sha256sum /workspace/FlagGems/src/flag_gems/fused/fused_moe.py | cut -d ' ' -f 1)" = 4f0d05e2aeb5c576a2e8342ede6de4c4df3e8e9f91fe8ea90ee88458c7629b03
test "$(docker exec "${container}" sha256sum /workspace/FlagGems/src/flag_gems/runtime/backend/_thead/fused/fused_moe.py | cut -d ' ' -f 1)" = 293dc46c352e6b7bd21d89000bf161d6258039bd1c3ae32266d52e2c34665259
test -z "$(ppu-smi --query-compute-apps=pid --format=csv,noheader,nounits)"
if ss -ltnp | grep -qE ':8023\b'; then exit 3; fi
docker exec --env CUDA_VISIBLE_DEVICES=0 --env PYTHONDONTWRITEBYTECODE=1 "${container}" \
  bash -lc "source /usr/local/PPU_SDK/envsetup.sh && python '${script_path}' '${result_path}'" \
  > "${log_path}" 2>&1
sha256sum "${script_path}" "${result_path}" "${log_path}"
