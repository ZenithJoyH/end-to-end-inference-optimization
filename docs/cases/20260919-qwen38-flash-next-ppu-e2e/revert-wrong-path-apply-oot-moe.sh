#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
repo=/workspace/vllm-plugin-FL-qwen38-adaptation
wrong_path_patch=${case_root}/patches/op-002-fused-moe-runtime-observation-01/combined.patch
patch_dir=${case_root}/patches/op-002-fused-moe-oot-block-m-02
patch_file=${patch_dir}/oot-block-m.patch

test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test -f "${wrong_path_patch}"
test ! -e "${patch_dir}"
if ss -ltnH 'sport = :8030' | grep -q .; then
  echo "port 8030 is still in use" >&2
  exit 3
fi
mkdir "${patch_dir}"
docker cp "${case_root}/commands/64-fused-moe-oot-block-m-corrected.patch" "${container}:${patch_file}"

docker exec "${container}" bash -lc "
set -e
cd '${repo}'
git status --short > '${patch_dir}/status-before.txt'
git diff --quiet -- vllm_fl/ops/fused_moe/fused_moe.py
git apply --check '${patch_file}'
git apply '${patch_file}'
python3 -m py_compile vllm_fl/ops/fused_moe/fused_moe.py vllm_fl/ops/fused_moe/fused_moe_utils.py
git diff --check
git status --short > '${patch_dir}/status-after.txt'
git diff -- vllm_fl/ops/fused_moe/fused_moe.py vllm_fl/ops/fused_moe/fused_moe_utils.py > '${patch_dir}/combined.patch'
sha256sum '${wrong_path_patch}' '${patch_file}' '${patch_dir}/combined.patch' > '${patch_dir}/sha256.txt'
"
