#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
repo=/workspace/vllm-plugin-FL-qwen38-adaptation
patch_dir=${case_root}/patches/op-002-fused-moe-runtime-observation-01
patch_file=${patch_dir}/runtime-observation.patch

test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test ! -e "${patch_dir}"
mkdir "${patch_dir}"
docker cp "${case_root}/commands/57-fused-moe-runtime-observation.patch" "${container}:${patch_file}"

docker exec "${container}" bash -lc "
set -e
cd '${repo}'
git status --short > '${patch_dir}/status-before.txt'
git apply --check '${patch_file}'
git apply '${patch_file}'
python3 -m py_compile vllm_fl/ops/fused_moe/fused_moe.py
git diff --check
git status --short > '${patch_dir}/status-after.txt'
git diff -- vllm_fl/ops/fused_moe/fused_moe.py > '${patch_dir}/combined.patch'
sha256sum '${patch_file}' '${patch_dir}/combined.patch' > '${patch_dir}/sha256.txt'
"
