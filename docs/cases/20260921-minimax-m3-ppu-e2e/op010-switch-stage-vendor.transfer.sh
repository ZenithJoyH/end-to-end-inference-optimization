#!/usr/bin/env bash
set -euo pipefail
action=${1:?usage: op010-switch-stage-vendor.sh apply|revert TRANSITION_ID}
transition_id=${2:?missing transition id}
case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
patch_path=${case_dir}/patches/op010-thead-invoke-m32-bk64.patch
transition=${case_dir}/transitions/${transition_id}
vendor_init=/workspace/FlagGems/src/flag_gems/runtime/backend/_thead/fused/__init__.py
vendor_new=/workspace/FlagGems/src/flag_gems/runtime/backend/_thead/fused/fused_moe.py
original_init=6a965e61477dde4bdc43e6c6587294a0e28debb9a91f4809eeb93e903c118994
candidate_init=fae31da546fd72fb937a9a79033e3dae09ac730446d90eeeb08367da1ace9f9d
candidate_vendor=0791a4715ec671e7eb6b55d747e4a5e0ce97e46b83380aea6023cb0333c2fc2d
case "${action}" in apply|revert) ;; *) exit 2 ;; esac
test ! -e "${transition}"
test "$(sha256sum "${patch_path}" | cut -d ' ' -f 1)" = e23d9c38db0d73a10898d28e75ecc92011a1f9ad68b589e7c134fed913752a62
test -z "$(ppu-smi --query-compute-apps=pid --format=csv,noheader,nounits)"
if docker exec "${container}" pgrep -f '^python -m vllm.entrypoints.openai.api_server .* --port 8023( |$)' >/dev/null; then exit 3; fi
if ss -ltnp | grep -qE ':8023\b'; then exit 3; fi
if [[ "${action}" == apply ]]; then
  test "$(docker exec "${container}" sha256sum "${vendor_init}" | cut -d ' ' -f 1)" = "${original_init}"
  docker exec "${container}" test ! -e "${vendor_new}"
  docker exec "${container}" sh -c "cd /workspace/FlagGems && git apply --check '${patch_path}'"
  docker exec "${container}" sh -c "cd /workspace/FlagGems && git apply '${patch_path}'"
  test "$(docker exec "${container}" sha256sum "${vendor_init}" | cut -d ' ' -f 1)" = "${candidate_init}"
  test "$(docker exec "${container}" sha256sum "${vendor_new}" | cut -d ' ' -f 1)" = "${candidate_vendor}"
else
  test "$(docker exec "${container}" sha256sum "${vendor_init}" | cut -d ' ' -f 1)" = "${candidate_init}"
  test "$(docker exec "${container}" sha256sum "${vendor_new}" | cut -d ' ' -f 1)" = "${candidate_vendor}"
  docker exec "${container}" sh -c "cd /workspace/FlagGems && git apply --check -R '${patch_path}'"
  docker exec "${container}" sh -c "cd /workspace/FlagGems && git apply -R '${patch_path}'"
  test "$(docker exec "${container}" sha256sum "${vendor_init}" | cut -d ' ' -f 1)" = "${original_init}"
  docker exec "${container}" test ! -e "${vendor_new}"
fi
docker exec "${container}" sh -c 'cd /workspace/FlagGems && git diff --check'
mkdir -p "${transition}"
docker exec "${container}" sha256sum "${vendor_init}" > "${transition}/source.SHA256SUMS"
if [[ "${action}" == apply ]]; then
  docker exec "${container}" sha256sum "${vendor_new}" >> "${transition}/source.SHA256SUMS"
fi
sha256sum "${patch_path}" "$0" > "${transition}/patches.SHA256SUMS"
docker exec "${container}" sh -c 'cd /workspace/FlagGems && git status --short' > "${transition}/git-status.txt"
cat "${transition}/source.SHA256SUMS"
