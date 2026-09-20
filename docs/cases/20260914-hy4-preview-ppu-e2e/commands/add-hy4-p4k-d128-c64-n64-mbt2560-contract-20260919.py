#!/usr/bin/env python3
import json
import sys
from pathlib import Path


run_root = Path(sys.argv[1]).resolve()
output = run_root / "experiment-contract-mbt2560.json"
with output.open("x", encoding="utf-8") as handle:
    json.dump(
        {
            "schema_version": 1,
            "mode": "targeted",
            "scope": "performance_only",
            "parent_scenario_id": "p4096-d1024-c64-n128",
            "scenario_id": "p4096-d128-c64-n64",
            "single_variable": "max_num_batched_tokens",
            "baseline": 2048,
            "candidate": 2560,
            "rationale": (
                "Bracket the steady-state throughput/tail-latency knee after 3072 "
                "improved output throughput by 5.07% but regressed p99 ITL by 23.2%, "
                "while 4096 improved throughput by only 2.05% and regressed p99 ITL by 48.0%."
            ),
            "cold_start_policy": "excluded_by_user request",
            "steady_state_policy": "one warmup round followed by two measured rounds",
            "promotion_rule": (
                "output throughput >=3% over 2048, p99 TPOT/ITL regression <=5%, "
                "p99 TTFT regression <=10%, complete token counts, measured spread <=8%"
            ),
            "conclusion_boundary": (
                "Milestone only; does not replace P4096/D1024/C64/N128 formal measurement."
            ),
        },
        handle,
        ensure_ascii=False,
        indent=2,
    )
    handle.write("\n")
print(output)

