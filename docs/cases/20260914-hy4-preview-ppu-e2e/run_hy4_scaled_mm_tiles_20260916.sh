#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
container=hy4-opt-20260914
run_id=scaled-mm-prefill-tiles-20260916-01
result_dir="${case_root}/results/operators/${run_id}"

test ! -e "${result_dir}"
mkdir -p "${result_dir}"

docker exec "${container}" python \
  "${case_root}/commands/benchmark_hy4_scaled_mm_tiles_20260916.py" \
  >"${result_dir}/benchmark.stdout" \
  2>"${result_dir}/benchmark.stderr"

grep '^SUMMARY=' "${result_dir}/benchmark.stdout" \
  | sed 's/^SUMMARY=//' \
  >"${result_dir}/summary.json"
python3 -m json.tool "${result_dir}/summary.json" >/dev/null
sha256sum "${result_dir}/summary.json" >"${result_dir}/summary.json.sha256"
