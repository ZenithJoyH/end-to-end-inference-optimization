#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
profile_id=p4k-d64-c16-n16-full-range-reprofile-20260916-05
service_dir="${case_dir}/logs/${profile_id}-service"
profile_root="${case_dir}/profiling/${profile_id}"
trace_dir="${profile_root}/traces"
result_dir="${case_dir}/results/profiling/${profile_id}"
commands_dir="${case_dir}/commands"
tool="${commands_dir}/evaluation/performance/vllm_profile.py"
model_path=/mnt/cpfs/models/Hy4-preview-W8A8-linear-moe/
plugin_repo=/workspace/vllm-plugin-FL
flaggems_repo=/workspace/FlagGems
expected_plugin_commit=38f350b13fc15f08eb4641e1d6d1980ba3fc16aa
expected_plugin_sha=bc567ade22696146200042e8e29745535c86fa2dc9479051c2d2f7892ed3c9f3
expected_thead_yaml_sha=7566eaddc29f026c131c9083a097bae150a3a975746bed4354f47da1e198b69b
expected_flaggems_commit=5c2b9a1618c36651f96108d56f076361965f2d53
expected_sparse_mla_sha=680eff6be15e259d36036f82958fb383ba1acc781bee1046caa246ae99e4f4fc
profiler_config="{\"profiler\":\"torch\",\"torch_profiler_dir\":\"${trace_dir}\",\"torch_profiler_with_stack\":false,\"torch_profiler_with_flops\":false,\"torch_profiler_use_gzip\":true,\"torch_profiler_record_shapes\":true,\"torch_profiler_with_memory\":false,\"ignore_frontend\":true}"

test ! -e "${service_dir}"
test ! -e "${profile_root}"
test ! -e "${result_dir}"
test -f "${tool}"
if pgrep -af '[v]llm bench serve' >/dev/null; then
  echo 'benchmark client is active' >&2
  exit 1
fi
if pgrep -af '[v]llm serve|^VLLM::(EngineCore|Worker)' >/dev/null; then
  echo 'vLLM service or worker is already active' >&2
  pgrep -af '[v]llm serve|^VLLM::(EngineCore|Worker)' >&2
  exit 1
fi
if ss -ltn 'sport = :8010' | grep -q ':8010'; then
  echo 'port 8010 is occupied' >&2
  exit 1
fi

test "$(git -C "${plugin_repo}" rev-parse HEAD)" = "${expected_plugin_commit}"
test "$(sha256sum "${plugin_repo}/vllm_fl/models/hy_v4.py" | awk '{print $1}')" = "${expected_plugin_sha}"
test "$(sha256sum "${plugin_repo}/vllm_fl/dispatch/config/thead.yaml" | awk '{print $1}')" = "${expected_thead_yaml_sha}"
test "$(git -C "${flaggems_repo}" rev-parse HEAD)" = "${expected_flaggems_commit}"
test "$(sha256sum "${flaggems_repo}/src/flag_gems/runtime/backend/_thead/fused/flashmla_sparse.py" | awk '{print $1}')" = "${expected_sparse_mla_sha}"
git -C "${plugin_repo}" diff --check
git -C "${flaggems_repo}" diff --check

mkdir -p "${service_dir}" "${trace_dir}" "${result_dir}"
git -C "${plugin_repo}" status --short --branch >"${service_dir}/plugin-status.txt"
git -C "${flaggems_repo}" status --short --branch >"${service_dir}/flaggems-status.txt"
find "${trace_dir}" -type f -printf '%P %s %T@\n' | sort >"${profile_root}/trace-inventory-before.txt"
printf '%s\n' \
  "profile_id=${profile_id}" \
  'parent_scenario=p4096-d1024-c64-n128' \
  'milestone_scenario=p4096-d64-c16-n16' \
  'workload_delta=output_1024_to_64,concurrency_64_to_16,requests_128_to_16' \
  'mode=reprofile' \
  'required_phase_coverage=prefill,decode,mixed' \
  'phase_boundary=execute_new_cached_markers' \
  'question=verify_full_range_bypass_removes_prefill_indexer_qk_topk_and_preserves_copy_sync_elimination' \
  'nearest_no_profiler=/mnt/nfs/users/jinghao/hy4-preview/test/benchmark_results/hy4/hy4_4096in_1024out_c64_n128_20260916_082820.csv' \
  'profiler_on_timing_claim=diagnostic_only' \
  'expected_ranks=16' >"${profile_root}/diagnostic-contract.txt"

