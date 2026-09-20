#!/usr/bin/env bash
set -euo pipefail

container=hy4-opt-20260914
run_dir=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/accuracy/formal-gate-20260918-f7d1aaa-a26a902-01
evidence="${run_dir}/service/runtime-evidence.txt"

{
  printf 'captured_at=%s\n' "$(date --iso-8601=seconds)"
  printf 'host_alias=PPU-07\n'
  printf 'container=%s\n' "${container}"
  printf 'container_id=%s\n' "$(docker inspect -f '{{.Id}}' "${container}")"
  printf 'container_image_id=%s\n' "$(docker inspect -f '{{.Image}}' "${container}")"
  printf 'models_sha256=%s\n' "$(sha256sum "${run_dir}/service/models.json" | awk '{print $1}')"
  printf 'start_script_sha256=%s\n' "$(sha256sum /mnt/nfs/users/jinghao/hy4-preview/start_hyv4-preview.sh | awk '{print $1}')"
  printf 'service_log_prefix_cache_false=%s\n' "$(grep -c 'enable_prefix_caching=False' "${run_dir}/service/service.log")"
  printf 'service_log_graph_capture_51=%s\n' "$(grep -c '100%.*51/51' "${run_dir}/service/service.log")"
  printf 'service_log_startup_complete=%s\n' "$(grep -c 'Application startup complete' "${run_dir}/service/service.log")"
  docker exec "${container}" bash -lc '
    set -euo pipefail
    found=0
    for proc in /proc/[0-9]*; do
      test "${proc##*/}" = "$$" && continue
      test -r "$proc/cmdline" || continue
      cmd="$(tr "\0" " " <"$proc/cmdline")"
      case "$cmd" in
        *"/usr/local/bin/vllm serve /mnt/cpfs/models/Hy4-preview-W8A8-linear-moe/"*"--port 8010"*)
          printf "container_api_pid=%s\napi_cmdline=%s\napi_starttime_ticks=%s\n" \
            "${proc##*/}" "$cmd" "$(awk "{print \$22}" "$proc/stat")"
          found=$((found + 1))
          ;;
      esac
    done
    test "$found" -eq 1
    python -c "import importlib.util; [print(name + \"_origin=\" + str(importlib.util.find_spec(name).origin)) for name in (\"vllm\", \"vllm_fl\", \"flag_gems\", \"flaggems_vllm\")]"
  '
  cat "${run_dir}/service/source-identities.txt"
  cat "${run_dir}/service/engine-identity.txt"
  cat "${run_dir}/service/model-identity-files.sha256"
  cat "${run_dir}/service/tokenizer-identity-files.sha256"
} >"${evidence}"

plugin_sha256="$(awk -F= '/^repo=vllm-plugin-FL$/{seen=1;next} seen && /^workspace_sha256=/{print $2; exit}' "${run_dir}/service/source-identities.txt")"
flaggems_sha256="$(awk -F= '/^repo=FlagGems$/{seen=1;next} seen && /^workspace_sha256=/{print $2; exit}' "${run_dir}/service/source-identities.txt")"
flaggems_vllm_sha256="$(awk -F= '/^repo=FlagGems-vllm$/{seen=1;next} seen && /^workspace_sha256=/{print $2; exit}' "${run_dir}/service/source-identities.txt")"
combined_flaggems_sha256="$(printf '%s\n%s\n' "${flaggems_sha256}" "${flaggems_vllm_sha256}" | sha256sum | awk '{print $1}')"

printf 'runtime_evidence_sha256=%s\nplugin_sha256=%s\nflaggems_sha256=%s\nflaggems_vllm_sha256=%s\ncombined_flaggems_sha256=%s\n' \
  "$(sha256sum "${evidence}" | awk '{print $1}')" \
  "${plugin_sha256}" "${flaggems_sha256}" "${flaggems_vllm_sha256}" \
  "${combined_flaggems_sha256}"
