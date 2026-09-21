#!/usr/bin/env python3
"""Fail if the live 8023 service no longer matches the frozen manifest."""

import json
import os
from pathlib import Path
import sys


manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
expected_argv = manifest["launch_config"]["launch_args"]
expected = manifest["service_instance_id"].split(":")
expected_pid = int(expected[-2])
expected_ticks = int(expected[-1])
matches = []
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        argv = [
            item.decode(errors="replace")
            for item in Path(f"/proc/{entry}/cmdline").read_bytes().split(b"\0")
            if item
        ]
        raw = Path(f"/proc/{entry}/stat").read_text()
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    if argv == expected_argv:
        matches.append((int(entry), int(raw[raw.rfind(")") + 2 :].split()[19])))
if matches != [(expected_pid, expected_ticks)]:
    raise SystemExit(f"live service identity changed: {matches!r}")
