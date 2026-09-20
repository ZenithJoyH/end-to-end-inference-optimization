#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
run_dir=${case_root}/accuracy/m64-semantic-minreg-02
python_script=${case_root}/commands/accuracy/run-m64-semantic-minreg.py
contract=${case_root}/commands/accuracy/m64-semantic-minreg-contract.json

test ! -e "${run_dir}"
test -f "${contract}"
set +e
python3 "${python_script}" 2>&1 | tee "${run_dir}.runner.log"
rc=${PIPESTATUS[0]}
set -e
if test -d "${run_dir}"; then
  mv "${run_dir}.runner.log" "${run_dir}/runner.log"
  printf '%s\n' "${rc}" > "${run_dir}/exit.code"
  sha256sum "${contract}" "${python_script}" "${run_dir}/process.json" \
    "${run_dir}/runner.log" "${run_dir}/result.json" \
    > "${run_dir}/SHA256SUMS" 2>/dev/null || true
fi
exit "${rc}"
