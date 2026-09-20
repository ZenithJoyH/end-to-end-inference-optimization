#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
expected_container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
repo=/workspace/FlagGems
patch=${case_root}/commands/143-qsa-row-range-topk-service.patch
evidence=${case_root}/patches/op-005-qsa-row-range-topk-05

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test ! -e "${evidence}"
test -f "${patch}"
if docker exec "${container}" sh -lc "ps -ef | grep '[v]llm serve' | grep -- '--port 8030'"; then
  echo "candidate service must be stopped before source modification" >&2
  exit 3
fi
mkdir -p "${evidence}"
docker exec "${container}" git -C "${repo}" rev-parse HEAD > "${evidence}/head.before.txt"
docker exec "${container}" git -C "${repo}" status --short > "${evidence}/status.before.txt"
test ! -s "${evidence}/status.before.txt"
sha256sum "${patch}" > "${evidence}/patch.sha256"
docker cp "${patch}" "${container}:/tmp/op-005-qsa-row-range-topk.patch"
docker exec "${container}" git -C "${repo}" apply --check /tmp/op-005-qsa-row-range-topk.patch
docker exec "${container}" git -C "${repo}" apply /tmp/op-005-qsa-row-range-topk.patch
docker exec "${container}" python3 -m py_compile "${repo}/src/flag_gems/fused/qsa.py"
docker exec \
  -e CUDA_VISIBLE_DEVICES=8 \
  -w "${repo}" \
  "${container}" bash -lc '
set -e
source /usr/local/PPU_SDK/envsetup.sh
pytest -q tests/test_qwen3_8_flash_next_qsa.py::test_qsa_cuda_full_select_matches_reference_and_graph
' > "${evidence}/focused-pytest.log" 2>&1
docker exec "${container}" git -C "${repo}" diff --check
docker exec "${container}" git -C "${repo}" diff -- src/flag_gems/fused/qsa.py > "${evidence}/applied.patch"
docker exec "${container}" git -C "${repo}" status --short > "${evidence}/status.after.txt"
grep -F 'M src/flag_gems/fused/qsa.py' "${evidence}/status.after.txt" >/dev/null
sha256sum \
  "${evidence}/head.before.txt" "${evidence}/status.before.txt" \
  "${evidence}/patch.sha256" "${evidence}/focused-pytest.log" \
  "${evidence}/applied.patch" "${evidence}/status.after.txt"
