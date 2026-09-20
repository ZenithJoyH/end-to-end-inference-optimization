#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
run_id=${1:?usage: restart-candidate-maxseq48-from64.sh UNIQUE_RUN_ID [MAXSEQ64_MANIFEST]}
source_manifest=${2:-${case_dir}/manifests/candidate-maxseq64-service-comparison.json}

export SOURCE_MAX_NUM_SEQS=64
export TARGET_MAX_NUM_SEQS=48
export TRANSITION_ROLE=candidate-maxseq48
export SOURCE_MANIFEST_DEFAULT="${case_dir}/manifests/candidate-maxseq64-service-comparison.json"

exec "${script_dir}/revert-candidate-maxseq32-draft.sh" \
  "${run_id}" "${source_manifest}"
