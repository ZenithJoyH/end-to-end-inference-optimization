#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
profile_root=${case_root}/profiling/prof-001-maxseq64-bt4096-mixed-capture
trace=$(find "${profile_root}/traces" -maxdepth 1 -type f -name 'dp0_pp0_tp0_*rank0.*.pt.trace.json.gz' -print)
output=${profile_root}/summaries/rank0.txt

test "$(printf '%s\n' "${trace}" | sed '/^$/d' | wc -l)" -eq 1
test ! -e "${profile_root}/summaries"
mkdir "${profile_root}/summaries"
python3 "${case_root}/commands/performance/trace_to_summary.py" \
  "${trace}" \
  --row-limit 50 \
  --output "${output}"
sha256sum "${trace}" "${output}"
