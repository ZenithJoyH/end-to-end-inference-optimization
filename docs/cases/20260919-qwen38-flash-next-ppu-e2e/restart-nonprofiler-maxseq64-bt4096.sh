#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
profile_root=${case_dir}/profiling/prof-001-maxseq64-bt4096-mixed-capture
trace_dir=${profile_root}/traces
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
run_id=${1:?usage: restart-nonprofiler-maxseq64-bt4096.sh UNIQUE_RUN_ID}
source_manifest=${case_dir}/manifests/profiler-maxseq64-bt4096-service-comparison.json
raw_manifest=${case_dir}/transitions/${run_id}/post-profiler-maxseq64-bt4096-raw.json
target_manifest=${case_dir}/manifests/candidate-maxseq64-bt4096-postprofiler-service-comparison.json
profiler_config=$(printf '{"profiler":"torch","torch_profiler_dir":"%s","torch_profiler_with_stack":true,"torch_profiler_record_shapes":true}' "${trace_dir}")

test -f "${source_manifest}"
test ! -e "${target_manifest}"

export SOURCE_MAX_NUM_SEQS=64
export TARGET_MAX_NUM_SEQS=64
export SOURCE_MAX_NUM_BATCHED_TOKENS=4096
export TARGET_MAX_NUM_BATCHED_TOKENS=4096
export SOURCE_PROFILER_CONFIG="${profiler_config}"
export TARGET_PROFILER_CONFIG=
export TRANSITION_ROLE=post-profiler-maxseq64-bt4096

bash "${script_dir}/revert-candidate-maxseq32-draft.sh" \
  "${run_id}" "${source_manifest}"

python3 "${case_dir}/commands/performance/normalize-maxseq-service-manifest.py" \
  "${raw_manifest}" "${target_manifest}" 64 4096
sha256sum "${raw_manifest}" "${target_manifest}"
