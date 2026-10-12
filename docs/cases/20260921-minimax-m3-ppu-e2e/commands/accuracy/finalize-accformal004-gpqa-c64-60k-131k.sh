#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
run_root="$case_root/accuracy/accformal-004-gpqa-c64-60k-131k-threshold88"
workspace="$case_root/commands/formal-eval-workspace"
launcher_pid=$(cat "$run_root/launcher.pid")

while kill -0 "$launcher_pid" 2>/dev/null; do
  sleep 30
done

mapfile -t records < <(find "$run_root/native" -type f -name run-record.json -print)
if [[ ${#records[@]} -eq 0 ]]; then
  printf '%s\n' "No run-record was created; the formal score was below threshold or evidence validation failed." \
    > "$run_root/gate-finalize-status.txt"
  printf '%s\n' "$(date -Iseconds)" > "$run_root/terminal-at.txt"
  exit 0
fi
if [[ ${#records[@]} -ne 1 ]]; then
  printf '%s\n' "Refusing to choose among ${#records[@]} run records." \
    > "$run_root/gate-finalize-status.txt"
  printf '%s\n' "$(date -Iseconds)" > "$run_root/terminal-at.txt"
  exit 1
fi

docker exec minimax-m3-eval-e2e-20260921 python3 \
  "$workspace/evaluation/accuracy/acceptance.py" issue \
  --run-record "${records[0]}" \
  --output "$run_root/accuracy-gate.json" \
  > "$run_root/gate-issue.log" 2>&1
printf '%s\n' "Accuracy gate issued from ${records[0]}." > "$run_root/gate-finalize-status.txt"
printf '%s\n' "$(date -Iseconds)" > "$run_root/terminal-at.txt"
