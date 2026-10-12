#!/usr/bin/env bash
set -euo pipefail

transition_id=${1:?usage: switch-minimax-service.sh TRANSITION_ID COMMAND_FILE LOG_FILE}
command_file=${2:?missing command file}
log_file=${3:?missing log file}
case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
transition=${case_dir}/transitions/${transition_id}

test -f "${command_file}"
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
docker top "${container}" -eo pid,ppid,etimes,stat,cmd > "${transition}/processes.after-stop.txt"
ppu-smi -q -d PIDS > "${transition}/ppu-pids.after-stop.txt" 2>&1

test ! -e "${log_file}"
docker exec -d --workdir "${case_dir}" "${container}" bash "${command_file}"
ready=false
for _ in $(seq 1 360); do
  if curl -fsS --max-time 5 http://127.0.0.1:8023/health >/dev/null 2>&1; then ready=true; break; fi
  sleep 5
done
test "${ready}" = true
grep -F "'enable_prefix_caching': False" "${log_file}" >/dev/null
grep -F 'Capturing CUDA graphs (decode, FULL): 100%' "${log_file}" >/dev/null
grep -F 'Application startup complete' "${log_file}" >/dev/null

payload='{"model":"MiniMax-M3","messages":[{"role":"user","content":"中国的首都是什么？只回答城市名。"}],"max_tokens":32,"temperature":0}'
printf '%s\n' "${payload}" > "${transition}/smoke.request.json"
curl -fsS --max-time 600 -H 'Content-Type: application/json' -d "${payload}" \
  http://127.0.0.1:8023/v1/chat/completions > "${transition}/smoke.response.json"
python3 -c 'import json,sys; x=json.load(open(sys.argv[1])); s=x["choices"][0]["message"]["content"]; assert "北京" in s and "\0" not in s' "${transition}/smoke.response.json"
docker top "${container}" -eo pid,ppid,etimes,stat,cmd > "${transition}/processes.after-launch.txt"
ppu-smi -q -d PIDS > "${transition}/ppu-pids.after-launch.txt" 2>&1
sha256sum "${command_file}" "${log_file}" "${transition}"/*.txt "${transition}"/*.json > "${transition}/SHA256SUMS"
