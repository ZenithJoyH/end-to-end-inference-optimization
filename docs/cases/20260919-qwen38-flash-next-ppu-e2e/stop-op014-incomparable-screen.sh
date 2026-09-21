#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
audit_dir=${case_root}/performance/op014-cross-device-screen-invalid-control
target_result_dir=${case_root}/performance/op014-screen-service51-candidate-01

test ! -e "${audit_dir}"
mkdir "${audit_dir}"
docker exec -i "${container}" python3 - "${target_result_dir}" <<'PY' > "${audit_dir}/client-before-signal.json"
import json
import os
import signal
import sys

result_dir = sys.argv[1]
found = []
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        argv = [item.decode(errors="replace") for item in open(
            f"/proc/{entry}/cmdline", "rb").read().split(b"\0") if item]
        raw = open(f"/proc/{entry}/stat", encoding="utf-8").read()
        tail = raw[raw.rfind(")") + 2:].split()
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    if "bench" not in argv or "serve" not in argv or "--result-dir" not in argv:
        continue
    if argv[argv.index("--result-dir") + 1] != result_dir:
        continue
    found.append({"pid": int(entry), "start_ticks": int(tail[19]), "argv": argv})
if len(found) != 1:
    raise SystemExit(f"expected one exact benchmark client, got {len(found)}")
target = found[0]
# Re-read identity immediately before the only signal.
raw = open(f"/proc/{target['pid']}/stat", encoding="utf-8").read()
tail = raw[raw.rfind(")") + 2:].split()
argv = [item.decode(errors="replace") for item in open(
    f"/proc/{target['pid']}/cmdline", "rb").read().split(b"\0") if item]
if int(tail[19]) != target["start_ticks"] or argv != target["argv"]:
    raise SystemExit("benchmark PID identity changed")
print(json.dumps(target, indent=2, sort_keys=True))
os.kill(target["pid"], signal.SIGINT)
PY

for _ in $(seq 1 60); do
  if ! docker exec -i "${container}" python3 - "${audit_dir}/client-before-signal.json" <<'PY'
import json
import sys

target = json.load(open(sys.argv[1], encoding="utf-8"))
try:
    raw = open(f"/proc/{target['pid']}/stat", encoding="utf-8").read()
except FileNotFoundError:
    raise SystemExit(1)
tail = raw[raw.rfind(")") + 2:].split()
raise SystemExit(0 if int(tail[19]) == target["start_ticks"] else 1)
PY
  then
    break
  fi
  sleep 1
done

curl -fsS http://127.0.0.1:8030/health >/dev/null
curl -fsS http://127.0.0.1:8031/health >/dev/null
python3 - "${audit_dir}" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
payload = {
    "schema_version": 1,
    "decision": "cross_device_group_screen_invalid_for_comparison",
    "reason": (
        "service51 warmup on PPU0-7 was about 35% slower than service50 on PPU8-15; "
        "this dominates the expected one-line metadata optimization and requires a same-device control"
    ),
    "action": "SIGINT sent only to the exact active benchmark client; both services remained healthy",
}
(root / "decision.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
sha256sum "${audit_dir}/client-before-signal.json" "${audit_dir}/decision.json"
