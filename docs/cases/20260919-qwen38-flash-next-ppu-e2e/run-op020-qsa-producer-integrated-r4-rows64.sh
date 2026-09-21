#!/usr/bin/env bash
set -euo pipefail

expected_script_sha=${1:?usage: run-op020-qsa-producer-integrated-r4-rows64.sh EXPECTED_SCRIPT_SHA256 EXPECTED_OP019_SHA256}
expected_op019_sha=${2:?usage: run-op020-qsa-producer-integrated-r4-rows64.sh EXPECTED_SCRIPT_SHA256 EXPECTED_OP019_SHA256}

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
script=${case_root}/commands/op020/op020-qsa-producer-integrated-r4-rows64.py
op019_module=${case_root}/commands/op019/op019-qsa-r4-direct-membership-microbench.py

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

# Integrity is checked before creating an artifact directory.  The runner does
# not upload files, alter source, or touch the retained service process.
check_sha "${expected_script_sha}" "${script}"
check_sha "${expected_op019_sha}" "${op019_module}"

stamp=$(date -u +%Y%m%dT%H%M%SZ)
run_id=op020-qsa-producer-integrated-r4-rows64-${stamp}-$$
result_root=${case_root}/microbench/${run_id}
result=${result_root}/result.json
snapshots=${result_root}/snapshots.pt
console=${result_root}/console.log
audit=${result_root}/audit.txt
checksums=${result_root}/SHA256SUMS

test ! -e "${result_root}"
mkdir -p "${result_root}"

finalize() {
  status=$?
  set +e
  ppu-smi > "${result_root}/ppu-smi.after.txt" 2>&1
  if {
    echo "exit_status=${status}"
    echo "run_id=${run_id}"
    echo "result_root=${result_root}"
    echo "expected_script_sha256=${expected_script_sha}"
    echo "expected_op019_sha256=${expected_op019_sha}"
    if test -f "${result}"; then
      python3 - "${result}" "${expected_script_sha}" "${expected_op019_sha}" <<'PY'
import json
import sys

path, expected_script_sha, expected_op019_sha = sys.argv[1:]
payload = json.load(open(path, encoding="utf-8"))
assert payload["experiment_id"] == "op-020-qsa-producer-integrated-r4-rows64"
assert payload["script_sha256"] == expected_script_sha
if payload["status"] == "passed":
    assert payload["op019_module_sha256"] == expected_op019_sha
    assert payload["method"]["graph_capture_count"] == 1
    assert payload["method"]["graph_replay_order"] == ["A", "B", "A"]
    assert payload["method"]["two_graph_fallback_used"] is False
    assert payload["method"]["performance_measured"] is False
    assert payload["promotion_allowed"] is False
    print("single_graph_rows64_gate=passed")
    print("snapshots_sha256=" + payload["snapshots_sha256"])
else:
    assert payload["status"] == "blocked"
    print("single_graph_rows64_gate=blocked")
    print("blockers=" + json.dumps(payload["blockers"], ensure_ascii=False))
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
    "${result}" \
    "${snapshots}" \
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
python3 '${script}' \
  --op019-module '${op019_module}' \
  --output '${result}' \
  --snapshot-output '${snapshots}'
" > "${console}" 2>&1

test -s "${result}"
test -s "${snapshots}"
