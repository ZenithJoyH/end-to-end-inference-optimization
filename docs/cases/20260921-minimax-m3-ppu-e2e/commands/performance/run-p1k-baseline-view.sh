#!/usr/bin/env bash
set -euo pipefail

view=${1:?usage: run-p1k-baseline-view.sh prefill|decode|mixed RUN_ID}
run_id=${2:?missing RUN_ID}
case_root=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
control=${case_root}/commands/performance
manifest=${case_root}/manifests/perf-baseline-service.json
output_root=${case_root}/performance

case "${view}" in
  prefill|decode|mixed) ;;
  *) echo "invalid view: ${view}" >&2; exit 2 ;;
esac

if [[ "${view}" == prefill ]]; then
  plan=${control}/perf-p1k-prefill-warmup3-plan.json
else
  plan=${control}/perf-p1k-${view}-plan.json
fi
for path in "${control}/vllm_perf.py" "${control}/performance_plan.py" "${control}/compare_performance.py" "${plan}" "${manifest}"; do
  test -f "${path}"
done
for path in "${output_root}/${run_id}" "${output_root}/${run_id}.dry-run.json" "${output_root}/${run_id}.console.log"; do
  test ! -e "${path}" || { echo "refusing to overwrite ${path}" >&2; exit 3; }
done

curl -fsS http://127.0.0.1:8023/health >/dev/null
docker exec "${container}" python3 "${control}/verify-live-baseline-service.py" "${manifest}"
mkdir -p "${output_root}"
docker exec "${container}" python3 "${control}/vllm_perf.py" \
  --config "${plan}" --service-manifest "${manifest}" \
  --role baseline --run-id "${run_id}" --scope performance_only \
  --output-dir "${output_root}" --dry-run > "${output_root}/${run_id}.dry-run.json"
test -s "${output_root}/${run_id}.dry-run.json"

docker exec "${container}" python3 "${control}/vllm_perf.py" \
  --config "${plan}" --service-manifest "${manifest}" \
  --role baseline --run-id "${run_id}" --scope performance_only \
  --output-dir "${output_root}" > "${output_root}/${run_id}.console.log" 2>&1

sha256sum "${plan}" "${manifest}" "${output_root}/${run_id}.dry-run.json" \
  "${output_root}/${run_id}/run-record.json" > "${output_root}/${run_id}.SHA256SUMS"
