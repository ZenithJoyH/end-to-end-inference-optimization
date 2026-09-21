#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
expected_container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
manifest=${case_root}/manifests/mm-native-d1024-candidate-service46.json
perf_dir=${case_root}/commands/performance
output_root=${case_root}/performance
run_id=p4k-d1024-mm-native-contract-candidate-01
dry_run=${output_root}/${run_id}.dry-run.json
console=${output_root}/${run_id}.console.log

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
python3 "${perf_dir}/verify-live-service-manifest.py" "${manifest}" "${container}" 8030 64
docker exec "${container}" curl -fsS http://127.0.0.1:8030/health >/dev/null
test ! -e "${output_root}/${run_id}"
test ! -e "${dry_run}"
test ! -e "${console}"

docker exec "${container}" python3 "${perf_dir}/vllm_perf.py" \
  --config "${perf_dir}/perf-p4k-mixed-entry-plan.json" \
  --comparison-contract "${perf_dir}/perf-p4k-d1024-mm-native-comparison.json" \
  --service-manifest "${manifest}" --role candidate \
  --run-id "${run_id}" --scope performance_only --output-dir "${output_root}" --dry-run > "${dry_run}"

docker exec "${container}" python3 "${perf_dir}/vllm_perf.py" \
  --config "${perf_dir}/perf-p4k-mixed-entry-plan.json" \
  --comparison-contract "${perf_dir}/perf-p4k-d1024-mm-native-comparison.json" \
  --service-manifest "${manifest}" --role candidate \
  --run-id "${run_id}" --scope performance_only --output-dir "${output_root}" 2>&1 | tee "${console}"
