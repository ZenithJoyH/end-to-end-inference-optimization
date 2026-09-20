#!/usr/bin/env bash
set -euo pipefail

# DRAFT ONLY. Run on PPU-01 from the host after review. The shared transition
# engine defaults to the inverse 64 -> 32 revert; these variables select the
# symmetric 32 -> 64 candidate transition without weakening its identity gates.

case_dir=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
run_id=${1:?usage: restart-candidate-maxseq64-corrected.sh UNIQUE_RUN_ID [MAXSEQ32_RAW_MANIFEST]}
source_manifest=${2:-${case_dir}/manifests/candidate-maxseq32-service-comparison.json}

export SOURCE_MAX_NUM_SEQS=32
export TARGET_MAX_NUM_SEQS=64
export TRANSITION_ROLE=candidate-maxseq64
export SOURCE_MANIFEST_DEFAULT="${case_dir}/manifests/candidate-maxseq32-service-comparison.json"

exec "${script_dir}/revert-candidate-maxseq32-draft.sh" \
  "${run_id}" "${source_manifest}"
