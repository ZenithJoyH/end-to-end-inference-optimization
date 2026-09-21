#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
result_dir="${case_root}/results/operator/p16k-cached-prefill-score-confirm-20260921-01"
script="${case_root}/commands/confirm-hy4-p16k-sparse-mla-score-hybrid-20260921.py"

test ! -e "${result_dir}"
mkdir -p "${result_dir}"
sha256sum "${script}" >"${result_dir}/command.sha256"
python "${script}" --output "${result_dir}/summary.json" \
  >"${result_dir}/stdout.log" 2>"${result_dir}/stderr.log" || status=$?
status=${status:-0}
sha256sum "${result_dir}/summary.json" >"${result_dir}/summary.sha256"
printf 'exit_status=%s\ncompleted_at=%s\n' "${status}" "$(date --iso-8601=seconds)" \
  >"${result_dir}/run-status.txt"
cat "${result_dir}/summary.json"
exit "${status}"
