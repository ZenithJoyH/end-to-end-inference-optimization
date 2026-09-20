#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
raw=${case_dir}/transitions/post-profiler-maxseq64-bt4096-service-01/post-profiler-maxseq64-bt4096-raw.json
target=${case_dir}/manifests/candidate-maxseq64-bt4096-postprofiler-service-comparison.json

test -f "${raw}"
test ! -e "${target}"
python3 "${case_dir}/commands/performance/normalize-maxseq-service-manifest.py" \
  "${raw}" "${target}" 64 4096
sha256sum "${raw}" "${target}"
