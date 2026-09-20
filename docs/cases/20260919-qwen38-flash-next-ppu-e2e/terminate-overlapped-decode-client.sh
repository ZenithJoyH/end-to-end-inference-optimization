#!/usr/bin/env bash
set -euo pipefail

container=qwen3.8-flash-opt-candidate-20260919
run_id=candidate-group-decode-baseline-01
mapfile -t pids < <(docker exec "${container}" python3 - "${run_id}" <<'PY'
import os
import sys
run_id = sys.argv[1]
found = []
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        args = [x.decode(errors="replace") for x in open(f"/proc/{entry}/cmdline", "rb").read().split(b"\0") if x]
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    text = " ".join(args)
    if run_id in text and ("vllm_perf.py" in text or "vllm bench serve" in text):
        found.append(int(entry))
for pid in sorted(found, reverse=True):
    print(pid)
PY
)
test "${#pids[@]}" -ge 1
for pid in "${pids[@]}"; do
  docker exec "${container}" kill -TERM "${pid}" 2>/dev/null || true
done
deadline=$((SECONDS + 30))
while true; do
  remaining=0
  for pid in "${pids[@]}"; do
    docker exec "${container}" test -d "/proc/${pid}" && remaining=$((remaining + 1)) || true
  done
  test "${remaining}" -eq 0 && break
  if test "${SECONDS}" -ge "${deadline}"; then
    echo "Decode client did not stop after SIGTERM; no force signal was sent." >&2
    exit 2
  fi
  sleep 1
done
timeout 5s curl -fsS http://127.0.0.1:8030/v1/models >/dev/null
echo "terminated_client_pids=${pids[*]}"
echo "candidate_service=healthy"
