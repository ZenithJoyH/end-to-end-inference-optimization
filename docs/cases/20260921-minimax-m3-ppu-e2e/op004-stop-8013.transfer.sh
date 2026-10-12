#!/usr/bin/env bash
set -euo pipefail

# One-time, exact-identity stop for the user-approved 8013 instance.
container=minimaxM3-opt-20260921
pid=1017803
expected_start_ticks=285091266
expected_log=/mnt/nfs/users/jinghao/minimaxM3/server.log

docker inspect -f '{{.State.Running}}' "$container" | grep -qx true
cmdline=$(docker exec "$container" sh -lc "tr '\000' ' ' </proc/$pid/cmdline")
start_ticks=$(docker exec "$container" sh -lc "awk '{print \$22}' /proc/$pid/stat")
stdout_path=$(docker exec "$container" sh -lc "readlink /proc/$pid/fd/1")

[[ "$cmdline" == *'/usr/local/bin/vllm serve /mnt/cpfs/models/MiniMax-M3'* ]]
[[ "$cmdline" == *' --port 8013 '* ]]
[[ "$cmdline" == *' --served-model-name MiniMax-M3-opt '* ]]
[[ "$cmdline" == *' --tensor-parallel-size 16 '* ]]
[[ "$start_ticks" == "$expected_start_ticks" ]]
[[ "$stdout_path" == "$expected_log" ]]

printf 'Stopping exact instance: container=%s pid=%s start_ticks=%s log=%s\n' \
  "$container" "$pid" "$start_ticks" "$stdout_path"
docker exec "$container" sh -lc "kill -TERM $pid"

for attempt in $(seq 1 15); do
  if ! docker exec "$container" sh -lc "test -e /proc/$pid"; then
    printf 'Target process exited after attempt %s\n' "$attempt"
    exit 0
  fi
  sleep 2
done

printf 'Target process did not exit within 30 seconds; no forced kill attempted\n' >&2
exit 1
