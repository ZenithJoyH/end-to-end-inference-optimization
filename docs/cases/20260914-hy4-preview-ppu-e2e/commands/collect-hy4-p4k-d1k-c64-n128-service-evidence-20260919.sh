#!/usr/bin/env bash
set -euo pipefail

container=hy4-opt-20260914
run_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/performance/20260919-p4k-d1k-c64-n128-current-opt-01
service_dir="${run_root}/service"
evidence="${service_dir}/runtime-evidence.txt"

curl --silent --show-error --fail --max-time 5 http://127.0.0.1:8010/health >/dev/null
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
' >"${evidence}"

{
  printf 'captured_at=%s\n' "$(date --iso-8601=seconds)"
  printf 'host_alias=PPU-07\n'
  printf 'container=%s\n' "${container}"
  printf 'container_id=%s\n' "$(docker inspect -f '{{.Id}}' "${container}")"
  printf 'container_image_id=%s\n' "$(docker inspect -f '{{.Image}}' "${container}")"
  printf 'models_sha256=%s\n' "$(sha256sum "${service_dir}/models.json" | awk '{print $1}')"
  printf 'start_script_sha256=%s\n' "$(sha256sum /mnt/nfs/users/jinghao/hy4-preview/start_hyv4-preview.sh | awk '{print $1}')"
  printf 'service_log_prefix_cache_false=%s\n' "$(grep -c 'enable_prefix_caching=False' "${service_dir}/service.log" || true)"
  printf 'service_log_graph_capture_51=%s\n' "$(grep -c '100%.*51/51' "${service_dir}/service.log" || true)"
  printf 'service_log_startup_complete=%s\n' "$(grep -c 'Application startup complete' "${service_dir}/service.log" || true)"
} >>"${evidence}"

sha256sum \
  "${service_dir}/container-inspect.json" \
  "${service_dir}/models.json" \
  "${service_dir}/runtime-evidence.txt" \
  "${service_dir}/service.log" \
  "${service_dir}/source-identities.txt" \
  "${service_dir}/start_hyv4-preview.sh" \
  >"${service_dir}/service-artifacts.sha256"

cat "${evidence}"
sha256sum "${evidence}"

