#!/usr/bin/env python3
import json
import sys
from pathlib import Path


run_root = Path(sys.argv[1]).resolve()
output = run_root / "experiment-contract-mbt2304.json"
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
            "candidate": 2304,
            "rationale": (
                "Bracket the throughput/tail-latency knee below 2560 after 2560 "
                "improved output throughput by 5.30% but regressed p99 ITL by 10.56%."
            ),
            "cold_start_policy": "excluded_by_user_request",
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

