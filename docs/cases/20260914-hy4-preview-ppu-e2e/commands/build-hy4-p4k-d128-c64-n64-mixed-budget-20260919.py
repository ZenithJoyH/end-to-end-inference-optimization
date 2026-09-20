#!/usr/bin/env python3
import json
import shutil
import sys
from pathlib import Path


run_root = Path(sys.argv[1]).resolve()
source_root = Path(sys.argv[2]).resolve()
if run_root.exists():
    raise SystemExit(f"refusing to overwrite existing run root: {run_root}")

(run_root / "config").mkdir(parents=True)
(run_root / "runs").mkdir()
(run_root / "service").mkdir()
(run_root / "bundle" / "evaluation" / "performance").mkdir(parents=True)

shutil.copy2(source_root / "config" / "plan.json", run_root / "config" / "plan.json")
shutil.copy2(
    source_root / "config" / "service-manifest-base.json",
    run_root / "config" / "service-manifest-base.json",
)
comparison = json.loads(
    (source_root / "config" / "comparison.json").read_text(encoding="utf-8")
)
comparison["hypothesis"] = (
    "At max-num-batched-tokens=2304, cap only mixed prefill/decode scheduler steps "
    "at 2048 to retain pure-prefill throughput while reducing p99 ITL."
)
comparison["variable_paths"] = [
    "/plugin_sha256",
    "/launch_config/max_num_batched_tokens",
    "/launch_config/mixed_max_num_batched_tokens",
    "/launch_config/async_scheduling",
]
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
            "baseline_context": str(
                source_root / "runs" / "mbt-2304" / "run-record.json"
            ),
            "candidate": {
                "max_num_batched_tokens": 2304,
                "mixed_max_num_batched_tokens": 2048,
                "async_scheduling": True,
            },
            "cold_start_policy": "excluded_by_user_request",
            "steady_state_policy": "one warmup round followed by two measured rounds",
            "promotion_rule": (
                "Against same-plan 2048 context: output throughput >=3%, p99 TPOT/ITL "
                "regression <=5%, p99 TTFT regression <=10%, complete token counts, "
                "measured spread <=8%. The prior 2304 run is diagnostic context because "
                "the Plugin source identity changed."
            ),
            "conclusion_boundary": (
                "Milestone only; a retained candidate requires a same-source checkpoint "
                "and then P4096/D1024/C64/N128 validation."
            ),
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
print(run_root)
