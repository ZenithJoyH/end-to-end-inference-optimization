#!/usr/bin/env bash
set -euo pipefail

phase=${1:?usage: run-op020-qsa-producer-integrated-r4-rows4096.sh prefill|mixed EXPECTED_SCRIPT_SHA256 EXPECTED_OP019_SHA256}
expected_script_sha=${2:?missing EXPECTED_SCRIPT_SHA256}
expected_op019_sha=${3:?missing EXPECTED_OP019_SHA256}

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
script=${case_root}/commands/op020/op020-qsa-producer-integrated-r4-rows4096-diag-v2.py
op019_module=${case_root}/commands/op019/op019-qsa-r4-direct-membership-microbench-boundary-fix-v3.py

case "${phase}" in
  prefill)
    fixture=${case_root}/profiling/op021-qsa-producer-prefill-005/op021-p4k-prefill-producer-001
    expected_manifest_sha=e9765fa23ae19d487c9c7773c3f0b5ea65e5870012eb6ab4cacf7be9efcaeabd
    ;;
  mixed)
    fixture=${case_root}/profiling/op021-qsa-producer-mixed-001/op021-p4k-mixed-producer-001
    expected_manifest_sha=4d066545ab78ea30d340ce9a76db0325dfd4acee15b14c46fd719790779a037e
    ;;
  *)
    echo "phase must be prefill or mixed" >&2
    exit 2
    ;;
esac

for value in "${expected_script_sha}" "${expected_op019_sha}"; do
  if ! [[ "${value}" =~ ^[0-9a-f]{64}$ ]]; then
    echo "expected SHA256 values must be 64 lowercase hex characters" >&2
    exit 2
  fi
done

check_sha() {
  expected=$1
  path=$2
  test -f "${path}"
  actual=$(sha256sum "${path}" | awk '{print $1}')
  if test "${actual}" != "${expected}"; then
    echo "SHA256 mismatch: ${path}: expected=${expected} actual=${actual}" >&2
    exit 1
  fi
}

check_sha "${expected_script_sha}" "${script}"
check_sha "${expected_op019_sha}" "${op019_module}"
check_sha "${expected_manifest_sha}" "${fixture}/manifest.json"
(cd "${fixture}" && sha256sum --quiet -c SHA256SUMS)

stamp=$(date -u +%Y%m%dT%H%M%SZ)
run_id=op020-qsa-producer-integrated-r4-rows4096-${phase}-${stamp}-$$
result_root=${case_root}/microbench/${run_id}
result=${result_root}/result.json
console=${result_root}/console.log
audit=${result_root}/audit.txt
checksums=${result_root}/SHA256SUMS

test ! -e "${result_root}"
mkdir -p "${result_root}"

assert_ppu0_free() {
  label=$1
  output=$2
  python3 - "${label}" "${output}" <<'PY'
import json
import os
import sys

label, output = sys.argv[1:]
busy = []
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        argv = [
            item.decode(errors="replace")
            for item in open(f"/proc/{entry}/cmdline", "rb").read().split(b"\0")
            if item
        ]
        env = dict(
            item.split(b"=", 1)
            for item in open(f"/proc/{entry}/environ", "rb").read().split(b"\0")
            if b"=" in item
        )
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    command = " ".join(argv).lower()
    if not any(name in command for name in ("vllm", "enginecore", "worker")):
        continue
    visible = env.get(b"CUDA_VISIBLE_DEVICES", b"").decode(errors="replace")
    try:
        cards = {int(item) for item in visible.split(",") if item}
    except ValueError:
        continue
    if 0 in cards:
        busy.append({"pid": int(entry), "visible": visible, "argv": argv})
payload = {
    "label": label,
    "ppu": 0,
    "status": "busy" if busy else "free",
    "matching_processes": busy,
}
with open(output, "x", encoding="utf-8") as stream:
    json.dump(payload, stream, indent=2, sort_keys=True)
    stream.write("\n")
if busy:
    print(json.dumps(payload, indent=2), file=sys.stderr)
    raise SystemExit("PPU0 is assigned to a vLLM/EngineCore/Worker process")
PY
}

finalize() {
  status=$?
  set +e
  ppu-smi > "${result_root}/ppu-smi.after.txt" 2>&1
  assert_ppu0_free after "${result_root}/ppu0-process-state.after.json"
  ppu0_after_status=$?
  if test "${ppu0_after_status}" -ne 0; then status=1; fi
  if {
    echo "exit_status=${status}"
    echo "phase=${phase}"
    echo "run_id=${run_id}"
    echo "result_root=${result_root}"
    if test -f "${result}"; then
      python3 - "${result}" "${phase}" "${expected_script_sha}" "${expected_op019_sha}" "${expected_manifest_sha}" "${status}" <<'PY'
import json
import sys

path, phase, script_sha, op019_sha, manifest_sha, shell_status = sys.argv[1:]
payload = json.load(open(path, encoding="utf-8"))
assert payload["experiment_id"] == "op-020-qsa-producer-integrated-r4-rows4096"
assert payload["phase"] == phase
assert payload["script_sha256"] == script_sha
if payload["status"] == "passed":
    assert payload["op019_module_sha256"] == op019_sha
    assert payload["fixture"]["manifest_sha256"] == manifest_sha
    assert payload["method"]["graph_capture_count"] == 1
    assert payload["method"]["graph_replay_order"] == ["A", "B", "A"]
    assert payload["method"]["external_input_writes_between_replays"] is False
    assert payload["method"]["performance_measured"] is False
    assert payload["shape_similarity"]["status"] == "passed"
    assert payload["promotion_allowed"] is False
    print("rows4096_consumer_correctness=passed")
elif payload["status"] == "blocked":
    print("rows4096_consumer_correctness=blocked")
    print("blockers=" + json.dumps(payload["blockers"], ensure_ascii=False))
    print("error_type=" + payload["error_type"])
    print("message=" + payload["message"])
    if int(shell_status) == 0:
        raise SystemExit(7)
else:
    assert payload["status"] == "failed"
    print("rows4096_consumer_correctness=failed")
    print("error_type=" + payload["error_type"])
    print("message=" + payload["message"])
    if int(shell_status) == 0:
        raise SystemExit(7)
PY
    else
      echo "result_json=missing"
    fi
  } > "${audit}" 2>&1; then
    :
  else
    status=1
  fi
  : > "${checksums}"
  for path in \
    "${script}" \
    "${op019_module}" \
    "${fixture}/manifest.json" \
    "${result}" \
    "${console}" \
    "${audit}" \
    "${result_root}/ppu0-process-state.before.json" \
    "${result_root}/ppu0-process-state.after.json" \
    "${result_root}/ppu-smi.before.txt" \
    "${result_root}/ppu-smi.after.txt"; do
    if test -f "${path}"; then
      sha256sum "${path}" >> "${checksums}"
    fi
  done
  cat "${audit}"
  cat "${checksums}"
  exit "${status}"
}
trap finalize EXIT

ppu-smi > "${result_root}/ppu-smi.before.txt"
assert_ppu0_free before "${result_root}/ppu0-process-state.before.json"

docker exec \
  -e CUDA_VISIBLE_DEVICES=0 \
  -w "${case_root}" \
  "${container}" \
  bash -lc "
set -e
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:\${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}
python3 '${script}' \
  --phase '${phase}' \
  --fixture '${fixture}' \
  --op019-module '${op019_module}' \
  --output '${result}'
" > "${console}" 2>&1

test -s "${result}"
