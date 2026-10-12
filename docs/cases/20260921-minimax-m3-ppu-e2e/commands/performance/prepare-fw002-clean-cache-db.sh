#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
cache_dir=/root/.flaggems-fw002-aabs0-clean-v2
db_file=${cache_dir}/config_cache/TunedConfig_thead_triton_3_6.db
evidence=${case_dir}/results/fw002-clean-cache-db-preparation.json

test ! -e "${evidence}"
docker exec "${container}" test ! -e "${cache_dir}"
docker exec "${container}" mkdir -p "${cache_dir}/config_cache"
docker exec -i "${container}" python3 - "${db_file}" > "${evidence}" <<'PY'
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

path = Path(sys.argv[1])
conn = sqlite3.connect(path, timeout=30.0)
mode = conn.execute("PRAGMA journal_mode=WAL").fetchone()[0]
conn.execute("PRAGMA synchronous=NORMAL")
conn.commit()
conn.close()
data = path.read_bytes()
print(json.dumps({
    "cache_dir": str(path.parent.parent),
    "database": str(path),
    "journal_mode": mode,
    "database_size_bytes": len(data),
    "database_sha256": hashlib.sha256(data).hexdigest(),
    "initialization": "single_process_python_sqlite3_before_tp16_launch",
}, indent=2, sort_keys=True))
PY

sha256sum "$0" "${evidence}" > "${case_dir}/results/fw002-clean-cache-db-preparation.SHA256SUMS"
