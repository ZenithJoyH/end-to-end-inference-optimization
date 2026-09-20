#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
patch=${case_root}/commands/plugin-hyv4-indexer-body-combined-20260919.patch
test ! -e "${patch}"
docker exec -w /workspace/vllm-plugin-FL hy4-opt-20260914 \
  git diff -- \
  vllm_fl/models/hy_v4.py \
  tests/unit_tests/models/test_hy_v4.py >"${patch}"
set +e
docker exec -w /workspace/vllm-plugin-FL hy4-opt-20260914 \
  git diff --no-index -- \
  /dev/null vllm_fl/dispatch/backends/vendor/thead/impl/hyv4_indexer.py \
  >>"${patch}"
vendor_diff_rc=$?
set -e
test "${vendor_diff_rc}" -eq 1
test -s "${patch}"
sha256sum "${patch}"
