#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
profile_root=${case_dir}/profiling/prof-002-current-131k-p1k-mixed
trace_dir=${profile_root}/traces
client_dir=${profile_root}/client
runner=${case_dir}/commands/performance/vllm_profile.py

test -f "${runner}"
test -d "${trace_dir}"
test -z "$(find "${trace_dir}" -maxdepth 1 -type f -print -quit)"
test -s "${profile_root}/dry-run.json"
test ! -e "${profile_root}/capture.console.log"
test ! -e "${client_dir}"
curl -fsS --max-time 5 http://127.0.0.1:8023/health >/dev/null
docker exec minimaxM3-opt-20260921 python3 \
  "${case_dir}/commands/performance/verify-live-baseline-service.py" \
  "${profile_root}/service-manifest.json"

docker exec minimaxM3-opt-20260921 python3 "${runner}" \
  --model MiniMax-M3 --tokenizer /mnt/cpfs/models/MiniMax-M3 \
  --host 127.0.0.1 --port 8023 --endpoint /v1/completions \
  --case 1024,128,64,64 --runs 2 --warmup-rounds 1 --profile-runs last \
  --timeout 1800 --profile-dir "${trace_dir}" --output-dir "${client_dir}" \
  > "${profile_root}/capture.console.log" 2>&1

find "${trace_dir}" -maxdepth 1 -type f -printf '%f\t%s\n' | sort > "${profile_root}/trace-inventory.txt"
sha256sum "${profile_root}/dry-run.json" "${profile_root}/capture.console.log" \
  "${profile_root}/trace-inventory.txt" > "${profile_root}/SHA256SUMS.control"
