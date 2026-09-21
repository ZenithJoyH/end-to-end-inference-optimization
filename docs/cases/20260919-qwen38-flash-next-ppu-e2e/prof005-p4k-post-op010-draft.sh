#!/usr/bin/env bash
# Draft only: this file has not been copied to or executed on PPU-01.
set -euo pipefail

mode=${1:?usage: prof005-p4k-post-op010-draft.sh start|dry-run|capture|restore|analyze|lifecycle}
case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
image_id=sha256:d87b7b26da3623b18863d47fa623135d0dfc3ba3288293be18aa6f928cb9bbe6
port=8030

comparison=${case_root}/performance/op010-p4k-d1024-sequential-abr-service46-47.json
source_transition=${case_root}/transitions/mm-native-d1024-native-restore-service-48
source_manifest=${case_root}/manifests/mm-native-d1024-native-restore-service48.json
source_process=${source_transition}/after-process.json
source_graph=${case_root}/smoke/op010-p4k-d1024-native-service48-graph-01/canonical.json

profile_id=prof-005-p4k-post-op010
profile_root=${case_root}/profiling/${profile_id}
trace_dir=${profile_root}/traces
client_dir=${profile_root}/client
profiler_transition_id=prof-005-p4k-post-op010-service-49
profiler_transition=${case_root}/transitions/${profiler_transition_id}
profiler_manifest=${profiler_transition}/${profiler_transition_id}-raw.json
profiler_process=${profiler_transition}/after-maxseq64-process.json

restore_transition_id=post-prof-005-restored-native-service-50
restore_transition=${case_root}/transitions/${restore_transition_id}
restore_raw=${restore_transition}/${restore_transition_id}-raw.json
restore_process=${restore_transition}/after-maxseq64-process.json
restore_manifest=${case_root}/manifests/post-prof005-native-service50.json
restore_graph_label=post-prof005-native-service50-graph-01
restore_graph_dir=${case_root}/smoke/${restore_graph_label}

tuned_config=${case_root}/configs/moe-bm16-decode-only-01
native_blacklist=_conv_depthwise2d,index,normal_,mm,mm_out
transition=${case_root}/commands/performance/transition-prof005-preserve-op010.sh
verifier=${case_root}/commands/performance/verify-live-service-manifest.py
profile_runner=${case_root}/commands/performance/vllm_profile.py
summarizer=${case_root}/commands/performance/trace_to_summary.py
phase_analyzer=${case_root}/commands/analyze-prof005-phases-v2.py
base_phase_analyzer=${case_root}/commands/analyze-prof001-phases.py
normalizer=${case_root}/commands/performance/normalize-mm-provider-service-manifest.py
graph_smoke=${case_root}/commands/performance/run-graph-replay-smoke.sh

profiler_config=$(printf '{"profiler":"torch","torch_profiler_dir":"%s","torch_profiler_with_stack":false,"torch_profiler_record_shapes":true}' "${trace_dir}")

assert_unused() {
  test ! -e "$1" || { echo "refusing to overwrite: $1" >&2; return 2; }
}

gate_passed() {
  test -f "${comparison}"
  python3 - "${comparison}" <<'PY'
import json
import sys

result = json.load(open(sys.argv[1], encoding="utf-8"))
if result.get("status") != "passed" or result.get("issues"):
    raise SystemExit("prof005 is blocked until the op010 D1024 comparator is passed")
if result.get("changed_paths") != [
    "/launch_config/selected_environment/VLLM_FL_FLAGOS_BLACKLIST_APPEND"
]:
    raise SystemExit("op010 comparison changed-path proof is not exact")
case = result.get("cases", {}).get("p4096-d1024-c64-n128")
if not isinstance(case, dict):
    raise SystemExit("passed comparison does not cover exact P4096/D1024/C64/N128")
PY
  if test -f "${profile_root}/frozen-inputs.sha256"; then
    sha256sum -c "${profile_root}/frozen-inputs.sha256" >/dev/null
  fi
}

