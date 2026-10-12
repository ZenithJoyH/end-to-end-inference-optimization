#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
source_path=/workspace/FlagGems/src/flag_gems/fused/fused_moe.py
patch_path=${case_dir}/patches/op008-moe-invoke-all-m-v2.patch
transition=${case_dir}/transitions/op008-filtered-to-all-m-diagnostic
expected_source=e820363142bb4ad2941dcd3fd12b2428caff96acef559c49fb8dd8c162a78541
expected_patch=b0b2a562066accd93609d32ea864fcd93f371561809cabeb587298801bfd9121

test ! -e "${transition}"
test "$(sha256sum "${patch_path}" | cut -d ' ' -f 1)" = "${expected_patch}"
test -z "$(ppu-smi --query-compute-apps=pid --format=csv,noheader,nounits)"
if docker exec "${container}" pgrep -f '^python -m vllm.entrypoints.openai.api_server .* --port 8023( |$)' >/dev/null; then
  echo "model service still active" >&2
  exit 3
fi
if ss -ltnp | grep -qE ':8023\b'; then
  echo "port 8023 still active" >&2
  exit 3
fi
test "$(docker exec "${container}" sha256sum "${source_path}" | cut -d ' ' -f 1)" = "${expected_source}"
docker exec "${container}" sh -c "cd /workspace/FlagGems && git apply --check '${patch_path}'"
docker exec "${container}" sh -c "cd /workspace/FlagGems && git apply '${patch_path}'"
docker exec "${container}" python -c "import ast; ast.parse(open('${source_path}').read())"
docker exec "${container}" sh -c 'cd /workspace/FlagGems && git diff --check'
mkdir -p "${transition}"
docker exec "${container}" sha256sum "${source_path}" > "${transition}/source.SHA256SUMS"
sha256sum "${patch_path}" "$0" > "${transition}/patches.SHA256SUMS"
cat "${transition}/source.SHA256SUMS"
