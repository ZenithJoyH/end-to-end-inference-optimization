#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
instance=${case_root}/smoke/op014-service56-revert-graph-01/service-instance.json
receipt=${case_root}/transitions/stop-op014-revert-service56-for-probe

test -f "${instance}"
test ! -e "${receipt}"
mkdir -p "${receipt}"

docker exec -i "${container}" python3 - "${instance}" <<'PY' > "${receipt}/before.json"
import json
import os
import signal
import sys
import time

instance = json.load(open(sys.argv[1], encoding="utf-8"))
pid = int(instance["pid"])
expected_start = int(instance["start_ticks"])

def stat_start(value):
    raw = open(f"/proc/{value}/stat", encoding="utf-8").read()
    return int(raw[raw.rfind(")") + 2:].split()[19])

if stat_start(pid) != expected_start:
    raise SystemExit("service56 PID identity changed")
children = {}
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        raw = open(f"/proc/{entry}/stat", encoding="utf-8").read()
        fields = raw[raw.rfind(")") + 2:].split()
        children[int(entry)] = int(fields[1])
    except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
        pass
tree = {pid}
changed = True
while changed:
    changed = False
    for child, parent in children.items():
        if parent in tree and child not in tree:
            tree.add(child)
            changed = True
print(json.dumps({"root_pid": pid, "root_start_ticks": expected_start, "tree": sorted(tree)}, indent=2))
os.kill(pid, signal.SIGTERM)
deadline = time.time() + 60
while time.time() < deadline:
    if not os.path.exists(f"/proc/{pid}"):
        break
    time.sleep(0.25)
else:
    raise SystemExit("service56 did not exit after SIGTERM")
PY

if curl -fsS http://127.0.0.1:8031/health >/dev/null 2>&1; then
  echo "port 8031 still healthy after exact stop" >&2
  exit 1
fi
sha256sum "${instance}" "${receipt}/before.json"
