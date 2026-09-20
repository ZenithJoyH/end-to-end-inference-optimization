#!/usr/bin/env bash
set -euo pipefail

container=hy4-opt-20260914
run_id=20260919-p4k-d1k-c64-n128-current-opt-01
case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
run_root="${case_root}/results/performance/${run_id}"
service_dir="${run_root}/service"
start_script=/mnt/nfs/users/jinghao/hy4-preview/start_hyv4-preview.sh

test ! -e "${service_dir}"
test ! -e "${run_root}/config"
test ! -e "${run_root}/runs"
if ss -lnt | grep -q ':8010 '; then
  echo 'port 8010 is already in use' >&2
  exit 1
fi
if docker exec "${container}" bash -lc "pgrep -af 'vllm serve|vllm.entrypoints.openai.api_server'"; then
  echo 'a vLLM process is already running in the optimization container' >&2
  exit 1
fi

mkdir -p "${service_dir}" "${run_root}/config" "${run_root}/bundle/evaluation/performance" "${run_root}/runs"
cp "${start_script}" "${service_dir}/start_hyv4-preview.sh"
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
  sha256sum \
    /workspace/vllm-plugin-FL/vllm_fl/models/hy_v4.py \
    /workspace/vllm-plugin-FL/tests/unit_tests/models/test_hy_v4.py \
    /workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/vendor/thead/impl/hyv4_indexer.py \
    /workspace/FlagGems-vllm/src/flaggems_vllm/runtime/backend/_thead/fused/flashmla_sparse.py \
    /workspace/FlagGems-vllm/src/flaggems_vllm/runtime/backend/_thead/ops/fused_moe.py \
    /workspace/FlagGems-vllm/tests/test_thead_hy4_ops.py
' >"${service_dir}/source-identities.txt"

docker exec "${container}" bash -lc "cd '${service_dir}' && bash '${start_script}'"

ready=0
for attempt in $(seq 1 180); do
  if curl --silent --show-error --fail --max-time 5 http://127.0.0.1:8010/health >/dev/null 2>&1; then
    ready=1
    break
  fi
  if ! docker exec "${container}" bash -lc "pgrep -af 'vllm serve|vllm.entrypoints.openai.api_server'" >/dev/null; then
    echo 'vLLM process exited before readiness' >&2
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
  exit 1
fi

curl --silent --show-error --fail http://127.0.0.1:8010/v1/models >"${service_dir}/models.json"
docker exec "${container}" bash -lc '
  set -euo pipefail
  found=0
  for proc in /proc/[0-9]*; do
    test -r "$proc/cmdline" || continue
    cmd="$(tr "\0" " " <"$proc/cmdline")"
    case "$cmd" in
      "/usr/local/bin/python3.12 /usr/local/bin/vllm serve /mnt/cpfs/models/Hy4-preview-W8A8-linear-moe/"*"--port 8010"*)
        printf "container_api_pid=%s\napi_cmdline=%s\napi_starttime_ticks=%s\n" \
          "${proc##*/}" "$cmd" "$(awk "{print \$22}" "$proc/stat")"
        found=$((found + 1))
        ;;
    esac
  done
  test "$found" -eq 1
  python - <<"PY"
import importlib.util
for name in ("vllm", "vllm_fl", "flag_gems", "flaggems_vllm"):
    print(f"{name}_origin={importlib.util.find_spec(name).origin}")
PY
' >"${service_dir}/runtime-evidence.txt"

{
  printf 'captured_at=%s\n' "$(date --iso-8601=seconds)"
  printf 'host_alias=PPU-07\n'
  printf 'container=%s\n' "${container}"
  printf 'container_id=%s\n' "$(docker inspect -f '{{.Id}}' "${container}")"
  printf 'container_image_id=%s\n' "$(docker inspect -f '{{.Image}}' "${container}")"
  printf 'models_sha256=%s\n' "$(sha256sum "${service_dir}/models.json" | awk '{print $1}')"
  printf 'start_script_sha256=%s\n' "$(sha256sum "${start_script}" | awk '{print $1}')"
  printf 'service_log_prefix_cache_false=%s\n' "$(grep -c 'enable_prefix_caching=False' "${service_dir}/service.log")"
  printf 'service_log_startup_complete=%s\n' "$(grep -c 'Application startup complete' "${service_dir}/service.log")"
} >>"${service_dir}/runtime-evidence.txt"

sha256sum \
  "${service_dir}/container-inspect.json" \
  "${service_dir}/models.json" \
  "${service_dir}/runtime-evidence.txt" \
  "${service_dir}/service.log" \
  "${service_dir}/source-identities.txt" \
  "${service_dir}/start_hyv4-preview.sh" \
  >"${service_dir}/service-artifacts.sha256"

printf 'run_root=%s\n' "${run_root}"
cat "${service_dir}/runtime-evidence.txt"
