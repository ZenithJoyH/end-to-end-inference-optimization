#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
script="${case_root}/commands/benchmark-hy4-sparse-mla-hq4-bk32-sq-sweep-20260916.py"
result="${case_root}/results/sparse-mla-hq4-bk32-sq-sweep-20260916.jsonl"

test ! -e "${result}"
test -f "${script}"
set +u
source /usr/local/PPU_SDK/envsetup.sh
set -u
CUDA_VISIBLE_DEVICES=0 python3 "${script}" | tee "${result}"
grep -q '^SUMMARY={"status": "passed"' "${result}"
