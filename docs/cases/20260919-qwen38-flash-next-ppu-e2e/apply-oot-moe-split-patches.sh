#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
repo=/workspace/vllm-plugin-FL-qwen38-adaptation
patch_dir=${case_root}/patches/op-002-fused-moe-oot-block-m-03
helper_patch=${patch_dir}/helper.patch
callsite_patch=${patch_dir}/callsite.patch

test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test ! -e "${patch_dir}"
if ss -ltnH 'sport = :8030' | grep -q .; then
  echo "port 8030 is still in use" >&2
  exit 3
fi
mkdir "${patch_dir}"
docker cp "${case_root}/commands/66-fused-moe-oot-helper.patch" "${container}:${helper_patch}"
docker cp "${case_root}/commands/67-fused-moe-oot-callsite.patch" "${container}:${callsite_patch}"

docker exec "${container}" bash -lc "
set -e
cd '${repo}'
git status --short > '${patch_dir}/status-before.txt'
git diff --quiet -- vllm_fl/ops/fused_moe/fused_moe.py vllm_fl/ops/fused_moe/fused_moe_utils.py
git apply --check '${helper_patch}'
git apply '${helper_patch}'
git apply --check '${callsite_patch}'
git apply '${callsite_patch}'
python3 -m py_compile vllm_fl/ops/fused_moe/fused_moe_utils.py
git diff --check
git status --short > '${patch_dir}/status-after.txt'
git diff -- vllm_fl/ops/fused_moe/fused_moe.py vllm_fl/ops/fused_moe/fused_moe_utils.py > '${patch_dir}/combined.patch'
sha256sum '${helper_patch}' '${callsite_patch}' '${patch_dir}/combined.patch' > '${patch_dir}/sha256.txt'
"
