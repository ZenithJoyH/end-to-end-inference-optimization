#!/usr/bin/env python3
import argparse
import json


parser = argparse.ArgumentParser()
parser.add_argument("prefill")
parser.add_argument("mixed")
args = parser.parse_args()
records = [json.load(open(path, encoding="utf-8")) for path in (args.prefill, args.mixed)]
for expected, record in zip(("prefill", "mixed"), records):
    if record["observed_phase"] != expected:
        raise SystemExit(f"phase mismatch: {record['observed_phase']} != {expected}")
rows = []
for group_rows in ("2", "4", "8", "16"):
    values = [record["group_rows"][group_rows] for record in records]
    passed_both = all(value["rho"] is not None and value["rho"] >= 0.12 for value in values)
    rows.append({"R": int(group_rows), "prefill": values[0], "mixed": values[1],
                 "passed_both_phases": passed_both})
print(json.dumps({"schema_version": 1, "experiment_id": "op-018",
                  "gate": "rho>=0.12 in both prefill and mixed",
                  "eligible_for_union_mask_microbenchmark": any(r["passed_both_phases"] for r in rows),
                  "rows": rows}, indent=2, sort_keys=True))
