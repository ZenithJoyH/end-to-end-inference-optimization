#!/usr/bin/env bash
set -euo pipefail

repo=/workspace/FlagGems-vllm
case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
output=${case_root}/commands/flaggems-vllm-hy4-current-optimizations-20260919.patch

if [[ -e "${output}" ]]; then
  echo "refusing to overwrite ${output}" >&2
  exit 1
fi

git -C "${repo}" diff -- \
  src/flaggems_vllm/runtime/backend/_thead/fused/flashmla_sparse.py \
  src/flaggems_vllm/runtime/backend/_thead/ops/fused_moe.py \
  tests/test_thead_hy4_ops.py >"${output}"
test -s "${output}"
git -C "${repo}" apply --check --reverse "${output}"
sha256sum "${output}"
