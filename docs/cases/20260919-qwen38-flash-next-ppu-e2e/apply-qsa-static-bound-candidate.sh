#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
expected_container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
fg_repo=/workspace/FlagGems
plugin_repo=/workspace/vllm-plugin-FL-qwen38-adaptation
fg_patch=${case_root}/commands/155-qsa-static-bound-flaggems.patch
plugin_patch=${case_root}/commands/156-qsa-static-bound-plugin.patch
evidence=${case_root}/patches/op-006-qsa-static-bound-08

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test -f "${fg_patch}"
test -f "${plugin_patch}"
test ! -e "${evidence}"
if ss -ltnH 'sport = :8030' | grep -q .; then
  echo "candidate service must be stopped before source modification" >&2
  exit 3
fi
mkdir "${evidence}"

docker exec "${container}" git -C "${fg_repo}" rev-parse HEAD > "${evidence}/flaggems-head.before.txt"
docker exec "${container}" git -C "${fg_repo}" status --short > "${evidence}/flaggems-status.before.txt"
test ! -s "${evidence}/flaggems-status.before.txt"
docker exec "${container}" git -C "${plugin_repo}" rev-parse HEAD > "${evidence}/plugin-head.before.txt"
docker exec "${container}" git -C "${plugin_repo}" status --short > "${evidence}/plugin-status.before.txt"
if grep -F 'vllm_fl/models/qwen3_8_flash_next.py' "${evidence}/plugin-status.before.txt"; then
  echo "target Plugin model file is already modified" >&2
  exit 3
fi

sha256sum "${fg_patch}" "${plugin_patch}" > "${evidence}/input-patches.sha256"
docker cp "${fg_patch}" "${container}:/tmp/op-006-qsa-static-bound-flaggems.patch"
docker cp "${plugin_patch}" "${container}:/tmp/op-006-qsa-static-bound-plugin.patch"
docker exec "${container}" git -C "${fg_repo}" apply --check /tmp/op-006-qsa-static-bound-flaggems.patch
docker exec "${container}" git -C "${plugin_repo}" apply --check /tmp/op-006-qsa-static-bound-plugin.patch
docker exec "${container}" git -C "${fg_repo}" apply /tmp/op-006-qsa-static-bound-flaggems.patch
docker exec "${container}" git -C "${plugin_repo}" apply /tmp/op-006-qsa-static-bound-plugin.patch

docker exec "${container}" python3 -m py_compile \
  "${fg_repo}/src/flag_gems/fused/qsa.py" \
  "${plugin_repo}/vllm_fl/models/qwen3_8_flash_next.py"
docker exec \
  -e CUDA_VISIBLE_DEVICES=8 \
  -w "${fg_repo}" \
  "${container}" bash -lc '
set -e
source /usr/local/PPU_SDK/envsetup.sh
pytest -q tests/test_qwen3_8_flash_next_qsa.py::test_qsa_cuda_full_select_matches_reference_and_graph
' > "${evidence}/flaggems-focused-pytest.log" 2>&1

docker exec "${container}" git -C "${fg_repo}" diff --check
docker exec "${container}" git -C "${plugin_repo}" diff --check
docker exec "${container}" git -C "${fg_repo}" diff -- src/flag_gems/fused/qsa.py > "${evidence}/flaggems.applied.patch"
docker exec "${container}" git -C "${plugin_repo}" diff -- vllm_fl/models/qwen3_8_flash_next.py > "${evidence}/plugin.applied.patch"
docker exec "${container}" git -C "${fg_repo}" status --short > "${evidence}/flaggems-status.after.txt"
docker exec "${container}" git -C "${plugin_repo}" status --short > "${evidence}/plugin-status.after.txt"
test "$(cat "${evidence}/flaggems-status.after.txt")" = ' M src/flag_gems/fused/qsa.py'
grep -F ' M vllm_fl/models/qwen3_8_flash_next.py' "${evidence}/plugin-status.after.txt" >/dev/null

sha256sum \
  "${evidence}/flaggems-head.before.txt" "${evidence}/plugin-head.before.txt" \
  "${evidence}/flaggems-status.before.txt" "${evidence}/plugin-status.before.txt" \
  "${evidence}/input-patches.sha256" "${evidence}/flaggems-focused-pytest.log" \
  "${evidence}/flaggems.applied.patch" "${evidence}/plugin.applied.patch" \
  "${evidence}/flaggems-status.after.txt" "${evidence}/plugin-status.after.txt"
