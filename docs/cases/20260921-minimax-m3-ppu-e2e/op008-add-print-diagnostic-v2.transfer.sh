#!/usr/bin/env bash
set -euo pipefail
case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
source_path=/workspace/FlagGems/src/flag_gems/fused/fused_moe.py
patch_path=${case_dir}/patches/op008-moe-invoke-print-v2.patch
transition=${case_dir}/transitions/op008-all-m-to-print-diagnostic-v2
test ! -e "${transition}"
test "$(sha256sum "${patch_path}" | cut -d ' ' -f 1)" = bde1fbe08077e918c1efedef94597fd01a356ccb4e49efbd734bcab0bba1bc22
test -z "$(ppu-smi --query-compute-apps=pid --format=csv,noheader,nounits)"
if docker exec "${container}" pgrep -f '^python -m vllm.entrypoints.openai.api_server .* --port 8023( |$)' >/dev/null; then exit 3; fi
if ss -ltnp | grep -qE ':8023\b'; then exit 3; fi
test "$(docker exec "${container}" sha256sum "${source_path}" | cut -d ' ' -f 1)" = ced8cef35d42deee5a84564bb82176843ae44f4e4cbbd5fc1f36947171ea2af4
docker exec "${container}" sh -c "cd /workspace/FlagGems && git apply --check --unidiff-zero '${patch_path}'"
docker exec "${container}" sh -c "cd /workspace/FlagGems && git apply --unidiff-zero '${patch_path}'"
docker exec "${container}" python -c "import ast; ast.parse(open('${source_path}').read())"
docker exec "${container}" sh -c 'cd /workspace/FlagGems && git diff --check'
mkdir -p "${transition}"
docker exec "${container}" sha256sum "${source_path}" > "${transition}/source.SHA256SUMS"
sha256sum "${patch_path}" "$0" > "${transition}/patches.SHA256SUMS"
cat "${transition}/source.SHA256SUMS"
