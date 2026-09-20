#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
run_id=candidate-group-mixed-baseline-clean-01

test "$(docker inspect --format '{{.Id}}' "${container}")" = "9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4"
test ! -e "${case_root}/performance/${run_id}"
docker exec "${container}" curl -fsS http://127.0.0.1:8030/health >/dev/null
python3 "${case_root}/commands/performance/verify-live-service-manifest.py" \
  "${case_root}/manifests/candidate-maxseq32-service-comparison.json" \
  "${container}" 8030 32

docker exec "${container}" \
  python3 "${case_root}/commands/performance/vllm_perf.py" \
  --config "${case_root}/commands/performance/perf-mixed-p1k-plan-v2.json" \
  --comparison-contract "${case_root}/commands/performance/perf-maxseq-mixed-comparison.json" \
  --service-manifest "${case_root}/manifests/candidate-maxseq32-service-comparison.json" \
  --role baseline \
  --run-id "${run_id}" \
  --scope diagnostic \
  --output-dir "${case_root}/performance" \
  2>&1 | tee "${case_root}/performance/${run_id}.console.log"
