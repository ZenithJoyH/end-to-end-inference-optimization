#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
repo=/workspace/vllm-plugin-FL-qwen38-adaptation
callsite_patch=${case_root}/patches/op-002-fused-moe-oot-block-m-04/callsite.patch
patch_dir=${case_root}/patches/op-002-fused-moe-config-symbol-01
symbol_patch=${patch_dir}/config-symbol.patch

test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test -f "${callsite_patch}"
test ! -e "${patch_dir}"
if ss -ltnH 'sport = :8030' | grep -q .; then
  echo "port 8030 is still in use" >&2
  exit 3
fi
mkdir "${patch_dir}"
docker cp "${case_root}/commands/71-patch-upstream-moe-config-symbol.patch" "${container}:${symbol_patch}"

docker exec "${container}" bash -lc "
set -e
cd '${repo}'
git status --short > '${patch_dir}/status-before.txt'
patch -R -p1 --dry-run < '${callsite_patch}'
patch -R -p1 < '${callsite_patch}'
grep -F '_maybe_tune_qwen38_flash_block_m' vllm_fl/ops/fused_moe/fused_moe_utils.py >/dev/null
patch -p1 --dry-run < '${symbol_patch}'
patch -p1 < '${symbol_patch}'
python3 -m py_compile vllm_fl/ops/custom_ops.py vllm_fl/ops/fused_moe/fused_moe_utils.py
git diff --check
git status --short > '${patch_dir}/status-after.txt'
git diff -- vllm_fl/ops/custom_ops.py vllm_fl/ops/fused_moe/fused_moe.py vllm_fl/ops/fused_moe/fused_moe_utils.py > '${patch_dir}/combined.patch'
sha256sum '${callsite_patch}' '${symbol_patch}' '${patch_dir}/combined.patch' > '${patch_dir}/sha256.txt'
"
