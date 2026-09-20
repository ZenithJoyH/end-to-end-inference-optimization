#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
repo=/workspace/vllm-plugin-FL-qwen38-adaptation
patch_dir=${case_root}/patches/op-002-fused-moe-config-symbol-observe-02
patch_file=${patch_dir}/ensure-hook-observe.patch

test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test ! -e "${patch_dir}"
if ss -ltnH 'sport = :8030' | grep -q .; then
  echo "port 8030 is still in use" >&2
  exit 3
fi
mkdir "${patch_dir}"
docker cp "${case_root}/commands/78-ensure-moe-config-hook-observe-corrected.patch" "${container}:${patch_file}"

docker exec "${container}" bash -lc "
set -e
cd '${repo}'
git status --short > '${patch_dir}/status-before.txt'
patch -p1 --dry-run < '${patch_file}'
patch -p1 < '${patch_file}'
python3 -m py_compile vllm_fl/ops/custom_ops.py vllm_fl/ops/fused_moe/fused_moe_utils.py
git diff --check
git status --short > '${patch_dir}/status-after.txt'
git diff -- vllm_fl/ops/custom_ops.py vllm_fl/ops/fused_moe/fused_moe_utils.py > '${patch_dir}/combined.patch'
sha256sum '${patch_file}' '${patch_dir}/combined.patch' > '${patch_dir}/sha256.txt'
"
