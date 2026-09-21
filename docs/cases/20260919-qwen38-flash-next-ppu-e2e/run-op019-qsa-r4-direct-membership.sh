#!/usr/bin/env bash
set -euo pipefail

phase=${1:?usage: run-op019-qsa-r4-direct-membership.sh smoke|full EXPECTED_SCRIPT_SHA256}
expected_script_sha=${2:?usage: run-op019-qsa-r4-direct-membership.sh smoke|full EXPECTED_SCRIPT_SHA256}

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
script=${case_root}/commands/op019/op019-qsa-r4-direct-membership-microbench.py
prefill_fixture=${case_root}/profiling/op019-qsa-exact-prefill-001/op019-p4k-prefill-fixture-001
mixed_fixture=${case_root}/profiling/op019-qsa-exact-mixed-001/op019-p4k-mixed-fixture-001

prefill_manifest_sha=480def84c7d2c17cb86fac9e2e340caa28806f89cd3bfe05ca7885e0378daf64
prefill_selected_sha=3a0d49fd904d074afde80c007027259cd1ee7a1dafc001fe15baf939c19ba4ed
mixed_manifest_sha=07fb120403a6af733417feb9db48af7fca8d0869b2ec18cbb1e9698c70455dd6
mixed_selected_sha=f99873bc244fad551ef1d25be3f07ced896c717bcbaa28e9b82e7b2660cdaac5

case "${phase}" in
  smoke)
    scope=first
    repeat_4096=1
    repeat_64=1
    minimum_samples=3
    maximum_samples=3
    ;;
  full)
    scope=full
    repeat_4096=5
    repeat_64=20
    minimum_samples=7
    maximum_samples=11
    ;;
  *)
    echo "unknown phase: ${phase}" >&2
    exit 2
    ;;
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
  if test "${actual}" != "${expected}"; then
    echo "SHA256 mismatch: ${path}: expected=${expected} actual=${actual}" >&2
    exit 1
  fi
}

# Integrity is a hard preflight: no result directory is created until the
# uploaded script and every frozen fixture file have passed SHA validation.
check_sha "${expected_script_sha}" "${script}"
check_sha "${prefill_manifest_sha}" "${prefill_fixture}/manifest.json"
check_sha "${prefill_selected_sha}" "${prefill_fixture}/selected.int32.bin"
check_sha "${mixed_manifest_sha}" "${mixed_fixture}/manifest.json"
check_sha "${mixed_selected_sha}" "${mixed_fixture}/selected.int32.bin"
(cd "${prefill_fixture}" && sha256sum --quiet -c SHA256SUMS)
(cd "${mixed_fixture}" && sha256sum --quiet -c SHA256SUMS)

stamp=$(date -u +%Y%m%dT%H%M%SZ)
run_id=op019-qsa-r4-direct-membership-${phase}-${stamp}-$$
result_root=${case_root}/microbench/${run_id}
result=${result_root}/result.json
console=${result_root}/console.log
checksums=${result_root}/SHA256SUMS
audit=${result_root}/audit.txt

test ! -e "${result_root}"
mkdir -p "${result_root}"

finalize() {
  status=$?
  set +e
  ppu-smi > "${result_root}/ppu-smi.after.txt" 2>&1
  if {
    echo "exit_status=${status}"
    echo "phase=${phase}"
    echo "scope=${scope}"
    echo "run_id=${run_id}"
    echo "result_root=${result_root}"
    echo "expected_script_sha256=${expected_script_sha}"
    if test -f "${result}"; then
      python3 - "${result}" "${scope}" "${expected_script_sha}" <<'PY'
import json
import sys

path, expected_scope, expected_script_sha = sys.argv[1:]
payload = json.load(open(path, encoding="utf-8"))
assert payload["experiment_id"] == "op-019-qsa-r4-direct-membership"
assert payload["scope"] == expected_scope
assert payload["script_sha256"] == expected_script_sha
assert payload["full_correctness_gate_complete"] is (expected_scope == "full")
print(f"primary_gate_passed={payload['primary_gate_passed']}")
print(f"rows64_guard_passed={payload['rows64_guard_passed']}")
print(f"promotion_allowed={payload['promotion_allowed']}")
for item in payload["results"]:
    eager = item.get("eager_timing")
    graph = item.get("graph_timing")
    fields = [item["phase"], str(item["rows"]), item["mode"]]
    if eager is not None:
        fields.append(f"eager_gain_pct={eager['gain_pct']:.6f}")
    if graph is not None:
        fields.append(f"graph_gain_pct={graph['gain_pct']:.6f}")
    print("case=" + ",".join(fields))
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
    "${result}" \
    "${console}" \
    "${audit}" \
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

docker exec \
  -e CUDA_VISIBLE_DEVICES=0 \
  -w "${case_root}" \
  "${container}" \
  bash -lc "
set -e
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:\${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}
python3 '${script}' \\
  --prefill-fixture '${prefill_fixture}' \\
  --mixed-fixture '${mixed_fixture}' \\
  --scope '${scope}' \\
  --repeat-4096 '${repeat_4096}' \\
  --repeat-64 '${repeat_64}' \\
  --minimum-samples '${minimum_samples}' \\
  --maximum-samples '${maximum_samples}' \\
  --output '${result}'
" > "${console}" 2>&1

test -s "${result}"
