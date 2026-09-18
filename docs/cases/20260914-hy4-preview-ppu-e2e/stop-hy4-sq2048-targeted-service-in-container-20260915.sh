#!/usr/bin/env bash
set -euo pipefail

test "$#" -eq 1
tag="$1"
case "$tag" in
  *[!A-Za-z0-9._-]*|'')
    echo "invalid service tag" >&2
    exit 2
    ;;
esac

container=hy4-opt-20260914
case_dir=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
service_dir="${case_dir}/logs/${tag}"
test -s "${service_dir}/api.pid"

# api.pid is written inside the container's PID namespace. Signal it in the
# same namespace instead of treating it as a host PID.
docker exec --env STOP_TAG="$tag" "$container" bash -lc '
  set -euo pipefail
  case_dir=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
  service_dir="${case_dir}/logs/${STOP_TAG}"
  pid="$(cat "${service_dir}/api.pid")"
  if kill -0 "$pid" >/dev/null 2>&1; then
    kill -TERM "$pid"
  fi
  for _attempt in $(seq 1 180); do
    if ! kill -0 "$pid" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  if kill -0 "$pid" >/dev/null 2>&1; then
    kill -KILL "$pid"
  fi
'

for _attempt in $(seq 1 60); do
  if ! docker top "$container" -eo pid,args | grep -Eq '[v]llm serve|VLLM::(EngineCore|Worker)'; then
    break
  fi
  sleep 1
done
if docker top "$container" -eo pid,args | grep -Eq '[v]llm serve|VLLM::(EngineCore|Worker)'; then
  echo "ERROR: vLLM processes remain in ${container} after stop" >&2
  docker top "$container" -eo pid,ppid,args >&2
  exit 1
fi
if ss -ltn | grep -q ':8010 '; then
  echo "ERROR: port 8010 remains occupied" >&2
  exit 1
fi

printf 'stopped_at=%s\nresult=stopped\npid_namespace=container\n' \
  "$(date --iso-8601=seconds)" >"${service_dir}/stop-result.txt"
echo "PASS: service stopped in container namespace tag=${tag}"
