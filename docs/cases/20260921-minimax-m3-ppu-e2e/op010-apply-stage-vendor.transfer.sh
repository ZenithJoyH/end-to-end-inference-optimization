#!/usr/bin/env bash
set -euo pipefail
case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
patch_path=${case_dir}/patches/op010-thead-invoke-m32-bk64.patch
transition=${case_dir}/transitions/op010-original-to-stage-vendor
vendor_init=/workspace/FlagGems/src/flag_gems/runtime/backend/_thead/fused/__init__.py
vendor_new=/workspace/FlagGems/src/flag_gems/runtime/backend/_thead/fused/fused_moe.py
backup=${case_dir}/patches/op010-thead-fused-init-original.py
test ! -e "${transition}"
test ! -e "${backup}"
test "$(sha256sum "${patch_path}" | cut -d ' ' -f 1)" = e23d9c38db0d73a10898d28e75ecc92011a1f9ad68b589e7c134fed913752a62
test -z "$(ppu-smi --query-compute-apps=pid --format=csv,noheader,nounits)"
if docker exec "${container}" pgrep -f '^python -m vllm.entrypoints.openai.api_server .* --port 8023( |$)' >/dev/null; then exit 3; fi
if ss -ltnp | grep -qE ':8023\b'; then exit 3; fi
test "$(docker exec "${container}" sha256sum "${vendor_init}" | cut -d ' ' -f 1)" = 6a965e61477dde4bdc43e6c6587294a0e28debb9a91f4809eeb93e903c118994
docker exec "${container}" test ! -e "${vendor_new}"
docker exec "${container}" sh -c "cd /workspace/FlagGems && git apply --check '${patch_path}'"
docker exec "${container}" cp "${vendor_init}" "${backup}"
test "$(sha256sum "${backup}" | cut -d ' ' -f 1)" = 6a965e61477dde4bdc43e6c6587294a0e28debb9a91f4809eeb93e903c118994
docker exec "${container}" sh -c "cd /workspace/FlagGems && git apply '${patch_path}'"
docker exec "${container}" python -c "import ast; [ast.parse(open(p).read()) for p in ('${vendor_init}','${vendor_new}')]"
docker exec "${container}" sh -c 'cd /workspace/FlagGems && git diff --check'
mkdir -p "${transition}"
docker exec "${container}" sha256sum "${vendor_init}" "${vendor_new}" > "${transition}/source.SHA256SUMS"
sha256sum "${patch_path}" "${backup}" "$0" > "${transition}/patches.SHA256SUMS"
docker exec "${container}" sh -c 'cd /workspace/FlagGems && git status --short' > "${transition}/git-status.txt"
cat "${transition}/source.SHA256SUMS"
