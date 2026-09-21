#!/usr/bin/env python3
"""Join prof-004 mm kernel external ids to recorded CPU operator shapes."""

import gzip
import json
from collections import defaultdict
from pathlib import Path

root = Path("/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/prof-004-p4k-post-op008")
trace = next((root / "traces").glob("dp0_pp0_tp0_*rank0.*.pt.trace.json.gz"))
with gzip.open(trace, "rt", encoding="utf-8") as handle:
    events = json.load(handle)["traceEvents"]

kernels = []
external_ids = set()
for event in events:
    if event.get("name") != "mm_kernel_general":
        continue
    args = event.get("args", {})
    external_id = args.get("External id")
    if external_id is None:
        continue
    external_ids.add(external_id)
    kernels.append({
        "external_id": external_id,
        "duration_us": event.get("dur"),
        "grid": args.get("grid"),
        "block": args.get("block"),
        "registers_per_thread": args.get("registers per thread"),
        "shared_memory": args.get("shared memory"),
    })

operators = defaultdict(list)
for event in events:
    args = event.get("args", {})
    external_id = args.get("External id")
    if external_id not in external_ids or event.get("name") == "mm_kernel_general":
        continue
    if not any(key in args for key in ("Input Dims", "Input type", "Concrete Inputs")):
        continue
    operators[external_id].append({
        "name": event.get("name"),
        "category": event.get("cat"),
        "duration_us": event.get("dur"),
        "input_dims": args.get("Input Dims"),
        "input_type": args.get("Input type"),
        "concrete_inputs": args.get("Concrete Inputs"),
    })

rows = []
for kernel in kernels:
    row = dict(kernel)
    row["operators"] = operators.get(kernel["external_id"], [])
    rows.append(row)

output = {
    "trace": str(trace),
    "kernel": "mm_kernel_general",
    "kernel_events_with_external_id": len(kernels),
    "unique_external_ids": len(external_ids),
    "mapped_external_ids": sum(bool(operators[value]) for value in external_ids),
    "rows": rows,
}
path = root / "summaries/mm-general-external-id-shape-map.json"
path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
print(path)
print(json.dumps(output, indent=2, sort_keys=True))
