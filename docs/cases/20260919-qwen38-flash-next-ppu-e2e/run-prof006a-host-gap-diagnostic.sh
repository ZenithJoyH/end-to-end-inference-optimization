#!/usr/bin/env bash
set -euo pipefail

mode=${1:?usage: run-prof006a-host-gap-diagnostic.sh preflight|install|run|revert ARM RUN_ID}
arm=${2:-}
run_id=${3:-}
case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
plugin_root=${PROF006A_PLUGIN_ROOT:?set PROF006A_PLUGIN_ROOT to the private experiment copy}
port=${PROF006A_PORT:-8031}
expected_revision=939600b323c02c21916f1f76bfb4cd8c2b02578d
asset_root=${case_root}/commands/prof006a
probe_source=${asset_root}/prof006a_probe.py
patch_file=${asset_root}/prof006a-plugin.patch
probe_target=${plugin_root}/vllm_fl/prof006a.py
benchmark=${case_root}/commands/performance/vllm_profile.py

target_files=(
  vllm_fl/__init__.py
  vllm_fl/worker/worker.py
  vllm_fl/worker/model_runner.py
)
initial_shas=(
  2a7e903978b57aa8ff82a1e4c0785e2b1c8a51a2c7de8664ed8055b063516ff4
  a8de1780d1b41bf4889c26f3d593e6ec54e91a5f61996ce64b4d79f2a97efa24
  2df8aa58559ae7f9a3576ebcd234b42c864f5054fdff8897110dd60b26cb8bc0
)

case "${plugin_root}" in /opt/qwen38-prof006a-*) ;; *) echo "unsafe private Plugin path" >&2; exit 2 ;; esac
test "${port}" = 8031

container_cmd() {
  docker exec -i -e PYTHONDONTWRITEBYTECODE=1 "${container}" "$@"
}

assert_target_shas() {
  local index actual
  for index in "${!target_files[@]}"; do
    actual=$(container_cmd sha256sum "${plugin_root}/${target_files[$index]}" | awk '{print $1}')
    test "${actual}" = "${initial_shas[$index]}"
  done
}

preflight() {
  test "$(container_cmd git -C "${plugin_root}" rev-parse HEAD)" = "${expected_revision}"
  test -f "${probe_source}"
  test -f "${patch_file}"
  test -f "${benchmark}"
  container_cmd test ! -e "${probe_target}"
  assert_target_shas
  container_cmd git -C "${plugin_root}" diff --cached --quiet -- "${target_files[@]}"
  container_cmd git -C "${plugin_root}" apply --check "${patch_file}"
  container_cmd python3 -c 'from pathlib import Path; p=Path(__import__("sys").argv[1]); compile(p.read_text(),str(p),"exec")' "${probe_source}"
}

install_probe() {
  preflight
  container_cmd install -m 0644 "${probe_source}" "${probe_target}"
  container_cmd git -C "${plugin_root}" apply "${patch_file}"
  container_cmd python3 -c 'from pathlib import Path; p=Path(__import__("sys").argv[1]); compile(p.read_text(),str(p),"exec")' "${probe_target}"
  container_cmd git -C "${plugin_root}" diff --check -- "${target_files[@]}" "${probe_target}"
  container_cmd sha256sum "${probe_source}" "${probe_target}" "${patch_file}"
}

signal_registered() {
  local probe_dir=$1
  local signal_name=$2
  container_cmd python3 - "${probe_dir}" "${signal_name}" <<'PY'
import json
import os
import signal
import sys
from pathlib import Path

root = Path(sys.argv[1])
sig = getattr(signal, sys.argv[2])
registrations = sorted(root.glob("*.registration.json"))
records = [json.loads(path.read_text(encoding="utf-8")) for path in registrations]
roles = {row["role"] for row in records}
expected = {"engine", *(f"worker-rank{rank}" for rank in range(8))}
if roles != expected or len(records) != 9:
    raise SystemExit(f"registration coverage mismatch: {sorted(roles)}")
for row in records:
    pid = int(row["pid"])
    raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    ticks = int(raw[raw.rfind(")") + 2:].split()[19])
    if ticks != int(row["start_ticks"]):
        raise SystemExit(f"PID reuse/identity drift for {row['role']}")
for row in records:
    os.kill(int(row["pid"]), sig)
print(json.dumps({"signal": sys.argv[2], "roles": sorted(roles)}, sort_keys=True))
PY
}

