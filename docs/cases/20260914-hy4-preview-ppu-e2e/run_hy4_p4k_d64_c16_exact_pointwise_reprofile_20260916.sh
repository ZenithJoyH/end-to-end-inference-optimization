#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
source_script="${case_dir}/commands/run-hy4-p4k-d64-c16-full-range-reprofile-20260916.sh"
generated=/tmp/run-hy4-p4k-d64-c16-exact-pointwise-reprofile-20260916-06.sh

test -f "${source_script}"
test ! -e "${generated}"
sed \
  -e 's/p4k-d64-c16-n16-full-range-reprofile-20260916-05/p4k-d64-c16-n16-exact-pointwise-reprofile-20260916-06/g' \
  -e 's/bc567ade22696146200042e8e29745535c86fa2dc9479051c2d2f7892ed3c9f3/7c1843727800a6e1bc5252c28aaf33f0801da672442aa4ad145c7ce613ec6ea2/g' \
  -e 's/verify_full_range_bypass_removes_prefill_indexer_qk_topk_and_preserves_copy_sync_elimination/verify_exact_fused_pointwise_reduces_indexer_scoring_cost_without_changing_logits/g' \
  "${source_script}" >"${generated}"
test -s "${generated}"
sha256sum "${generated}" >"${generated}.sha256"
bash "${generated}"