assert_live() {
  local manifest=$1
  local process=$2
  local expected_profiler=$3
  python3 "${verifier}" "${manifest}" "${container}" "${port}" 64 >/dev/null
  docker exec -i "${container}" python3 - \
    "${manifest}" "${process}" "${native_blacklist}" "${expected_profiler}" <<'PY'
import json
import os
import sys

manifest_path, process_path, blacklist, expected_profiler = sys.argv[1:]
manifest = json.load(open(manifest_path, encoding="utf-8"))
expected = json.load(open(process_path, encoding="utf-8"))
pid = int(expected["pid"])
raw = open(f"/proc/{pid}/stat", encoding="utf-8").read()
tail = raw[raw.rfind(")") + 2:].split()
ticks = int(tail[19])
argv = [item.decode(errors="replace") for item in open(
    f"/proc/{pid}/cmdline", "rb").read().split(b"\0") if item]
if ticks != int(expected["start_ticks"]) or argv != expected["args"]:
    raise SystemExit("PID/start-ticks/argv identity changed")
container_id = "9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4"
instance = f"{container_id[:12]}-8030-{pid}-{ticks}"
if manifest.get("service_instance_id") != instance:
    raise SystemExit("manifest is not bound to the exact live PID")
environment = {}
for item in open(f"/proc/{pid}/environ", "rb").read().split(b"\0"):
    if b"=" in item:
        key, value = item.split(b"=", 1)
        environment[key.decode(errors="replace")] = value.decode(errors="replace")
if environment.get("VLLM_FL_FLAGOS_BLACKLIST_APPEND") != blacklist:
    raise SystemExit("native mm/mm_out provider is not retained")
if environment.get("VLLM_FL_QSA_STATIC_SCORE_COLUMNS") != "8448":
    raise SystemExit("QSA bound drift")
if environment.get("VLLM_TUNED_CONFIG_FOLDER") != (
    "/mnt/nfs/users/jinghao/qwen3.8-flash/"
    "20260919-qwen38-flash-next-ppu-e2e/configs/moe-bm16-decode-only-01"
):
    raise SystemExit("MoE config drift")
launch_args = manifest.get("launch_config", {}).get("launch_args", [])
positions = [i for i, value in enumerate(launch_args) if value == "--profiler-config"]
if len(positions) > 1 or (positions and positions[0] + 1 >= len(launch_args)):
    raise SystemExit("malformed profiler launch argument")
actual_profiler = launch_args[positions[0] + 1] if positions else ""
if actual_profiler != expected_profiler:
    raise SystemExit("profiler config differs from the frozen mode")
print(instance)
PY
}

require_control_files() {
  for path in \
    "${transition}" "${verifier}" "${profile_runner}" "${summarizer}" \
    "${phase_analyzer}" "${base_phase_analyzer}" "${normalizer}" \
    "${graph_smoke}"; do
    test -f "${path}"
  done
}

start_profiler_service() {
  gate_passed
  require_control_files
  test "$(docker inspect --format '{{.Id}}' "${container}")" = "${container_id}"
  test "$(docker inspect --format '{{.Image}}' "${container}")" = "${image_id}"
  test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
  test -f "${source_manifest}"
  test -f "${source_process}"
  test -f "${source_graph}"
  assert_live "${source_manifest}" "${source_process}" ""
  assert_unused "${profile_root}"
  assert_unused "${profiler_transition}"
  mkdir -p "${trace_dir}"
  printf '%s\n' "${profiler_config}" > "${profile_root}/profiler-config.json"
  sha256sum \
    "${comparison}" "${source_manifest}" "${source_process}" "${source_graph}" \
    "${transition}" "${verifier}" "${profile_runner}" "${summarizer}" \
    "${phase_analyzer}" "${base_phase_analyzer}" "${normalizer}" "${graph_smoke}" \
    > "${profile_root}/frozen-inputs.sha256"

  export SOURCE_MAX_NUM_SEQS=64 TARGET_MAX_NUM_SEQS=64
  export SOURCE_MAX_NUM_BATCHED_TOKENS=4096 TARGET_MAX_NUM_BATCHED_TOKENS=4096
  export SOURCE_PROFILER_CONFIG=
  export TARGET_PROFILER_CONFIG="${profiler_config}"
  export TUNED_CONFIG_FOLDER="${tuned_config}"
  export TARGET_BLACKLIST="${native_blacklist}"
  export TARGET_QSA_STATIC_SCORE_COLUMNS=8448
  export TRANSITION_ROLE="${profiler_transition_id}"
  bash "${transition}" "${profiler_transition_id}" "${source_manifest}"

  assert_live "${profiler_manifest}" "${profiler_process}" "${profiler_config}" \
    > "${profile_root}/profiler-service-instance.txt"
  docker exec "${container}" curl -fsS "http://127.0.0.1:${port}/health" >/dev/null
}

