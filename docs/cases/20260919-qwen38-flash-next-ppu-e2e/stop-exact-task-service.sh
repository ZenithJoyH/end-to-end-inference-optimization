#!/usr/bin/env bash
set -euo pipefail

label=${1:?usage: stop-exact-task-service.sh LABEL CONTAINER MANIFEST PORT}
container=${2:?missing container}
manifest=${3:?missing manifest}
port=${4:?missing port}
case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
run_dir=${case_root}/transitions/${label}
before=${run_dir}/before-stop-process.json

case "${label}" in *[!A-Za-z0-9._-]*|'') exit 2;; esac
case "${port}" in 8020|8030) ;; *) echo "unexpected task service port" >&2; exit 2;; esac
test -f "${manifest}"
test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test ! -e "${run_dir}"
mkdir "${run_dir}"

docker exec -i "${container}" python3 - "${manifest}" "${port}" <<'PY' > "${before}"
import json
import os
import sys

manifest_path, port = sys.argv[1:]
model = "/mnt/cpfs/models/Qwen3.8-Flash-Next"
manifest = json.load(open(manifest_path, encoding="utf-8"))


def stat(pid):
    raw = open(f"/proc/{pid}/stat", encoding="utf-8").read()
    tail = raw[raw.rfind(")") + 2 :].split()
    return {"ppid": int(tail[1]), "start_ticks": int(tail[19])}


def args(pid):
    return [
        value.decode(errors="replace")
        for value in open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0")
        if value
    ]


processes = {}
services = []
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        argv = args(entry)
        info = stat(entry)
    except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
        continue
    pid = int(entry)
    processes[pid] = {"pid": pid, "args": argv, **info}
    if not any(os.path.basename(value) == "vllm" for value in argv):
        continue
    if "serve" not in argv or model not in argv or "--port" not in argv:
        continue
    if argv[argv.index("--port") + 1] == port:
        services.append(processes[pid])
if len(services) != 1:
    raise SystemExit(f"expected one task service on port {port}, got {len(services)}")
service = dict(services[0])
vllm_index = next(
    index for index, value in enumerate(service["args"])
    if os.path.basename(value) == "vllm"
)
live_launch_args = service["args"][vllm_index + 1 :]
if live_launch_args != manifest["launch_config"]["launch_args"]:
    raise SystemExit("live argv differs from frozen service manifest")
container_id = open("/proc/1/cpuset", encoding="utf-8").read().strip().split("/")[-1]
if len(container_id) < 12:
    # cgroup v2 may not expose the id; the caller still verifies argv/PID/start.
    container_id = manifest["service_instance_id"].split("-", 1)[0]
instance_id = f"{container_id[:12]}-{port}-{service['pid']}-{service['start_ticks']}"
if instance_id != manifest["service_instance_id"]:
    raise SystemExit(
        f"live service identity differs: {instance_id} != {manifest['service_instance_id']}"
    )
tree = {service["pid"]}
changed = True
while changed:
    changed = False
    for pid, process in processes.items():
        if pid not in tree and process["ppid"] in tree:
            tree.add(pid)
            changed = True
service["tree"] = [processes[pid] for pid in sorted(tree)]
print(json.dumps(service, indent=2, sort_keys=True))
PY

docker exec -i "${container}" python3 - "${before}" <<'PY'
import json
import os
import signal
import sys

expected = json.load(open(sys.argv[1], encoding="utf-8"))
pid = expected["pid"]
raw = open(f"/proc/{pid}/stat", encoding="utf-8").read()
tail = raw[raw.rfind(")") + 2 :].split()
argv = [
    value.decode(errors="replace")
    for value in open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0")
    if value
]
if int(tail[19]) != expected["start_ticks"] or argv != expected["args"]:
    raise SystemExit("PID identity changed; refusing to signal")
os.kill(pid, signal.SIGTERM)
PY

docker exec -i "${container}" python3 - "${before}" <<'PY'
import json
import sys
import time

expected = json.load(open(sys.argv[1], encoding="utf-8"))["tree"]


def same_process(item):
    try:
        raw = open(f"/proc/{item['pid']}/stat", encoding="utf-8").read()
    except FileNotFoundError:
        return False
    tail = raw[raw.rfind(")") + 2 :].split()
    return int(tail[19]) == item["start_ticks"]


deadline = time.monotonic() + 240
while True:
    live = [item for item in expected if same_process(item)]
    if not live:
        break
    if time.monotonic() >= deadline:
        raise SystemExit(f"timed out waiting for exact process tree: {live}")
    time.sleep(2)
PY

if ss -ltnH "sport = :${port}" | grep -q .; then
  echo "port ${port} is still in use" >&2
  exit 3
fi
sha256sum "${manifest}" "${before}"
