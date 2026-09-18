#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
repo=/workspace/vllm-plugin-FL
patch="${case_dir}/commands/plugin-hy4-indexer-exact-fused-pointwise-20260916.patch"
before="${case_dir}/commands/plugin-before-indexer-exact-fused-pointwise-20260916.patch"

test -f "${patch}"
test ! -e "${before}"
git -C "${repo}" diff >"${before}"
test -s "${before}"
git -C "${repo}" apply --check "${patch}"
git -C "${repo}" apply "${patch}"
git -C "${repo}" diff --check
sha256sum \
  "${before}" \
  "${patch}" \
  "${repo}/vllm_fl/models/hy_v4.py" \
  >"${case_dir}/commands/indexer-exact-fused-pointwise-sha256-20260916.txt"
