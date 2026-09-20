#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
profile_root=${case_root}/profiling/prof-001-maxseq64-bt4096-mixed-capture
pids=()

for rank in 1 2 3 4 5 6; do
  trace=$(find "${profile_root}/traces" -maxdepth 1 -type f -name "dp0_pp0_tp${rank}_*rank${rank}.*.pt.trace.json.gz" -print)
  output=${profile_root}/summaries/rank${rank}.txt
  test "$(printf '%s\n' "${trace}" | sed '/^$/d' | wc -l)" -eq 1
  test ! -e "${output}"
  python3 "${case_root}/commands/performance/trace_to_summary.py" \
    "${trace}" --row-limit 50 --output "${output}" &
  pids+=("$!")
done

failed=0
for pid in "${pids[@]}"; do
  wait "${pid}" || failed=1
done
test "${failed}" -eq 0
sha256sum "${profile_root}"/summaries/rank{1,2,3,4,5,6}.txt
