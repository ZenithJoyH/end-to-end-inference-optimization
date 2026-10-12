#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
experiment=${case_root}/performance/perf-015-p16k-post-rb001-unbounded-entry-20260922
container=qwen3.8-flash-opt-candidate-20260919
perf_dir=${case_root}/commands/performance
manifest=${experiment}/manifests/service-8000.json

if docker exec "${container}" pgrep -af 'vllm bench serve' >/dev/null; then
  echo 'another vllm benchmark client is active' >&2
  exit 1
fi

for phase in prefill decode mixed; do
  run_id=perf015-p16k-unbounded-${phase}-01
  plan=${experiment}/commands/perf-p16k-${phase}-entry-plan.json
  contract=${experiment}/commands/perf-p16k-${phase}-comparison.json
  dry_run=${experiment}/${run_id}.dry-run.json
  console=${experiment}/${run_id}.console.log

  test ! -e "${experiment}/${run_id}"
  test ! -e "${dry_run}"
  test ! -e "${console}"
  python3 "${perf_dir}/verify-live-service-manifest.py" "${manifest}" "${container}" 8000 64
  docker exec "${container}" curl -fsS http://127.0.0.1:8000/health >/dev/null
  docker exec "${container}" curl -fsS http://127.0.0.1:8010/health >/dev/null

  docker exec "${container}" python3 "${perf_dir}/vllm_perf.py" \
    --config "${plan}" --comparison-contract "${contract}" \
    --service-manifest "${manifest}" --role baseline \
    --run-id "${run_id}" --scope performance_only \
    --output-dir "${experiment}" --dry-run >"${dry_run}"

  docker exec "${container}" python3 "${perf_dir}/vllm_perf.py" \
    --config "${plan}" --comparison-contract "${contract}" \
    --service-manifest "${manifest}" --role baseline \
    --run-id "${run_id}" --scope performance_only \
    --output-dir "${experiment}" 2>&1 | tee "${console}"
done
