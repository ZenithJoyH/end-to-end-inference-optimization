#!/usr/bin/env bash
# Draft only. Copy this file and the frozen dependencies listed below to the
# remote case commands/performance directory before review and execution.
# This local artifact has not been executed against PPU-01.
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
image_id=sha256:d87b7b26da3623b18863d47fa623135d0dfc3ba3288293be18aa6f928cb9bbe6
port=8030
max_num_seqs=64
control_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

plan=${control_dir}/perf-p4k-mixed-entry-plan.json
contract=${control_dir}/perf-p4k-d1024-mm-native-comparison.json
runner=${control_dir}/vllm_perf.py
comparator=${control_dir}/compare_performance.py
verifier=${control_dir}/verify-live-service-manifest.py
normalizer=${control_dir}/normalize-mm-provider-service-manifest.py
transition=${control_dir}/transition-moe-drain-bm16-service.sh
graph_smoke=${control_dir}/run-graph-replay-smoke.sh

expected_plan_sha=da18d8b1eb558d098bcf2855b73a3102b28aecdacc4ad5bf6589170f664cb3ec
expected_contract_sha=207089003f68945b03d0261e5064d440bddc0f30e75b033bb352c7a12ecb2ee3
expected_normalizer_sha=c9507cca4d37793fcf872cad70b738241549c0bd3211bde3275cac9e5ba4c2aa
expected_transition_sha=09f75105bc6b4134cb14f85f95510b62f4e8b486648f50088cc2fd967b71fffd
expected_graph_smoke_sha=61671cb1f72838a90334923a8f8aa1a33aee86d5d77e6bbe8ec206745eef75a7

tuned_config=${case_root}/configs/moe-bm16-decode-only-01
normal_blacklist=_conv_depthwise2d,index,normal_
native_blacklist=_conv_depthwise2d,index,normal_,mm,mm_out

candidate_transition=${case_root}/transitions/mm-native-contract-retained-service-46
candidate_raw=${candidate_transition}/mm-native-contract-retained-service-46-raw.json
candidate_process=${candidate_transition}/after-process.json
candidate_graph=${candidate_transition}/graph-replay-smoke.json
candidate_manifest=${case_root}/manifests/mm-native-d1024-candidate-service46.json
candidate_run_id=p4k-d1024-mm-native-contract-candidate-01
candidate_record=${case_root}/performance/${candidate_run_id}/run-record.json
expected_candidate_instance=9b65cc77d73c-8030-2636577-259878814

normal_transition_id=mm-native-d1024-normal-service-47
normal_transition=${case_root}/transitions/${normal_transition_id}
normal_raw=${normal_transition}/${normal_transition_id}-raw.json
normal_process=${normal_transition}/after-process.json
normal_manifest=${case_root}/manifests/mm-native-d1024-baseline-revert-service47.json
normal_graph_label=op010-p4k-d1024-normal-service47-graph-01
normal_graph_dir=${case_root}/smoke/${normal_graph_label}

baseline_run_id=p4k-d1024-mm-normal-baseline-service47-01
revert_run_id=p4k-d1024-mm-normal-revert-service47-01
baseline_record=${case_root}/performance/${baseline_run_id}/run-record.json
revert_record=${case_root}/performance/${revert_run_id}/run-record.json

restore_transition_id=mm-native-d1024-native-restore-service-48
restore_transition=${case_root}/transitions/${restore_transition_id}
restore_raw=${restore_transition}/${restore_transition_id}-raw.json
restore_process=${restore_transition}/after-process.json
restore_manifest=${case_root}/manifests/mm-native-d1024-native-restore-service48.json
restore_graph_label=op010-p4k-d1024-native-service48-graph-01
restore_graph_dir=${case_root}/smoke/${restore_graph_label}

comparison_result=${case_root}/performance/op010-p4k-d1024-sequential-abr-service46-47.json
audit_id=op010-p4k-d1024-sequential-abr-control-01
audit_dir=${case_root}/transitions/${audit_id}

sha256_of() {
  sha256sum "$1" | awk '{print $1}'
}

require_sha() {
  local path=$1
  local expected=$2
  test -f "${path}"
  test "$(sha256_of "${path}")" = "${expected}"
}

assert_unused_path() {
  test ! -e "$1" || {
    echo "refusing to overwrite existing path: $1" >&2
    exit 2
  }
}

