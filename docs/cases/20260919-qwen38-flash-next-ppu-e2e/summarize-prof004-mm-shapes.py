#!/usr/bin/env python3
"""Collapse prof-004 GEMM external-id rows into tensor-shape signatures."""

import json
from collections import defaultdict
from pathlib import Path

root = Path("/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/prof-004-p4k-post-op008/summaries")
source = root / "mm-general-external-id-shape-map.json"
document = json.loads(source.read_text())
groups = defaultdict(lambda: {"count": 0, "total_us": 0.0, "min_us": float("inf"), "max_us": 0.0})
shape_totals = defaultdict(lambda: {"count": 0, "total_us": 0.0})

for row in document["rows"]:
    operators = [item for item in row["operators"] if item["name"] == "aten::mm"]
    if len(operators) != 1:
        continue
    dims = tuple(tuple(value) for value in operators[0]["input_dims"])
    signature = (
        dims,
        tuple(row["grid"]),
        tuple(row["block"]),
        row["registers_per_thread"],
        row["shared_memory"],
    )
    duration = float(row["duration_us"])
    values = groups[signature]
    values["count"] += 1
    values["total_us"] += duration
    values["min_us"] = min(values["min_us"], duration)
    values["max_us"] = max(values["max_us"], duration)
    shape_totals[dims]["count"] += 1
    shape_totals[dims]["total_us"] += duration

rows = []
for signature, values in groups.items():
    dims, grid, block, registers, shared_memory = signature
    rows.append({
        "input_dims": [list(value) for value in dims],
        "M": dims[0][0] if dims and dims[0] else None,
        "grid": list(grid),
        "block": list(block),
        "registers_per_thread": registers,
        "shared_memory": shared_memory,
        **values,
        "avg_us": values["total_us"] / values["count"],
    })
rows.sort(key=lambda item: item["total_us"], reverse=True)

shapes = []
for dims, values in shape_totals.items():
    shapes.append({
        "input_dims": [list(value) for value in dims],
        "M": dims[0][0] if dims and dims[0] else None,
        **values,
        "avg_us": values["total_us"] / values["count"],
    })
shapes.sort(key=lambda item: item["total_us"], reverse=True)

output = {
    "schema_version": 1,
    "source": str(source),
    "mapped_mm_events": sum(item["count"] for item in rows),
    "shape_signatures": rows,
    "shape_totals": shapes,
}
path = root / "mm-general-shape-signatures.json"
path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
print(path)
print(json.dumps({
    "mapped_mm_events": output["mapped_mm_events"],
    "top_decode_shapes": [item for item in shapes if item["M"] <= 64][:20],
    "top_decode_signatures": [item for item in rows if item["M"] <= 64][:30],
}, indent=2, sort_keys=True))
