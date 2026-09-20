#!/usr/bin/env bash
set -euo pipefail

container=hy4-opt-20260914
run_dir=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/accuracy/formal-gate-20260918-f7d1aaa-a26a902-01
start_script=/mnt/nfs/users/jinghao/hy4-preview/start_hyv4-preview.sh

mkdir -p "${run_dir}/service"
if ss -lnt | grep -q ':8010 '; then
  echo 'port 8010 is already in use' >&2
  exit 1
fi
if docker exec "${container}" bash -lc "pgrep -af 'vllm serve|vllm.entrypoints.openai.api_server'"; then
  echo 'a vLLM process is already running in the optimization container' >&2
  exit 1
fi
docker exec "${container}" bash -lc "cd '${run_dir}/service' && bash '${start_script}'"
