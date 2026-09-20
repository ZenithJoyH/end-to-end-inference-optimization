#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
eval_name=qwen38-eval-e2e-20260919

docker inspect "${eval_name}" > "${case_root}/manifests/${eval_name}.retry.inspect.json"
docker exec "${eval_name}" \
  python3 "${case_root}/commands/accuracy/llmrun.py" \
  "${case_root}/commands/accuracy/baseline-sanity-retry.json" \
  2>&1 | tee "${case_root}/accuracy/baseline-sanity/runner-retry8192.log"
