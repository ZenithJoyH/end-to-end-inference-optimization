#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
result_root="$case_root/results/accdiag-002-gpqa-below-threshold"
samples=$(find "$case_root/accuracy/fw006-formal-gpqa-c64-threshold88" -name 'samples_*.jsonl' -type f | head -1)
test -n "$samples"
test ! -e "$result_root/repeated-current-service.json"
nohup python3 "$case_root/commands/accuracy/repeat-gpqa-requests.py" \
  --samples "$samples" \
  --output "$result_root/repeated-current-service.json" \
  > "$result_root/repeated-current-service.log" 2>&1 &
printf '%s\n' "$!" > "$result_root/repeated-current-service.pid"
printf '%s\n' "$(date -Iseconds)" > "$result_root/repeated-current-service.started-at"