assert_live_service() {
  local manifest=$1
  local process=$2
  local expected_instance=$3
  local expected_blacklist=$4
  docker exec -i "${container}" python3 - \
    "${manifest}" "${process}" "${expected_instance}" "${expected_blacklist}" <<'PY'
import json
import os
import sys

manifest_path, process_path, expected_instance, expected_blacklist = sys.argv[1:]
manifest = json.load(open(manifest_path, encoding="utf-8"))
expected = json.load(open(process_path, encoding="utf-8"))
pid = int(expected["pid"])

raw = open(f"/proc/{pid}/stat", encoding="utf-8").read()
tail = raw[raw.rfind(")") + 2:].split()
start_ticks = int(tail[19])
argv = [item.decode(errors="replace") for item in open(
    f"/proc/{pid}/cmdline", "rb").read().split(b"\0") if item]
if start_ticks != int(expected["start_ticks"]) or argv != expected["args"]:
    raise SystemExit("live PID/start-ticks/argv differs from frozen process evidence")
container_id = "9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4"
instance = f"{container_id[:12]}-8030-{pid}-{start_ticks}"
if instance != expected_instance or manifest.get("service_instance_id") != instance:
    raise SystemExit("service manifest does not identify the exact live PID")
environment = {}
for item in open(f"/proc/{pid}/environ", "rb").read().split(b"\0"):
    if b"=" in item:
        key, value = item.split(b"=", 1)
        environment[key.decode(errors="replace")] = value.decode(errors="replace")
if environment.get("VLLM_FL_FLAGOS_BLACKLIST_APPEND") != expected_blacklist:
    raise SystemExit("live provider blacklist differs from expected role")
if environment.get("VLLM_FL_QSA_STATIC_SCORE_COLUMNS") != "8448":
    raise SystemExit("QSA bound drift")
if environment.get("VLLM_TUNED_CONFIG_FOLDER") != (
    "/mnt/nfs/users/jinghao/qwen3.8-flash/"
    "20260919-qwen38-flash-next-ppu-e2e/configs/moe-bm16-decode-only-01"
):
    raise SystemExit("MoE tuned config drift")
print(instance)
PY
}

run_role() {
  local role=$1
  local run_id=$2
  local manifest=$3
  local dry_run=${case_root}/performance/${run_id}.dry-run.json
  local console=${case_root}/performance/${run_id}.console.log
  assert_unused_path "${case_root}/performance/${run_id}"
  assert_unused_path "${dry_run}"
  assert_unused_path "${console}"
  docker exec "${container}" python3 "${runner}" \
    --config "${plan}" --comparison-contract "${contract}" \
    --service-manifest "${manifest}" --role "${role}" \
    --run-id "${run_id}" --scope performance_only \
    --output-dir "${case_root}/performance" --dry-run > "${dry_run}"
  docker exec "${container}" python3 "${runner}" \
    --config "${plan}" --comparison-contract "${contract}" \
    --service-manifest "${manifest}" --role "${role}" \
    --run-id "${run_id}" --scope performance_only \
    --output-dir "${case_root}/performance" 2>&1 | tee "${console}"
}

restore_needed=0
restore_attempted=0
restore_live=0

restore_native() {
  restore_attempted=1
  assert_unused_path "${restore_transition}" || return $?
  assert_unused_path "${restore_manifest}" || return $?
  assert_unused_path "${restore_graph_dir}" || return $?
  env \
    SOURCE_MANIFEST="${normal_raw}" \
    SOURCE_PROCESS="${normal_process}" \
    SOURCE_CONFIG="${tuned_config}" \
    TARGET_CONFIG="${tuned_config}" \
    SOURCE_BLACKLIST="${normal_blacklist}" \
    TARGET_BLACKLIST="${native_blacklist}" \
    RUN_ID="${restore_transition_id}" \
    bash "${transition}" || return $?
  restore_live=1
  python3 "${normalizer}" "${restore_raw}" "${restore_manifest}" "${native_blacklist}" || return $?
  python3 "${verifier}" "${restore_manifest}" "${container}" "${port}" "${max_num_seqs}" || return $?
  bash "${graph_smoke}" \
    "${restore_graph_label}" "${restore_manifest}" "${max_num_seqs}" \
    "${normal_graph_dir}/canonical.json" "${container}" "${port}" || return $?
}

