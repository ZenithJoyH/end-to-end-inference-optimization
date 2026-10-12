#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
output_dir=${case_dir}/accuracy/op007-minimal-regression
config=${case_dir}/commands/accuracy/minimax-m3-op007-minimal-regression.json
manifest=${case_dir}/results/op007-candidate-performance-manifest.json
eval_container=minimax-m3-eval-e2e-20260921

test ! -e "${output_dir}"
test -f "${config}"
test -f "${manifest}"
test "$(docker inspect -f '{{.Id}}' "${eval_container}" | cut -c1-12)" = 5511b52cf225
test "$(docker inspect -f '{{.State.Running}}' "${eval_container}")" = true
curl -fsS --max-time 5 http://127.0.0.1:8023/health >/dev/null
docker exec minimaxM3-opt-20260921 python3 \
  "${case_dir}/commands/performance/verify-live-baseline-service.py" "${manifest}"

mkdir "${output_dir}"
docker inspect -f '{{.Id}} {{.Image}} {{.State.Running}}' "${eval_container}" \
  > "${output_dir}/evaluator.identity.txt"
docker exec "${eval_container}" python3 \
  "${case_dir}/commands/accuracy/llmrun.py" "${config}" --preflight-only \
  > "${output_dir}/preflight.log" 2>&1
grep -F 'Preflight completed; lm-eval was not started' \
  "${output_dir}/preflight.log" >/dev/null
sha256sum "${config}" "${manifest}" "${output_dir}/evaluator.identity.txt" \
  "${output_dir}/preflight.log" > "${output_dir}/SHA256SUMS.preflight"
