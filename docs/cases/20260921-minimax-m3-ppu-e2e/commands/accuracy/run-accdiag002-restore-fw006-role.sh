#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
result_root=${case_root}/results/accdiag-002-gpqa-below-threshold
patch=${case_root}/commands/performance/fw006-targeted-schema-reflection.patch
repeat=${case_root}/commands/accuracy/repeat-gpqa-requests.py
switch=${case_root}/commands/performance/switch-minimax-service.sh
service=${case_root}/commands/accuracy/minimax-m3-accdiag002-restored-fw006-service.sh
log=${case_root}/logs/accdiag002-restored-fw006-server.log
samples=$(find "${case_root}/accuracy/fw006-formal-gpqa-c64-threshold88" -name 'samples_*.jsonl' -type f | head -1)

test -n "${samples}"
test -f "${result_root}/repeated-original-reflection.json"
test ! -e "${result_root}/repeated-restored-fw006.json"
test -z "$(pgrep -f '[r]epeat-gpqa-requests.py' || true)"
docker exec minimaxM3-opt-20260921 bash -lc \
  "cd /workspace/FlagGems && git apply --check '${patch}' && git apply '${patch}' && git diff --check"
bash "${switch}" accdiag002-restore-fw006 "${service}" "${log}"
python3 "${repeat}" --samples "${samples}" \
  --output "${result_root}/repeated-restored-fw006.json" --repeats 1
sha256sum "${result_root}/repeated-restored-fw006.json" > \
  "${result_root}/repeated-restored-fw006.SHA256"
