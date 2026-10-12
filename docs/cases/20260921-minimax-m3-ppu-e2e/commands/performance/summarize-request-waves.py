#!/usr/bin/env python3
"""Summarize per-request timing waves from maintained vLLM raw results."""

import json
import math
from pathlib import Path
import statistics
import sys


def percentile(values, q):
    values = sorted(values)
    index = (len(values) - 1) * q
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return values[low]
    return values[low] * (high - index) + values[high] * (index - low)


root = Path(sys.argv[1]).resolve()
pattern = sys.argv[2]
payload = {"schema_version": 1, "root": str(root), "rounds": []}
for path in sorted(root.glob(pattern)):
    raw = json.loads(path.read_text(encoding="utf-8"))
    ttfts = raw["ttfts"]
    itls = raw["itls"]
    if len(ttfts) != raw["num_prompts"] or len(itls) != raw["num_prompts"]:
        raise SystemExit(f"per-request vectors incomplete: {path}")
    request_elapsed = [ttft + sum(gaps) for ttft, gaps in zip(ttfts, itls)]
    max_gaps = [max(gaps) if gaps else 0.0 for gaps in itls]
    payload["rounds"].append(
        {
            "file": path.name,
            "duration_s": raw["duration"],
            "output_throughput": raw["output_throughput"],
            "ttft_s": {
                "p50": percentile(ttfts, 0.50),
                "p75": percentile(ttfts, 0.75),
                "p90": percentile(ttfts, 0.90),
                "p99": percentile(ttfts, 0.99),
                "max": max(ttfts),
                "over_80s": sum(value > 80 for value in ttfts),
            },
            "request_elapsed_s": {
                "p50": percentile(request_elapsed, 0.50),
                "p75": percentile(request_elapsed, 0.75),
                "p90": percentile(request_elapsed, 0.90),
                "p99": percentile(request_elapsed, 0.99),
                "max": max(request_elapsed),
            },
            "max_single_itl_s": {
                "median": statistics.median(max_gaps),
                "p90": percentile(max_gaps, 0.90),
                "p99": percentile(max_gaps, 0.99),
                "max": max(max_gaps),
            },
            "slowest_ttft_s": sorted(ttfts, reverse=True)[:16],
        }
    )
json.dump(payload, sys.stdout, indent=2, sort_keys=True)
sys.stdout.write("\n")
