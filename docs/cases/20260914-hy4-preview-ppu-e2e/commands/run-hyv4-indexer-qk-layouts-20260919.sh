#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
script=${case_root}/commands/benchmark-hyv4-indexer-qk-layouts-20260919.py
result_root=${case_root}/results/operator/hyv4-indexer-qk-layouts-20260919-01
result=${result_root}/summary.json
log=${result_root}/benchmark.log

test -s "${script}"
test ! -e "${result}"
test ! -e "${log}"
mkdir -p "${result_root}"

set +e
docker exec \
  -e CUDA_VISIBLE_DEVICES=0 \
  -w /workspace/vllm-plugin-FL \
  hy4-opt-20260914 \
  timeout 900 python3 "${script}" --output "${result}" \
  >"${log}" 2>&1
rc=$?
set -e
cat "${log}"
exit "${rc}"
