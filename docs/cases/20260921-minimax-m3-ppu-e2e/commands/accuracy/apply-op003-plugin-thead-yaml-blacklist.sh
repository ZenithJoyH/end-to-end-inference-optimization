#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
repo=/workspace/vllm-plugin-FL
patch=${case_dir}/commands/op003-plugin-thead-yaml-conv3d-blacklist.patch
evidence=${case_dir}/results/op003-conv3d-blacklist

test -f "${patch}"
test ! -e "${evidence}"
mkdir -p "${evidence}"
docker exec "${container}" git -C "${repo}" rev-parse HEAD > "${evidence}/revision.before.txt"
docker exec "${container}" git -C "${repo}" status --short > "${evidence}/status.before.txt"
docker exec -i "${container}" git -C "${repo}" apply --check - < "${patch}"
docker exec -i "${container}" git -C "${repo}" apply - < "${patch}"
docker exec "${container}" git -C "${repo}" diff --check
docker exec "${container}" git -C "${repo}" diff -- vllm_fl/dispatch/config/thead.yaml \
  > "${evidence}/change.diff"
docker exec "${container}" bash -lc 'cd /workspace/vllm-plugin-FL && python - <<'"'"'PY'"'"'
from vllm_fl.utils import get_flag_gems_whitelist_blacklist, use_flaggems_op

whitelist, blacklist = get_flag_gems_whitelist_blacklist()
assert whitelist is None, whitelist
assert blacklist == ["conv3d"], blacklist
assert not use_flaggems_op("conv3d")
assert use_flaggems_op("linear")
print("whitelist", whitelist)
print("blacklist", blacklist)
print("conv3d_allowed", use_flaggems_op("conv3d"))
print("linear_allowed", use_flaggems_op("linear"))
PY' > "${evidence}/config-check.txt"
sha256sum "${patch}" "${evidence}/change.diff" "${evidence}/config-check.txt" \
  > "${evidence}/SHA256SUMS"