set +u
source /usr/local/PPU_SDK/envsetup.sh
set -u
export PATH="/usr/lib64/openmpi/bin:${PATH}"
export LD_LIBRARY_PATH="/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:${LD_LIBRARY_PATH:-}"
export GLOO_SOCKET_IFNAME=eth0
export NCCL_IB_HCA=fic2_soe_bond
export NCCL_IB_GID_INDEX=1
export NCCL_IB_ADDR_FAMILY=6
export NCCL_SOCKET_IFNAME=bond
export NCCL_SOCKET_FAMILY=AF_INET6

mkdir -p /tmp/hy4-p4k-d64-c16-full-range-reprofile-20260916-05
nohup env \
  CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15 \
  VLLM_WORKER_MULTIPROC_METHOD=spawn \
  VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=1800 \
  TMPDIR=/tmp/hy4-p4k-d64-c16-full-range-reprofile-20260916-05 \
  vllm serve "${model_path}" \
  --served-model-name hy4 \
  --host 0.0.0.0 \
  --port 8010 \
  --trust-remote-code \
  --reasoning-parser hy_v4 \
  --tensor-parallel-size 16 \
  --max-model-len 100000 \
  --max-num-batched-tokens 2048 \
  --no-enable-prefix-caching \
  --compilation-config '{"cudagraph_mode":"FULL_DECODE_ONLY"}' \
  --profiler-config "${profiler_config}" \
  >"${service_dir}/service.log" 2>&1 &
api_pid=$!
printf '%s\n' "${api_pid}" >"${service_dir}/api.pid"
printf 'api_pid=%s\nstarted_at=%s\nplugin_commit=%s\nplugin_sha256=%s\nflaggems_commit=%s\nsparse_mla_sha256=%s\nprofiler_config=%s\n' \
  "${api_pid}" "$(date --iso-8601=seconds)" "${expected_plugin_commit}" "${expected_plugin_sha}" \
  "${expected_flaggems_commit}" "${expected_sparse_mla_sha}" "${profiler_config}" >"${service_dir}/launch-result.txt"

for _attempt in $(seq 1 240); do
  if ! kill -0 "${api_pid}" >/dev/null 2>&1; then
    echo 'profiling service exited before readiness' >&2
    tail -120 "${service_dir}/service.log" >&2
    exit 1
  fi
  if curl --fail --silent --show-error --max-time 10 http://127.0.0.1:8010/v1/models >"${service_dir}/models.json.tmp"; then
    mv "${service_dir}/models.json.tmp" "${service_dir}/models.json"
    break
  fi
  rm -f "${service_dir}/models.json.tmp"
  sleep 10
done
test -s "${service_dir}/models.json"
tr '\0' ' ' <"/proc/${api_pid}/cmdline" >"${service_dir}/api-command.txt"
grep -E -i 'profiler|prefix cach|cudagraph|graph capture|KV cache size|maximum concurrency|Starting vLLM API server' \
  "${service_dir}/service.log" >"${service_dir}/runtime-evidence.txt" || true
printf 'ready_at=%s\n' "$(date --iso-8601=seconds)" >>"${service_dir}/launch-result.txt"

common=(
  python3 "${tool}"
  --model hy4
  --tokenizer "${model_path}"
  --host 127.0.0.1
  --port 8010
  --endpoint /v1/completions
  --case 4096,64,16,16
  --runs 2
  --warmup-rounds 1
  --seed 49013
  --timeout 1800
  --profile-runs last
  --profile-dir "${trace_dir}"
  --output-dir "${result_dir}"
)
printf 'started_at=%s\n' "$(date --iso-8601=seconds)" >"${result_dir}/orchestration-status.txt"
"${common[@]}" --dry-run >"${result_dir}/dry-run.json" 2>"${result_dir}/dry-run.stderr"
timeout 3700 "${common[@]}" >"${result_dir}/wrapper.stdout" 2>"${result_dir}/wrapper.stderr"
printf 'client_finished_at=%s\n' "$(date --iso-8601=seconds)" >>"${result_dir}/orchestration-status.txt"

