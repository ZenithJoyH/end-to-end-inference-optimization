#!/usr/bin/env bash
set -euo pipefail

action=${1:?usage: op007-switch-moe-source.sh candidate|revert TRANSITION_ID [EXPECTED_CANDIDATE_SHA256]}
transition_id=${2:?missing TRANSITION_ID}
candidate_sha=${3:-}
case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
source_path=/workspace/FlagGems/src/flag_gems/fused/fused_moe.py
backup_path=${case_dir}/patches/op007-generic-fused-moe-original.py
patch_path=${case_dir}/patches/op007-generic-moe-gemm2-bk64-v2.patch
transition=${case_dir}/transitions/${transition_id}
original_sha=a780da6348ba611640b546b47c60b79baa1312094386ce8f49d99d0d8e4750af

case "${action}" in
  candidate|revert) ;;
  *) echo "invalid action: ${action}" >&2; exit 2 ;;
esac
test ! -e "${transition}"
test -f "${patch_path}"
test -z "$(ppu-smi --query-compute-apps=pid --format=csv,noheader,nounits)"
if docker exec "${container}" pgrep -f '^python -m vllm.entrypoints.openai.api_server .* --port 8023( |$)' >/dev/null; then
  echo "model service still active" >&2
  exit 3
fi
if ss -ltnp | grep -qE ':8023\b'; then
  echo "port 8023 still active" >&2
  exit 3
fi

current_sha=$(docker exec "${container}" sha256sum "${source_path}" | cut -d ' ' -f 1)
if [[ "${action}" == candidate ]]; then
  test "${current_sha}" = "${original_sha}"
  test ! -e "${backup_path}"
  docker exec "${container}" cp "${source_path}" "${backup_path}"
  test "$(sha256sum "${backup_path}" | cut -d ' ' -f 1)" = "${original_sha}"
  docker exec "${container}" sh -c \
    "cd /workspace/FlagGems && git apply --check '${patch_path}'"
  docker exec "${container}" sh -c \
    "cd /workspace/FlagGems && git apply '${patch_path}'"
else
  test -n "${candidate_sha}"
  test "${current_sha}" = "${candidate_sha}"
  test "$(sha256sum "${backup_path}" | cut -d ' ' -f 1)" = "${original_sha}"
  docker exec "${container}" cp "${backup_path}" "${source_path}"
fi

mkdir -p "${transition}"
docker exec "${container}" sha256sum "${source_path}" > "${transition}/source.SHA256SUMS"
sha256sum "${backup_path}" "${patch_path}" > "${transition}/patches.SHA256SUMS"
docker exec "${container}" sh -c 'cd /workspace/FlagGems && git status --short' \
  > "${transition}/flaggems-status.txt"
cat "${transition}/source.SHA256SUMS"
