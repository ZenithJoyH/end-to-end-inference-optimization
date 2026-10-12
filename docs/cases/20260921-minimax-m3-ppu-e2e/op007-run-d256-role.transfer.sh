#!/usr/bin/env bash
set -euo pipefail

role=${1:?usage: op007-run-d256-role.sh baseline|candidate|revert RUN_ID SERVICE_MANIFEST EXPECTED_MOE_SHA256}
run_id=${2:?missing RUN_ID}
manifest=${3:?missing SERVICE_MANIFEST}
expected_moe=${4:?missing EXPECTED_MOE_SHA256}
case_root=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
control=${case_root}/commands/performance
plan=${control}/op007-p1k-d256-milestone-plan.json
contract=${control}/op007-p1k-d256-milestone-comparison.json
output_root=${case_root}/performance

case "${role}" in
  baseline|candidate|revert) ;;
  *) echo "invalid role: ${role}" >&2; exit 2 ;;
esac
for path in "${control}/vllm_perf.py" "${control}/performance_plan.py" \
  "${control}/verify-live-baseline-service.py" "${plan}" "${contract}" "${manifest}"; do
  test -f "${path}"
done
for path in "${output_root}/${run_id}" "${output_root}/${run_id}.dry-run.json" \
  "${output_root}/${run_id}.console.log" "${output_root}/${run_id}.SHA256SUMS"; do
  test ! -e "${path}" || { echo "refusing to overwrite ${path}" >&2; exit 3; }
done
actual_moe=$(docker exec "${container}" sha256sum /workspace/FlagGems/src/flag_gems/fused/fused_moe.py | cut -d ' ' -f 1)
test "${actual_moe}" = "${expected_moe}"
curl -fsS --max-time 5 http://127.0.0.1:8023/health >/dev/null
docker exec "${container}" python3 "${control}/verify-live-baseline-service.py" "${manifest}"
mkdir -p "${output_root}"
docker exec "${container}" python3 "${control}/vllm_perf.py" \
  --config "${plan}" --service-manifest "${manifest}" \
  --comparison-contract "${contract}" --role "${role}" --run-id "${run_id}" \
  --scope performance_only --output-dir "${output_root}" --dry-run \
  > "${output_root}/${run_id}.dry-run.json"
test -s "${output_root}/${run_id}.dry-run.json"

docker exec "${container}" python3 "${control}/vllm_perf.py" \
  --config "${plan}" --service-manifest "${manifest}" \
  --comparison-contract "${contract}" --role "${role}" --run-id "${run_id}" \
  --scope performance_only --output-dir "${output_root}" \
  > "${output_root}/${run_id}.console.log" 2>&1

sha256sum "${plan}" "${contract}" "${manifest}" "${output_root}/${run_id}.dry-run.json" \
  "${output_root}/${run_id}/run-record.json" > "${output_root}/${run_id}.SHA256SUMS"
