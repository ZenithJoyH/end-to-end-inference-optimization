#!/usr/bin/env bash
set -euo pipefail

container=hy4-opt-20260914
case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
parent_root="${case_root}/results/performance/20260920-p16k-d1k-c64-n128-scenario-entry-01"
run_root="${case_root}/results/performance/20260920-p16k-d128-c16-n16-dual-partial-prefill-01"
command_root="${case_root}/commands/p16k-dual-partial-prefill-20260920"
config_dir="${run_root}/config"
service_root="${run_root}/service"
runner="${run_root}/bundle/evaluation/performance/vllm_perf.py"
comparator="${run_root}/bundle/evaluation/performance/compare_performance.py"
api_pid=
active_service_dir=

test ! -e "${run_root}"
test -f "${command_root}/plan.json"
test -f "${command_root}/comparison.json"
test -f "${command_root}/build-service-manifest.py"
test -f "${parent_root}/config/service-manifest.json"
test -d "${parent_root}/bundle/evaluation/performance"
if ss -lnt | grep -q ':8010 '; then
  echo 'port 8010 is already in use' >&2
  exit 1
fi
if docker exec "${container}" bash -lc "pgrep -af 'vllm serve|vllm.entrypoints.openai.api_server'"; then
  echo 'a vLLM process is already running in the optimization container' >&2
  exit 1
fi

mkdir -p "${config_dir}" "${service_root}" "${run_root}/bundle/evaluation" "${run_root}/runs"
cp -a "${parent_root}/bundle/evaluation/performance" "${run_root}/bundle/evaluation/"
cp "${command_root}/plan.json" "${config_dir}/plan.json"
cp "${command_root}/comparison.json" "${config_dir}/comparison.json"
cp "${parent_root}/config/service-manifest.json" "${config_dir}/service-manifest-base.json"

cleanup() {
  set +e
  if [[ -n "${api_pid}" ]]; then
    docker exec "${container}" kill -TERM "${api_pid}" >/dev/null 2>&1
  fi
  for _ in $(seq 1 90); do
    if ! ss -lnt | grep -q ':8010 '; then
      break
    fi
    sleep 2
  done
  if [[ -n "${active_service_dir}" ]]; then
    {
      printf 'cleanup_at=%s\n' "$(date --iso-8601=seconds)"
      printf 'api_pid=%s\n' "${api_pid:-not-captured}"
      printf 'port_8010_listeners=%s\n' "$(ss -lnt | grep -c ':8010 ' || true)"
    } >>"${active_service_dir}/stop-evidence.txt"
  fi
}
trap cleanup EXIT

