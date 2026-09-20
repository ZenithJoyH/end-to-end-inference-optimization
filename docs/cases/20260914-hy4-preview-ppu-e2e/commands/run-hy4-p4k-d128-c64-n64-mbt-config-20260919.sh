#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -lt 2 || "$#" -gt 4 ]]; then
  echo "usage: $0 <run-root> <max-num-batched-tokens> [mixed-token-budget-cap] [async-scheduling]" >&2
  exit 2
fi

run_root=$1
mbt=$2
mixed_cap=${3:-0}
async_scheduling=${4:-0}
case "$mbt" in
  2048|2256|2304|2560|3072|4096) ;;
  *) echo "unsupported max-num-batched-tokens: $mbt" >&2; exit 2 ;;
esac
case "$async_scheduling" in
  0|1) ;;
  *) echo "async-scheduling must be 0 or 1: $async_scheduling" >&2; exit 2 ;;
esac
case "$mixed_cap" in
  0|2048) ;;
  *) echo "unsupported mixed token budget cap: $mixed_cap" >&2; exit 2 ;;
esac

container=hy4-opt-20260914
case_id=p4096-d128-c64-n64
run_id="mbt-${mbt}"
if [[ "$async_scheduling" == 1 ]]; then
  run_id="${run_id}-async"
fi
if [[ "$mixed_cap" != 0 ]]; then
  run_id="${run_id}-mixed-cap-${mixed_cap}"
fi
service_dir="${run_root}/service/${run_id}"
config_dir="${run_root}/config"
base_manifest="${config_dir}/service-manifest-base.json"
service_manifest="${config_dir}/service-manifest-${run_id}.json"
runner="${run_root}/bundle/evaluation/performance/vllm_perf.py"
api_pid=

test -d "$run_root"
test -f "${config_dir}/plan.json"
test -f "${config_dir}/comparison.json"
test -f "$base_manifest"
test -f "$runner"
test ! -e "$service_dir"
test ! -e "${run_root}/runs/${run_id}"
mkdir -p "$service_dir"

if ss -lnt | grep -q ':8010 '; then
  echo 'port 8010 is already in use' >&2
  exit 1
fi
if docker exec "$container" bash -lc "pgrep -af 'vllm serve|vllm.entrypoints.openai.api_server'"; then
  echo 'a vLLM process is already running in the optimization container' >&2
  exit 1
fi

stop_service() {
  set +e
  if [[ -n "${api_pid}" ]]; then
    docker exec "$container" kill -TERM "$api_pid" >>"${service_dir}/stop-evidence.txt" 2>&1
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
    docker exec "$container" bash -lc "pgrep -af 'vllm serve|vllm.entrypoints.openai.api_server' || true"
  } >>"${service_dir}/stop-evidence.txt" 2>&1
  ppu-smi >"${service_dir}/ppu-smi-after-stop.txt" 2>&1
}
trap stop_service EXIT

docker inspect "$container" >"${service_dir}/container-inspect.json"
ppu-smi >"${service_dir}/ppu-smi-before.txt"
docker exec "$container" bash -lc '
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

cat >"${service_dir}/start-service.sh" <<EOF
#!/usr/bin/env bash
set -eo pipefail
source /usr/local/PPU_SDK/envsetup.sh
set -u
export PATH="/usr/lib64/openmpi/bin:\${PATH}"
export LD_LIBRARY_PATH="/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}"
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=1800
export VLLM_FL_MIXED_MAX_NUM_BATCHED_TOKENS=${mixed_cap}
export GLOO_SOCKET_IFNAME=eth0
export NCCL_IB_HCA=fic2_soe_bond
export NCCL_IB_GID_INDEX=1
export NCCL_IB_ADDR_FAMILY=6
export NCCL_SOCKET_IFNAME=bond
export NCCL_SOCKET_FAMILY=AF_INET6
async_arg=
if [[ ${async_scheduling} == 1 ]]; then
  async_arg=--async-scheduling
fi
exec vllm serve /mnt/cpfs/models/Hy4-preview-W8A8-linear-moe/ \
  --served-model-name hy4 \
  --host 0.0.0.0 \
  --port 8010 \
  --trust-remote-code \
  --reasoning-parser hy_v4 \
  --tensor-parallel-size 16 \
  --max-model-len 100000 \
  --max-num-batched-tokens ${mbt} \
  --no-enable-prefix-caching \
  \${async_arg} \
  --compilation-config '{"cudagraph_mode":"FULL_DECODE_ONLY"}'
EOF
chmod +x "${service_dir}/start-service.sh"

docker exec "$container" bash -lc \
  "cd '${service_dir}' && nohup bash ./start-service.sh >./service.log 2>&1 </dev/null &"

ready=0
for attempt in $(seq 1 180); do
  if curl --silent --show-error --fail --max-time 5 http://127.0.0.1:8010/health >/dev/null 2>&1; then
    ready=1
    break
  fi
  if ! docker exec "$container" bash -lc "pgrep -af 'vllm serve|vllm.entrypoints.openai.api_server'" >/dev/null; then
    echo "service mbt=${mbt} exited before readiness" >&2
    tail -n 200 "${service_dir}/service.log" >&2
    exit 1
  fi
  if (( attempt % 6 == 0 )); then
    printf 'mbt=%s readiness_wait_seconds=%s\n' "$mbt" "$((attempt * 10))"
  fi
  sleep 10
done
if [[ "$ready" != 1 ]]; then
  echo "service mbt=${mbt} did not become ready within 1800 seconds" >&2
  tail -n 200 "${service_dir}/service.log" >&2
  exit 1
