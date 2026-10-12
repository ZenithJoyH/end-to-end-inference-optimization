#!/usr/bin/env bash
set -euo pipefail

root=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/accuracy/accdiag-003-gpqa-truncated-60k
pid=$(cat "${root}/runner.pid")
expected='run-accdiag003-truncated-60k.py'
args=$(ps -p "${pid}" -o args=)
grep -F "${expected}" <<<"${args}" >/dev/null
cp "${root}/progress.json" "${root}/progress.before-user-requested-restart.json"
kill -TERM "${pid}"
stopped=false
for _ in $(seq 1 120); do
  if ! kill -0 "${pid}" 2>/dev/null; then
    stopped=true
    break
  fi
  sleep 1
done
test "${stopped}" = true
date --iso-8601=seconds > "${root}/cancelled-at.txt"
printf '%s\n' 'user requested conv3d blacklist and fresh 131K service rerun' > "${root}/cancel-reason.txt"
curl -fsS --max-time 5 http://127.0.0.1:8023/health >/dev/null
printf 'cancelled pid=%s; preserved_responses=%s\n' \
  "${pid}" "$(find "${root}/responses" -maxdepth 1 -type f | wc -l)"