run_arm() {
  case "${arm}" in event|event_host) ;; *) echo "invalid probe arm" >&2; return 2 ;; esac
  test -n "${run_id}"
  case "${run_id}" in *[!A-Za-z0-9._-]*|'') echo "invalid run id" >&2; return 2 ;; esac
  local run_root=${PROF006A_RUN_ROOT:-${case_root}/profiling/prof006a/${run_id}}
  case "${run_root}" in "${case_root}"/profiling/prof006a/*) ;; *) echo "unsafe run root" >&2; return 2 ;; esac
  local probe_dir=${run_root}/probe
  local client_root=${run_root}/client
  test -d "${probe_dir}"
  test ! -e "${client_root}"
  curl -fsS "http://127.0.0.1:${port}/health" >/dev/null
  container_cmd python3 - "${probe_dir}" "${arm}" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
records = [json.loads(path.read_text()) for path in root.glob("*.registration.json")]
if len(records) != 9 or any(row.get("arm") != sys.argv[2] for row in records):
    raise SystemExit("probe registration/arm mismatch")
PY

  mkdir "${client_root}"
  container_cmd python3 "${benchmark}" \
    --model Qwen3.8-Flash-Next \
    --tokenizer /mnt/cpfs/models/Qwen3.8-Flash-Next \
    --host 127.0.0.1 --port "${port}" --endpoint /v1/completions \
    --case 4096,128,64,64 --runs 1 --warmup-rounds 0 \
    --no-profile --seed 42 --timeout 1800 \
    --output-dir "${client_root}/warmup"

  signal_registered "${probe_dir}" SIGUSR1 > "${run_root}/activate.json"
  container_cmd python3 "${benchmark}" \
    --model Qwen3.8-Flash-Next \
    --tokenizer /mnt/cpfs/models/Qwen3.8-Flash-Next \
    --host 127.0.0.1 --port "${port}" --endpoint /v1/completions \
    --case 4096,128,64,64 --runs 3 --warmup-rounds 0 \
    --no-profile --seed 42 --timeout 1800 \
    --output-dir "${client_root}/measured"
  signal_registered "${probe_dir}" SIGUSR2 > "${run_root}/flush.json"
  container_cmd curl -fsS "http://127.0.0.1:${port}/v1/completions" \
    -H 'Content-Type: application/json' \
    -d '{"model":"Qwen3.8-Flash-Next","prompt":"flush-one","max_tokens":2,"temperature":0}' \
    > "${run_root}/flush-trigger-response-1.json"
  sleep 2
  container_cmd curl -fsS "http://127.0.0.1:${port}/v1/completions" \
    -H 'Content-Type: application/json' \
    -d '{"model":"Qwen3.8-Flash-Next","prompt":"flush-two","max_tokens":1,"temperature":0}' \
    > "${run_root}/flush-trigger-response-2.json"

  container_cmd python3 - "${probe_dir}" <<'PY'
import json, time, sys
from pathlib import Path
root = Path(sys.argv[1])
deadline = time.monotonic() + 120
while time.monotonic() < deadline:
    results = sorted(root.glob("*.result.json"))
    errors = sorted(root.glob("*.error.json"))
    if errors:
        raise SystemExit("probe export failed: " + ", ".join(str(x) for x in errors))
    if len(results) == 9:
        break
    time.sleep(0.25)
else:
    raise SystemExit("timed out waiting for nine probe result files")
for path in results:
    row = json.loads(path.read_text(encoding="utf-8"))
    if row.get("dropped") != 0:
        raise SystemExit(f"ring overflow in {path}")
print(json.dumps({"results": [str(x) for x in results]}, indent=2))
PY
  find "${client_root}/measured" -type f -name diagnostic.json -print | sort > "${run_root}/measured-diagnostic-path.txt"
  test "$(wc -l < "${run_root}/measured-diagnostic-path.txt")" -eq 1
  sha256sum "${probe_dir}"/*.json "${run_root}/activate.json" "${run_root}/flush.json" "${run_root}"/flush-trigger-response-*.json > "${run_root}/SHA256SUMS.probe"
}

revert_probe() {
  container_cmd test -f "${probe_target}"
  test "$(sha256sum "${probe_source}" | awk '{print $1}')" = \
       "$(container_cmd sha256sum "${probe_target}" | awk '{print $1}')"
  container_cmd git -C "${plugin_root}" apply -R --check "${patch_file}"
  container_cmd git -C "${plugin_root}" apply -R "${patch_file}"
  container_cmd rm "${probe_target}"
  assert_target_shas
}

case "${mode}" in
  preflight) preflight ;;
  install) install_probe ;;
  run) run_arm ;;
  revert) revert_probe ;;
  *) echo "invalid mode: ${mode}" >&2; exit 2 ;;
esac
