#!/usr/bin/env bash
set -euo pipefail
case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
patch_path=${case_dir}/patches/op009-thead-m32-gemm2-bk64-v2.patch
transition=${case_dir}/transitions/op009-nohit-vendor-revert
generic=/workspace/FlagGems/src/flag_gems/fused/fused_moe.py
vendor_init=/workspace/FlagGems/src/flag_gems/runtime/backend/_thead/fused/__init__.py
vendor_new=/workspace/FlagGems/src/flag_gems/runtime/backend/_thead/fused/fused_moe.py
test ! -e "${transition}"
test "$(sha256sum "${patch_path}" | cut -d ' ' -f 1)" = f12bf9784309178be35fa7f8e934f96cb973ec482d067caec150faed32a1f79f
test -z "$(ppu-smi --query-compute-apps=pid --format=csv,noheader,nounits)"
if docker exec "${container}" pgrep -f '^python -m vllm.entrypoints.openai.api_server .* --port 8023( |$)' >/dev/null; then exit 3; fi
if ss -ltnp | grep -qE ':8023\b'; then exit 3; fi
test "$(docker exec "${container}" sha256sum "${generic}" | cut -d ' ' -f 1)" = 4f0d05e2aeb5c576a2e8342ede6de4c4df3e8e9f91fe8ea90ee88458c7629b03
test "$(docker exec "${container}" sha256sum "${vendor_init}" | cut -d ' ' -f 1)" = f237d52c7bd47195c86f9ca2b295c17d2a8ff9070a3f6e68c475962806898336
test "$(docker exec "${container}" sha256sum "${vendor_new}" | cut -d ' ' -f 1)" = 293dc46c352e6b7bd21d89000bf161d6258039bd1c3ae32266d52e2c34665259
docker exec "${container}" sh -c "cd /workspace/FlagGems && git apply --check -R '${patch_path}'"
docker exec "${container}" sh -c "cd /workspace/FlagGems && git apply -R '${patch_path}'"
test "$(docker exec "${container}" sha256sum "${generic}" | cut -d ' ' -f 1)" = a780da6348ba611640b546b47c60b79baa1312094386ce8f49d99d0d8e4750af
test "$(docker exec "${container}" sha256sum "${vendor_init}" | cut -d ' ' -f 1)" = 6a965e61477dde4bdc43e6c6587294a0e28debb9a91f4809eeb93e903c118994
docker exec "${container}" test ! -e "${vendor_new}"
mkdir -p "${transition}"
docker exec "${container}" sha256sum "${generic}" "${vendor_init}" > "${transition}/source.SHA256SUMS"
sha256sum "${patch_path}" "$0" > "${transition}/patches.SHA256SUMS"
docker exec "${container}" sh -c 'cd /workspace/FlagGems && git status --short' > "${transition}/git-status.txt"
cat "${transition}/source.SHA256SUMS"