for _attempt in $(seq 1 120); do
  trace_count="$(find "${trace_dir}" -maxdepth 1 -type f -name '*.json.gz' | wc -l)"
  test "${trace_count}" -eq 16 && break
  sleep 5
done
test "$(find "${trace_dir}" -maxdepth 1 -type f -name '*.json.gz' | wc -l)" -eq 16
for rank in $(seq 0 15); do
  test "$(find "${trace_dir}" -maxdepth 1 -type f -name "*_rank${rank}.*.json.gz" | wc -l)" -eq 1
done
find "${trace_dir}" -maxdepth 1 -type f -printf '%P %s %T@\n' | sort >"${profile_root}/trace-inventory-after-1.txt"
sleep 10
find "${trace_dir}" -maxdepth 1 -type f -printf '%P %s %T@\n' | sort >"${profile_root}/trace-inventory-after-2.txt"
cmp "${profile_root}/trace-inventory-after-1.txt" "${profile_root}/trace-inventory-after-2.txt"
find "${trace_dir}" -maxdepth 1 -type f -name '*.json.gz' -print0 | sort -z | xargs -0 sha256sum >"${profile_root}/trace-inventory-after.sha256"
printf 'trace_files=16\ntrace_export_stable=true\ncompleted_at=%s\n' \
  "$(date --iso-8601=seconds)" >>"${result_dir}/orchestration-status.txt"

printf 'stopped_pid=%s\nstopped_at=%s\nreason=profiling_complete\n' \
  "${api_pid}" "$(date --iso-8601=seconds)" >"${service_dir}/stop-result.txt"
kill -TERM "${api_pid}"
for _attempt in $(seq 1 240); do
  test ! -e "/proc/${api_pid}" && break
  sleep 1
done
test ! -e "/proc/${api_pid}"
for _attempt in $(seq 1 240); do
  pgrep -f '^VLLM::(EngineCore|Worker)' >/dev/null || break
  sleep 1
done
test -z "$(pgrep -f '^VLLM::(EngineCore|Worker)' || true)"
if ss -ltn 'sport = :8010' | grep -q ':8010'; then
  echo 'port 8010 remains occupied after profiling' >&2
  exit 1
fi
printf 'released_at=%s\nport_8010_released=true\nworkers_released=true\n' \
  "$(date --iso-8601=seconds)" >>"${service_dir}/stop-result.txt"

sampled_json="${result_dir}/phase-analysis-sampled.json"
cpu_json="${result_dir}/phase-analysis-rank0-cpu.json"
indexer_json="${result_dir}/indexer-breakdown-rank0.json"
indexer_md="${result_dir}/indexer-breakdown-rank0.md"
rank0_trace="$(find "${trace_dir}" -maxdepth 1 -type f -name '*_rank0.*.json.gz' -print -quit)"
test -n "${rank0_trace}"

python3 "${commands_dir}/analyze-hy4-profile-sampled-phases-20260915.py" \
  --trace-dir "${trace_dir}" --output "${sampled_json}" --top 120 --analyzed-ranks 0,1,15 \
  >"${result_dir}/phase-analysis-sampled.stdout" 2>"${result_dir}/phase-analysis-sampled.stderr" &
sampled_pid=$!
python3 "${commands_dir}/analyze_hy4_indexer_breakdown_v2.py" \
  "${rank0_trace}" "${indexer_json}" "${indexer_md}" \
  >"${result_dir}/indexer-breakdown-rank0.stdout" 2>"${result_dir}/indexer-breakdown-rank0.stderr" &
indexer_pid=$!
wait "${sampled_pid}"
wait "${indexer_pid}"
python3 "${commands_dir}/analyze-hy4-profile-rank0-cpu-phases-20260915.py" \
  --trace-dir "${trace_dir}" --output "${cpu_json}" --top 120 --analyzed-ranks 0 \
  >"${result_dir}/phase-analysis-rank0-cpu.stdout" 2>"${result_dir}/phase-analysis-rank0-cpu.stderr"
test -s "${sampled_json}"
test -s "${cpu_json}"
test -s "${indexer_json}"
test -s "${indexer_md}"
printf 'analysis_completed_at=%s\ndeeply_analyzed_ranks=0,1,15\nindexer_rank=0\nservice_stopped=true\n' \
  "$(date --iso-8601=seconds)" >"${result_dir}/analysis-status.txt"
echo "PASS: ${profile_id} captured, validated, analyzed, and stopped"
