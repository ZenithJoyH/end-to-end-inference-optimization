#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
repo=/workspace/vllm-plugin-FL
result="${case_dir}/results/plugin-indexer-full-range-validation-20260916.txt"

test ! -e "${result}"
test "$(git -C "${repo}" rev-parse HEAD)" = 38f350b13fc15f08eb4641e1d6d1980ba3fc16aa
test "$(sha256sum "${repo}/vllm_fl/models/hy_v4.py" | awk '{print $1}')" = bc567ade22696146200042e8e29745535c86fa2dc9479051c2d2f7892ed3c9f3
test "$(sha256sum "${repo}/tests/unit_tests/models/test_hy_v4.py" | awk '{print $1}')" = cc0805e7cd2e0ab7310532629f442b8afb0676261d57f93c20bff5df744ac9e8
git -C "${repo}" diff --check

set +u
source /usr/local/PPU_SDK/envsetup.sh
set -u
cd "${repo}"
python3 -m pytest tests/unit_tests/models/test_hy_v4.py -q | tee "${result}"
grep -Eq '[0-9]+ passed' "${result}"
sha256sum "${result}" >"${result}.sha256"
