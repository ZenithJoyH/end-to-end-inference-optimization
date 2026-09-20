#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
export SOURCE_MAX_NUM_SEQS=64
export TARGET_MAX_NUM_SEQS=64
export SOURCE_MAX_NUM_BATCHED_TOKENS=6144
export TARGET_MAX_NUM_BATCHED_TOKENS=4096
export SOURCE_PROFILER_CONFIG=
export TARGET_PROFILER_CONFIG=
export TUNED_CONFIG_FOLDER=${case_root}/configs/moe-bm16-decode-only-01
export TRANSITION_ROLE=p4k-maxbt6144-failed-restored4096-service-15

bash "${case_root}/commands/108-transition-scheduler-limits-preserve-moe-config.sh" \
  p4k-maxbt6144-failed-restored4096-service-15 \
  "${case_root}/transitions/p4k-maxbt4096-to6144-service-14/p4k-maxbt4096-to6144-service-14-raw.json"
