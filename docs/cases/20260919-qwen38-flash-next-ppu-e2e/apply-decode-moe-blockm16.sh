#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
expected_container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
repo=/workspace/vllm-plugin-FL-qwen38-adaptation
target=vllm_fl/ops/fused_moe/fused_moe.py
patch=${case_root}/commands/49-fused-moe-block-m-decode-only.patch
run_dir=${case_root}/patches/op-002-fused-moe-block-m-decode-only-01

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test -f "${patch}"
test ! -e "${run_dir}"
if docker exec "${container}" sh -lc "ps -ef | grep '[v]llm serve' | grep -- '--port 8030'"; then
  echo "candidate service is still live" >&2
  exit 3
fi
mkdir -p "${run_dir}"

docker exec "${container}" git -C "${repo}" rev-parse HEAD > "${run_dir}/head.before.txt"
docker exec "${container}" git -C "${repo}" status --short > "${run_dir}/status.before.txt"
docker exec "${container}" git -C "${repo}" diff --check
docker exec "${container}" git -C "${repo}" diff --quiet -- "${target}"
docker exec "${container}" sha256sum "${repo}/${target}" > "${run_dir}/target.before.sha256"
sha256sum "${patch}" > "${run_dir}/input-patch.sha256"

docker exec "${container}" git -C "${repo}" apply --check "${patch}"
docker exec "${container}" git -C "${repo}" apply "${patch}"
docker exec "${container}" python3 -m py_compile "${repo}/${target}"
docker exec "${container}" git -C "${repo}" diff --check -- "${target}"
docker exec "${container}" git -C "${repo}" diff --binary -- "${target}" > "${run_dir}/applied.patch"
docker exec "${container}" git -C "${repo}" status --short > "${run_dir}/status.after.txt"
docker exec "${container}" sha256sum "${repo}/${target}" > "${run_dir}/target.after.sha256"

test -s "${run_dir}/applied.patch"
cmp -s "${run_dir}/head.before.txt" <(docker exec "${container}" git -C "${repo}" rev-parse HEAD)
sha256sum "${run_dir}/applied.patch" "${run_dir}/status.before.txt" "${run_dir}/status.after.txt"
