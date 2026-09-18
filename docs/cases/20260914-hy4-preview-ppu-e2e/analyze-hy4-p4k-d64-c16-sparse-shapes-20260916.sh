#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
profile_id=p4k-d64-c16-n16-concurrency-capture-20260916-04
trace_dir="${case_dir}/profiling/${profile_id}/traces"
result_dir="${case_dir}/results/profiling/${profile_id}"
tool="${case_dir}/commands/inspect_sparse_mla_trace_shapes-20260915.py"
output="${result_dir}/sparse-mla-shape-correlation-rank0.json"

test -f "${tool}"
test ! -e "${output}"
rank0_trace="$(find "${trace_dir}" -maxdepth 1 -type f -name '*_rank0.*.json.gz' -print -quit)"
test -n "${rank0_trace}"

python3 "${tool}" "${rank0_trace}" "${output}" --sample-limit 32
test -s "${output}"
sha256sum "${output}" >"${output}.sha256"
echo "PASS: ${output}"