fi

api_pid=$(docker exec "$container" bash -lc '
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
start_ticks=$(docker exec "$container" awk '{print $22}' "/proc/${api_pid}/stat")
api_cmdline=$(docker exec "$container" bash -lc "tr '\\0' ' ' </proc/${api_pid}/cmdline")
curl --silent --show-error --fail http://127.0.0.1:8010/v1/models >"${service_dir}/models.json"
{
  printf 'captured_at=%s\n' "$(date --iso-8601=seconds)"
  printf 'host_alias=PPU-07\n'
  printf 'container=%s\n' "$container"
  printf 'container_id=%s\n' "$(docker inspect -f '{{.Id}}' "$container")"
  printf 'container_image_id=%s\n' "$(docker inspect -f '{{.Image}}' "$container")"
  printf 'container_api_pid=%s\n' "$api_pid"
  printf 'api_starttime_ticks=%s\n' "$start_ticks"
  printf 'api_cmdline=%s\n' "$api_cmdline"
  printf 'service_log_prefix_cache_false=%s\n' "$(grep -c 'enable_prefix_caching=False' "${service_dir}/service.log" || true)"
  printf 'service_log_startup_complete=%s\n' "$(grep -c 'Application startup complete' "${service_dir}/service.log" || true)"
} >"${service_dir}/runtime-evidence.txt"

container_id=$(docker inspect -f '{{.Id}}' "$container")
runtime_sha=$(sha256sum "${service_dir}/runtime-evidence.txt" | awk '{print $1}')
plugin_sha=$(docker exec "$container" bash -lc 'sha256sum /workspace/vllm-plugin-FL/vllm_fl/models/hy_v4.py /workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/vendor/thead/impl/hyv4_indexer.py /workspace/vllm-plugin-FL/vllm_fl/worker/scheduler_fl.py' | sha256sum | awk '{print $1}')
fgv_sha=$(docker exec "$container" bash -lc 'sha256sum /workspace/FlagGems-vllm/src/flaggems_vllm/runtime/backend/_thead/fused/flashmla_sparse.py /workspace/FlagGems-vllm/src/flaggems_vllm/runtime/backend/_thead/ops/fused_moe.py' | sha256sum | awk '{print $1}')
fg_sha=$(docker exec "$container" bash -lc 'git -C /workspace/FlagGems rev-parse HEAD; git -C /workspace/FlagGems status --porcelain' | sha256sum | awk '{print $1}')

python3 - "$base_manifest" "$service_manifest" "$mbt" "$mixed_cap" "$async_scheduling" \
  "$container_id" "$api_pid" "$start_ticks" "$runtime_sha" \
  "$plugin_sha" "$fgv_sha" "$fg_sha" <<'PY'
import json
import sys
from pathlib import Path

(
    _, base_path, output_path, mbt, mixed_cap, async_scheduling, container_id, api_pid, start_ticks,
    runtime_sha, plugin_sha, fgv_sha, fg_sha,
) = sys.argv
data = json.loads(Path(base_path).read_text(encoding="utf-8"))
mbt_i = int(mbt)
mixed_cap_i = int(mixed_cap)
async_scheduling_enabled = bool(int(async_scheduling))
data["service_instance_id"] = f"{container_id}:{api_pid}:{start_ticks}"
data["plugin_sha256"] = plugin_sha
data["flaggems_vllm_sha256"] = fgv_sha
data["flaggems_sha256"] = fg_sha
data["runtime_evidence_sha256"] = runtime_sha
data["launch_config"]["max_num_batched_tokens"] = mbt_i
data["launch_config"]["mixed_max_num_batched_tokens"] = mixed_cap_i
data["launch_config"]["async_scheduling"] = async_scheduling_enabled
data["launch_config"]["launch_args"] = [
    "--served-model-name=hy4",
    "--port=8010",
    "--trust-remote-code",
    "--reasoning-parser=hy_v4",
    "--tensor-parallel-size=16",
    "--max-model-len=100000",
    f"--max-num-batched-tokens={mbt_i}",
    "--no-enable-prefix-caching",
    '--compilation-config={"cudagraph_mode":"FULL_DECODE_ONLY"}',
]
if async_scheduling_enabled:
    data["launch_config"]["launch_args"].append("--async-scheduling")
data["performance_context"]["cache_preparation"] = (
    "Prefix caching disabled in exact service process arguments and startup log; "
    "one maintained-runner warmup round is excluded from the steady-state result."
)
Path(output_path).write_text(
    json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
PY

sha256sum \
  "${service_dir}/container-inspect.json" \
  "${service_dir}/models.json" \
  "${service_dir}/runtime-evidence.txt" \
  "${service_dir}/source-identities.txt" \
  "${service_dir}/start-service.sh" \
  >"${service_dir}/service-artifacts-before-run.sha256"

role=candidate
if [[ "$mbt" == 2048 ]]; then
  role=baseline
fi
docker exec "$container" python3 "$runner" \
  --config "${config_dir}/plan.json" \
  --comparison-contract "${config_dir}/comparison.json" \
  --service-manifest "$service_manifest" \
  --role "$role" \
  --run-id "$run_id" \
  --scope performance_only \
  --output-dir "${run_root}/runs"

sha256sum "${service_dir}/service.log" >"${service_dir}/service-log-after-run.sha256"
printf 'completed mbt=%s run_record=%s\n' \
  "$mbt" "${run_root}/runs/${run_id}/run-record.json"
