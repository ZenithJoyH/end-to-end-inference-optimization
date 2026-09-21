#!/usr/bin/env python3
"""Prepare a steady-state A/B run for the opt-in native Decode sparse MLA."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


CASE = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
BASE = CASE / "results/performance/20260919-p4k-d128-c64-n64-mbt-sweep-sq4096-02"
ROOT = CASE / "results/performance/20260920-p4k-d128-c64-n64-native-decode-03"
SOURCE_RUNNER = CASE / "commands/run-hy4-p4k-d128-c64-n64-mbt-config-20260919.sh"
RUNNER = CASE / "commands/run-hy4-p4k-d128-c64-n64-native-decode-20260920-v2.sh"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


if ROOT.exists() or RUNNER.exists():
    raise SystemExit("refusing to overwrite native Decode experiment artifacts")

(ROOT / "config").mkdir(parents=True)
(ROOT / "runs").mkdir()
(ROOT / "service").mkdir()
shutil.copytree(BASE / "bundle", ROOT / "bundle")
shutil.copy2(
    BASE / "config/service-manifest-base.json",
    ROOT / "config/service-manifest-base.json",
)

plan = json.loads((BASE / "config/plan.json").read_text())
(ROOT / "config/plan.json").write_text(json.dumps(plan, indent=2) + "\n")

comparison = {
    "schema_version": 1,
    "scope": "performance_only",
    "hypothesis": (
        "On T-Head pure Decode, the PPU native sparse-MLA kernel improves the "
        "steady P4096/D128/C64/N64 milestone while Prefill remains on FlagGems."
    ),
    "variable_paths": ["/launch_config/thead_native_sparse_mla_decode"],
    "primary": {
        "metric": "output_throughput",
        "direction": "higher",
        "min_improvement": 0.02,
    },
    "guardrails": [
        {"metric": "p99_ttft_ms", "direction": "lower", "max_regression": 0.05},
        {"metric": "p99_tpot_ms", "direction": "lower", "max_regression": 0.05},
        {"metric": "p99_itl_ms", "direction": "lower", "max_regression": 0.05},
        {
            "metric": "total_token_throughput",
            "direction": "higher",
            "max_regression": 0.02,
        },
    ],
    "repeats": {
        "min_processes": 1,
        "min_measured_rounds": 2,
        "max_relative_spread": 0.08,
        "max_baseline_drift": 0.15,
    },
}
(ROOT / "config/comparison.json").write_text(
    json.dumps(comparison, indent=2) + "\n"
)
(ROOT / "experiment-contract.json").write_text(
    json.dumps(
        {
            "schema_version": 1,
            "mode": "targeted",
            "scope": "performance_only",
            "parent_scenario_id": "p4096-d1024-c64-n128",
            "scenario_id": "p4096-d128-c64-n64",
            "stage": "mixed",
            "single_variable": "thead_native_sparse_mla_decode",
            "values": [False, True],
            "cold_start_policy": "excluded_by_user_request",
            "steady_state_policy": "one warmup round followed by two measured rounds",
            "promotion_rule": (
                "output throughput >=2%, p99 TTFT/TPOT/ITL regression <=5%, "
                "complete token counts, measured spread <=8%, native hit log present"
            ),
            "accuracy_boundary": (
                "Operator output max abs error 3.05e-5; a new model accuracy gate "
                "is required before promotion."
            ),
            "conclusion_boundary": (
                "P4096/D128/C64/N64 milestone only; not the parent D1K formal result."
            ),
        },
        indent=2,
    )
    + "\n"
)

runner = SOURCE_RUNNER.read_text()
runner = replace_once(
    runner,
    '''if [[ "$#" -lt 2 || "$#" -gt 4 ]]; then
  echo "usage: $0 <run-root> <max-num-batched-tokens> [mixed-token-budget-cap] [async-scheduling]" >&2
  exit 2
fi

run_root=$1
mbt=$2
mixed_cap=${3:-0}
async_scheduling=${4:-0}
case "$mbt" in
  2048|2256|2304|2560|3072|4096) ;;
  *) echo "unsupported max-num-batched-tokens: $mbt" >&2; exit 2 ;;
esac
case "$async_scheduling" in
  0|1) ;;
  *) echo "async-scheduling must be 0 or 1: $async_scheduling" >&2; exit 2 ;;
esac
case "$mixed_cap" in
  0|2048) ;;
  *) echo "unsupported mixed token budget cap: $mixed_cap" >&2; exit 2 ;;
esac
''',
    '''if [[ "$#" -ne 2 ]]; then
  echo "usage: $0 <run-root> <native-decode:0|1>" >&2
  exit 2
fi

run_root=$1
native_decode=$2
mbt=2048
mixed_cap=0
async_scheduling=0
case "$native_decode" in
  0|1) ;;
  *) echo "native-decode must be 0 or 1: $native_decode" >&2; exit 2 ;;
esac
''',
    "arguments",
)
runner = replace_once(
    runner,
    '''run_id="mbt-${mbt}"
if [[ "$async_scheduling" == 1 ]]; then
  run_id="${run_id}-async"
fi
if [[ "$mixed_cap" != 0 ]]; then
  run_id="${run_id}-mixed-cap-${mixed_cap}"
fi
''',
    'run_id="native-decode-${native_decode}"\n',
    "run id",
)
runner = replace_once(
    runner,
    "export VLLM_FL_MIXED_MAX_NUM_BATCHED_TOKENS=${mixed_cap}\n",
    "export VLLM_FL_MIXED_MAX_NUM_BATCHED_TOKENS=${mixed_cap}\n"
    "export VLLM_FL_THEAD_NATIVE_SPARSE_MLA_DECODE=${native_decode}\n",
    "candidate environment",
)
runner = replace_once(
    runner,
    '''    /workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/vendor/thead/impl/hyv4_indexer.py \\
''',
    '''    /workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/vendor/thead/impl/hyv4_indexer.py \\
    /workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/vendor/thead/impl/mla_decode.py \\
    /workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/flaggems/impl/mla_sparse.py \\
''',
    "source identities",
)
runner = replace_once(
    runner,
    '''python3 - "$base_manifest" "$service_manifest" "$mbt" "$mixed_cap" "$async_scheduling" \\
  "$container_id" "$api_pid" "$start_ticks" "$runtime_sha" \\
''',
    '''python3 - "$base_manifest" "$service_manifest" "$mbt" "$mixed_cap" "$async_scheduling" "$native_decode" \\
  "$container_id" "$api_pid" "$start_ticks" "$runtime_sha" \\
''',
    "manifest arguments",
)
runner = replace_once(
    runner,
    '''    _, base_path, output_path, mbt, mixed_cap, async_scheduling, container_id, api_pid, start_ticks,
''',
    '''    _, base_path, output_path, mbt, mixed_cap, async_scheduling, native_decode, container_id, api_pid, start_ticks,
''',
    "manifest argv",
)
runner = replace_once(
    runner,
    '''data["launch_config"]["async_scheduling"] = async_scheduling_enabled
''',
    '''data["launch_config"]["async_scheduling"] = async_scheduling_enabled
data["launch_config"]["thead_native_sparse_mla_decode"] = bool(int(native_decode))
''',
    "manifest variable",
)
runner = replace_once(
    runner,
    '''role=candidate
if [[ "$mbt" == 2048 ]]; then
  role=baseline
fi
''',
    '''role=candidate
if [[ "$native_decode" == 0 ]]; then
  role=baseline
fi
''',
    "role",
)
runner = replace_once(
    runner,
    '''printf 'completed mbt=%s run_record=%s\\n' \\
  "$mbt" "${run_root}/runs/${run_id}/run-record.json"
''',
    '''printf 'completed native_decode=%s run_record=%s\\n' \\
  "$native_decode" "${run_root}/runs/${run_id}/run-record.json"
''',
    "completion",
)
RUNNER.write_text(runner)
RUNNER.chmod(0o755)
print(ROOT)
print(RUNNER)
