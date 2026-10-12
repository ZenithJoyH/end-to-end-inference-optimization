#!/usr/bin/env bash
set -euo pipefail
role=${1:?usage: op010-run-d256-role.sh baseline|candidate|revert}
case "${role}" in baseline|candidate|revert) ;; *) exit 2 ;; esac
case_root=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
control=${case_root}/commands/performance
plan=${control}/op010-p1k-d256-plan.json
contract=${control}/op010-p1k-d256-comparison.json
manifest=${case_root}/results/op010-perf-${role}-performance-manifest.json
run_id=op010-d256-${role}-01
output_root=${case_root}/performance

for path in "${control}/vllm_perf.py" "${control}/performance_plan.py" \
  "${control}/verify-live-baseline-service.py" "${plan}" "${contract}" "${manifest}"; do
  test -f "${path}"
done
for path in "${output_root}/${run_id}" "${output_root}/${run_id}.dry-run.json" \
  "${output_root}/${run_id}.console.log" "${output_root}/${run_id}.SHA256SUMS"; do
  test ! -e "${path}" || { echo "refusing to overwrite ${path}" >&2; exit 3; }
done
test "$(docker exec "${container}" sha256sum /workspace/FlagGems/src/flag_gems/fused/fused_moe.py | cut -d ' ' -f 1)" = a780da6348ba611640b546b47c60b79baa1312094386ce8f49d99d0d8e4750af
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
