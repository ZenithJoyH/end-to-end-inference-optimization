#!/usr/bin/env bash
set -euo pipefail

container=hy4-opt-20260914
run_dir=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/accuracy/formal-gate-20260918-f7d1aaa-a26a902-01
record="${run_dir}/service/stopped-misconfigured-startup-container-namespace.txt"

test ! -e "${record}"
docker exec "${container}" bash -lc '
  set -euo pipefail
  pid="$(pgrep -f "^/usr/local/bin/python3.12 /usr/local/bin/vllm serve .*--port 8010$")"
  test -n "$pid"
  test "$pid" = "${pid%%$'\n'*}"
  printf "container_api_pid=%s\n" "$pid"
  kill -TERM "$pid"
  for _attempt in $(seq 1 60); do
    kill -0 "$pid" >/dev/null 2>&1 || exit 0
    sleep 1
  done
  exit 1
' >"${record}"
printf 'reason=prefix_cache_runtime_default_true\nstopped_at=%s\n' \
  "$(date --iso-8601=seconds)" >>"${record}"
for _attempt in $(seq 1 60); do
  if ! docker top "${container}" -eo pid,args | grep -Eq '[v]llm serve|VLLM::(EngineCore|Worker)'; then
    break
  fi
  sleep 1
done
if docker top "${container}" -eo pid,args | grep -E 'vllm serve|VLLM::(EngineCore|Worker)' >/dev/null; then
  docker top "${container}" -eo pid,args >&2
  exit 1
fi
if ss -ltn 'sport = :8010' | grep -q ':8010'; then
  echo 'port 8010 is still occupied' >&2
  exit 1
fi
printf 'port_8010_released=true\nworkers_released=true\n' >>"${record}"
