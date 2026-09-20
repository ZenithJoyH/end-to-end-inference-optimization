#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
export SOURCE_MAX_NUM_SEQS=64
export TARGET_MAX_NUM_SEQS=64
export SOURCE_MAX_NUM_BATCHED_TOKENS=8192
export TARGET_MAX_NUM_BATCHED_TOKENS=4096
export SOURCE_PROFILER_CONFIG=
export TARGET_PROFILER_CONFIG=
export TUNED_CONFIG_FOLDER=${case_root}/configs/moe-bm16-decode-only-01
export TRANSITION_ROLE=p4k-maxbt8192-failed-restored4096-service-13

bash "${case_root}/commands/106-transition-scheduler-limits-preserve-moe-config.sh" \
  p4k-maxbt8192-failed-restored4096-service-13 \
  "${case_root}/manifests/candidate-maxseq64-bt8192-moe-bm16-service-screen-12.json"
