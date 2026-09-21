#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
trace_dir=${case_root}/profiling/prof-004-p4k-post-op008/traces
source_manifest=${case_root}/transitions/prof-004-p4k-post-op008-service-36/prof-004-p4k-post-op008-service-36-raw.json
profiler_config=$(printf '{"profiler":"torch","torch_profiler_dir":"%s","torch_profiler_with_stack":false,"torch_profiler_record_shapes":true}' "${trace_dir}")
test -f "${source_manifest}"
export SOURCE_MAX_NUM_SEQS=64 TARGET_MAX_NUM_SEQS=64
export SOURCE_MAX_NUM_BATCHED_TOKENS=4096 TARGET_MAX_NUM_BATCHED_TOKENS=4096
export SOURCE_PROFILER_CONFIG="${profiler_config}"
export TARGET_PROFILER_CONFIG=
export TUNED_CONFIG_FOLDER=${case_root}/configs/moe-bm16-decode-only-01
export TRANSITION_ROLE=post-prof-004-restored-op008-service-37
bash "${case_root}/commands/174-transition-prof003-preserve-qsa.sh" \
  post-prof-004-restored-op008-service-37 "${source_manifest}"
