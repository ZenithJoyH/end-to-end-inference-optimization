#!/usr/bin/env python3
"""Summarize vLLM periodic metrics by prompt-active versus decode-only windows."""

from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path


PATTERN = re.compile(
    r"Avg prompt throughput: (?P<prompt>[0-9.]+) tokens/s, "
    r"Avg generation throughput: (?P<generation>[0-9.]+) tokens/s, "
    r"Running: (?P<running>\d+) reqs, Waiting: (?P<waiting>\d+) reqs, "
    r"GPU KV cache usage: (?P<kv>[0-9.]+)%"
)


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("empty values")
    index = round((len(ordered) - 1) * fraction)
    return ordered[index]


def summarize(rows: list[dict[str, float]]) -> dict[str, float | int]:
    generations = [row["generation"] for row in rows]
    prompts = [row["prompt"] for row in rows]
    kv = [row["kv"] for row in rows]
    return {
        "windows": len(rows),
        "prompt_throughput_mean": round(statistics.fmean(prompts), 3),
        "generation_throughput_mean": round(statistics.fmean(generations), 3),
        "generation_throughput_median": round(statistics.median(generations), 3),
        "generation_throughput_p10": round(percentile(generations, 0.10), 3),
        "generation_throughput_p90": round(percentile(generations, 0.90), 3),
        "kv_usage_mean_pct": round(statistics.fmean(kv), 3),
        "kv_usage_max_pct": round(max(kv), 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    rows: list[dict[str, float]] = []
    for line in args.log.read_text(encoding="utf-8", errors="replace").splitlines():
        match = PATTERN.search(line)
        if match:
            rows.append({name: float(value) for name, value in match.groupdict().items()})
    if not rows:
        raise SystemExit("no periodic metric rows found")

    groups = {
        "all": rows,
        "prompt_active": [row for row in rows if row["prompt"] > 0],
        "decode_only": [row for row in rows if row["prompt"] == 0 and row["generation"] > 0],
    }
    result = {
        "schema_version": 1,
        "source": str(args.log),
        "groups": {name: summarize(group) for name, group in groups.items() if group},
    }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
