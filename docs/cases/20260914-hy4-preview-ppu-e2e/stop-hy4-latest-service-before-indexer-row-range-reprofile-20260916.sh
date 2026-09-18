#!/usr/bin/env bash
set -euo pipefail

container=hy4-opt-20260914
case_dir=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
record="${case_dir}/logs/stop-before-indexer-row-range-reprofile-20260916.txt"

test "$(docker inspect -f '{{.State.Status}}' "${container}")" = running
api_pid="$(ss -lntp 'sport = :8010' | sed -n 's/.*pid=\([0-9][0-9]*\).*/\1/p' | head -n 1)"
test -n "${api_pid}"
test -r "/proc/${api_pid}/cmdline"
api_command="$(tr '\0' ' ' <"/proc/${api_pid}/cmdline")"
test "${api_command}" != "${api_command/vllm serve/}"
test "${api_command}" != "${api_command/--port 8010/}"
docker top "${container}" -eo pid,args | awk -v pid="${api_pid}" '$1 == pid && /vllm serve/ {found=1} END {exit !found}'

test ! -e "${record}"
printf 'container=%s\npid=%s\ncommand=%s\nreason=indexer_row_range_reprofile\nstopped_at=%s\n' \
  "${container}" "${api_pid}" "${api_command}" "$(date --iso-8601=seconds)" >"${record}"
kill -TERM "${api_pid}"
for _attempt in $(seq 1 240); do
  test ! -e "/proc/${api_pid}" && break
  sleep 1
done
test ! -e "/proc/${api_pid}"
for _attempt in $(seq 1 240); do
  if ! docker top "${container}" -eo pid,args | grep -E 'vllm serve|VLLM::(EngineCore|Worker)' >/dev/null; then
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
printf 'released_at=%s\nport_8010_released=true\nworkers_released=true\n' \
  "$(date --iso-8601=seconds)" >>"${record}"
echo "PASS: stopped ${container} vLLM service pid=${api_pid}"
