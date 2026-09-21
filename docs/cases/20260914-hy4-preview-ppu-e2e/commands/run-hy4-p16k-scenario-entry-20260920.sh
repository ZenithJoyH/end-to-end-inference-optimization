#!/usr/bin/env bash
set -euo pipefail

container=hy4-opt-20260914
case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
run_id=20260920-p16k-d1k-c64-n128-scenario-entry-01
run_root="${case_root}/results/performance/${run_id}"
command_root="${case_root}/commands/p16k-scenario-entry-20260920"
old_root="${case_root}/results/performance/20260919-p4k-d1k-c64-n128-current-opt-01"
service_dir="${run_root}/service"
config_dir="${run_root}/config"
runner="${run_root}/bundle/evaluation/performance/vllm_perf.py"
api_pid=

test ! -e "${run_root}"
test -f "${command_root}/plan.json"
test -f "${command_root}/comparison.json"
test -f "${command_root}/build-service-manifest.py"
test -f /mnt/nfs/users/jinghao/hy4-preview/start_hyv4-preview.sh
test -d "${old_root}/bundle/evaluation/performance"
test -f "${old_root}/config/service-manifest.json"

if ss -lnt | grep -q ':8010 '; then
  echo 'port 8010 is already in use' >&2
  exit 1
fi
if docker exec "${container}" bash -lc "pgrep -af 'vllm serve|vllm.entrypoints.openai.api_server'"; then
  echo 'a vLLM process is already running in the optimization container' >&2
  exit 1
fi

mkdir -p "${service_dir}" "${config_dir}" "${run_root}/bundle/evaluation" "${run_root}/runs"
cp -a "${old_root}/bundle/evaluation/performance" "${run_root}/bundle/evaluation/"
cp "${command_root}/plan.json" "${config_dir}/plan.json"
cp "${command_root}/comparison.json" "${config_dir}/comparison.json"
cp "${old_root}/config/service-manifest.json" "${config_dir}/service-manifest-base.json"
cp /mnt/nfs/users/jinghao/hy4-preview/start_hyv4-preview.sh "${service_dir}/start_hyv4-preview.sh"
docker inspect "${container}" >"${service_dir}/container-inspect.json"
ppu-smi >"${service_dir}/ppu-smi-before.txt"

stop_service() {
  set +e
  if [[ -n "${api_pid}" ]]; then
    docker exec "${container}" kill -TERM "${api_pid}" >>"${service_dir}/stop-evidence.txt" 2>&1
  fi
  for _ in $(seq 1 90); do
    if ! ss -lnt | grep -q ':8010 '; then
      break
    fi
    sleep 2
  done
  {
    printf 'stopped_at=%s\n' "$(date --iso-8601=seconds)"
    printf 'api_pid=%s\n' "${api_pid:-not-captured}"
    printf 'port_8010_listeners_after_stop=%s\n' "$(ss -lnt | grep -c ':8010 ' || true)"
  } >>"${service_dir}/stop-evidence.txt" 2>&1
  ppu-smi >"${service_dir}/ppu-smi-after-stop.txt" 2>&1
}
trap stop_service EXIT

docker exec "${container}" bash -lc '
  set -euo pipefail
  for repo in /workspace/vllm-plugin-FL /workspace/FlagGems-vllm /workspace/FlagGems; do
    printf "repo=%s\n" "$repo"
    git -C "$repo" branch --show-current
    git -C "$repo" rev-parse HEAD
    git -C "$repo" status --short
  done
' >"${service_dir}/source-identities.txt"

docker exec "${container}" bash -lc \
  "cd '${service_dir}' && nohup bash ./start_hyv4-preview.sh >./service.log 2>&1 </dev/null &"

ready=0
for attempt in $(seq 1 180); do
  if curl --silent --show-error --fail --max-time 5 http://127.0.0.1:8010/health >/dev/null 2>&1; then
    ready=1
    break
  fi
  if ! docker exec "${container}" bash -lc "pgrep -af 'vllm serve|vllm.entrypoints.openai.api_server'" >/dev/null; then
    echo 'service exited before readiness' >&2
    tail -n 200 "${service_dir}/service.log" >&2
    exit 1
  fi
  if (( attempt % 6 == 0 )); then
    printf 'readiness_wait_seconds=%s\n' "$((attempt * 10))"
  fi
  sleep 10
done
if [[ "${ready}" != 1 ]]; then
  echo 'service did not become ready within 1800 seconds' >&2
  tail -n 200 "${service_dir}/service.log" >&2
  exit 1
fi

