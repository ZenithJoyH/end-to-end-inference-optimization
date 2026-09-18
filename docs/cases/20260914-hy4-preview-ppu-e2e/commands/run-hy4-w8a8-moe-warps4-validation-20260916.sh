#!/usr/bin/env bash
set -euo pipefail

CASE_ROOT=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
RESULT_ROOT=${CASE_ROOT}/results/operator/fused-moe-warps4-20260916
CONTAINER=hy4-opt-20260914

mkdir -p "${RESULT_ROOT}"
docker cp \
  /tmp/validate-hy4-w8a8-moe-warps4-20260916.py \
  "${CONTAINER}:/tmp/validate-hy4-w8a8-moe-warps4-20260916.py"

for m in 128 256 512 1024 2048; do
  docker exec "${CONTAINER}" bash -lc \
    "PYTHONPATH=/workspace/FlagGems/src python /tmp/validate-hy4-w8a8-moe-warps4-20260916.py --m ${m}" \
    > "${RESULT_ROOT}/m${m}.json"
  sed -n '/^{/,$p' "${RESULT_ROOT}/m${m}.json"
done
