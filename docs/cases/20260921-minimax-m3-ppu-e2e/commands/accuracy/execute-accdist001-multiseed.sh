#!/usr/bin/env bash
set -u -o pipefail

case_root=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
run_root=${case_root}/accuracy/accdist-001-gpqa-c64-multiseed3
workspace=${case_root}/commands/formal-eval-workspace

date -Iseconds > "${run_root}/started-at.txt"
overall=0
for seed in 1234 2026 3407; do
  seed_root=${run_root}/seed-${seed}
  date -Iseconds > "${seed_root}/started-at.txt"
  docker exec minimax-m3-eval-e2e-20260921 python3 \
    "${workspace}/evaluation/accuracy/formal_accuracy.py" \
    --config "${seed_root}/config.json" \
    --contract "${seed_root}/contract.json" \
    --service-manifest "${run_root}/service-manifest.json" \
    --evaluation-inspect "${run_root}/evaluator.inspect.json" \
    > "${seed_root}/formal-run.log" 2>&1
  rc=$?
  printf '%s\n' "${rc}" > "${seed_root}/exit-code.txt"
  date -Iseconds > "${seed_root}/finished-at.txt"
  if ! find "${seed_root}/native" -name 'samples_*.jsonl' -type f | grep -q .; then
    overall=1
    break
  fi
  if ! find "${seed_root}/native" -name 'results_*.json' -type f | grep -q .; then
    overall=1
    break
  fi
done

if [ "${overall}" -eq 0 ]; then
  python3 "${run_root}/control/aggregate-accdist001.py" \
    --root "${run_root}" \
    --contract "${run_root}/aggregate-contract.json" \
    --output "${run_root}/aggregate-result.json" \
    > "${run_root}/aggregate.log" 2>&1 || overall=$?
fi
printf '%s\n' "${overall}" > "${run_root}/overall-exit-code.txt"
date -Iseconds > "${run_root}/finished-at.txt"
if [ -f "${run_root}/aggregate-result.json" ]; then
  sha256sum "${run_root}/aggregate-result.json" > "${run_root}/aggregate-result.SHA256"
fi
exit "${overall}"
