#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
profile_root=${case_dir}/profiling/prof-001-maxseq64-bt4096-mixed-capture
trace_dir=${profile_root}/traces
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
run_id=${1:?usage: restart-profiler-maxseq64-bt4096-from-bt2048.sh UNIQUE_RUN_ID [BT2048_MANIFEST]}
source_manifest=${2:-${case_dir}/manifests/candidate-maxseq64-bt2048-service-comparison.json}

test ! -e "${profile_root}"
mkdir -p "${trace_dir}"
profiler_config=$(printf '{"profiler":"torch","torch_profiler_dir":"%s","torch_profiler_with_stack":true,"torch_profiler_record_shapes":true}' "${trace_dir}")

export SOURCE_MAX_NUM_SEQS=64
export TARGET_MAX_NUM_SEQS=64
export SOURCE_MAX_NUM_BATCHED_TOKENS=2048
export TARGET_MAX_NUM_BATCHED_TOKENS=4096
export SOURCE_PROFILER_CONFIG=
export TARGET_PROFILER_CONFIG="${profiler_config}"
export TRANSITION_ROLE=profiler-maxseq64-bt4096
export SOURCE_MANIFEST_DEFAULT="${case_dir}/manifests/candidate-maxseq64-bt2048-service-comparison.json"

exec "${script_dir}/revert-candidate-maxseq32-draft.sh" \
  "${run_id}" "${source_manifest}"
