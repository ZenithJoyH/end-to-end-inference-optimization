#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-20260919
expected_container_id=2eafbddebde1b14c691173de29d1965bc48064829a86ee4150056ef1fc5297f7
run_id=release-baseline-service-for-isolated-probes-01
run_dir=${case_root}/transitions/${run_id}
before=${run_dir}/before-process.json
after_ppu=${run_dir}/host-ppu-smi.after-release.txt

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test ! -e "${run_dir}"
mkdir "${run_dir}"

docker exec -i "${container}" python3 - "${before}" <<'PY'
import json
import os
import signal
import sys

output = sys.argv[1]
model = "/mnt/cpfs/models/Qwen3.8-Flash-Next"

def snapshot(pid):
    raw = open(f"/proc/{pid}/stat", encoding="utf-8").read()
    tail = raw[raw.rfind(")") + 2:].split()
    args = [value.decode(errors="replace") for value in open(
        f"/proc/{pid}/cmdline", "rb").read().split(b"\0") if value]
    return {"pid": pid, "ppid": int(tail[1]), "start_ticks": int(tail[19]), "args": args}

processes = {}
matches = []
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        item = snapshot(int(entry))
    except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
        continue
    processes[item["pid"]] = item
    args = item["args"]
    if "serve" in args and model in args and "--port" in args:
        if args[args.index("--port") + 1] == "8020":
            matches.append(item)
if len(matches) != 1:
    raise SystemExit(f"expected exactly one port-8020 model service, found {matches}")
service = matches[0]
environment = {}
for entry in open(f"/proc/{service['pid']}/environ", "rb").read().split(b"\0"):
    if b"=" not in entry:
        continue
    key, value = entry.split(b"=", 1)
    key = key.decode(errors="replace")
    if key in {
        "CUDA_VISIBLE_DEVICES", "VLLM_TUNED_CONFIG_FOLDER",
        "VLLM_FL_FLAGOS_BLACKLIST_APPEND", "VLLM_FL_QSA_STATIC_SCORE_COLUMNS",
    }:
        environment[key] = value.decode(errors="replace")
if environment.get("CUDA_VISIBLE_DEVICES") != "0,1,2,3,4,5,6,7":
    raise SystemExit(f"unexpected device assignment: {environment}")

tree = {service["pid"]}
changed = True
while changed:
    changed = False
    for pid, item in processes.items():
        if pid not in tree and item["ppid"] in tree:
            tree.add(pid)
            changed = True
evidence = dict(service)
evidence["selected_environment"] = environment
evidence["tree"] = [processes[pid] for pid in sorted(tree)]
open(output, "w", encoding="utf-8").write(
    json.dumps(evidence, indent=2, sort_keys=True) + "\n"
)
os.kill(service["pid"], signal.SIGTERM)
PY

docker exec -i "${container}" python3 - "${before}" <<'PY'
import json
import sys
import time

tree = json.load(open(sys.argv[1], encoding="utf-8"))["tree"]

def still_same(item):
    try:
        raw = open(f"/proc/{item['pid']}/stat", encoding="utf-8").read()
    except FileNotFoundError:
        return False
    return int(raw[raw.rfind(")") + 2:].split()[19]) == item["start_ticks"]

deadline = time.monotonic() + 300
while True:
    live = [item for item in tree if still_same(item)]
    if not live:
        break
    if time.monotonic() >= deadline:
        raise SystemExit(f"timed out waiting for exact service tree: {live}")
    time.sleep(2)
PY

if ss -ltnH 'sport = :8020' | grep -q .; then
  echo "port 8020 remains in use" >&2
  exit 3
fi
ppu-smi > "${after_ppu}"
sha256sum "${before}" "${after_ppu}"
