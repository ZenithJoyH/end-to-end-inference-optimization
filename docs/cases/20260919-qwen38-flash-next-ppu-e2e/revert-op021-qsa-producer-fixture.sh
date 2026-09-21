#!/usr/bin/env bash
set -euo pipefail

manifest=${1:?usage: revert-op021-qsa-producer-fixture.sh PATCH_MANIFEST_JSON}
python3 - "${manifest}" <<'PY'
import hashlib
import json
import os
import shutil
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
digest = lambda path: hashlib.sha256(open(path, "rb").read()).hexdigest()
qsa_sha = digest(data["qsa_path"])
helper_exists = os.path.exists(data["helper_path"])
helper_sha = digest(data["helper_path"]) if helper_exists else None
if qsa_sha not in (data["before_sha256"], data["patched_sha256"]):
    raise SystemExit("qsa.py is neither exact before nor exact patched state")
if helper_exists and helper_sha != data["helper_sha256"]:
    raise SystemExit("capture helper changed; refusing blind removal")
if qsa_sha == data["patched_sha256"]:
    shutil.copy2(data["backup_path"], data["qsa_path"])
if helper_exists:
    os.unlink(data["helper_path"])
if digest(data["qsa_path"]) != data["before_sha256"]:
    raise SystemExit("restored qsa.py SHA mismatch")
print(data["before_sha256"])
PY
