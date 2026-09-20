#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
builder=${case_root}/commands/build-hy4-sparse-mla-full-prefix-threshold384-benchmark-20260919.py
script=${case_root}/commands/benchmark-hy4-sparse-mla-full-prefix-threshold384-20260919.py
result_root=${case_root}/results/operator/sparse-mla-full-prefix-threshold384-20260919-06
result=${result_root}/summary.json
log=${result_root}/benchmark.log

test -s "${builder}"
test ! -e "${script}"
test ! -e "${result}"
test ! -e "${log}"
if pgrep -af '[v]llm serve|^VLLM::(EngineCore|Worker)' >/dev/null; then
  echo 'vLLM service or worker is active' >&2
  exit 1
fi
python3 "${builder}"
mkdir -p "${result_root}"

set +e
docker exec \
  -e CUDA_VISIBLE_DEVICES=0 \
  -w /workspace/FlagGems-vllm \
  hy4-opt-20260914 \
  timeout 1200 python "${script}" --output "${result}" \
  >"${log}" 2>&1
rc=$?
set -e
cat "${log}"
exit "${rc}"
