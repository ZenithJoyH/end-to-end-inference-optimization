#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
run_root="$case_root/accuracy/accformal-004-gpqa-c64-60k-131k-threshold88"
finalizer="$case_root/commands/accuracy/finalize-accformal004-gpqa-c64-60k-131k.sh"

test -f "$run_root/launcher.pid"
test ! -e "$run_root/finalizer.pid"
cp "$finalizer" "$run_root/control/"
nohup "$finalizer" > "$run_root/gate-finalizer.log" 2>&1 &
printf '%s\n' "$!" > "$run_root/finalizer.pid"
