#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
profile_root=${case_dir}/profiling/fw-003-bounded-mixed-stall-capture
trace_dir=${profile_root}/traces
client_dir=${profile_root}/client
runner=${case_dir}/commands/performance/vllm_profile.py

test -f "${runner}"
test -d "${trace_dir}"
test ! -e "${profile_root}/capture.console.log"
mkdir -p "${profile_root}/timelines"

cleanup() {
  local child
  for child in ${monitor_pids:-}; do
    kill "${child}" 2>/dev/null || true
  done
  wait ${monitor_pids:-} 2>/dev/null || true
}
trap cleanup EXIT INT TERM

ppu-smi --query-ppu=timestamp,index,utilization.ppu,utilization.memory,memory.used,power.draw,temperature.ppu,clocks.current.cu \
  --format=csv,noheader,nounits --loop=2 > "${profile_root}/timelines/ppu.csv" 2>&1 &
monitor_pids=$!
vmstat -t 1 > "${profile_root}/timelines/vmstat.txt" 2>&1 &
monitor_pids="${monitor_pids} $!"
pidstat -u -r -d -h 1 > "${profile_root}/timelines/pidstat.txt" 2>&1 &
monitor_pids="${monitor_pids} $!"

docker exec minimaxM3-opt-20260921 python3 "${runner}" \
  --model MiniMax-M3 --tokenizer /mnt/cpfs/models/MiniMax-M3 \
  --host 127.0.0.1 --port 8023 --endpoint /v1/completions \
  --case 1024,256,64,128 --runs 3 --warmup-rounds 1 --profile-runs all \
  --timeout 1800 --profile-dir "${trace_dir}" --output-dir "${client_dir}" \
  --dry-run > "${profile_root}/dry-run.json"
test -s "${profile_root}/dry-run.json"

docker exec minimaxM3-opt-20260921 python3 "${runner}" \
  --model MiniMax-M3 --tokenizer /mnt/cpfs/models/MiniMax-M3 \
  --host 127.0.0.1 --port 8023 --endpoint /v1/completions \
  --case 1024,256,64,128 --runs 3 --warmup-rounds 1 --profile-runs all \
  --timeout 1800 --profile-dir "${trace_dir}" --output-dir "${client_dir}" \
  > "${profile_root}/capture.console.log" 2>&1

cleanup
trap - EXIT INT TERM
find "${trace_dir}" -maxdepth 1 -type f -printf '%f\t%s\n' | sort > "${profile_root}/trace-inventory.txt"
sha256sum "${profile_root}/dry-run.json" "${profile_root}/capture.console.log" \
  "${profile_root}/trace-inventory.txt" "${profile_root}"/timelines/* > "${profile_root}/SHA256SUMS.control"
