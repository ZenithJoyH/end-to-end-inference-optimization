#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
root=${case_dir}/profiling/fw-004-bounded-worker-stack-on-stall
client_dir=${root}/client
runner=${case_dir}/commands/performance/vllm_profile.py
container=minimaxM3-opt-20260921

test -f "${runner}"
test ! -e "${root}"
curl -fsS --max-time 5 http://127.0.0.1:8023/health >/dev/null
service_argv=$(docker exec "${container}" pgrep -af '^python -m vllm.entrypoints.openai.api_server .* --port 8023( |$)')
test -n "${service_argv}"
if grep -q -- '--profiler-config' <<< "${service_argv}"; then
  echo "profiler service is unexpectedly active" >&2
  exit 2
fi

mkdir -p "${root}/trigger"
docker top "${container}" -eo pid,ppid,etimes,stat,pcpu,pmem,cmd > "${root}/processes.before.txt"
mapfile -t worker_pids < <(docker top "${container}" -eo pid,cmd | awk '/VLLM::Worker_TP/ {print $1}' | sort -n)
test "${#worker_pids[@]}" -eq 16
printf '%s\n' "${worker_pids[@]}" > "${root}/worker-host-pids.txt"

docker exec "${container}" python3 "${runner}" \
  --model MiniMax-M3 --tokenizer /mnt/cpfs/models/MiniMax-M3 \
  --host 127.0.0.1 --port 8023 --endpoint /v1/completions \
  --case 1024,256,64,128 --runs 6 --warmup-rounds 0 --no-profile \
  --timeout 1800 --output-dir "${client_dir}" \
  --dry-run > "${root}/dry-run.json"

docker exec "${container}" python3 "${runner}" \
  --model MiniMax-M3 --tokenizer /mnt/cpfs/models/MiniMax-M3 \
  --host 127.0.0.1 --port 8023 --endpoint /v1/completions \
  --case 1024,256,64,128 --runs 6 --warmup-rounds 0 --no-profile \
  --timeout 1800 --output-dir "${client_dir}" \
  > "${root}/capture.console.log" 2>&1 &
client_pid=$!

armed=false
streak=0
triggered=false
current_bench_pid=""
while kill -0 "${client_pid}" 2>/dev/null; do
  bench_pid=$(pgrep -f '^/usr/local/bin/python[^ ]* /usr/local/bin/vllm bench serve .*--port 8023( |$)' | head -1 || true)
  if [[ -z "${bench_pid}" ]]; then
    current_bench_pid=""
    armed=false
    streak=0
    printf '%s\tactive=0\n' "$(date -Iseconds)" >> "${root}/trigger-samples.tsv"
    sleep 1
    continue
  fi
  if [[ "${bench_pid}" != "${current_bench_pid}" ]]; then
    current_bench_pid=${bench_pid}
    armed=false
    streak=0
  fi
  mapfile -t utils < <(ppu-smi --query-ppu=index,utilization.ppu --format=csv,noheader,nounits | awk -F, '{gsub(/ /,"",$2); print $2}')
  test "${#utils[@]}" -eq 16
  max_util=$(printf '%s\n' "${utils[@]}" | sort -n | tail -1)
  min_util=$(printf '%s\n' "${utils[@]}" | sort -n | head -1)
  if (( max_util >= 50 )); then
    armed=true
  fi
  if [[ "${armed}" = true ]] && (( max_util <= 20 )); then
    streak=$((streak + 1))
  else
    streak=0
  fi
  printf '%s\tactive=1\tbench_pid=%s\tarmed=%s\tmin=%s\tmax=%s\tstreak=%s\n' \
    "$(date -Iseconds)" "${bench_pid}" "${armed}" "${min_util}" "${max_util}" "${streak}" \
    >> "${root}/trigger-samples.tsv"
  if (( streak >= 2 )); then
    triggered=true
    date -Iseconds > "${root}/trigger/time.txt"
    ppu-smi --query-ppu=timestamp,index,utilization.ppu,utilization.memory,memory.used,power.draw \
      --format=csv,noheader,nounits > "${root}/trigger/ppu.csv"
    ps -eo pid,ppid,stat,pcpu,pmem,minflt,majflt,rss,vsz,wchan:24,cmd > "${root}/trigger/processes.txt"
    representative=("${worker_pids[0]}" "${worker_pids[5]}" "${worker_pids[10]}" "${worker_pids[15]}")
    for pid in "${representative[@]}"; do
      test -r "/proc/${pid}/status" || continue
      cp "/proc/${pid}/status" "${root}/trigger/${pid}.status"
      cp "/proc/${pid}/smaps_rollup" "${root}/trigger/${pid}.smaps_rollup"
      cat "/proc/${pid}/wchan" > "${root}/trigger/${pid}.wchan"
      cat "/proc/${pid}/stack" > "${root}/trigger/${pid}.kernel-stack" 2>&1 || true
      timeout 8 eu-stack -n 96 -p "${pid}" > "${root}/trigger/${pid}.eu-stack" 2>&1 || true
    done
    timeout 15 gstack "${representative[0]}" > "${root}/trigger/${representative[0]}.gstack" 2>&1 || true
    break
  fi
  sleep 1
done

wait "${client_pid}"
printf '%s\n' "${triggered}" > "${root}/triggered.txt"
diagnostic=$(find "${client_dir}/MiniMax-M3" -type f -name diagnostic.json -print -quit)
test -n "${diagnostic}"
python3 "${case_dir}/commands/performance/summarize-request-waves.py" \
  "$(dirname "${diagnostic}")" 'p1024-d256-c64-r?-????????.json' > "${root}/request-wave-summary.json"
curl -fsS --max-time 5 http://127.0.0.1:8023/health >/dev/null
payload='{"model":"MiniMax-M3","messages":[{"role":"user","content":"中国的首都是什么？只回答城市名。"}],"max_tokens":32,"temperature":0}'
printf '%s\n' "${payload}" > "${root}/smoke.request.json"
curl -fsS --max-time 600 -H 'Content-Type: application/json' -d "${payload}" \
  http://127.0.0.1:8023/v1/chat/completions > "${root}/smoke.response.json"
python3 -c 'import json,sys; x=json.load(open(sys.argv[1])); s=x["choices"][0]["message"]["content"]; assert "北京" in s and "\0" not in s' "${root}/smoke.response.json"
docker top "${container}" -eo pid,ppid,etimes,stat,pcpu,pmem,cmd > "${root}/processes.after.txt"
sha256sum "${root}/dry-run.json" "${root}/capture.console.log" "${root}/trigger-samples.tsv" \
  "${root}/triggered.txt" "${root}/request-wave-summary.json" > "${root}/SHA256SUMS.control"
