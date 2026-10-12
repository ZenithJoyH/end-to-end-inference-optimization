#!/usr/bin/env bash
set -uo pipefail
case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
output_dir=${case_dir}/accuracy/op010-minimal-regression
config=${case_dir}/commands/accuracy/minimax-m3-op010-minimal-regression.json
manifest=${case_dir}/results/op010-candidate-performance-manifest.json
log=${output_dir}/runner.log
exit_record=${output_dir}/runner.exit-code.txt
eval_container=minimax-m3-eval-e2e-20260921
test -d "${output_dir}" || exit 2
test -f "${config}" || exit 2
test -f "${manifest}" || exit 2
test ! -e "${log}" || exit 3
test ! -e "${exit_record}" || exit 3
test "$(docker inspect -f '{{.Id}}' "${eval_container}" | cut -c1-12)" = 5511b52cf225 || exit 4
curl -fsS --max-time 5 http://127.0.0.1:8023/health >/dev/null || exit 5
docker exec minimaxM3-opt-20260921 python3 \
    "${case_dir}/commands/performance/verify-live-baseline-service.py" "${manifest}" || exit 6
date -Is > "${output_dir}/runner.started-at.txt"
docker exec "${eval_container}" python3 "${case_dir}/commands/accuracy/llmrun.py" "${config}" > "${log}" 2>&1
rc=$?
printf '%s\n' "${rc}" > "${exit_record}"
date -Is > "${output_dir}/runner.finished-at.txt"
sha256sum "${config}" "${manifest}" "${log}" "${exit_record}" \
    > "${output_dir}/SHA256SUMS.runner"
exit "${rc}"