run_profile() {
  local action=$1
  gate_passed
  assert_live "${profiler_manifest}" "${profiler_process}" "${profiler_config}" \
    > "${profile_root}/live-service-instance.${action}.txt"
  common=(
    python3 "${profile_runner}"
    --model Qwen3.8-Flash-Next
    --tokenizer /mnt/cpfs/models/Qwen3.8-Flash-Next
    --host 127.0.0.1 --port 8030 --endpoint /v1/completions
    --case 4096,128,64,64
    --runs 2 --warmup-rounds 1 --profile-runs last
    --seed 42 --timeout 1800
    --profile-dir "${trace_dir}" --output-dir "${client_dir}"
  )
  case "${action}" in
    dry-run)
      assert_unused "${profile_root}/dry-run.json"
      docker exec "${container}" "${common[@]}" --dry-run \
        > "${profile_root}/dry-run.json"
      ;;
    capture)
      test -f "${profile_root}/dry-run.json"
      assert_unused "${client_dir}"
      assert_unused "${profile_root}/capture.console.log"
      find "${trace_dir}" -maxdepth 1 -type f -printf '%f %s %T@\n' \
        | sort > "${profile_root}/trace-inventory.before.txt"
      docker exec "${container}" "${common[@]}" 2>&1 \
        | tee "${profile_root}/capture.console.log"
      ;;
    *) return 2 ;;
  esac
}

diagnostic_path() {
  find "${client_dir}" -type f -name diagnostic.json -print
}

assert_capture_complete() {
  local diagnostic
  diagnostic=$(diagnostic_path)
  test "$(printf '%s\n' "${diagnostic}" | sed '/^$/d' | wc -l)" -eq 1
  python3 - "${diagnostic}" <<'PY'
import json
import sys
record = json.load(open(sys.argv[1], encoding="utf-8"))
if record.get("status") != "complete" or record.get("errors"):
    raise SystemExit("profile diagnostic is not complete")
rounds = record.get("rounds", [])
if len(rounds) != 2:
    raise SystemExit("expected one warmup and one measured round")
if rounds[0].get("phase") != "warmup" or rounds[0].get("profile_requested"):
    raise SystemExit("warmup round contract drift")
if rounds[1].get("phase") != "measured" or rounds[1].get("profile_requested") is not True:
    raise SystemExit("bounded profiled round contract drift")
if rounds[1].get("case") != [4096, 128, 64, 64] or not rounds[1].get("valid"):
    raise SystemExit("profiled workload or validation drift")
if not rounds[1].get("traces"):
    raise SystemExit("runner did not attest new trace artifacts")
PY
}

assert_trace_coverage() {
  python3 - "${trace_dir}" <<'PY'
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
paths = sorted(root.glob("*.pt.trace.json.gz"))
if len(paths) != 9:
    raise SystemExit(f"expected async + 8 TP traces, got {len(paths)}")
async_paths = [path for path in paths if ".async_llm." in path.name]
if len(async_paths) != 1:
    raise SystemExit("expected exactly one async_llm trace")
ranks = {}
pattern = re.compile(r"dp0_pp0_tp([0-7])_dcp0_ep([0-7])_rank([0-7])\.")
for path in paths:
    if path in async_paths:
        continue
    match = pattern.search(path.name)
    if not match or len(set(match.groups())) != 1:
        raise SystemExit(f"invalid TP trace identity: {path.name}")
    rank = int(match.group(1))
    if rank in ranks:
        raise SystemExit(f"duplicate rank trace: {rank}")
    if path.stat().st_size <= 0:
        raise SystemExit(f"empty trace: {path}")
    ranks[rank] = path.name
if set(ranks) != set(range(8)):
    raise SystemExit(f"rank coverage mismatch: {sorted(ranks)}")
PY
  find "${trace_dir}" -maxdepth 1 -type f -name '*.pt.trace.json.gz' -print0 \
    | xargs -0 -n1 gzip -t
}

