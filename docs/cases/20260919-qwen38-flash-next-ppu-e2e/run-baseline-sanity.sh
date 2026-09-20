#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
eval_name=qwen38-eval-e2e-20260919
eval_image=harbor.baai.ac.cn/flageval/flageval-llmeval:v1
dataset_source=/mnt/nfs/users/jinghao/hy4-preview/06-cache/huggingface/datasets/Idavidrein___gpqa
dataset_target=/root/.cache/huggingface/datasets/Idavidrein___gpqa

if docker container inspect "${eval_name}" >/dev/null 2>&1; then
  echo "Refusing to replace existing container: ${eval_name}" >&2
  exit 1
fi

mkdir -p "${case_root}/accuracy/baseline-sanity"

docker run -d \
  --name "${eval_name}" \
  --network host \
  --mount "type=bind,src=/mnt/nfs/users/jinghao/qwen3.8-flash,dst=/mnt/nfs/users/jinghao/qwen3.8-flash" \
  --mount "type=bind,src=${dataset_source},dst=${dataset_target},readonly" \
  "${eval_image}" \
  sleep infinity

docker inspect "${eval_name}" > "${case_root}/manifests/${eval_name}.inspect.json"
docker exec "${eval_name}" \
  python3 "${case_root}/commands/accuracy/llmrun.py" \
  "${case_root}/commands/accuracy/baseline-sanity.json" \
  2>&1 | tee "${case_root}/accuracy/baseline-sanity/runner.log"
