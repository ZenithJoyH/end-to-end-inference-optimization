#!/usr/bin/env bash
set -eo pipefail

case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
script_path="$case_dir/commands/performance/benchmark-op007-generic-moe-config.py"
result_path="$case_dir/results/op007-generic-moe-config-screen.json"
container_name=minimaxM3-opt-20260921

test -f "$script_path"
test ! -e "$result_path"
sha256sum "$script_path"
docker exec "$container_name" python "$script_path" "$result_path"
sha256sum "$result_path"
