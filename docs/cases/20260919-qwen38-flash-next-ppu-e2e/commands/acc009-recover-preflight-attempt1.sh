#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-009-full-gpqa-dual-qsa-unbounded-20260922
eval_dir=${case_dir}/evaluation
archive=${eval_dir}/preflight-failed-attempt-1
test -f "${eval_dir}/FINISHED"
test "$(cat "${eval_dir}/exit.code")" = 124
test ! -e "${archive}"
mkdir "${archive}"
for name in STARTED FINISHED exit.code runner.pid proxy.pid proxy.log proxy-models.json \
  smoke-8000.json smoke-8010.json preflight.log; do
  test -e "${eval_dir}/${name}"
  mv "${eval_dir}/${name}" "${archive}/${name}"
done
if test -e "${case_dir}/services/service-manifest.json"; then
  mv "${case_dir}/services/service-manifest.json" "${archive}/service-manifest.json"
fi
date -Iseconds > "${archive}/ARCHIVED"
