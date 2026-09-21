#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
profile_root=${case_root}/profiling/prof-004-p4k-post-op008
trace_dir=${profile_root}/traces
summary_dir=${profile_root}/summaries
rank0=$(find "${trace_dir}" -maxdepth 1 -type f -name 'dp0_pp0_tp0_*rank0.*.pt.trace.json.gz' -print)
test "$(find "${trace_dir}" -maxdepth 1 -type f -name '*.pt.trace.json.gz' | wc -l)" -eq 9
test "$(printf '%s\n' "${rank0}" | sed '/^$/d' | wc -l)" -eq 1
find "${trace_dir}" -maxdepth 1 -type f -name '*.pt.trace.json.gz' -print0 | xargs -0 -n1 gzip -t
test ! -e "${summary_dir}"
mkdir "${summary_dir}"
find "${trace_dir}" -maxdepth 1 -type f -name '*.pt.trace.json.gz' -print0 | sort -z | xargs -0 sha256sum > "${summary_dir}/trace-SHA256SUMS"
python3 "${case_root}/commands/performance/trace_to_summary.py" "${rank0}" --row-limit 120 --output "${summary_dir}/rank0.txt"
python3 "${case_root}/commands/analyze-prof001-phases.py" "${rank0}" --output "${summary_dir}/phase-rank0.json"
sha256sum "${summary_dir}/trace-SHA256SUMS" "${summary_dir}/rank0.txt" "${summary_dir}/phase-rank0.json" > "${summary_dir}/summary-SHA256SUMS"
cat "${summary_dir}/summary-SHA256SUMS"
