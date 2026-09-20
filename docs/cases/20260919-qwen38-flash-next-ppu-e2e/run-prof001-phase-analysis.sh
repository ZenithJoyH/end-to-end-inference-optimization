#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
profile_root=${case_root}/profiling/prof-001-maxseq64-bt4096-mixed-capture
rank0=$(find "${profile_root}/traces" -maxdepth 1 -type f -name 'dp0_pp0_tp0_*rank0.*.pt.trace.json.gz' -print)
output=${profile_root}/summaries/phase-rank0.json

test "$(printf '%s\n' "${rank0}" | sed '/^$/d' | wc -l)" -eq 1
test ! -e "${output}"
python3 "${case_root}/commands/analyze-prof001-phases.py" \
  "${rank0}" --output "${output}"
sha256sum "${rank0}" "${output}"
