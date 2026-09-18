#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
profile_id=p4k-d128-c64-n64-current-stack-reprofile-20260917-08
service_dir="${case_root}/logs/${profile_id}-service"
profile_root="${case_root}/profiling/${profile_id}"
trace_dir="${profile_root}/traces"
result_dir="${case_root}/results/profiling/${profile_id}"
recovery="${result_dir}/stop-profile-recovery.txt"

test -d "${trace_dir}"
test -f "${service_dir}/api.pid"
test ! -e "${recovery}"

api_pid="$(cat "${service_dir}/api.pid")"
test -r "/proc/${api_pid}/cmdline"
tr '\0' ' ' <"/proc/${api_pid}/cmdline" | grep -F -- "--profiler-config" >/dev/null
tr '\0' ' ' <"/proc/${api_pid}/cmdline" | grep -F -- "${profile_id}" >/dev/null

{
  printf 'reason=stop_profile_shared_memory_return_stalled_after_all_rank_traces_exported\n'
  printf 'recovery_started_at=%s\n' "$(date --iso-8601=seconds)"
  printf 'api_pid=%s\n' "${api_pid}"
  pgrep -af 'vllm_profile.py|vllm bench serve|^VLLM::(EngineCore|Worker)' || true
} >"${recovery}"

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
test "${service_pids[0]}" = "${api_pid}"
declare -A service_start_times
for pid in "${service_pids[@]}"; do
  test -r "/proc/${pid}/stat"
  service_start_times["${pid}"]="$(awk '{print $22}' "/proc/${pid}/stat")"
done
printf 'service_pids=%s\n' "${service_pids[*]}" >>"${recovery}"

mapfile -t client_pids < <(
  pgrep -f 'vllm_profile.py.*p4k-d128-c64-n64-current-stack-reprofile-20260917-08|vllm bench serve.*p4k-d128-c64-n64-current-stack-reprofile-20260917-08' || true
)
for pid in "${client_pids[@]}"; do
  test "${pid}" = "$$" && continue
  kill -TERM "${pid}" 2>/dev/null || true
done

kill -TERM "${api_pid}"
for _attempt in $(seq 1 240); do
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
    printf 'service_term_timeout_pid=%s\n' "${pid}" >>"${recovery}"
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

find "${trace_dir}" -maxdepth 1 -type f -name '*.json.gz' -printf '%P %s %T@\n' \
  | sort >"${profile_root}/trace-inventory-recovery-1.txt"
sleep 10
find "${trace_dir}" -maxdepth 1 -type f -name '*.json.gz' -printf '%P %s %T@\n' \
  | sort >"${profile_root}/trace-inventory-recovery-2.txt"
cmp "${profile_root}/trace-inventory-recovery-1.txt" "${profile_root}/trace-inventory-recovery-2.txt"
test "$(wc -l <"${profile_root}/trace-inventory-recovery-2.txt")" -eq 16
find "${trace_dir}" -maxdepth 1 -type f -name '*.json.gz' -print0 \
  | sort -z | xargs -0 gzip -t
find "${trace_dir}" -maxdepth 1 -type f -name '*.json.gz' -print0 \
  | sort -z | xargs -0 sha256sum >"${profile_root}/trace-inventory-recovery.sha256"

{
  printf 'recovery_completed_at=%s\n' "$(date --iso-8601=seconds)"
  printf 'trace_files=16\n'
  printf 'trace_export_stable=true\n'
  printf 'trace_gzip_valid=true\n'
  printf 'client_result_state=incomplete_stop_profile_response_missing\n'
  printf 'port_8010_released=true\n'
  printf 'workers_released=true\n'
} >>"${recovery}"