on_exit() {
  local rc=$?
  trap - EXIT
  if test "${restore_needed}" -eq 1 && test "${restore_attempted}" -eq 0; then
    echo "attempting native service48 restore after earlier failure" >&2
    if ! restore_native; then
      echo "AUTOMATIC RESTORE FAILED; preserve all evidence and inspect exact live PID before signaling" >&2
      exit 4
    fi
  fi
  if test "${restore_needed}" -eq 1 && test "${restore_live}" -ne 1; then
    echo "native restore is not proven live" >&2
    exit 4
  fi
  exit "${rc}"
}
trap on_exit EXIT

# Frozen control-plane inputs.  vllm_perf and compare_performance are also
# required but intentionally not pinned here: the existing candidate run will
# make the maintained comparator reject any client/tool evidence drift.
require_sha "${plan}" "${expected_plan_sha}"
require_sha "${contract}" "${expected_contract_sha}"
require_sha "${normalizer}" "${expected_normalizer_sha}"
require_sha "${transition}" "${expected_transition_sha}"
require_sha "${graph_smoke}" "${expected_graph_smoke_sha}"
for path in "${runner}" "${comparator}" "${verifier}"; do test -f "${path}"; done

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${container_id}"
test "$(docker inspect --format '{{.Image}}' "${container}")" = "${image_id}"
test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true

for path in \
  "${candidate_raw}" "${candidate_process}" "${candidate_graph}" \
  "${candidate_manifest}" "${candidate_record}"; do
  test -f "${path}"
done
for path in \
  "${audit_dir}" "${normal_transition}" "${normal_manifest}" "${normal_graph_dir}" \
  "${case_root}/performance/${baseline_run_id}" \
  "${case_root}/performance/${revert_run_id}" \
  "${restore_transition}" "${restore_manifest}" "${restore_graph_dir}" \
  "${comparison_result}"; do
  assert_unused_path "${path}"
done

python3 - "${plan}" "${contract}" "${candidate_record}" "${candidate_graph}" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

plan = json.load(open(sys.argv[1], encoding="utf-8"))
contract = json.load(open(sys.argv[2], encoding="utf-8"))
candidate = json.load(open(sys.argv[3], encoding="utf-8"))
graph = json.load(open(sys.argv[4], encoding="utf-8"))
case = plan.get("cases")
if case != [{
    "id": "p4096-d1024-c64-n128", "input_tokens": 4096,
    "output_tokens": 1024, "concurrency": 64, "requests": 128,
    "load_mode": "finite_batch", "stage": "mixed",
    "request_rate": None, "burstiness": 1,
}]:
    raise SystemExit("plan is not exact P4096/D1024/C64/N128 Mixed")
measurement = plan.get("measurement", {})
if measurement.get("warmup_rounds") != 3 or measurement.get("measured_rounds") != 3:
    raise SystemExit("plan is not frozen at 3 warmup + 3 measured rounds")
needed = {
    contract["primary"]["metric"],
    *(item["metric"] for item in contract["guardrails"]),
}
if not needed.issubset(set(measurement.get("required_metrics", []))):
    raise SystemExit("plan required_metrics do not cover comparator decisions")
if contract.get("scope") != "performance_only":
    raise SystemExit("unexpected comparison scope")
if contract.get("variable_paths") != [
    "/launch_config/selected_environment/VLLM_FL_FLAGOS_BLACKLIST_APPEND"
]:
    raise SystemExit("comparison contract does not isolate the provider blacklist")
repeats = contract.get("repeats", {})
if repeats.get("min_processes") != 1 or repeats.get("min_measured_rounds") != 3:
    raise SystemExit("comparison repeat contract changed")
if candidate.get("status") != "complete" or candidate.get("role") != "candidate":
    raise SystemExit("existing service46 candidate run is not complete")
if candidate.get("inputs_verified_before") is not True or candidate.get("inputs_verified_after") is not True:
    raise SystemExit("existing candidate did not verify frozen inputs before/after")

def checked(ref):
    path = Path(ref["path"])
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != ref["sha256"]:
        raise SystemExit(f"candidate artifact hash mismatch: {path}")
    return path

