#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
expected_container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
repo=/workspace/FlagGems
applied_patch=${case_root}/patches/op-005-qsa-row-range-topk-05/applied.patch
evidence=${case_root}/patches/op-005-qsa-row-range-topk-revert-06

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test -f "${applied_patch}"
test ! -e "${evidence}"
if docker exec "${container}" sh -lc "ps -ef | grep '[v]llm serve' | grep -- '--port 8030'"; then
  echo "candidate service must be stopped before source rollback" >&2
  exit 3
fi
if ss -ltnH 'sport = :8030' | grep -q .; then
  echo "host port 8030 is still in use" >&2
  exit 3
fi

mkdir "${evidence}"
docker exec "${container}" git -C "${repo}" rev-parse HEAD > "${evidence}/head.before.txt"
docker exec "${container}" git -C "${repo}" status --short > "${evidence}/status.before.txt"
docker exec "${container}" git -C "${repo}" diff -- src/flag_gems/fused/qsa.py > "${evidence}/current.patch"
cmp "${applied_patch}" "${evidence}/current.patch"

docker cp "${applied_patch}" "${container}:/tmp/op-005-qsa-row-range-applied.patch"
docker exec "${container}" git -C "${repo}" apply -R --check /tmp/op-005-qsa-row-range-applied.patch
docker exec "${container}" git -C "${repo}" apply -R /tmp/op-005-qsa-row-range-applied.patch
docker exec "${container}" python3 -m py_compile "${repo}/src/flag_gems/fused/qsa.py"
docker exec "${container}" git -C "${repo}" diff --check
docker exec "${container}" git -C "${repo}" status --short > "${evidence}/status.after.txt"
test ! -s "${evidence}/status.after.txt"
docker exec "${container}" git -C "${repo}" diff --exit-code -- src/flag_gems/fused/qsa.py

sha256sum \
  "${applied_patch}" "${evidence}/head.before.txt" \
  "${evidence}/status.before.txt" "${evidence}/current.patch" \
  "${evidence}/status.after.txt"
