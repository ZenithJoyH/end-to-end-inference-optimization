#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
expected_container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
manifest=${case_root}/manifests/candidate-maxseq64-bt4096-moe-bm16-service-comparison-10.json
perf_dir=${case_root}/commands/performance
output_root=${case_root}/performance

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
python3 "${perf_dir}/verify-live-service-manifest.py" "${manifest}" "${container}" 8030 64
docker exec "${container}" curl -fsS http://127.0.0.1:8030/health >/dev/null

run_case() {
  local phase=$1
  local plan=$2
  local contract=$3
  local run_id=p4k-entry-${phase}-baseline-01
  local dry_run=${output_root}/${run_id}.dry-run.json
  local console=${output_root}/${run_id}.console.log
  test ! -e "${output_root}/${run_id}"
  test ! -e "${dry_run}"
  test ! -e "${console}"
  docker exec "${container}" \
    python3 "${perf_dir}/vllm_perf.py" \
    --config "${plan}" \
    --comparison-contract "${contract}" \
    --service-manifest "${manifest}" \
    --role baseline \
    --run-id "${run_id}" \
    --scope performance_only \
    --output-dir "${output_root}" \
    --dry-run > "${dry_run}"
  docker exec "${container}" \
    python3 "${perf_dir}/vllm_perf.py" \
    --config "${plan}" \
    --comparison-contract "${contract}" \
    --service-manifest "${manifest}" \
    --role baseline \
    --run-id "${run_id}" \
    --scope performance_only \
    --output-dir "${output_root}" \
    2>&1 | tee "${console}"
}

# The three phase views intentionally share one service and are serialized.
run_case prefill "${perf_dir}/perf-p4k-prefill-entry-plan.json" "${perf_dir}/perf-p4k-prefill-comparison.json"
run_case decode "${perf_dir}/perf-p4k-decode-entry-plan.json" "${perf_dir}/perf-p4k-decode-comparison.json"
run_case mixed "${perf_dir}/perf-p4k-mixed-entry-plan.json" "${perf_dir}/perf-p4k-mixed-comparison.json"
