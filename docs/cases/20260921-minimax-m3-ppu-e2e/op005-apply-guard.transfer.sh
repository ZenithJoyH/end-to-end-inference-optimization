#!/bin/sh
set -eu

case_root=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
expected_container=bd37abcbf719
expected_source=4d46bae0804ac32b698582d010d5f0e02d3570c6703efff9d1d666e2bf43fd94
source_file=/workspace/FlagGems/src/flag_gems/ops/linear.py
backup_file="$case_root/patches/op005-linear-original.py"
patch_file="$case_root/commands/op005-linear-native-guard.patch"

actual_container=$(docker inspect -f '{{.Id}}' "$container" | cut -c1-12)
test "$actual_container" = "$expected_container"
test -f "$patch_file"

if docker exec "$container" sh -lc "ps -eo args | grep -E '[v]llm serve|[a]pi_server'"; then
    echo 'Refusing to patch while an inference service is active' >&2
    exit 1
fi

actual_source=$(docker exec "$container" sha256sum "$source_file" | cut -d ' ' -f 1)
test "$actual_source" = "$expected_source"
mkdir -p "$case_root/patches"
test ! -e "$backup_file"
docker cp "$container:$source_file" "$backup_file"
backup_sha=$(sha256sum "$backup_file" | cut -d ' ' -f 1)
test "$backup_sha" = "$expected_source"

docker exec "$container" sh -lc \
    "cd /workspace/FlagGems && patch --dry-run -p0 -i '$patch_file'"
docker exec "$container" sh -lc \
    "cd /workspace/FlagGems && patch --batch -p0 -i '$patch_file'"
docker exec "$container" sh -lc \
    "cd /workspace/FlagGems && git diff --check -- src/flag_gems/ops/linear.py && python3 -c 'import ast; from pathlib import Path; ast.parse(Path(\"src/flag_gems/ops/linear.py\").read_text())' && sha256sum src/flag_gems/ops/linear.py && git status --short"
