#!/usr/bin/env bash
set -euo pipefail

pid=1514737
expected_start_ticks=258891048
expected_cmdline_sha256=2f2d2866796afc1a4a1630d88c18bd150cac3b0f2f39b85d30f4c0d53dcb5702
case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
evidence=${case_root}/profiling/prof-004-p4k-post-op008/orchestrator-stop-evidence.txt

test -r "/proc/${pid}/cmdline"
actual_start_ticks=$(awk '{print $22}' "/proc/${pid}/stat")
actual_cmdline_sha256=$(sha256sum "/proc/${pid}/cmdline" | awk '{print $1}')
test "${actual_start_ticks}" = "${expected_start_ticks}"
test "${actual_cmdline_sha256}" = "${expected_cmdline_sha256}"
args=$(tr '\0' ' ' < "/proc/${pid}/cmdline")
case "${args}" in *"commands/performance/vllm_profile.py"*) ;; *) exit 1 ;; esac
case "${args}" in *"--case 4096,128,64,64"*) ;; *) exit 1 ;; esac
case "${args}" in *"prof-004-p4k-post-op008"*) ;; *) exit 1 ;; esac

{
  date --iso-8601=seconds
  echo "pid=${pid}"
  echo "start_ticks=${actual_start_ticks}"
  echo "cmdline_sha256=${actual_cmdline_sha256}"
  echo "argv=${args}"
  echo "reason=both benchmark rounds and nine gzip-valid traces completed; outer vllm_profile remained blocked after child exit"
} > "${evidence}"

kill -TERM "${pid}"
for _ in $(seq 1 30); do
  test ! -e "/proc/${pid}" && break
  sleep 1
done
test ! -e "/proc/${pid}"
echo "stopped_pid=${pid}"
