#!/usr/bin/env bash
set -euo pipefail

repo=/workspace/vllm-plugin-FL
case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
patch_file="${case_root}/commands/optimize-hy4-indexer-prefill-host-metadata-v2-20260916.patch"
snapshot_dir="${case_root}/source-snapshots/indexer-prefill-host-metadata-20260916"

install -d -m 0755 "${snapshot_dir}/vllm_fl/models" "${snapshot_dir}/tests/unit_tests/models"
install -m 0644 "${repo}/vllm_fl/models/hy_v4.py" "${snapshot_dir}/vllm_fl/models/hy_v4.py"
install -m 0644 "${repo}/tests/unit_tests/models/test_hy_v4.py" "${snapshot_dir}/tests/unit_tests/models/test_hy_v4.py"
sha256sum \
  "${snapshot_dir}/vllm_fl/models/hy_v4.py" \
  "${snapshot_dir}/tests/unit_tests/models/test_hy_v4.py" \
  > "${snapshot_dir}/SHA256SUMS"
git -C "${repo}" diff -- vllm_fl/models/hy_v4.py tests/unit_tests/models/test_hy_v4.py \
  > "${snapshot_dir}/pre-change.diff"

git -C "${repo}" apply --check --recount "${patch_file}"
git -C "${repo}" apply --recount "${patch_file}"
git -C "${repo}" diff --check -- vllm_fl/models/hy_v4.py tests/unit_tests/models/test_hy_v4.py
git -C "${repo}" diff -- vllm_fl/models/hy_v4.py tests/unit_tests/models/test_hy_v4.py \
  > "${snapshot_dir}/post-change.diff"
