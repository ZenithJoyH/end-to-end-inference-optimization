#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
container=hy4-opt-20260914
repo=/workspace/FlagGems
config=src/flag_gems/runtime/backend/_thead/tune_configs.yaml
patch_file="${case_root}/commands/add-thead-scaled-mm-prefill-configs-20260916.patch"
record_dir="${case_root}/results/operators/scaled-mm-prefill-config-apply-20260916-01"

test ! -e "${record_dir}"
mkdir -p "${record_dir}"

if ss -ltn | grep -q ':8010 '; then
  echo 'refusing to modify FlagGems while port 8010 is listening' >&2
  exit 1
fi

docker exec "${container}" sh -lc "
  set -eu
  cd '${repo}'
  test -z \"\$(git diff -- '${config}')\"
  ! grep -q '^scaled_mm:' '${config}'
  sha256sum '${config}'
  git status --short
  git diff --check
" >"${record_dir}/preflight.txt"

docker exec "${container}" sh -lc "cd '${repo}' && git apply --check '${patch_file}'"
docker exec "${container}" sh -lc "cd '${repo}' && git apply '${patch_file}'"

docker exec "${container}" python - <<'PY' >"${record_dir}/yaml-validation.txt"
from pathlib import Path
import yaml

path = Path('/workspace/FlagGems/src/flag_gems/runtime/backend/_thead/tune_configs.yaml')
data = yaml.safe_load(path.read_text())
configs = data['scaled_mm']
assert len(configs) == 7, len(configs)
required = {
    (128, 64, 64, 3, 4),
    (128, 128, 64, 3, 4),
    (64, 256, 64, 3, 4),
}
actual = {
    (
        row['META']['BLOCK_M'],
        row['META']['BLOCK_N'],
        row['META']['BLOCK_K'],
        row['num_stages'],
        row['num_warps'],
    )
    for row in configs
}
assert required <= actual, (required, actual)
print({'scaled_mm_config_count': len(configs), 'required_present': True})
PY

docker exec "${container}" sh -lc "
  set -eu
  cd '${repo}'
  sha256sum '${config}'
  git diff --check
  git diff -- '${config}'
" >"${record_dir}/post-apply.txt"

sha256sum "${record_dir}/preflight.txt" \
  "${record_dir}/yaml-validation.txt" \
  "${record_dir}/post-apply.txt" \
  >"${record_dir}/SHA256SUMS"
