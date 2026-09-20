#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
run_id=${1:?usage: restart-candidate-maxseq64-bt2048-from48.sh UNIQUE_RUN_ID [MAXSEQ48_MANIFEST]}
source_manifest=${2:-${case_dir}/manifests/candidate-maxseq48-service-comparison.json}

export SOURCE_MAX_NUM_SEQS=48
export TARGET_MAX_NUM_SEQS=64
export SOURCE_MAX_NUM_BATCHED_TOKENS=4096
export TARGET_MAX_NUM_BATCHED_TOKENS=2048
export TRANSITION_ROLE=candidate-maxseq64-bt2048
export SOURCE_MANIFEST_DEFAULT="${case_dir}/manifests/candidate-maxseq48-service-comparison.json"

exec "${script_dir}/revert-candidate-maxseq32-draft.sh" \
  "${run_id}" "${source_manifest}"
