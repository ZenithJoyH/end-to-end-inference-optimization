#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
profile_id=p4k-d128-c64-n64-current-stack-reprofile-20260917-08
trace_dir="${case_root}/profiling/${profile_id}/traces"
result_dir="${case_root}/results/profiling/${profile_id}"
recovery="${result_dir}/stop-profile-recovery.txt"
sampled_json="${result_dir}/phase-analysis-sampled.json"
cpu_json="${result_dir}/phase-analysis-rank0-cpu.json"
indexer_json="${result_dir}/indexer-breakdown-rank0.json"
indexer_md="${result_dir}/indexer-breakdown-rank0.md"
analysis_status="${result_dir}/analysis-status.txt"

grep -Fx 'trace_files=16' "${recovery}"
grep -Fx 'trace_export_stable=true' "${recovery}"
grep -Fx 'trace_gzip_valid=true' "${recovery}"
test "$(find "${trace_dir}" -maxdepth 1 -type f -name '*.json.gz' | wc -l)" -eq 16
test ! -e "${sampled_json}"
test ! -e "${cpu_json}"
test ! -e "${indexer_json}"
test ! -e "${indexer_md}"
test ! -e "${analysis_status}"

rank0_trace="$(find "${trace_dir}" -maxdepth 1 -type f -name '*_rank0.*.json.gz' -print -quit)"
test -n "${rank0_trace}"

python3 "${case_root}/commands/analyze-hy4-profile-sampled-phases-20260915.py" \
  --trace-dir "${trace_dir}" --output "${sampled_json}" --top 160 \
  --analyzed-ranks 0,1,15 \
  >"${result_dir}/phase-analysis-sampled.stdout" \
  2>"${result_dir}/phase-analysis-sampled.stderr" &
sampled_pid=$!

python3 "${case_root}/commands/analyze_hy4_indexer_breakdown_v2.py" \
  "${rank0_trace}" "${indexer_json}" "${indexer_md}" \
  >"${result_dir}/indexer-breakdown-rank0.stdout" \
  2>"${result_dir}/indexer-breakdown-rank0.stderr" &
indexer_pid=$!

wait "${sampled_pid}"
wait "${indexer_pid}"

python3 "${case_root}/commands/analyze-hy4-profile-rank0-cpu-phases-20260915.py" \
  --trace-dir "${trace_dir}" --output "${cpu_json}" --top 160 \
  --analyzed-ranks 0 \
  >"${result_dir}/phase-analysis-rank0-cpu.stdout" \
  2>"${result_dir}/phase-analysis-rank0-cpu.stderr"

test -s "${sampled_json}"
test -s "${cpu_json}"
test -s "${indexer_json}"
test -s "${indexer_md}"
printf 'analysis_completed_at=%s\ntrace_validity=salvaged_16_of_16_gzip_valid\nclient_result_state=incomplete_stop_profile_response_missing\ndeeply_analyzed_ranks=0,1,15\nindexer_rank=0\nservice_stopped=true\n' \
  "$(date --iso-8601=seconds)" >"${analysis_status}"
