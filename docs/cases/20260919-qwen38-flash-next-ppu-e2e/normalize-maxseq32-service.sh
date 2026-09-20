#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
source_manifest=${case_root}/manifests/candidate-service.json
destination=${case_root}/manifests/candidate-maxseq32-service-comparison.json

python3 "${case_root}/commands/performance/normalize-maxseq-service-manifest.py" \
  "${source_manifest}" \
  "${destination}" \
  32
sha256sum "${source_manifest}" "${destination}"
