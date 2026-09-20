#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
profile_root=${case_root}/profiling/prof-002-p4k-bt4096-mixed-tail
trace_dir=${profile_root}/traces
test ! -e "${profile_root}"
mkdir -p "${trace_dir}"
profiler_config=$(printf '{"profiler":"torch","torch_profiler_dir":"%s","torch_profiler_with_stack":true,"torch_profiler_record_shapes":true}' "${trace_dir}")

export SOURCE_MAX_NUM_SEQS=64
export TARGET_MAX_NUM_SEQS=64
export SOURCE_MAX_NUM_BATCHED_TOKENS=4096
export TARGET_MAX_NUM_BATCHED_TOKENS=4096
export SOURCE_PROFILER_CONFIG=
export TARGET_PROFILER_CONFIG="${profiler_config}"
export TUNED_CONFIG_FOLDER=${case_root}/configs/moe-bm16-decode-only-01
export TRANSITION_ROLE=prof-002-p4k-bt4096-service-16

bash "${case_root}/commands/108-transition-scheduler-limits-preserve-moe-config.sh" \
  prof-002-p4k-bt4096-service-16 \
  "${case_root}/transitions/p4k-maxbt6144-failed-restored4096-service-15/p4k-maxbt6144-failed-restored4096-service-15-raw.json"
