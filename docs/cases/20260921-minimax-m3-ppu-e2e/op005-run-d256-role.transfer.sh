#!/usr/bin/env bash
set -euo pipefail

role=${1:?usage: op005-run-d256-role.sh baseline|candidate|revert RUN_ID SERVICE_MANIFEST}
run_id=${2:?missing RUN_ID}
manifest=${3:?missing SERVICE_MANIFEST}
case_root=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
control=${case_root}/commands/performance
plan=${control}/op005-p1k-d256-milestone-plan.json
contract=${control}/op005-p1k-d256-milestone-comparison.json
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

if [[ "${role}" == candidate ]]; then
  expected_linear=40468058e6e664448573e10663b89b5aa467b052a0b2c56191243760c5c99bef
else
  expected_linear=4d46bae0804ac32b698582d010d5f0e02d3570c6703efff9d1d666e2bf43fd94
fi
actual_linear=$(docker exec "${container}" sha256sum /workspace/FlagGems/src/flag_gems/ops/linear.py | cut -d ' ' -f 1)
test "${actual_linear}" = "${expected_linear}"
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
