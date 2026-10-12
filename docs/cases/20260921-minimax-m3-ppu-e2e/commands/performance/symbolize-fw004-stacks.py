#!/usr/bin/env python3
"""Resolve captured fw-004 main-thread addresses with saved process maps."""

import json
from pathlib import Path
import re
import subprocess
import sys


root = Path(sys.argv[1]).resolve()


def load_maps(pid):
    rows = []
    for line in (root / f"{pid}.maps").read_text(encoding="utf-8").splitlines():
        parts = line.split(maxsplit=5)
        if len(parts) < 5:
            continue
        low, high = (int(value, 16) for value in parts[0].split("-"))
        rows.append({"low": low, "high": high, "offset": int(parts[2], 16),
                     "path": parts[5] if len(parts) == 6 else ""})
    return rows


def resolve(pid, address, maps):
    value = int(address, 16)
    match = next((row for row in maps if row["low"] <= value < row["high"]), None)
    if match is None or not match["path"].startswith("/"):
        return {"address": address, "status": "unmapped"}
    file_offset = value - match["low"] + match["offset"]
    executable = f"/proc/{pid}/root{match['path']}"
    command = ["eu-addr2line", "-C", "-f", "-i", "-e", executable, hex(file_offset)]
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {
        "address": address,
        "mapping": match["path"],
        "file_offset": hex(file_offset),
        "returncode": completed.returncode,
        "symbols": completed.stdout.strip().splitlines(),
        "stderr": completed.stderr.strip(),
    }


result = {"schema_version": 1, "eu_stack_main_threads": [], "gstack_main_thread": []}
for path in sorted(root.glob("*.eu-stack")):
    pid = int(path.name.split(".", 1)[0])
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(rf"TID {pid}:\n#0\s+(0x[0-9a-f]+)", text)
    if not match:
        result["eu_stack_main_threads"].append({"pid": pid, "status": "main_frame_missing"})
        continue
    result["eu_stack_main_threads"].append(
        {"pid": pid, "frame0": resolve(pid, match.group(1), load_maps(pid))}
    )

gstack_paths = list(root.glob("*.gstack"))
if len(gstack_paths) != 1:
    raise SystemExit(f"expected one gstack, got {len(gstack_paths)}")
gstack_path = gstack_paths[0]
pid = int(gstack_path.name.split(".", 1)[0])
text = gstack_path.read_text(encoding="utf-8", errors="replace")
match = re.search(rf"Thread 1 \(LWP {pid}\):\n((?:#\d+\s+0x[0-9a-f]+.*\n?)+)", text)
if not match:
    raise SystemExit("gstack main thread missing")
maps = load_maps(pid)
for frame, address in re.findall(r"#(\d+)\s+(0x[0-9a-f]+)", match.group(1)):
    row = resolve(pid, address, maps)
    row["frame"] = int(frame)
    result["gstack_main_thread"].append(row)

json.dump(result, sys.stdout, indent=2, sort_keys=True)
sys.stdout.write("\n")
