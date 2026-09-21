#!/usr/bin/env bash
set -euo pipefail

phase=${1:?usage: run-op022-qsa-r4-complete-consumer-timing.sh prefill|mixed EXPECTED_SCRIPT_SHA256}
expected_script_sha=${2:?missing EXPECTED_SCRIPT_SHA256}

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
script=${case_root}/commands/op022/op022-qsa-r4-complete-consumer-timing.py
op020_module=${case_root}/commands/op020/op020-qsa-producer-integrated-r4-rows4096-diag-v2.py
op019_module=${case_root}/commands/op019/op019-qsa-r4-direct-membership-microbench-boundary-fix-v3.py
qsa_path=/workspace/FlagGems/src/flag_gems/fused/qsa.py
expected_op020_sha=13bf633180074fb578bc99897ab645b922fc5e63efccb0ae585417b78aa08fd5
expected_op019_sha=7a2dd94e2918a2cf88be803235a62d9362d9a71bb6da13a49cc9d0dd7fc36acc
expected_qsa_sha=e18fbb229d9c4a5c2b06a6858ae4679596e1a6f971a4ff8878acbbc4f469db23

case "${phase}" in
  prefill)
    fixture=${case_root}/profiling/op021-qsa-producer-prefill-005/op021-p4k-prefill-producer-001
    expected_manifest_sha=e9765fa23ae19d487c9c7773c3f0b5ea65e5870012eb6ab4cacf7be9efcaeabd
    ;;
  mixed)
    fixture=${case_root}/profiling/op021-qsa-producer-mixed-001/op021-p4k-mixed-producer-001
    expected_manifest_sha=4d066545ab78ea30d340ce9a76db0325dfd4acee15b14c46fd719790779a037e
    ;;
  *) echo "phase must be prefill or mixed" >&2; exit 2 ;;
esac

if ! [[ "${expected_script_sha}" =~ ^[0-9a-f]{64}$ ]]; then
  echo "EXPECTED_SCRIPT_SHA256 must be 64 lowercase hex characters" >&2
  exit 2
fi

check_sha() {
  expected=$1
  path=$2
  test -f "${path}"
  actual=$(sha256sum "${path}" | awk '{print $1}')
  test "${actual}" = "${expected}" || {
    echo "SHA256 mismatch: ${path}: expected=${expected} actual=${actual}" >&2
    exit 1
  }
}

check_container_qsa_sha() {
  docker exec -i "${container}" python3 - "${qsa_path}" "${expected_qsa_sha}" <<'PY'
import hashlib
import sys

path, expected = sys.argv[1:]
actual = hashlib.sha256(open(path, "rb").read()).hexdigest()
print(actual)
raise SystemExit(0 if actual == expected else 1)
PY
}

check_sha "${expected_script_sha}" "${script}"
check_sha "${expected_op020_sha}" "${op020_module}"
check_sha "${expected_op019_sha}" "${op019_module}"
check_sha "${expected_manifest_sha}" "${fixture}/manifest.json"
(cd "${fixture}" && sha256sum --quiet -c SHA256SUMS)
check_container_qsa_sha >/dev/null

stamp=$(date -u +%Y%m%dT%H%M%SZ)
run_id=op022-qsa-r4-complete-consumer-timing-${phase}-${stamp}-$$
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
        argv = [x.decode(errors="replace") for x in open(f"/proc/{entry}/cmdline", "rb").read().split(b"\0") if x]
        env = dict(x.split(b"=", 1) for x in open(f"/proc/{entry}/environ", "rb").read().split(b"\0") if b"=" in x)
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
payload = {"label": label, "ppu": 0, "status": "busy" if busy else "free", "matching_processes": busy}
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
  free_rc=$?
  curl -fsS http://127.0.0.1:8030/health > "${result_root}/retained-health.after.json"
  health_rc=$?
  check_container_qsa_sha > "${result_root}/qsa-sha.after.txt"
  qsa_rc=$?
  if ((free_rc || health_rc || qsa_rc)); then status=1; fi
  if {
    echo "exit_status=${status}"
    echo "phase=${phase}"
    echo "run_id=${run_id}"
    echo "result_root=${result_root}"
    echo "ppu0_free_after_status=${free_rc}"
    echo "retained_health_after_status=${health_rc}"
    echo "qsa_sha_after_status=${qsa_rc}"
    if test -f "${result}"; then
      python3 - "${result}" "${phase}" "${expected_script_sha}" "${expected_op020_sha}" "${expected_op019_sha}" "${expected_manifest_sha}" "${status}" <<'PY'
import json
import sys

path, phase, script_sha, op020_sha, op019_sha, manifest_sha, shell_status = sys.argv[1:]
x = json.load(open(path, encoding="utf-8"))
assert x["experiment_id"] == "op-022-qsa-r4-complete-consumer-timing"
assert x["phase"] == phase
assert x["script_sha256"] == script_sha
if x["status"] == "passed":
    assert x["dependencies"]["op020_sha256"] == op020_sha
    assert x["dependencies"]["op019_boundary_fixed_sha256"] == op019_sha
    assert x["dependencies"]["imported_baseline_source_sha256"] == "e18fbb229d9c4a5c2b06a6858ae4679596e1a6f971a4ff8878acbbc4f469db23"
    assert x["fixture"]["manifest_sha256"] == manifest_sha
    assert x["timing"]["eager"]["samples"] in (7, 11)
    assert x["timing"]["graph"]["samples"] in (7, 11)
    assert x["four_way_gate"]["single_phase_cannot_promote"] is True
    print("op022_status=passed")
    print("phase_gate_passed=" + str(x["phase_gate_passed"]).lower())
else:
    assert x["status"] in ("blocked", "failed")
    print("op022_status=" + x["status"])
    print("error_type=" + x["error_type"])
    print("message=" + x["message"])
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
    "${script}" "${op020_module}" "${op019_module}" \
    "${fixture}/manifest.json" "${result}" "${console}" "${audit}" \
    "${result_root}/ppu0-process-state.before.json" \
    "${result_root}/ppu0-process-state.after.json" \
    "${result_root}/ppu-smi.before.txt" "${result_root}/ppu-smi.after.txt" \
    "${result_root}/retained-health.before.json" \
    "${result_root}/retained-health.after.json" \
    "${result_root}/qsa-sha.before.txt" "${result_root}/qsa-sha.after.txt"; do
    if test -f "${path}"; then sha256sum "${path}" >> "${checksums}"; fi
  done
  cat "${audit}"
  cat "${checksums}"
  exit "${status}"
}
trap finalize EXIT

ppu-smi > "${result_root}/ppu-smi.before.txt"
assert_ppu0_free before "${result_root}/ppu0-process-state.before.json"
curl -fsS http://127.0.0.1:8030/health > "${result_root}/retained-health.before.json"
check_container_qsa_sha > "${result_root}/qsa-sha.before.txt"

timeout --signal=TERM --kill-after=30s 1800s \
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
  --op020-module '${op020_module}' \
  --op019-module '${op019_module}' \
  --output '${result}'
" > "${console}" 2>&1

test -s "${result}"
