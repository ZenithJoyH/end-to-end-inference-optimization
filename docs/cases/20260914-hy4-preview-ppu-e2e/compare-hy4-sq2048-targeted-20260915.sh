#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e

/usr/local/bin/python3.12 \
  "${case_root}/commands/evaluation/performance/compare_performance.py" \
  --contract "${case_root}/configs/comparison-sq2048-bk32-targeted-p4k-20260915.json" \
  --run-record "${case_root}/results/performance/baseline-sq2048-bk32-p4k-20260915-01/run-record.json" \
  --run-record "${case_root}/results/performance/candidate-sq2048-bk32-p4k-20260915-01/run-record.json" \
  --run-record "${case_root}/results/performance/revert-sq2048-bk32-p4k-20260915-01/run-record.json" \
  --output "${case_root}/results/performance/sq2048-bk32-targeted-comparison-20260915.json"
