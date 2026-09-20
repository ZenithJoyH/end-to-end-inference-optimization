#!/usr/bin/env python3
import json
import shutil
import sys
from pathlib import Path


run_root = Path(sys.argv[1]).resolve()
base_root = Path(sys.argv[2]).resolve()
if run_root.exists():
    raise SystemExit(f"refusing to overwrite existing run root: {run_root}")

(run_root / "config").mkdir(parents=True)
(run_root / "runs").mkdir()
(run_root / "service").mkdir()
(run_root / "bundle" / "evaluation" / "performance").mkdir(parents=True)

base_config = base_root / "config"
shutil.copy2(
    base_config / "service-manifest.json",
    run_root / "config" / "service-manifest-base.json",
)

plan = json.loads((base_config / "plan.json").read_text(encoding="utf-8"))
plan["measurement"]["warmup_rounds"] = 1
plan["measurement"]["measured_rounds"] = 2
plan["measurement"]["timeout_s"] = 3600
plan["cases"] = [
    {
        "id": "p4096-d128-c64-n64",
        "input_tokens": 4096,
        "output_tokens": 128,
        "concurrency": 64,
        "requests": 64,
        "load_mode": "finite_batch",
        "stage": "mixed",
        "request_rate": None,
        "burstiness": 1,
    }
]

comparison = {
    "schema_version": 1,
    "scope": "performance_only",
    "hypothesis": (
        "With the Hy4 HQ4 sparse-MLA specialization extended through SQ=4096, "
        "raising max-num-batched-tokens above 2048 improves the steady-state "
        "P4096/D128/C64/N64 milestone without material latency regression."
    ),
    "variable_paths": ["/launch_config/max_num_batched_tokens"],
    "primary": {
        "metric": "output_throughput",
        "direction": "higher",
        "min_improvement": 0.03,
    },
    "guardrails": [
        {"metric": "p99_ttft_ms", "direction": "lower", "max_regression": 0.10},
        {"metric": "p99_tpot_ms", "direction": "lower", "max_regression": 0.05},
        {"metric": "p99_itl_ms", "direction": "lower", "max_regression": 0.05},
        {
            "metric": "total_token_throughput",
            "direction": "higher",
            "max_regression": 0.05,
        },
    ],
    "repeats": {
        "min_processes": 1,
        "min_measured_rounds": 2,
        "max_relative_spread": 0.08,
        "max_baseline_drift": 0.15,
    },
}

(run_root / "config" / "plan.json").write_text(
    json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
(run_root / "config" / "comparison.json").write_text(
    json.dumps(comparison, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
(run_root / "experiment-contract.json").write_text(
    json.dumps(
        {
            "schema_version": 1,
            "mode": "targeted",
            "scope": "performance_only",
            "parent_scenario_id": "p4096-d1024-c64-n128",
            "scenario_id": "p4096-d128-c64-n64",
            "stage": "mixed",
            "single_variable": "max_num_batched_tokens",
            "values": [2048, 3072, 4096],
            "cold_start_policy": "excluded_by_user_request",
            "steady_state_policy": "one warmup round followed by two measured rounds",
            "promotion_rule": (
                "output throughput >=3% over 2048, p99 TPOT/ITL regression <=5%, "
                "p99 TTFT regression <=10%, complete token counts, measured spread <=8%"
            ),
            "conclusion_boundary": (
                "Milestone only; does not replace P4096/D1024/C64/N128 formal measurement."
            ),
            "omitted_formal_scenarios": [
                "p1024-d1024-c64-n128",
                "p4096-d1024-c64-n128",
                "p16384-d1024-c64-n128",
                "p32768-d1024-c64-n128",
            ],
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
print(run_root)