api_pid=$(docker exec "${container}" bash -lc '
  set -euo pipefail
  found=()
  for proc in /proc/[0-9]*; do
    test -r "$proc/cmdline" || continue
    cmd="$(tr "\0" " " <"$proc/cmdline")"
    case "$cmd" in
      "/usr/local/bin/python3.12 /usr/local/bin/vllm serve /mnt/cpfs/models/Hy4-preview-W8A8-linear-moe/"*"--port 8010"*)
        found+=("${proc##*/}")
        ;;
    esac
  done
  test "${#found[@]}" -eq 1
  printf "%s" "${found[0]}"
')
start_ticks=$(docker exec "${container}" awk '{print $22}' "/proc/${api_pid}/stat")
api_cmdline=$(docker exec "${container}" bash -lc "tr '\\0' ' ' </proc/${api_pid}/cmdline")
curl --silent --show-error --fail http://127.0.0.1:8010/v1/models >"${service_dir}/models.json"
{
  printf 'captured_at=%s\n' "$(date --iso-8601=seconds)"
  printf 'host_alias=PPU-07\n'
  printf 'container=%s\n' "${container}"
  printf 'container_id=%s\n' "$(docker inspect -f '{{.Id}}' "${container}")"
  printf 'container_image_id=%s\n' "$(docker inspect -f '{{.Image}}' "${container}")"
  printf 'container_api_pid=%s\n' "${api_pid}"
  printf 'api_starttime_ticks=%s\n' "${start_ticks}"
  printf 'api_cmdline=%s\n' "${api_cmdline}"
  printf 'service_log_prefix_cache_false=%s\n' "$(grep -c 'enable_prefix_caching=False' "${service_dir}/service.log" || true)"
  printf 'service_log_startup_complete=%s\n' "$(grep -c 'Application startup complete' "${service_dir}/service.log" || true)"
} >"${service_dir}/runtime-evidence.txt"

plugin_sha=$(docker exec "${container}" bash -lc 'sha256sum /workspace/vllm-plugin-FL/vllm_fl/models/hy_v4.py /workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/vendor/thead/impl/hyv4_indexer.py /workspace/vllm-plugin-FL/vllm_fl/worker/scheduler_fl.py' | sha256sum | awk '{print $1}')
fgv_sha=$(docker exec "${container}" bash -lc 'sha256sum /workspace/FlagGems-vllm/src/flaggems_vllm/runtime/backend/_thead/fused/flashmla_sparse.py /workspace/FlagGems-vllm/src/flaggems_vllm/runtime/backend/_thead/ops/fused_moe.py' | sha256sum | awk '{print $1}')
fg_sha=$(docker exec "${container}" bash -lc 'git -C /workspace/FlagGems rev-parse HEAD; git -C /workspace/FlagGems status --porcelain' | sha256sum | awk '{print $1}')

python3 "${command_root}/build-service-manifest.py" \
  --base "${config_dir}/service-manifest-base.json" \
  --runtime-evidence "${service_dir}/runtime-evidence.txt" \
  --plugin-sha256 "${plugin_sha}" \
  --flaggems-vllm-sha256 "${fgv_sha}" \
  --flaggems-sha256 "${fg_sha}" \
  --output "${config_dir}/service-manifest.json"

docker exec "${container}" python3 "${runner}" \
  --config "${config_dir}/plan.json" \
  --comparison-contract "${config_dir}/comparison.json" \
  --service-manifest "${config_dir}/service-manifest.json" \
  --role baseline \
  --run-id scenario-entry-dry-run \
  --scope performance_only \
  --output-dir "${run_root}/runs" \
  --dry-run >"${config_dir}/dry-run.json"

set +e
docker exec "${container}" timeout --signal=TERM --kill-after=60 7200 \
  python3 "${runner}" \
  --config "${config_dir}/plan.json" \
  --comparison-contract "${config_dir}/comparison.json" \
  --service-manifest "${config_dir}/service-manifest.json" \
  --role baseline \
  --run-id scenario-entry-01 \
  --scope performance_only \
  --output-dir "${run_root}/runs" \
  >"${run_root}/runner.stdout" 2>"${run_root}/runner.stderr"
runner_rc=$?
set -e
printf '%s\n' "${runner_rc}" >"${run_root}/runner.exit-code"

sha256sum \
  "${config_dir}/plan.json" \
  "${config_dir}/comparison.json" \
  "${config_dir}/service-manifest.json" \
  "${config_dir}/dry-run.json" \
  "${service_dir}/runtime-evidence.txt" \
  "${service_dir}/source-identities.txt" \
  >"${run_root}/artifacts.sha256"

exit "${runner_rc}"
