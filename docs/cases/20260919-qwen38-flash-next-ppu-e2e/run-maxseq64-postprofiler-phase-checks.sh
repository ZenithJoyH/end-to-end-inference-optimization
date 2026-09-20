#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
manifest=${case_root}/manifests/candidate-maxseq64-bt4096-postprofiler-service-comparison.json
baseline_canonical=${case_root}/smoke/maxseq32-before-screen-01/canonical.json
output_root=${case_root}/performance

test -f "${manifest}"
test -f "${baseline_canonical}"
python3 "${case_root}/commands/performance/verify-live-service-manifest.py" \
  "${manifest}" "${container}" 8030 64

bash "${case_root}/commands/27-run-graph-replay-smoke.sh" \
  maxseq64-postprofiler-screen-01 "${manifest}" 64 "${baseline_canonical}"

run_case() {
  local phase=$1
  local plan=$2
  local contract=$3
  local run_id=maxseq64-postprofiler-${phase}-candidate-01
  test ! -e "${output_root}/${run_id}"
  test ! -e "${output_root}/${run_id}.console.log"
  docker exec "${container}" \
    python3 "${case_root}/commands/performance/vllm_perf.py" \
    --config "${plan}" \
    --comparison-contract "${contract}" \
    --service-manifest "${manifest}" \
    --role candidate \
    --run-id "${run_id}" \
    --scope performance_only \
    --output-dir "${output_root}" \
    2>&1 | tee "${output_root}/${run_id}.console.log"
}

# These share one service and are intentionally serialized to prevent workload
# overlap from contaminating either phase baseline/candidate comparison.
run_case prefill \
  "${case_root}/commands/performance/perf-prefill-plan-v2.json" \
  "${case_root}/commands/performance/perf-maxseq-prefill-comparison.json"
run_case decode \
  "${case_root}/commands/performance/perf-decode-plan-v2.json" \
  "${case_root}/commands/performance/perf-maxseq-decode-comparison.json"
