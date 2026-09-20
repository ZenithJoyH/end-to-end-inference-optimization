#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
record=${case_root}/transitions/post-prof002-restored-bt4096-service-17/before-maxseq64-process.json
evidence=${case_root}/transitions/post-prof002-stuck-tree-cleanup-18
before=${evidence}/before-sigkill.json
after=${evidence}/after-sigkill.json

test -f "${record}"
test ! -e "${evidence}"
mkdir "${evidence}"

docker exec -i "${container}" python3 - "${record}" "${before}" "${after}" <<'PY'
import json
import os
import signal
import sys
import time

record_path, before_path, after_path = sys.argv[1:]
expected = json.load(open(record_path, encoding="utf-8"))["tree"]


def snapshot(pid):
    raw = open(f"/proc/{pid}/stat", encoding="utf-8").read()
    tail = raw[raw.rfind(")") + 2 :].split()
    argv = [
        value.decode(errors="replace")
        for value in open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0")
        if value
    ]
    return {
        "pid": pid,
        "ppid": int(tail[1]),
        "state": tail[0],
        "start_ticks": int(tail[19]),
        "args": argv,
    }


live = []
for item in expected:
    try:
        current = snapshot(item["pid"])
    except FileNotFoundError:
        continue
    if current["start_ticks"] != item["start_ticks"]:
        raise SystemExit(f"PID start_ticks changed; refusing SIGKILL: {item['pid']}")
    if current["state"] != "Z" and current["args"] != item["args"]:
        raise SystemExit(f"PID identity changed; refusing SIGKILL: {item['pid']}")
    live.append(current)
open(before_path, "w", encoding="utf-8").write(json.dumps(live, indent=2, sort_keys=True) + "\n")

# Children first, then the exact recorded service root. Zombies disappear when
# their exact parent exits; no unrecorded PID receives a signal.
for item in sorted(live, key=lambda row: row["pid"] == expected[0]["pid"]):
    if item["state"] != "Z":
        os.kill(item["pid"], signal.SIGKILL)

deadline = time.monotonic() + 120
while True:
    remaining = []
    for item in live:
        try:
            current = snapshot(item["pid"])
        except FileNotFoundError:
            continue
        if current["start_ticks"] == item["start_ticks"]:
            remaining.append(current)
    if not remaining:
        break
    if time.monotonic() >= deadline:
        raise SystemExit(f"exact processes remain after SIGKILL: {remaining}")
    time.sleep(1)
open(after_path, "w", encoding="utf-8").write(json.dumps({"remaining": []}, indent=2) + "\n")
PY

if ss -ltnH 'sport = :8030' | grep -q .; then
  echo "port 8030 unexpectedly in use after cleanup" >&2
  exit 3
fi
sha256sum "${record}" "${before}" "${after}"
