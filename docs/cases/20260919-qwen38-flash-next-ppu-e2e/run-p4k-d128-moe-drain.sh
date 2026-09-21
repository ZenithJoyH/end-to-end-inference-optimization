#!/usr/bin/env bash
set -euo pipefail

role=${1:?usage: run-p4k-d128-moe-drain.sh baseline|candidate|mm_candidate|mm_revert|contract_candidate|contract_baseline|contract_revert}
case "${role}" in
  baseline)
    manifest_rel=transitions/post-prof-004-restored-op008-service-37/post-prof-004-restored-op008-service-37-raw.json
    run_id=p4k-d128-moe-drain-baseline-01
    ;;
  candidate)
    manifest_rel=transitions/moe-drain-bm16-service-38/moe-drain-bm16-service-38-raw.json
    run_id=p4k-d128-moe-drain-candidate-01
    benchmark_role=candidate
    ;;
  mm_candidate)
    manifest_rel=transitions/mm-native-provider-service-41/mm-native-provider-service-41-raw.json
    run_id=p4k-d128-mm-native-candidate-01
    benchmark_role=candidate
    ;;
  mm_revert)
    manifest_rel=transitions/mm-native-revert-service-42/mm-native-revert-service-42-raw.json
    run_id=p4k-d128-mm-native-revert-01
    benchmark_role=revert
    ;;
  contract_candidate)
    manifest_rel=manifests/mm-native-contract-candidate-service43.json
    run_id=p4k-d128-mm-native-contract-candidate-01
    benchmark_role=candidate
    ;;
  contract_baseline)
    manifest_rel=manifests/mm-native-contract-baseline-service44.json
    run_id=p4k-d128-mm-native-contract-baseline-01
    benchmark_role=baseline
    ;;
  contract_revert)
    manifest_rel=manifests/mm-native-contract-revert-service45.json
    run_id=p4k-d128-mm-native-contract-revert-01
    benchmark_role=revert
    ;;
  *) echo "invalid role: ${role}" >&2; exit 2 ;;
esac
benchmark_role=${benchmark_role:-${role}}

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
expected_container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
manifest=${case_root}/${manifest_rel}
perf_dir=${case_root}/commands/performance
comparison_contract=${perf_dir}/perf-p4k-d128-mm-native-comparison.json
output_root=${case_root}/performance
dry_run=${output_root}/${run_id}.dry-run.json
console=${output_root}/${run_id}.console.log

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
test -f "${manifest}"
python3 "${perf_dir}/verify-live-service-manifest.py" "${manifest}" "${container}" 8030 64
docker exec "${container}" curl -fsS http://127.0.0.1:8030/health >/dev/null
test ! -e "${output_root}/${run_id}"
test ! -e "${dry_run}"
test ! -e "${console}"

docker exec "${container}" python3 "${perf_dir}/vllm_perf.py" \
  --config "${perf_dir}/perf-p4k-d128-moe-drain-plan.json" \
  --comparison-contract "${comparison_contract}" \
  --service-manifest "${manifest}" --role "${benchmark_role}" \
  --run-id "${run_id}" --scope performance_only --output-dir "${output_root}" --dry-run > "${dry_run}"

docker exec "${container}" python3 "${perf_dir}/vllm_perf.py" \
  --config "${perf_dir}/perf-p4k-d128-moe-drain-plan.json" \
  --comparison-contract "${comparison_contract}" \
  --service-manifest "${manifest}" --role "${benchmark_role}" \
  --run-id "${run_id}" --scope performance_only --output-dir "${output_root}" 2>&1 | tee "${console}"
