#!/usr/bin/env bash
set -euo pipefail

container=hy4-opt-20260914
run_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/performance/20260919-p4k-d1k-c64-n128-current-opt-01
service_dir="${run_root}/service"

docker exec "${container}" bash -lc '
  set -euo pipefail
  pids=()
  for proc in /proc/[0-9]*; do
    test -r "$proc/cmdline" || continue
    cmd="$(tr "\0" " " <"$proc/cmdline")"
    case "$cmd" in
      "/usr/local/bin/python3.12 /usr/local/bin/vllm serve /mnt/cpfs/models/Hy4-preview-W8A8-linear-moe/"*"--port 8010"*)
        pids+=("${proc##*/}")
        ;;
    esac
  done
  test "${#pids[@]}" -eq 1
  printf "stopping_container_api_pid=%s\n" "${pids[0]}"
  kill -TERM "${pids[0]}"
' >"${service_dir}/stop-evidence.txt"

stopped=0
for attempt in $(seq 1 60); do
  if ! ss -lnt | grep -q ':8010 '; then
    stopped=1
    break
  fi
  sleep 2
done
if [[ "${stopped}" != 1 ]]; then
  echo 'service did not stop after SIGTERM within 120 seconds' >&2
  exit 1
fi

{
  printf 'stopped_at=%s\n' "$(date --iso-8601=seconds)"
  printf 'port_8010_listeners_after_stop=%s\n' "$(ss -lnt | grep -c ':8010 ' || true)"
  docker exec "${container}" bash -lc "pgrep -af 'vllm serve|vllm.entrypoints.openai.api_server' || true"
} >>"${service_dir}/stop-evidence.txt"
ppu-smi >"${service_dir}/ppu-smi-after-stop.txt"
sha256sum "${service_dir}/stop-evidence.txt" "${service_dir}/ppu-smi-after-stop.txt" \
  >"${service_dir}/stop-artifacts.sha256"
cat "${service_dir}/stop-evidence.txt"

