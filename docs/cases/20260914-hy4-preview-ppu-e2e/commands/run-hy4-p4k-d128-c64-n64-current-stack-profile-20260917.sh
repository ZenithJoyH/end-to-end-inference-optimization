#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
builder="${case_root}/commands/build-hy4-p4k-d128-c64-n64-current-stack-profile-20260917.py"
generated="${case_root}/commands/run-hy4-p4k-d128-c64-n64-current-stack-reprofile-generated-20260917.sh"

test -f "${builder}"
test ! -e "${generated}"
python3 "${builder}"
test -s "${generated}"
bash -n "${generated}"
sha256sum "${generated}" >"${generated}.sha256"
bash "${generated}"
