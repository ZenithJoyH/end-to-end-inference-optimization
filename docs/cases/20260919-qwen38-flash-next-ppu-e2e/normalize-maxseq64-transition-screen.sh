#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
transition_id=maxseq64-screen-01
source_manifest=${case_root}/transitions/${transition_id}/candidate-maxseq64-raw.json
destination=${case_root}/manifests/candidate-maxseq64-service-comparison.json

test -f "${source_manifest}"
test ! -e "${destination}"
python3 "${case_root}/commands/performance/normalize-maxseq-service-manifest.py" \
  "${source_manifest}" \
  "${destination}" \
  64
python3 "${case_root}/commands/performance/verify-live-service-manifest.py" \
  "${destination}" qwen3.8-flash-opt-candidate-20260919 8030 64
sha256sum "${source_manifest}" "${destination}"
