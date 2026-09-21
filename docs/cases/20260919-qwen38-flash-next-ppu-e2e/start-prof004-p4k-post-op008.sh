#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
profile_root=${case_root}/profiling/prof-004-p4k-post-op008
trace_dir=${profile_root}/traces
source_manifest=${case_root}/manifests/candidate-maxseq64-bt4096-qsa-runtime-bound8448-moe-bm16-service-35.json

test ! -e "${profile_root}"
test -f "${source_manifest}"
mkdir -p "${trace_dir}"
profiler_config=$(printf '{"profiler":"torch","torch_profiler_dir":"%s","torch_profiler_with_stack":false,"torch_profiler_record_shapes":true}' "${trace_dir}")

export SOURCE_MAX_NUM_SEQS=64 TARGET_MAX_NUM_SEQS=64
export SOURCE_MAX_NUM_BATCHED_TOKENS=4096 TARGET_MAX_NUM_BATCHED_TOKENS=4096
export SOURCE_PROFILER_CONFIG=
export TARGET_PROFILER_CONFIG="${profiler_config}"
export TUNED_CONFIG_FOLDER=${case_root}/configs/moe-bm16-decode-only-01
export TRANSITION_ROLE=prof-004-p4k-post-op008-service-36
bash "${case_root}/commands/174-transition-prof003-preserve-qsa.sh" \
  prof-004-p4k-post-op008-service-36 "${source_manifest}"
