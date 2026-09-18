#!/usr/bin/env python3
"""Group Hy4 sparse-MLA device time by launch grid for the C16 trace."""

from collections import defaultdict
import gzip
import json
from pathlib import Path
import re

import ijson


CASE_DIR = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e"
)
PROFILE_ID = "p4k-d64-c16-n16-concurrency-capture-20260916-04"
TRACE_DIR = CASE_DIR / "profiling" / PROFILE_ID / "traces"
OUTPUT = (
    CASE_DIR
    / "results"
    / "profiling"
    / PROFILE_ID
    / "sparse-mla-kernel-grids-rank0.json"
)
TARGETS = {
    "triton_flash_mla_sparse_fwd",
    "_flash_mla_sparse_splitk_stage1",
    "_flash_mla_sparse_splitk_stage2",
}


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit(f"output already exists: {OUTPUT}")
    traces = [p for p in TRACE_DIR.glob("*.json.gz") if re.search(r"_rank0\.", p.name)]
    if len(traces) != 1:
        raise SystemExit(f"expected one rank0 trace, found {len(traces)}")

    groups = defaultdict(lambda: {"count": 0, "total_us": 0.0, "min_us": None, "max_us": 0.0})
    with gzip.open(traces[0], "rb") as stream:
        for event in ijson.items(stream, "traceEvents.item", use_float=True):
            name = event.get("name")
            if name not in TARGETS or event.get("ph") != "X":
                continue
            args = event.get("args") if isinstance(event.get("args"), dict) else {}
            grid = tuple(args.get("grid", []))
            duration = float(event.get("dur", 0.0))
            row = groups[(name, grid)]
            row["count"] += 1
            row["total_us"] += duration
            row["min_us"] = duration if row["min_us"] is None else min(row["min_us"], duration)
            row["max_us"] = max(row["max_us"], duration)

    rows = []
    for (name, grid), row in sorted(groups.items()):
        item = {"name": name, "grid": list(grid), **row}
        item["average_us"] = item["total_us"] / item["count"]
        if name == "triton_flash_mla_sparse_fwd" and grid:
            item["inferred_sq"] = grid[0]
        elif name == "_flash_mla_sparse_splitk_stage2" and grid:
            item["inferred_sq"] = grid[0] // 8
        rows.append(item)

    result = {
        "schema_version": 1,
        "profile_id": PROFILE_ID,
        "trace": str(traces[0]),
        "rank": 0,
        "rows": rows,
        "notes": [
            "The generic/prefill kernel launches grid=(SQ,1,1).",
            "Split-K stage2 launches grid=(SQ*HQ*2,1,1), with HQ=4.",
            "Stage1 grid is SQ*NUM_SPLITS; NUM_SPLITS is 16 for SQ<=32 and 8 otherwise.",
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