assert_no_profile_client() {
  docker exec -i "${container}" python3 - <<'PY'
import os
found = []
for entry in os.listdir("/proc"):
    if not entry.isdigit() or int(entry) == os.getpid():
        continue
    try:
        args = [item.decode(errors="replace") for item in open(
            f"/proc/{entry}/cmdline", "rb").read().split(b"\0") if item]
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    text = " ".join(args)
    is_runner = "vllm_profile.py" in text and "--port 8030" in text
    is_bench = (
        any(os.path.basename(value) == "vllm" for value in args)
        and "bench" in args and "serve" in args and "--port" in args
    )
    if is_runner or is_bench:
        found.append({"pid": int(entry), "args": args})
if found:
    raise SystemExit(f"profiling client/orchestrator still live: {found}")
PY
}

restore_native() {
  gate_passed
  assert_live "${profiler_manifest}" "${profiler_process}" "${profiler_config}" >/dev/null
  assert_no_profile_client
  # If capture started, asynchronous export must be complete and all traces
  # present before any restart.  A dry-run-only profiler service is safe to
  # restore because it never sent inference traffic.
  if test -e "${profile_root}/capture.console.log"; then
    assert_capture_complete
    assert_trace_coverage
  fi
  assert_unused "${restore_transition}"
  assert_unused "${restore_manifest}"
  assert_unused "${restore_graph_dir}"

  export SOURCE_MAX_NUM_SEQS=64 TARGET_MAX_NUM_SEQS=64
  export SOURCE_MAX_NUM_BATCHED_TOKENS=4096 TARGET_MAX_NUM_BATCHED_TOKENS=4096
  export SOURCE_PROFILER_CONFIG="${profiler_config}"
  export TARGET_PROFILER_CONFIG=
  export TUNED_CONFIG_FOLDER="${tuned_config}"
  export TARGET_BLACKLIST="${native_blacklist}"
  export TARGET_QSA_STATIC_SCORE_COLUMNS=8448
  export TRANSITION_ROLE="${restore_transition_id}"
  bash "${transition}" "${restore_transition_id}" "${profiler_manifest}"

  python3 "${normalizer}" "${restore_raw}" "${restore_manifest}" "${native_blacklist}"
  assert_live "${restore_manifest}" "${restore_process}" "" \
    > "${profile_root}/restored-service-instance.txt"
  bash "${graph_smoke}" \
    "${restore_graph_label}" "${restore_manifest}" 64 \
    "${source_graph}" "${container}" "${port}"
}

