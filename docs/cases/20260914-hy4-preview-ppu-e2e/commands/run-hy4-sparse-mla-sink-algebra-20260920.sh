#!/usr/bin/env bash
set -e

case_dir=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
experiment_dir="${case_dir}/results/operator/sparse-mla-exp2-softmax-20260920-04"
script="${case_dir}/commands/benchmark-hy4-sparse-mla-sink-algebra-20260920.py"

test ! -e "${experiment_dir}"
mkdir -p "${experiment_dir}"
sha256sum "${script}" > "${experiment_dir}/command.sha256"
docker exec hy4-opt-20260914 bash -lc \
  "source /usr/local/PPU_SDK/envsetup.sh && cd /workspace/FlagGems-vllm && python '${script}' --output '${experiment_dir}/summary.json'" \
  > "${experiment_dir}/stdout.log" \
  2> "${experiment_dir}/stderr.log"