artifacts = candidate.get("artifacts", {})
candidate_contract = checked(artifacts["comparison_contract"])
candidate_plan = checked(artifacts["plan"])
candidate_service = checked(artifacts["service"])
if json.load(open(sys.argv[1], encoding="utf-8")) != json.loads(
    candidate_plan.read_text(encoding="utf-8")
):
    raise SystemExit("existing candidate used a semantically different effective plan")
if hashlib.sha256(Path(sys.argv[2]).read_bytes()).hexdigest() != hashlib.sha256(candidate_contract.read_bytes()).hexdigest():
    raise SystemExit("existing candidate used a different comparison contract")
service = json.loads(candidate_service.read_text(encoding="utf-8"))
if service.get("service_instance_id") != "9b65cc77d73c-8030-2636577-259878814":
    raise SystemExit("existing candidate run is not bound to service46")
rounds = candidate.get("rounds", [])
if [row.get("phase") for row in rounds] != [
    "warmup", "warmup", "warmup", "measured", "measured", "measured"
]:
    raise SystemExit("existing candidate is not a 3+3 run")
if graph.get("replays") != 2:
    raise SystemExit("service46 lacks the frozen two-replay evidence")
responses = graph.get("responses", [])
if len(responses) != 2 or responses[0].get("text") != responses[1].get("text"):
    raise SystemExit("service46 replay text is not stable")
PY

python3 "${verifier}" \
  "${candidate_manifest}" "${container}" "${port}" "${max_num_seqs}"
assert_live_service \
  "${candidate_manifest}" "${candidate_process}" \
  "${expected_candidate_instance}" "${native_blacklist}"
docker exec "${container}" curl -fsS "http://127.0.0.1:${port}/health" >/dev/null

mkdir "${audit_dir}"
sha256sum \
  "${plan}" "${contract}" "${normalizer}" "${transition}" "${graph_smoke}" \
  "${candidate_raw}" "${candidate_process}" "${candidate_graph}" \
  "${candidate_manifest}" "${candidate_record}" > "${audit_dir}/frozen-inputs.sha256"

# service46(native candidate) -> service47(normal baseline/revert)
env \
  SOURCE_MANIFEST="${candidate_raw}" \
  SOURCE_PROCESS="${candidate_process}" \
  SOURCE_CONFIG="${tuned_config}" \
  TARGET_CONFIG="${tuned_config}" \
  SOURCE_BLACKLIST="${native_blacklist}" \
  TARGET_BLACKLIST="${normal_blacklist}" \
  RUN_ID="${normal_transition_id}" \
  bash "${transition}"
restore_needed=1

python3 "${normalizer}" "${normal_raw}" "${normal_manifest}" "${normal_blacklist}"
python3 "${verifier}" "${normal_manifest}" "${container}" "${port}" "${max_num_seqs}"
normal_instance=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["service_instance_id"])' "${normal_manifest}")
assert_live_service "${normal_manifest}" "${normal_process}" "${normal_instance}" "${normal_blacklist}"
bash "${graph_smoke}" \
  "${normal_graph_label}" "${normal_manifest}" "${max_num_seqs}" \
  "" "${container}" "${port}"

# The maintained contract currently permits one service process per role.
# Baseline and revert are separate physical 3+3 runs with unique artifacts,
# but intentionally share the fresh normal service47 process.
run_role baseline "${baseline_run_id}" "${normal_manifest}"
run_role revert "${revert_run_id}" "${normal_manifest}"

# Always restore the retained native provider before comparing evidence.
# service48 is operational restore evidence, not a second candidate run.
restore_native
restore_needed=0

python3 "${comparator}" \
  --contract "${contract}" \
  --run-record "${baseline_record}" \
  --run-record "${candidate_record}" \
  --run-record "${revert_record}" \
  --output "${comparison_result}"

sha256sum \
  "${normal_raw}" "${normal_process}" "${normal_manifest}" \
  "${normal_graph_dir}/canonical.json" "${baseline_record}" "${revert_record}" \
  "${restore_raw}" "${restore_process}" "${restore_manifest}" \
  "${restore_graph_dir}/canonical.json" "${comparison_result}" \
  > "${audit_dir}/completed-evidence.sha256"

python3 - "${comparison_result}" <<'PY'
import json
import sys
result = json.load(open(sys.argv[1], encoding="utf-8"))
if result.get("status") != "passed":
    raise SystemExit(f"comparison did not pass: {result.get('status')} {result.get('issues')}")
print(json.dumps(result, indent=2, sort_keys=True))
PY
