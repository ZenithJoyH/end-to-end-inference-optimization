#!/usr/bin/env python3
"""Bind the fw-002 cache/logging environment to a captured service manifest."""

import json
from pathlib import Path
import subprocess
import sys


if len(sys.argv) != 5:
    raise SystemExit(
        "usage: augment-fw002-service-manifest.py BASE_JSON CACHE_DIR "
        "PRINT_AUTOTUNING OUTPUT_JSON"
    )
base_path = Path(sys.argv[1]).resolve()
expected_cache = sys.argv[2]
expected_print = sys.argv[3]
output_path = Path(sys.argv[4]).resolve()
if expected_print not in ("0", "1"):
    raise SystemExit("PRINT_AUTOTUNING must be 0 or 1")
if output_path.exists():
    raise SystemExit(f"refusing to overwrite {output_path}")

manifest = json.loads(base_path.read_text(encoding="utf-8"))
pid = manifest["service_instance_id"].split(":")[-2]
raw = subprocess.check_output(
    [
        "docker",
        "exec",
        "minimaxM3-opt-20260921",
        "python3",
        "-c",
        f"import pathlib; print(pathlib.Path('/proc/{pid}/environ').read_bytes().hex())",
    ],
    text=True,
).strip()
environment = {}
for item in bytes.fromhex(raw).split(b"\0"):
    if b"=" in item:
        key, value = item.split(b"=", 1)
        environment[key.decode(errors="replace")] = value.decode(errors="replace")
actual = {
    "FLAGGEMS_CACHE_DIR": environment.get("FLAGGEMS_CACHE_DIR"),
    "TRITON_PRINT_AUTOTUNING": environment.get("TRITON_PRINT_AUTOTUNING", "0"),
    "FLAGTREE_AABS": environment.get("FLAGTREE_AABS"),
}
expected = {
    "FLAGGEMS_CACHE_DIR": expected_cache,
    "TRITON_PRINT_AUTOTUNING": expected_print,
    "FLAGTREE_AABS": "0",
}
if actual != expected:
    raise SystemExit(f"live service environment differs: {actual!r}")
manifest["launch_config"]["flaggems_cache_dir"] = expected_cache
manifest["launch_config"]["triton_print_autotuning"] = expected_print == "1"
manifest["launch_config"]["flagtree_aabs"] = 0
manifest["performance_context"]["cache_preparation"] = (
    "FlagGems tuning cache is isolated at the recorded directory; diagnostic "
    f"autotune logging is {'enabled' if expected_print == '1' else 'disabled'}."
)
output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
