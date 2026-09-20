#!/usr/bin/env bash
set -euo pipefail

container=qwen3.8-flash-opt-candidate-20260919
run_id=candidate-group-decode-baseline-01
mapfile -t pids < <(docker exec -i "${container}" python3 - "${run_id}" <<'PY'
import os
import sys
run_id = sys.argv[1]
processes = {}
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        stat = open(f"/proc/{entry}/stat").read().split()
        args = [x.decode(errors="replace") for x in open(f"/proc/{entry}/cmdline", "rb").read().split(b"\0") if x]
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    processes[int(entry)] = {"ppid": int(stat[3]), "text": " ".join(args)}
roots = [pid for pid, item in processes.items() if run_id in item["text"] and "vllm_perf.py" in item["text"]]
if len(roots) != 1:
    raise SystemExit(f"Expected one benchmark wrapper, got {roots}")
selected = {roots[0]}
changed = True
while changed:
    changed = False
    for pid, item in processes.items():
        if item["ppid"] in selected and pid not in selected:
            selected.add(pid)
            changed = True
for pid in sorted(selected, reverse=True):
    print(pid)
PY
)
test "${#pids[@]}" -ge 2
for pid in "${pids[@]}"; do
  docker exec "${container}" kill -KILL "${pid}" 2>/dev/null || true
done
sleep 2
for pid in "${pids[@]}"; do
  if docker exec "${container}" test -d "/proc/${pid}"; then
    echo "Benchmark PID ${pid} survived SIGKILL." >&2
    exit 2
  fi
done
timeout 5s curl -fsS http://127.0.0.1:8030/v1/models >/dev/null
echo "killed_benchmark_tree=${pids[*]}"
echo "candidate_service=healthy"
