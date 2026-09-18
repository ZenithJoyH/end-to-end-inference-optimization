#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
profile_id=p4k-d128-c32-n32-scaled-mm-reprofile-20260916-07
trace_dir="${case_root}/profiling/${profile_id}/traces"
result_dir="${case_root}/results/profiling/${profile_id}"
output="${result_dir}/fused-moe-shapes-rank0.json"
script="${case_root}/commands/analyze-hy4-fused-moe-shapes-20260916.py"

test ! -e "${output}"
rank0_trace="$(find "${trace_dir}" -maxdepth 1 -type f -name '*_rank0.*.json.gz' -print -quit)"
test -n "${rank0_trace}"
python3 "${script}" "${rank0_trace}" --output "${output}"
test -s "${output}"
python3 -m json.tool "${output}" >/dev/null
sha256sum "${output}" >"${output}.sha256"
