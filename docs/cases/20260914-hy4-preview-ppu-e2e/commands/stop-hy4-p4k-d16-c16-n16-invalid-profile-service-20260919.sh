#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
profile_id=p4k-d16-c16-n16-full-prefix-hit-profile-20260919-10
service_dir="${case_root}/logs/${profile_id}-service"
result_dir="${case_root}/results/profiling/${profile_id}"
stop_record="${service_dir}/stop-result.txt"

test -f "${service_dir}/api.pid"
test ! -e "${stop_record}"
api_pid="$(cat "${service_dir}/api.pid")"
test -r "/proc/${api_pid}/cmdline"
tr '\0' ' ' <"/proc/${api_pid}/cmdline" | grep -F -- "${profile_id}" >/dev/null
tr '\0' ' ' <"/proc/${api_pid}/cmdline" | grep -F -- "--profiler-config" >/dev/null

mapfile -t service_pids < <(
  python3 - "${api_pid}" <<'PY'
import pathlib
import sys

root = int(sys.argv[1])
children = {}
for entry in pathlib.Path("/proc").iterdir():
    if not entry.name.isdigit():
        continue
    try:
        fields = (entry / "stat").read_text().split()
        pid = int(fields[0])
        ppid = int(fields[3])
    except (FileNotFoundError, PermissionError, ValueError, IndexError):
        continue
    children.setdefault(ppid, []).append(pid)
stack = [root]
seen = set()
while stack:
    pid = stack.pop()
    if pid in seen:
        continue
    seen.add(pid)
    stack.extend(children.get(pid, ()))
for pid in sorted(seen):
    print(pid)
PY
)
declare -A service_start_times
for pid in "${service_pids[@]}"; do
  service_start_times["${pid}"]="$(awk '{print $22}' "/proc/${pid}/stat")"
done

printf 'reason=profiling_dry_run_rejected_runs_equal_warmups\nstopped_pid=%s\nstopped_at=%s\nservice_pids=%s\n' \
  "${api_pid}" "$(date --iso-8601=seconds)" "${service_pids[*]}" >"${stop_record}"
printf 'status=incomplete\nreason=invalid_measurement_contract_runs_equal_warmups\nrequests_sent=0\ntrace_files=0\n' \
  >"${result_dir}/trace-validity.txt"

kill -TERM "${api_pid}"
for _attempt in $(seq 1 120); do
  alive=0
  for pid in "${service_pids[@]}"; do
    if test -r "/proc/${pid}/stat" && \
       test "$(awk '{print $22}' "/proc/${pid}/stat")" = "${service_start_times[${pid}]}"; then
      alive=1
      break
    fi
  done
  test "${alive}" -eq 0 && break
  sleep 1
done
for pid in "${service_pids[@]}"; do
  if test -r "/proc/${pid}/stat" && \
     test "$(awk '{print $22}' "/proc/${pid}/stat")" = "${service_start_times[${pid}]}"; then
    printf 'service_term_timeout_pid=%s\n' "${pid}" >>"${stop_record}"
    kill -KILL "${pid}"
  fi
done
for _attempt in $(seq 1 60); do
  ss -ltn 'sport = :8010' | grep -q ':8010' || break
  sleep 1
done
if ss -ltn 'sport = :8010' | grep -q ':8010'; then
  echo 'port 8010 remains occupied' >&2
  exit 1
fi
printf 'released_at=%s\nport_8010_released=true\nworkers_released=true\n' \
  "$(date --iso-8601=seconds)" >>"${stop_record}"
