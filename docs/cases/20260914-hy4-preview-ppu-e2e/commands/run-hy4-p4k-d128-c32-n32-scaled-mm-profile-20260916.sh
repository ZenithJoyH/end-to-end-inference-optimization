#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
builder="${case_root}/commands/build-hy4-p4k-d128-c32-n32-scaled-mm-profile-20260916.py"
generated="${case_root}/commands/run-hy4-p4k-d128-c32-n32-scaled-mm-reprofile-generated-20260916.sh"

test -f "${builder}"
test ! -e "${generated}"
python3 "${builder}"
test -s "${generated}"
bash -n "${generated}"
sha256sum "${generated}" >"${generated}.sha256"
bash "${generated}"
