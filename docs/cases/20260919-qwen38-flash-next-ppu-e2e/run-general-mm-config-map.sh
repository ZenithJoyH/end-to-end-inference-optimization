#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
expected_container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
script=${case_root}/commands/243-general-mm-config-map.py
result_root=${case_root}/microbench/general-mm-config-map-001

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
test -f "${script}"
test ! -e "${result_root}"
curl -fsS http://127.0.0.1:8030/v1/models >/dev/null
mkdir -p "${case_root}/microbench"

docker exec \
  -e CUDA_VISIBLE_DEVICES=15 \
  -w "${case_root}" \
  "${container}" \
  bash -lc "
set -e
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:\${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}
python3 '${script}' --device 0 --output '${result_root}/result.json'
" > "${case_root}/microbench/general-mm-config-map-001.console.log" 2>&1

sha256sum \
  "${script}" "${result_root}/result.json" \
  "${case_root}/microbench/general-mm-config-map-001.console.log"
