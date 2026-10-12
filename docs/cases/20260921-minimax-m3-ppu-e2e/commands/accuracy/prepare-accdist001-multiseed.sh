#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
run_root=${case_root}/accuracy/accdist-001-gpqa-c64-multiseed3
control=${case_root}/commands/accuracy
workspace=${case_root}/commands/formal-eval-workspace
startup=${case_root}/logs/fw006-targeted-reflection-retained-server.log

test ! -e "${run_root}"
mkdir -p "${run_root}/control"
cp "${control}/accdist001-aggregate-contract.json" "${run_root}/aggregate-contract.json"
cp "${control}/aggregate-accdist001.py" "${run_root}/control/aggregate-accdist001.py"
docker inspect minimax-m3-eval-e2e-20260921 > "${run_root}/evaluator.inspect.json"
docker exec minimaxM3-opt-20260921 python3 \
  "${case_root}/commands/performance/capture-baseline-service.py" > "${run_root}/service-runtime.json"
python3 "${control}/build-fw006-formal-service-manifest.py" \
  "${run_root}/service-runtime.json" "${startup}" "${run_root}/service-manifest.json"

for seed in 1234 2026 3407; do
  seed_root=${run_root}/seed-${seed}
  mkdir -p "${seed_root}/native"
  cp "${control}/accdist001-seed-${seed}.json" "${seed_root}/config.json"
  docker exec minimax-m3-eval-e2e-20260921 python3 \
    "${workspace}/evaluation/accuracy/formal_accuracy.py" \
    --config "${seed_root}/config.json" \
    --evaluation-inspect "${run_root}/evaluator.inspect.json" \
    --capture-provenance "${seed_root}/task-provenance.json" \
    > "${seed_root}/provenance.log" 2>&1
  python3 "${control}/freeze-fw006-formal-contract.py" \
    "${seed_root}/task-provenance.json" "${seed_root}/contract.json"
  docker exec minimax-m3-eval-e2e-20260921 python3 \
    "${workspace}/evaluation/accuracy/formal_accuracy.py" \
    --config "${seed_root}/config.json" \
    --contract "${seed_root}/contract.json" \
    --service-manifest "${run_root}/service-manifest.json" \
    --evaluation-inspect "${run_root}/evaluator.inspect.json" \
    --preflight-only > "${seed_root}/preflight.log" 2>&1
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
