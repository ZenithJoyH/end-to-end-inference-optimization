#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
patch_path=${case_dir}/patches/op009-thead-m32-gemm2-bk64-v2.patch
transition=${case_dir}/transitions/op009-original-to-vendor-candidate
source_dir=/workspace/FlagGems/src/flag_gems
generic=${source_dir}/fused/fused_moe.py
vendor_init=${source_dir}/runtime/backend/_thead/fused/__init__.py
vendor_new=${source_dir}/runtime/backend/_thead/fused/fused_moe.py
generic_backup=${case_dir}/patches/op009-generic-original.py
vendor_init_backup=${case_dir}/patches/op009-thead-fused-init-original.py

test ! -e "${transition}"
test ! -e "${generic_backup}"
test ! -e "${vendor_init_backup}"
test "$(sha256sum "${patch_path}" | cut -d ' ' -f 1)" = f12bf9784309178be35fa7f8e934f96cb973ec482d067caec150faed32a1f79f
test -z "$(ppu-smi --query-compute-apps=pid --format=csv,noheader,nounits)"
if docker exec "${container}" pgrep -f '^python -m vllm.entrypoints.openai.api_server .* --port 8023( |$)' >/dev/null; then exit 3; fi
if ss -ltnp | grep -qE ':8023\b'; then exit 3; fi
test "$(docker exec "${container}" sha256sum "${generic}" | cut -d ' ' -f 1)" = a780da6348ba611640b546b47c60b79baa1312094386ce8f49d99d0d8e4750af
test "$(docker exec "${container}" sha256sum "${vendor_init}" | cut -d ' ' -f 1)" = 6a965e61477dde4bdc43e6c6587294a0e28debb9a91f4809eeb93e903c118994
docker exec "${container}" test ! -e "${vendor_new}"
docker exec "${container}" sh -c "cd /workspace/FlagGems && git apply --check '${patch_path}'"
docker exec "${container}" cp "${generic}" "${generic_backup}"
docker exec "${container}" cp "${vendor_init}" "${vendor_init_backup}"
test "$(sha256sum "${generic_backup}" | cut -d ' ' -f 1)" = a780da6348ba611640b546b47c60b79baa1312094386ce8f49d99d0d8e4750af
test "$(sha256sum "${vendor_init_backup}" | cut -d ' ' -f 1)" = 6a965e61477dde4bdc43e6c6587294a0e28debb9a91f4809eeb93e903c118994
docker exec "${container}" sh -c "cd /workspace/FlagGems && git apply '${patch_path}'"
docker exec "${container}" python -c "import ast; [ast.parse(open(p).read()) for p in ('${generic}','${vendor_init}','${vendor_new}')]"
docker exec "${container}" sh -c 'cd /workspace/FlagGems && git diff --check'
mkdir -p "${transition}"
docker exec "${container}" sha256sum "${generic}" "${vendor_init}" "${vendor_new}" > "${transition}/source.SHA256SUMS"
sha256sum "${patch_path}" "${generic_backup}" "${vendor_init_backup}" "$0" > "${transition}/patches.SHA256SUMS"
docker exec "${container}" sh -c 'cd /workspace/FlagGems && git status --short' > "${transition}/git-status.txt"
cat "${transition}/source.SHA256SUMS"
