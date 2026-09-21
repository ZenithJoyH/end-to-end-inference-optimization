#!/usr/bin/env bash
set -euo pipefail

repo=/workspace/vllm-plugin-FL
case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
patch_path="${case_root}/commands/plugin-hy4-native-decode-sparse-mla-20260920-final.patch"
status_path="${case_root}/results/operator/plugin-native-decode-sparse-mla-revert-20260920-01.txt"
helper=vllm_fl/dispatch/backends/vendor/thead/impl/mla_decode.py

cd "$repo"
test ! -e "$patch_path"
git diff -- \
  vllm_fl/dispatch/backends/flaggems/impl/mla_sparse.py \
  tests/unit_tests/dispatch/test_flaggems_mla_sparse.py >"$patch_path"
git diff --no-index /dev/null "$helper" >>"$patch_path" || test "$?" -eq 1
test -s "$patch_path"
git apply --check -R "$patch_path"
git apply -R "$patch_path"
test ! -e "$helper"
test -z "$(git status --short -- \
  vllm_fl/dispatch/backends/flaggems/impl/mla_sparse.py \
  tests/unit_tests/dispatch/test_flaggems_mla_sparse.py)"
{
  date --iso-8601=seconds
  sha256sum "$patch_path"
  git branch --show-current
  git rev-parse HEAD
  git status --short
} >"$status_path"
cat "$status_path"
