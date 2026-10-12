#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
run_root="$case_root/accuracy/accformal-004-gpqa-c64-60k-131k-threshold88"
workspace="$case_root/commands/formal-eval-workspace"

test -f "$run_root/preflight.log"
test -f "$run_root/heartbeat-automation-id.txt"
test ! -e "$run_root/launcher.pid"
nohup docker exec minimax-m3-eval-e2e-20260921 python3 \
  "$workspace/evaluation/accuracy/formal_accuracy.py" \
  --config "$run_root/config.json" \
  --contract "$run_root/contract.json" \
  --service-manifest "$run_root/service-manifest.json" \
  --evaluation-inspect "$run_root/evaluator.inspect.json" \
  > "$run_root/formal-run.log" 2>&1 &
launcher_pid=$!
printf '%s\n' "$launcher_pid" > "$run_root/launcher.pid"
printf '%s\n' "$(date -Iseconds)" > "$run_root/launched-at.txt"
