#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
run_id=p4k-longprefill2048-mixed-candidate-01
evidence_dir=${case_root}/transitions/stop-p4k-longprefill2048-after-warmup-20
before=${evidence_dir}/before-term.json
after=${evidence_dir}/after-term.json

test ! -e "${evidence_dir}"
mkdir "${evidence_dir}"
docker exec -i "${container}" python3 - "${run_id}" "${before}" <<'PY'
import json
import os
import sys
from pathlib import Path

run_id, output = sys.argv[1:]
processes = {}
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        raw = open(f"/proc/{entry}/stat", encoding="utf-8").read()
        tail = raw[raw.rfind(")") + 2 :].split()
        argv = [
            value.decode(errors="replace")
            for value in open(f"/proc/{entry}/cmdline", "rb").read().split(b"\0")
            if value
        ]
    except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
        continue
    processes[int(entry)] = {
        "pid": int(entry),
        "ppid": int(tail[1]),
        "state": tail[0],
        "start_ticks": int(tail[19]),
        "args": argv,
    }
roots = [
    pid for pid, item in processes.items()
    if run_id in " ".join(item["args"]) and "vllm_perf.py" in " ".join(item["args"])
]
if len(roots) != 1:
    raise SystemExit(f"expected one benchmark wrapper, got {roots}")
selected = {roots[0]}
changed = True
while changed:
    changed = False
    for pid, item in processes.items():
        if pid not in selected and item["ppid"] in selected:
            selected.add(pid)
            changed = True
payload = {"run_id": run_id, "root_pid": roots[0], "tree": [processes[p] for p in sorted(selected)]}
Path(output).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

docker exec -i "${container}" python3 - "${before}" <<'PY'
import json
import os
import signal
import sys

expected = json.load(open(sys.argv[1], encoding="utf-8"))
for item in sorted(expected["tree"], key=lambda row: row["pid"], reverse=True):
    pid = item["pid"]
    try:
        raw = open(f"/proc/{pid}/stat", encoding="utf-8").read()
        tail = raw[raw.rfind(")") + 2 :].split()
        argv = [
            value.decode(errors="replace")
            for value in open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0")
            if value
        ]
    except FileNotFoundError:
        continue
    if int(tail[19]) != item["start_ticks"] or argv != item["args"]:
        raise SystemExit(f"PID identity changed; refusing signal: {pid}")
    os.kill(pid, signal.SIGTERM)
PY

docker exec -i "${container}" python3 - "${before}" "${after}" <<'PY'
import json
import sys
import time
from pathlib import Path

expected = json.load(open(sys.argv[1], encoding="utf-8"))["tree"]
output = sys.argv[2]

def still_same(item):
    try:
        raw = open(f"/proc/{item['pid']}/stat", encoding="utf-8").read()
    except FileNotFoundError:
        return False
    tail = raw[raw.rfind(")") + 2 :].split()
    return int(tail[19]) == item["start_ticks"]

deadline = time.monotonic() + 60
while True:
    live = [item for item in expected if still_same(item)]
    if not live:
        break
    if time.monotonic() >= deadline:
        raise SystemExit(f"timed out waiting for exact benchmark tree: {live}")
    time.sleep(1)
Path(output).write_text(json.dumps({"remaining": []}, indent=2) + "\n", encoding="utf-8")
PY

for _ in $(seq 1 120); do
  metrics=$(docker exec "${container}" curl -fsS http://127.0.0.1:8030/metrics)
  running=$(printf '%s\n' "${metrics}" | awk '/^vllm:num_requests_running\{/ {print $2; exit}')
  waiting=$(printf '%s\n' "${metrics}" | awk '/^vllm:num_requests_waiting\{/ {print $2; exit}')
  if test "${running:-1}" = 0.0 && test "${waiting:-1}" = 0.0; then
    break
  fi
  sleep 1
done
test "${running:-1}" = 0.0
test "${waiting:-1}" = 0.0
docker exec "${container}" curl -fsS http://127.0.0.1:8030/v1/models >/dev/null
sha256sum "${before}" "${after}"
