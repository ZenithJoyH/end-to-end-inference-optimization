#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
repo=/workspace/vllm-plugin-FL-qwen38-adaptation
patch_dir=${case_root}/patches/op-002-revert-plugin-hooks-use-tuned-folder-01
revert_patch=${patch_dir}/reverted-plugin-hooks.patch
config_dir=${case_root}/configs/moe-bm16-decode-only-01
config_file=${config_dir}/E=512,N=80,device_name=thead.json

test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test ! -e "${patch_dir}"
test ! -e "${config_dir}"
if ss -ltnH 'sport = :8030' | grep -q .; then
  echo "port 8030 is still in use" >&2
  exit 3
fi
mkdir "${patch_dir}"
mkdir -p "${config_dir}"

docker exec "${container}" bash -lc "
set -e
cd '${repo}'
git status --short > '${patch_dir}/status-before.txt'
git diff -- vllm_fl/__init__.py vllm_fl/ops/custom_ops.py vllm_fl/ops/fused_moe/fused_moe.py vllm_fl/ops/fused_moe/fused_moe_utils.py > '${revert_patch}'
test -s '${revert_patch}'
git apply -R --check '${revert_patch}'
git apply -R '${revert_patch}'
git diff --quiet -- vllm_fl/__init__.py vllm_fl/ops/custom_ops.py vllm_fl/ops/fused_moe/fused_moe.py vllm_fl/ops/fused_moe/fused_moe_utils.py
git status --short > '${patch_dir}/status-after.txt'
"

docker exec -i "${container}" bash -lc 'source /usr/local/PPU_SDK/envsetup.sh >/dev/null; python3 - "$@"' -- "${config_file}" "${patch_dir}/config-summary.json" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

from vllm.model_executor.layers.fused_moe.fused_moe import get_default_config

config_path = Path(sys.argv[1])
summary_path = Path(sys.argv[2])
configs = {}
for tokens in range(1, 4097):
    configs[str(tokens)] = get_default_config(
        tokens, 512, 80, 2560, 10, None, None
    )
baseline_64 = configs["64"].copy()
expected = {
    "BLOCK_SIZE_M": 32,
    "BLOCK_SIZE_N": 64,
    "BLOCK_SIZE_K": 128,
    "GROUP_SIZE_M": 1,
    "SPLIT_K": 1,
    "num_warps": 4,
    "num_stages": 3,
}
assert baseline_64 == expected, (baseline_64, expected)
configs["64"] = baseline_64 | {"BLOCK_SIZE_M": 16}
payload = json.dumps(configs, indent=2, sort_keys=True) + "\n"
config_path.write_text(payload, encoding="utf-8")
summary = {
    "schema_version": 1,
    "range": [1, 4096],
    "entries": len(configs),
    "baseline_m64": baseline_64,
    "candidate_m64": configs["64"],
    "m63": configs["63"],
    "m65": configs["65"],
    "m4096": configs["4096"],
    "config_sha256": hashlib.sha256(payload.encode()).hexdigest(),
}
summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

sha256sum "${revert_patch}" "${config_file}" "${patch_dir}/config-summary.json" > "${patch_dir}/sha256.txt"
