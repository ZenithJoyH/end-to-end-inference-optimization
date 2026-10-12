#!/usr/bin/env bash
set -euo pipefail

transition_id=${1:?usage: stop-minimax-service-for-microbenchmark.sh TRANSITION_ID}
case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
transition=${case_dir}/transitions/${transition_id}

test ! -e "${transition}"
if ps -eo args | grep -q '[v]llm bench serve.*--port 8023'; then
  echo "benchmark client is still active" >&2
  exit 2
fi
mkdir -p "${transition}"
docker top "${container}" -eo pid,ppid,etimes,stat,cmd > "${transition}/processes.before.txt"
ppu-smi -q -d PIDS > "${transition}/ppu-pids.before.txt" 2>&1
mapfile -t pids < <(docker exec "${container}" pgrep -f '^python -m vllm.entrypoints.openai.api_server .* --port 8023( |$)')
test "${#pids[@]}" -eq 1
old_pid=${pids[0]}
printf '%s\n' "${old_pid}" > "${transition}/service.pid"
docker exec "${container}" kill -TERM "${old_pid}"
stopped=false
for _ in $(seq 1 240); do
  if ! docker exec "${container}" kill -0 "${old_pid}" 2>/dev/null; then stopped=true; break; fi
  sleep 1
done
test "${stopped}" = true
for _ in $(seq 1 240); do
  test -z "$(ppu-smi --query-compute-apps=pid --format=csv,noheader,nounits)" && break
  sleep 1
done
test -z "$(ppu-smi --query-compute-apps=pid --format=csv,noheader,nounits)"
if ss -ltnp | grep -qE ':8023\b'; then
  echo "port 8023 remains in use" >&2
  exit 3
fi
docker top "${container}" -eo pid,ppid,etimes,stat,cmd > "${transition}/processes.after.txt"
ppu-smi -q -d PIDS > "${transition}/ppu-pids.after.txt" 2>&1
sha256sum "$0" "${transition}"/*.txt > "${transition}/SHA256SUMS"
