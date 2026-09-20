#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
profile_id=p4k-d16-c16-n16-full-prefix-hit-profile-20260919-11
trace_dir=${case_root}/profiling/${profile_id}/traces
result_dir=${case_root}/results/profiling/${profile_id}
script=${case_root}/commands/analyze-hy4-indexer-body-shapes-20260919.py
output=${result_dir}/indexer-body-shapes-rank0.json
log=${result_dir}/indexer-body-shapes-rank0.log

test -s "${script}"
test ! -e "${output}"
test ! -e "${log}"
rank0_trace="$(find "${trace_dir}" -maxdepth 1 -type f -name '*_rank0.*.json.gz' -print -quit)"
test -n "${rank0_trace}"
python3 "${script}" "${rank0_trace}" --output "${output}" >"${log}" 2>&1
test -s "${output}"
