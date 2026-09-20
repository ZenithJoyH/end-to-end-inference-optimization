#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
profile_id=p4k-d16-c16-n16-indexer-body-reprofile-20260919-12
trace_dir=${case_root}/profiling/${profile_id}/traces
result_dir=${case_root}/results/profiling/${profile_id}
shape_script=${case_root}/commands/analyze-hy4-indexer-body-shapes-20260919.py
parent_script=${case_root}/commands/analyze-hy4-indexer-parent-chains-20260919.py
shape_output=${result_dir}/indexer-body-shapes-rank0.json
shape_log=${result_dir}/indexer-body-shapes-rank0.log
parent_output=${result_dir}/indexer-parent-chains-rank0.json
parent_log=${result_dir}/indexer-parent-chains-rank0.log

test -s "${result_dir}/analysis-status.txt"
test -s "${shape_script}"
test -s "${parent_script}"
test ! -e "${shape_output}"
test ! -e "${shape_log}"
test ! -e "${parent_output}"
test ! -e "${parent_log}"

rank0_trace="$(find "${trace_dir}" -maxdepth 1 -type f -name '*_rank0.*.json.gz' -print -quit)"
test -n "${rank0_trace}"

python3 "${shape_script}" "${rank0_trace}" --output "${shape_output}" >"${shape_log}" 2>&1 &
shape_pid=$!
python3 "${parent_script}" "${rank0_trace}" --output "${parent_output}" >"${parent_log}" 2>&1 &
parent_pid=$!
wait "${shape_pid}"
wait "${parent_pid}"

test -s "${shape_output}"
test -s "${parent_output}"
printf 'shape_analysis=%s\nparent_chain_analysis=%s\n' "${shape_output}" "${parent_output}"
