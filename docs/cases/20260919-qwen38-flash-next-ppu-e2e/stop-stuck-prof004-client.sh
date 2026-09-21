#!/usr/bin/env bash
set -euo pipefail

pid=1536202
expected_start_ticks=258897372
expected_cmdline_sha256=2006cf8b0351b7249fbbee38925229c9670f252bdf3af941b4c1b5af3f16906b
case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
evidence=${case_root}/profiling/prof-004-p4k-post-op008/client-stop-evidence.txt

test -r "/proc/${pid}/cmdline"
actual_start_ticks=$(awk '{print $22}' "/proc/${pid}/stat")
actual_cmdline_sha256=$(sha256sum "/proc/${pid}/cmdline" | awk '{print $1}')
test "${actual_start_ticks}" = "${expected_start_ticks}"
test "${actual_cmdline_sha256}" = "${expected_cmdline_sha256}"
args=$(tr '\0' ' ' < "/proc/${pid}/cmdline")
case "${args}" in *"/usr/local/bin/vllm bench serve"*) ;; *) exit 1 ;; esac
case "${args}" in *"--port 8030"*) ;; *) exit 1 ;; esac
case "${args}" in *"--profile"*) ;; *) exit 1 ;; esac
case "${args}" in *"prof-004-p4k-post-op008"*) ;; *) exit 1 ;; esac

{
  date --iso-8601=seconds
  echo "pid=${pid}"
  echo "start_ticks=${actual_start_ticks}"
  echo "cmdline_sha256=${actual_cmdline_sha256}"
  echo "argv=${args}"
  echo "reason=all nine gzip-valid traces completed and service is idle; client remained blocked in stop_profile"
} > "${evidence}"

kill -TERM "${pid}"
for _ in $(seq 1 30); do
  test ! -e "/proc/${pid}" && break
  sleep 1
done
test ! -e "/proc/${pid}"
echo "stopped_pid=${pid}"
