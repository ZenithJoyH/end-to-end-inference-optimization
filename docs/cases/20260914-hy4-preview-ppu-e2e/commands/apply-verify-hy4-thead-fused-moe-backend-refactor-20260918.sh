#!/usr/bin/env bash
set -euo pipefail

container=hy4-opt-20260914
case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
bundle="${case_root}/commands/flaggems-thead-fused-moe-backend-refactor-retry1-20260918.bundle"
verify_script="${case_root}/commands/verify-hy4-thead-fused-moe-backend-refactor-retry1-20260918.py"
container_bundle=/tmp/flaggems-thead-fused-moe-backend-refactor-retry1-20260918.bundle
container_verify_script=/tmp/verify-hy4-thead-fused-moe-backend-refactor-retry1-20260918.py
result_dir="${case_root}/results/operator/fused-moe-backend-refactor-20260918"
repo=/workspace/FlagGems
base=7bca7a3a60fb3fa75c3ab15ecf4d96b7d3cce680
candidate=0e02755770011d517c8de591bf91998bbcf30ad1

test -f "${bundle}"
test -f "${verify_script}"
test "$(sha256sum "${bundle}" | awk '{print $1}')" = \
  0f3dcc6d21e2f851da80a9606c615f06281cd4e67cc26537dd5b908dc522583d
test ! -e "${result_dir}"
test "$(docker exec "${container}" git -C "${repo}" rev-parse HEAD)" = "${base}"
test -z "$(docker exec "${container}" git -C "${repo}" status --short)"

docker cp "${bundle}" "${container}:${container_bundle}"
docker cp "${verify_script}" "${container}:${container_verify_script}"
docker exec "${container}" git -C "${repo}" fetch "${container_bundle}" \
  refs/heads/support-hy4-preview:refs/heads/codex-thead-fused-moe-refactor-20260918
test "$(docker exec "${container}" git -C "${repo}" rev-parse \
  codex-thead-fused-moe-refactor-20260918)" = "${candidate}"
docker exec "${container}" git -C "${repo}" merge --ff-only "${candidate}"

test -z "$(docker exec "${container}" git -C "${repo}" diff \
  5c2b9a1618c36651f96108d56f076361965f2d53 -- \
  src/flag_gems/fused/fused_moe.py src/flag_gems/fused/moe_sum.py)"
docker exec "${container}" python -m compileall -q \
  "${repo}/src/flag_gems/runtime/backend/_thead/fused/fused_moe.py" \
  "${repo}/src/flag_gems/runtime/backend/_thead/fused/moe_sum.py"
docker exec "${container}" bash -lc \
  "cd '${repo}' && python -m pytest -q \
  tests/test_DSA/test_flashmla_sparse_small_heads.py \
  tests/test_fused_moe.py tests/test_moe_sum.py tests/test_thead_fused_moe.py"

mkdir -p "${result_dir}"
docker exec "${container}" python "${container_verify_script}" \
  >"${result_dir}/source-and-graph-validation.json"
sha256sum "${result_dir}/source-and-graph-validation.json" \
  >"${result_dir}/source-and-graph-validation.json.sha256"
docker exec "${container}" git -C "${repo}" diff --check
test -z "$(docker exec "${container}" git -C "${repo}" status --short)"
cat "${result_dir}/source-and-graph-validation.json"
