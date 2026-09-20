#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
profile_root=${case_root}/profiling/prof-001-maxseq64-bt4096-mixed-capture
rank0=$(find "${profile_root}/traces" -maxdepth 1 -type f -name 'dp0_pp0_tp0_*rank0.*.pt.trace.json.gz' -print)
rank7=$(find "${profile_root}/traces" -maxdepth 1 -type f -name 'dp0_pp0_tp7_*rank7.*.pt.trace.json.gz' -print)

test "$(printf '%s\n' "${rank0}" | sed '/^$/d' | wc -l)" -eq 1
test "$(printf '%s\n' "${rank7}" | sed '/^$/d' | wc -l)" -eq 1
test -d "${profile_root}/summaries"
test ! -e "${profile_root}/summaries/rank7.txt"
test ! -e "${profile_root}/summaries/phase-rank0.json"

python3 "${case_root}/commands/performance/trace_to_summary.py" \
  "${rank7}" --row-limit 50 --output "${profile_root}/summaries/rank7.txt" &
rank7_pid=$!
python3 "${case_root}/commands/analyze-prof001-phases.py" \
  "${rank0}" --output "${profile_root}/summaries/phase-rank0.json" &
phase_pid=$!

rank7_rc=0
phase_rc=0
wait "${rank7_pid}" || rank7_rc=$?
wait "${phase_pid}" || phase_rc=$?
test "${rank7_rc}" -eq 0
test "${phase_rc}" -eq 0
sha256sum \
  "${profile_root}/summaries/rank7.txt" \
  "${profile_root}/summaries/phase-rank0.json"