run_config() {
  local label=$1
  local role=$2
  local mbt=$3
  local partial=$4
  local long_partial=$5
  local threshold=$6
  local service_dir="${service_root}/${label}"
  local manifest="${config_dir}/service-${label}.json"
  local run_id="${label}-01"
  active_service_dir="${service_dir}"
  api_pid=

  test ! -e "${service_dir}"
  test ! -e "${run_root}/runs/${run_id}"
  if ss -lnt | grep -q ':8010 '; then
    echo "port 8010 is in use before ${label}" >&2
    return 1
  fi
  mkdir -p "${service_dir}"
  docker inspect "${container}" >"${service_dir}/container-inspect.json"
  ppu-smi >"${service_dir}/ppu-smi-before.txt"
  docker exec "${container}" bash -lc '
    set -euo pipefail
    for repo in /workspace/vllm-plugin-FL /workspace/FlagGems-vllm /workspace/FlagGems; do
      printf "repo=%s\n" "$repo"
      git -C "$repo" branch --show-current
      git -C "$repo" rev-parse HEAD
      git -C "$repo" status --short
    done
  ' >"${service_dir}/source-identities.txt"

  docker exec "${container}" bash -lc "
    set -eo pipefail
    source /usr/local/PPU_SDK/envsetup.sh
    export PATH=/usr/lib64/openmpi/bin:\${PATH}
    export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}
    export GLOO_SOCKET_IFNAME=eth0
    export NCCL_IB_HCA=fic2_soe_bond
    export NCCL_IB_GID_INDEX=1
    export NCCL_IB_ADDR_FAMILY=6
    export NCCL_SOCKET_IFNAME=bond
    export NCCL_SOCKET_FAMILY=AF_INET6
    cd '${service_dir}'
    nohup env CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15 \
      VLLM_WORKER_MULTIPROC_METHOD=spawn VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=3600 \
      vllm serve /mnt/cpfs/models/Hy4-preview-W8A8-linear-moe/ \
      --served-model-name hy4 --host 0.0.0.0 --port 8010 --trust-remote-code \
      --reasoning-parser hy_v4 --tensor-parallel-size 16 --max-model-len 100000 \
      --max-num-batched-tokens '${mbt}' \
      --max-num-partial-prefills '${partial}' \
      --max-long-partial-prefills '${long_partial}' \
      --long-prefill-token-threshold '${threshold}' \
      --no-enable-prefix-caching \
      --compilation-config '{\"cudagraph_mode\":\"FULL_DECODE_ONLY\"}' \
      >service.log 2>&1 </dev/null &
  "

  local ready=0
  for attempt in $(seq 1 180); do
    if curl --silent --show-error --fail --max-time 5 http://127.0.0.1:8010/health >/dev/null 2>&1; then
      ready=1
      break
    fi
    if ! docker exec "${container}" bash -lc "pgrep -af 'vllm serve|vllm.entrypoints.openai.api_server'" >/dev/null; then
      tail -n 200 "${service_dir}/service.log" >&2
      return 1
    fi
    if (( attempt % 6 == 0 )); then
      printf 'label=%s readiness_wait_seconds=%s\n' "${label}" "$((attempt * 10))"
    fi
    sleep 10
  done
  test "${ready}" -eq 1

  api_pid=$(docker exec "${container}" bash -lc '
    set -euo pipefail
    found=()
    for proc in /proc/[0-9]*; do
      test -r "$proc/cmdline" || continue
      cmd="$(tr "\0" " " <"$proc/cmdline")"
      case "$cmd" in
        "/usr/local/bin/python3.12 /usr/local/bin/vllm serve /mnt/cpfs/models/Hy4-preview-W8A8-linear-moe/"*"--port 8010"*) found+=("${proc##*/}") ;;
      esac
    done
    test "${#found[@]}" -eq 1
    printf "%s" "${found[0]}"
  ')
  local start_ticks
  local api_cmdline
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

  local plugin_sha
  local fgv_sha
  local fg_sha
  plugin_sha=$(docker exec "${container}" bash -lc 'sha256sum /workspace/vllm-plugin-FL/vllm_fl/models/hy_v4.py /workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/vendor/thead/impl/hyv4_indexer.py /workspace/vllm-plugin-FL/vllm_fl/worker/scheduler_fl.py' | sha256sum | awk '{print $1}')
  fgv_sha=$(docker exec "${container}" bash -lc 'sha256sum /workspace/FlagGems-vllm/src/flaggems_vllm/runtime/backend/_thead/fused/flashmla_sparse.py /workspace/FlagGems-vllm/src/flaggems_vllm/runtime/backend/_thead/ops/fused_moe.py' | sha256sum | awk '{print $1}')
  fg_sha=$(docker exec "${container}" bash -lc 'git -C /workspace/FlagGems rev-parse HEAD; git -C /workspace/FlagGems status --porcelain' | sha256sum | awk '{print $1}')

  python3 "${command_root}/build-service-manifest.py" \
    --base "${config_dir}/service-manifest-base.json" \
    --runtime-evidence "${service_dir}/runtime-evidence.txt" \
    --plugin-sha256 "${plugin_sha}" \
    --flaggems-vllm-sha256 "${fgv_sha}" \
    --flaggems-sha256 "${fg_sha}" \
    --max-num-batched-tokens "${mbt}" \
    --max-num-partial-prefills "${partial}" \
    --max-long-partial-prefills "${long_partial}" \
    --long-prefill-token-threshold "${threshold}" \
    --output "${manifest}"

  docker exec "${container}" python3 "${runner}" \
    --config "${config_dir}/plan.json" \
    --comparison-contract "${config_dir}/comparison.json" \
    --service-manifest "${manifest}" \
    --role "${role}" --run-id "${run_id}" --scope performance_only \
    --output-dir "${run_root}/runs" --dry-run >"${config_dir}/dry-run-${label}.json"
  docker exec "${container}" python3 "${runner}" \
    --config "${config_dir}/plan.json" \
    --comparison-contract "${config_dir}/comparison.json" \
    --service-manifest "${manifest}" \
    --role "${role}" --run-id "${run_id}" --scope performance_only \
    --output-dir "${run_root}/runs"

  docker exec "${container}" kill -TERM "${api_pid}"
  for _ in $(seq 1 90); do
    if ! ss -lnt | grep -q ':8010 '; then
      break
    fi
    sleep 2
  done
  if ss -lnt | grep -q ':8010 '; then
    echo "service ${label} did not stop" >&2
    return 1
  fi
  printf 'stopped_at=%s\napi_pid=%s\nport_released=true\n' \
    "$(date --iso-8601=seconds)" "${api_pid}" >"${service_dir}/stop-evidence.txt"
  ppu-smi >"${service_dir}/ppu-smi-after-stop.txt"
  api_pid=
  active_service_dir=
}

run_config baseline baseline 2048 1 1 0
run_config candidate candidate 4096 2 2 2048
run_config revert revert 2048 1 1 0

docker exec "${container}" python3 "${comparator}" \
  --contract "${config_dir}/comparison.json" \
  --run-record "${run_root}/runs/baseline-01/run-record.json" \
  --run-record "${run_root}/runs/candidate-01/run-record.json" \
  --run-record "${run_root}/runs/revert-01/run-record.json" \
  --output "${run_root}/comparison-result.json"

sha256sum \
  "${config_dir}/plan.json" "${config_dir}/comparison.json" \
  "${config_dir}/service-baseline.json" "${config_dir}/service-candidate.json" \
  "${config_dir}/service-revert.json" "${run_root}/comparison-result.json" \
  >"${run_root}/artifacts.sha256"
echo "PASS: ${run_root}"
