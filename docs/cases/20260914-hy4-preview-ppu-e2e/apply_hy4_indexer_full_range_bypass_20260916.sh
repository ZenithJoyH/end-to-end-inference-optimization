#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
repo=/workspace/vllm-plugin-FL
model_file="${repo}/vllm_fl/models/hy_v4.py"
test_file="${repo}/tests/unit_tests/models/test_hy_v4.py"
patch="${case_dir}/commands/plugin-hy4-indexer-full-range-bypass-v3-20260916.patch"
before="${case_dir}/commands/plugin-before-indexer-full-range-bypass-v3-20260916.patch"

test "$(git -C "${repo}" rev-parse HEAD)" = 38f350b13fc15f08eb4641e1d6d1980ba3fc16aa
test "$(sha256sum "${model_file}" | awk '{print $1}')" = 38a7965b6bd9a2f27de64fb4dd8c9b96eca97b8179c74296a4d1e1e5a865a4b7
test "$(sha256sum "${test_file}" | awk '{print $1}')" = 04eea3ae22662b6c305daa28e7f70f1cdd996b6532cde38028de04f9735acd31
test -f "${patch}"
test ! -e "${before}"

git -C "${repo}" diff -- vllm_fl/models/hy_v4.py tests/unit_tests/models/test_hy_v4.py >"${before}"
test -s "${before}"
git -C "${repo}" apply --check "${patch}"
git -C "${repo}" apply "${patch}"
git -C "${repo}" diff --check
sha256sum "${model_file}" "${test_file}"
