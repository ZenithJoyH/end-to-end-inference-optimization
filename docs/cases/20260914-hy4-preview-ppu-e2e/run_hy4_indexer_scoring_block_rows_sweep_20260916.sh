#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
tool="${case_dir}/commands/benchmark_hy4_indexer_scoring_block_rows-r3-20260916.py"
output="${case_dir}/results/indexer-scoring-block-rows-sweep-r3-20260916.jsonl"

test -f "${tool}"
test ! -e "${output}"
set +u
source /usr/local/PPU_SDK/envsetup.sh
set -u
CUDA_VISIBLE_DEVICES=0 python3 "${tool}" | tee "${output}"
grep -q '^SUMMARY={"status": "passed"' "${output}"
sha256sum "${output}" >"${output}.sha256"
