#!/usr/bin/env bash
set -e

case_dir=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
script="${case_dir}/commands/apply-hy4-plugin-native-decode-sparse-mla-20260920.py"

sha256sum "${script}"
docker exec hy4-opt-20260914 bash -lc \
  "cd /workspace/vllm-plugin-FL && python '${script}'"
docker exec hy4-opt-20260914 bash -lc \
  "cd /workspace/vllm-plugin-FL && python -m compileall -q vllm_fl/dispatch/backends/flaggems/impl/mla_sparse.py vllm_fl/dispatch/backends/vendor/thead/impl/mla_decode.py tests/unit_tests/dispatch/test_flaggems_mla_sparse.py"
docker exec hy4-opt-20260914 bash -lc \
  "cd /workspace/vllm-plugin-FL && git diff --check && pytest -q tests/unit_tests/dispatch/test_flaggems_mla_sparse.py"
