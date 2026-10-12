#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
run_root=${case_root}/accuracy/accdist-001-gpqa-c64-multiseed3
runner=${case_root}/commands/accuracy/execute-accdist001-multiseed.sh

test -f "${run_root}/prepared-at.txt"
test -f "${run_root}/heartbeat-automation-id.txt"
test ! -e "${run_root}/launcher.pid"
nohup bash "${runner}" > "${run_root}/launcher.log" 2>&1 &
launcher_pid=$!
printf '%s\n' "${launcher_pid}" > "${run_root}/launcher.pid"
printf '%s\n' "$(date -Iseconds)" > "${run_root}/launched-at.txt"