analyze() {
  gate_passed
  test -f "${restore_manifest}"
  test -f "${restore_graph_dir}/canonical.json"
  cmp -s "${source_graph}" "${restore_graph_dir}/canonical.json"
  assert_live "${restore_manifest}" "${restore_process}" "" >/dev/null
  assert_capture_complete
  assert_trace_coverage
  # summaries/ is preserved as the invalid fixed-marker analysis.  v2 uses
  # the source-backed num_new/num_cached semantics without overwriting it.
  local summary_dir=${profile_root}/summaries-v2
  assert_unused "${summary_dir}"
  mkdir "${summary_dir}"
  sha256sum "${phase_analyzer}" "${base_phase_analyzer}" \
    > "${summary_dir}/analysis-inputs.sha256"
  find "${trace_dir}" -maxdepth 1 -type f -name '*.pt.trace.json.gz' -print0 \
    | sort -z | xargs -0 sha256sum > "${summary_dir}/trace-SHA256SUMS"
  local async_trace
  async_trace=$(find "${trace_dir}" -maxdepth 1 -type f -name '*.async_llm.*.pt.trace.json.gz' -print)
  python3 "${summarizer}" "${async_trace}" --row-limit 120 \
    --output "${summary_dir}/async-llm.txt"
  for rank in 0 1 2 3 4 5 6 7; do
    local trace
    trace=$(find "${trace_dir}" -maxdepth 1 -type f \
      -name "dp0_pp0_tp${rank}_dcp0_ep${rank}_rank${rank}.*.pt.trace.json.gz" -print)
    test "$(printf '%s\n' "${trace}" | sed '/^$/d' | wc -l)" -eq 1
    python3 "${summarizer}" "${trace}" --row-limit 120 \
      --output "${summary_dir}/rank${rank}.txt"
    python3 "${phase_analyzer}" "${trace}" \
      --base-analyzer "${base_phase_analyzer}" \
      --output "${summary_dir}/phase-rank${rank}.json"
  done
  python3 - "${summary_dir}" \
    "${summary_dir}/phase-completeness.json" <<'PY'
import json
import re
import sys
from pathlib import Path

required = ("prefill_graph", "decode_graph", "mixed_graph")
marker_pattern = re.compile(r"^execute_new_(\d+)_cached_(\d+)$")


def marker_phase(name):
    match = marker_pattern.match(name)
    if match is None:
        return None
    num_new, num_cached = (int(value) for value in match.groups())
    if num_new > 0 and num_cached == 0:
        return "prefill_graph"
    if num_new == 0 and num_cached > 0:
        return "decode_graph"
    if num_new > 0 and num_cached > 0:
        return "mixed_graph"
    return None


summary_dir = Path(sys.argv[1])
rank_checks = {}
coverages = {}
methods = {}
marker_counts = {}
for rank in range(8):
    source = json.loads(
        (summary_dir / f"phase-rank{rank}.json").read_text(encoding="utf-8")
    )
    coverage = source.get("device_coverage", {})
    markers = source.get("markers", {})
    checks = {
        f"{name}_present": (
            isinstance(coverage.get(name), dict)
            and coverage[name].get("events", 0) > 0
            and coverage[name].get("total_us", 0) > 0
        )
        for name in required
    }
    checks["prefill_markers_present"] = any(
        marker_phase(name) == "prefill_graph" for name in markers
    )
    checks["decode_markers_present"] = any(
        marker_phase(name) == "decode_graph" for name in markers
    )
    checks["mixed_markers_present"] = any(
        marker_phase(name) == "mixed_graph" for name in markers
    )
    checks["outside_graph_accounted"] = isinstance(
        coverage.get("outside_graph_windows"), dict
    )
    rank_checks[f"rank{rank}"] = checks
    coverages[f"rank{rank}"] = coverage
    methods[f"rank{rank}"] = source.get("method")
    marker_counts[f"rank{rank}"] = sum(
        item.get("count", 0) for item in markers.values()
    )
method_values = [json.dumps(value, sort_keys=True) for value in methods.values()]
method_consistent = len(set(method_values)) == 1
complete = method_consistent and all(
    all(checks.values()) for checks in rank_checks.values()
)
payload = {
    "schema_version": 1,
    "scenario_id": "p4096-d128-c64-n64-post-op010-profile",
    "phase_boundary_method": methods["rank0"],
    "method_consistent_across_ranks": method_consistent,
    "rank_checks": rank_checks,
    "device_coverage_by_rank": coverages,
    "marker_count_by_rank": marker_counts,
    "status": "complete" if complete else "incomplete",
    "boundary": (
        "Profiler-on activity is diagnostic only. Category sums may overlap; "
        "they are not critical-path or no-profiler speedup evidence."
    ),
}
Path(sys.argv[2]).write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
if payload["status"] != "complete":
    raise SystemExit(f"phase coverage incomplete: {rank_checks}")
PY
  sha256sum "${summary_dir}"/* > "${summary_dir}/summary-SHA256SUMS"
}

case "${mode}" in
  start) start_profiler_service ;;
  dry-run) run_profile dry-run ;;
  capture) run_profile capture ;;
  restore) restore_native ;;
  analyze) analyze ;;
  lifecycle)
    # Intentionally no EXIT auto-restart after capture failure: asynchronous
    # export/profiler state must be inspected first, per the Profiling Skill.
    start_profiler_service
    run_profile dry-run
    if ! run_profile capture; then
      echo "capture failed/incomplete; inspect profiler state and trace export before restore" >&2
      exit 3
    fi
    restore_native
    analyze
    ;;
  *) exit 2 ;;
esac
