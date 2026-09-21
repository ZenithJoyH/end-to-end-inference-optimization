#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
result_dir="${case_root}/results/operator/p16k-cached-prefill-hybrid-validation-20260921-02"
benchmark_result="${case_root}/results/operator/sparse-mla-p16k-cached-prefill-hybrid-20260921-03"
wrapper="${case_root}/commands/benchmark-hy4-p16k-cached-prefill-sparse-mla-integrated-20260921.py"

test ! -e "${result_dir}"
test ! -e "${benchmark_result}"
mkdir -p "${result_dir}" "${benchmark_result}"

python -m compileall -q \
  /workspace/FlagGems-vllm/src/flaggems_vllm/runtime/backend/_thead/fused/flashmla_sparse.py \
  /workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/flaggems/impl/mla_sparse.py \
  >"${result_dir}/compileall.stdout" 2>"${result_dir}/compileall.stderr"

cd /workspace/vllm-plugin-FL
pytest -q tests/unit_tests/dispatch/test_flaggems_mla_sparse.py \
  >"${result_dir}/plugin-pytest.stdout" 2>"${result_dir}/plugin-pytest.stderr"

cd /workspace/FlagGems-vllm
pytest -q tests/test_thead_hy4_ops.py \
  >"${result_dir}/flaggems-vllm-pytest.stdout" \
  2>"${result_dir}/flaggems-vllm-pytest.stderr"

python "${wrapper}" --output "${benchmark_result}/summary.json" \
  >"${benchmark_result}/stdout.log" 2>"${benchmark_result}/stderr.log"
grep -F '"status": "candidate"' "${benchmark_result}/summary.json"

git -C /workspace/FlagGems-vllm diff --check
git -C /workspace/vllm-plugin-FL diff --check
sha256sum \
  /workspace/FlagGems-vllm/src/flaggems_vllm/runtime/backend/_thead/fused/flashmla_sparse.py \
  /workspace/FlagGems-vllm/src/flaggems_vllm/runtime/backend/_thead/fused/__init__.py \
  /workspace/FlagGems-vllm/tests/test_thead_hy4_ops.py \
  /workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/flaggems/impl/mla_sparse.py \
  /workspace/vllm-plugin-FL/tests/unit_tests/dispatch/test_flaggems_mla_sparse.py \
  "${case_root}/commands/flaggems-vllm-hy4-p16k-cached-prefill-hybrid-20260921.patch" \
  "${case_root}/commands/plugin-hy4-p16k-cached-prefill-hybrid-20260921.patch" \
  "${benchmark_result}/summary.json" \
  >"${result_dir}/sha256.txt"
printf 'status=passed\ncompleted_at=%s\n' "$(date --iso-8601=seconds)" \
  >"${result_dir}/status.txt"
cat "${result_dir}/plugin-pytest.stdout"
cat "${result_dir}/flaggems-vllm-pytest.stdout"
cat "${benchmark_result}/summary.json"
cat "${result_dir}/sha256.txt"
