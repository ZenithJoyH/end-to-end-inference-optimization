#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
script_path=${case_dir}/commands/performance/op008-live-stage-bk64-micro.py
result_path=${case_dir}/results/op008-live-stage-bk64-micro.json
log_path=${case_dir}/logs/op008-live-stage-bk64-micro.log
test ! -e "${result_path}"
test ! -e "${log_path}"
test "$(sha256sum "${script_path}" | cut -d ' ' -f 1)" = dd91701ba5f30008454b7c107276d3889655315a05dc6ca469d7d91df69ac900
test "$(docker exec "${container}" sha256sum /workspace/FlagGems/src/flag_gems/fused/fused_moe.py | cut -d ' ' -f 1)" = a780da6348ba611640b546b47c60b79baa1312094386ce8f49d99d0d8e4750af
test -z "$(ppu-smi --query-compute-apps=pid --format=csv,noheader,nounits)"
if ss -ltnp | grep -qE ':8023\b'; then exit 3; fi
docker exec --env CUDA_VISIBLE_DEVICES=0 --env PYTHONDONTWRITEBYTECODE=1 "${container}" \
  bash -lc "source /usr/local/PPU_SDK/envsetup.sh && python '${script_path}' '${result_path}'" \
  > "${log_path}" 2>&1
sha256sum "${script_path}" "${result_path}" "${log_path}"
