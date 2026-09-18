#!/usr/bin/env bash
set -euo pipefail

repo=/workspace/FlagGems
case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
patch_file="${case_root}/commands/extend-hy4-sparse-mla-bk32-prefill-range-v2-20260916.patch"
snapshot_dir="${case_root}/source-snapshots/sparse-mla-bk32-prefill-range-20260916"

install -d -m 0755 \
  "${snapshot_dir}/src/flag_gems/runtime/backend/_thead/fused" \
  "${snapshot_dir}/tests/test_DSA"
install -m 0644 \
  "${repo}/src/flag_gems/runtime/backend/_thead/fused/flashmla_sparse.py" \
  "${snapshot_dir}/src/flag_gems/runtime/backend/_thead/fused/flashmla_sparse.py"
install -m 0644 \
  "${repo}/tests/test_DSA/test_flashmla_sparse_small_heads.py" \
  "${snapshot_dir}/tests/test_DSA/test_flashmla_sparse_small_heads.py"
sha256sum \
  "${snapshot_dir}/src/flag_gems/runtime/backend/_thead/fused/flashmla_sparse.py" \
  "${snapshot_dir}/tests/test_DSA/test_flashmla_sparse_small_heads.py" \
  > "${snapshot_dir}/SHA256SUMS"
git -C "${repo}" diff -- \
  src/flag_gems/runtime/backend/_thead/fused/flashmla_sparse.py \
  tests/test_DSA/test_flashmla_sparse_small_heads.py \
  > "${snapshot_dir}/pre-change.diff"

git -C "${repo}" apply --check --recount "${patch_file}"
git -C "${repo}" apply --recount "${patch_file}"
git -C "${repo}" diff --check -- \
  src/flag_gems/runtime/backend/_thead/fused/flashmla_sparse.py \
  tests/test_DSA/test_flashmla_sparse_small_heads.py
git -C "${repo}" diff -- \
  src/flag_gems/runtime/backend/_thead/fused/flashmla_sparse.py \
  tests/test_DSA/test_flashmla_sparse_small_heads.py \
  > "${snapshot_dir}/post-change.diff"
