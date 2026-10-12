#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
source_path=/workspace/FlagGems/src/flag_gems/fused/fused_moe.py
patch_path=${case_dir}/patches/op008-moe-invoke-print.patch
transition=${case_dir}/transitions/op008-all-m-to-print-diagnostic
expected_source=ced8cef35d42deee5a84564bb82176843ae44f4e4cbbd5fc1f36947171ea2af4
expected_patch=027f1552efed52c8536228da27b8d484c13c6baee20065b13b0bf2c06261e4c8

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
