#!/usr/bin/env bash
set -euo pipefail

container=hy4-opt-20260914
case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
commands="${case_root}/commands"
plugin_repo=/workspace/vllm-plugin-FL
flaggems_repo=/workspace/FlagGems
plugin_base=38f350b13fc15f08eb4641e1d6d1980ba3fc16aa
flaggems_base=5c2b9a1618c36651f96108d56f076361965f2d53
plugin_patch="${commands}/plugin-hy4-current-optimizations-final-20260918.patch"
flaggems_patch="${commands}/flaggems-hy4-current-optimizations-final-20260918.patch"
plugin_bundle="${commands}/plugin-hy4-current-optimizations-20260918.bundle"
flaggems_bundle="${commands}/flaggems-hy4-current-optimizations-20260918.bundle"
commit_record="${commands}/current-optimization-commits-20260918.txt"

for path in \
  "${plugin_patch}" \
  "${flaggems_patch}" \
  "${plugin_bundle}" \
  "${flaggems_bundle}" \
  "${commit_record}"; do
  test ! -e "${path}"
done

test "$(docker exec "${container}" git -C "${plugin_repo}" rev-parse HEAD)" = "${plugin_base}"
test "$(docker exec "${container}" git -C "${flaggems_repo}" rev-parse HEAD)" = "${flaggems_base}"

docker exec "${container}" git -C "${plugin_repo}" diff --check
docker exec "${container}" git -C "${flaggems_repo}" diff --check

docker exec "${container}" git -C "${plugin_repo}" diff --binary -- \
  tests/unit_tests/models/test_hy_v4.py \
  vllm_fl/dispatch/config/thead.yaml \
  vllm_fl/models/hy_v4.py >"${plugin_patch}"
docker exec "${container}" git -C "${flaggems_repo}" diff --binary -- \
  src/flag_gems/fused/fused_moe.py \
  src/flag_gems/fused/moe_sum.py \
  src/flag_gems/runtime/backend/_thead/fused/flashmla_sparse.py \
  src/flag_gems/runtime/backend/_thead/tune_configs.yaml \
  tests/test_DSA/test_flashmla_sparse_small_heads.py \
  tests/test_fused_moe.py \
  tests/test_moe_sum.py >"${flaggems_patch}"
test -s "${plugin_patch}"
test -s "${flaggems_patch}"

docker exec "${container}" git -C "${plugin_repo}" add -- \
  tests/unit_tests/models/test_hy_v4.py \
  vllm_fl/dispatch/config/thead.yaml \
  vllm_fl/models/hy_v4.py
docker exec "${container}" git -C "${plugin_repo}" diff --cached --check
docker exec "${container}" git -C "${plugin_repo}" commit \
  -m "perf(hy4): optimize indexer and router paths"

docker exec "${container}" git -C "${flaggems_repo}" add -- \
  src/flag_gems/fused/fused_moe.py \
  src/flag_gems/fused/moe_sum.py \
  src/flag_gems/runtime/backend/_thead/fused/flashmla_sparse.py \
  src/flag_gems/runtime/backend/_thead/tune_configs.yaml \
  tests/test_DSA/test_flashmla_sparse_small_heads.py \
  tests/test_fused_moe.py \
  tests/test_moe_sum.py
docker exec "${container}" git -C "${flaggems_repo}" diff --cached --check
docker exec "${container}" git -C "${flaggems_repo}" commit \
  -m "perf(thead): optimize Hy4 inference kernels"

plugin_commit="$(docker exec "${container}" git -C "${plugin_repo}" rev-parse HEAD)"
flaggems_commit="$(docker exec "${container}" git -C "${flaggems_repo}" rev-parse HEAD)"
test "${plugin_commit}" != "${plugin_base}"
test "${flaggems_commit}" != "${flaggems_base}"

docker exec "${container}" git -C "${plugin_repo}" bundle create \
  /tmp/plugin-hy4-current-optimizations-20260918.bundle \
  codex/deploy-pr477-20260910 "^${plugin_base}"
docker exec "${container}" git -C "${flaggems_repo}" bundle create \
  /tmp/flaggems-hy4-current-optimizations-20260918.bundle \
  support-hy4-preview "^${flaggems_base}"
docker cp \
  "${container}:/tmp/plugin-hy4-current-optimizations-20260918.bundle" \
  "${plugin_bundle}"
docker cp \
  "${container}:/tmp/flaggems-hy4-current-optimizations-20260918.bundle" \
  "${flaggems_bundle}"

{
  printf 'plugin_base=%s\n' "${plugin_base}"
  printf 'plugin_commit=%s\n' "${plugin_commit}"
  printf 'plugin_branch=%s\n' "$(docker exec "${container}" git -C "${plugin_repo}" branch --show-current)"
  printf 'flaggems_base=%s\n' "${flaggems_base}"
  printf 'flaggems_commit=%s\n' "${flaggems_commit}"
  printf 'flaggems_branch=%s\n' "$(docker exec "${container}" git -C "${flaggems_repo}" branch --show-current)"
} >"${commit_record}"
sha256sum \
  "${plugin_patch}" \
  "${flaggems_patch}" \
  "${plugin_bundle}" \
  "${flaggems_bundle}" \
  "${commit_record}" >"${commit_record}.sha256"

docker exec "${container}" git -C "${plugin_repo}" status --short
docker exec "${container}" git -C "${flaggems_repo}" status --short
cat "${commit_record}"
