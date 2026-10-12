#!/usr/bin/env bash
set -euo pipefail

run_root=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/accuracy/accdist-001-gpqa-c64-multiseed3

test ! -e "${run_root}/prepared-at.txt"
for seed in 1234 2026 3407; do
  grep -F 'Preflight passed; no evaluation was started' \
    "${run_root}/seed-${seed}/preflight.log" >/dev/null
done
sha256sum \
  "${run_root}/aggregate-contract.json" \
  "${run_root}/control/aggregate-accdist001.py" \
  "${run_root}/evaluator.inspect.json" \
  "${run_root}/service-runtime.json" \
  "${run_root}/service-manifest.json" \
  "${run_root}"/seed-*/config.json \
  "${run_root}"/seed-*/task-provenance.json \
  "${run_root}"/seed-*/contract.json > "${run_root}/SHA256SUMS.preflight"
date -Iseconds > "${run_root}/prepared-at.txt"
