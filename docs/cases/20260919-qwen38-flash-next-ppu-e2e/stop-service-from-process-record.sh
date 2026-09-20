#!/usr/bin/env bash
set -euo pipefail

container=qwen3.8-flash-opt-candidate-20260919
case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
record=${case_root}/transitions/moe-bm16-restored-service-10/after-process.json
run_dir=${case_root}/transitions/stop-moe-bm16-restored-service-10
before=${run_dir}/before-stop-process.json

test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test -f "${record}"
test ! -e "${run_dir}"
mkdir "${run_dir}"

docker exec -i "${container}" python3 - "${record}" "${before}" <<'PY'
import json
import os
import signal
import sys
import time

record_path, before_path = sys.argv[1:]
expected = json.load(open(record_path, encoding="utf-8"))
pid = expected["pid"]


def snapshot(target_pid):
    raw = open(f"/proc/{target_pid}/stat", encoding="utf-8").read()
    tail = raw[raw.rfind(")") + 2 :].split()
    argv = [
        value.decode(errors="replace")
        for value in open(f"/proc/{target_pid}/cmdline", "rb").read().split(b"\0")
        if value
    ]
    return {"pid": target_pid, "ppid": int(tail[1]), "start_ticks": int(tail[19]), "args": argv}


live = snapshot(pid)
if live["start_ticks"] != expected["start_ticks"] or live["args"] != expected["args"]:
    raise SystemExit("PID identity changed; refusing to signal")

processes = {}
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        item = snapshot(int(entry))
    except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
        continue
    processes[item["pid"]] = item
tree = {pid}
changed = True
while changed:
    changed = False
    for child_pid, item in processes.items():
        if child_pid not in tree and item["ppid"] in tree:
            tree.add(child_pid)
            changed = True
evidence = {"service": live, "tree": [processes[value] for value in sorted(tree)]}
open(before_path, "w", encoding="utf-8").write(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
os.kill(pid, signal.SIGTERM)

deadline = time.monotonic() + 240
while True:
    remaining = []
    for item in evidence["tree"]:
        try:
            current = snapshot(item["pid"])
        except FileNotFoundError:
            continue
        if current["start_ticks"] == item["start_ticks"]:
            remaining.append(item["pid"])
    if not remaining:
        break
    if time.monotonic() >= deadline:
        raise SystemExit(f"timed out waiting for exact process tree: {remaining}")
    time.sleep(2)
PY

if ss -ltnH 'sport = :8030' | grep -q .; then
  echo "port 8030 is still in use" >&2
  exit 3
fi
sha256sum "${record}" "${before}"
