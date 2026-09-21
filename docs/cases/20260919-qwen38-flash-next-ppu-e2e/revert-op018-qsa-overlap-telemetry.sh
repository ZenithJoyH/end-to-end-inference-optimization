#!/usr/bin/env bash
set -euo pipefail

manifest=${1:?usage: revert-op018-qsa-overlap-telemetry.sh PATCH_MANIFEST_JSON}
python3 - "${manifest}" <<'PY'
import hashlib
import json
import os
import shutil
import sys

path = sys.argv[1]
data = json.load(open(path, encoding="utf-8"))
digest = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
if digest(data["qsa_path"]) != data["patched_sha256"]:
    raise SystemExit("patched qsa.py changed; refusing blind revert")
if digest(data["helper_path"]) != data["helper_sha256"]:
    raise SystemExit("telemetry helper changed; refusing blind removal")
shutil.copy2(data["backup_path"], data["qsa_path"])
os.unlink(data["helper_path"])
if digest(data["qsa_path"]) != data["before_sha256"]:
    raise SystemExit("restored qsa.py SHA mismatch")
print(data["before_sha256"])
PY
