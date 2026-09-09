#!/usr/bin/env python3
"""
Parse a vLLM torch profiler trace (.json.gz) and generate a summary .txt file
with cumulative event durations (not self time or elapsed device busy time).

Usage:
    python perf_test/trace_to_summary.py ./vllm_profile/trace.json.gz
    python perf_test/trace_to_summary.py ./vllm_profile/  # process all .gz files in dir

Output:
    For each .json.gz file, generates a corresponding .txt summary file
    in the same directory.
"""

import argparse
import gzip
import json
import os
import glob
import math
from pathlib import Path
from collections import defaultdict


def load_trace(filepath):
    """Load a Chrome trace JSON file (supports .json.gz and .json)."""
    if filepath.endswith(".gz"):
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            data = json.load(f)
    else:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

    # Chrome trace format: either {"traceEvents": [...]} or just [...]
    if isinstance(data, dict):
        events = data.get("traceEvents")
    elif isinstance(data, list):
        events = data
    else:
        events = None

    if not isinstance(events, list) or any(not isinstance(event, dict) for event in events):
        raise ValueError("trace must contain a list of event objects")
    return events


DEVICE_CATEGORIES = frozenset(("kernel", "gpu_memcpy", "gpu_memset"))
CPU_CATEGORIES = frozenset(("cpu_op", "user_annotation", "python_function", "cuda_runtime", "cuda_driver"))


def categorize_event(event, device_categories=DEVICE_CATEGORIES):
    """Runtime launch/sync APIs execute on CPU, even when args name a stream.

    Unknown platform categories remain unclassified until explicitly mapped.
    """
    categories = {part.strip() for part in str(event.get("cat", "")).split(",")}
    if categories & CPU_CATEGORIES:
        return "cpu"
    if categories & set(device_categories):
        return "device"
    return "unclassified"


def aggregate_events(events, device_categories=DEVICE_CATEGORIES):
    def bucket():
        return defaultdict(lambda: {"count": 0, "total_us": 0.0, "min_us": float("inf"), "max_us": 0.0})
    groups = {key: bucket() for key in ("cpu", "device", "unclassified")}
    for event in events:
        if event.get("ph") != "X":
            continue
        name = event.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("complete trace event has no name")
        dur = event.get("dur")
        if type(dur) not in (int, float) or not math.isfinite(dur) or dur < 0:
            raise ValueError(f"event {name!r} has invalid duration")
        if dur == 0:
            continue
        stats = groups[categorize_event(event, device_categories)][name]
        stats["count"] += 1
        stats["total_us"] += dur
        stats["min_us"] = min(stats["min_us"], dur)
        stats["max_us"] = max(stats["max_us"], dur)
    if not any(groups.values()):
        raise ValueError("trace contains no positive-duration complete events")
    return groups["cpu"], groups["device"], groups["unclassified"]


def format_time(us):
    """Format microseconds to a human-readable string."""
    if us >= 1_000_000:
        return f"{us / 1_000_000:.3f}s"
    elif us >= 1_000:
        return f"{us / 1_000:.3f}ms"
    else:
        return f"{us:.3f}us"


def generate_table(stats, sort_by="total_us", row_limit=100):
    """Generate a formatted table from aggregated stats."""
    if not stats:
        return "  (no events)\n"

    # Sort by total time descending
    sorted_items = sorted(stats.items(), key=lambda x: x[1][sort_by], reverse=True)
    if row_limit:
        sorted_items = sorted_items[:row_limit]

    # Calculate column widths
    name_width = max(len(name) for name, _ in sorted_items)
    name_width = max(name_width, 4)  # minimum "Name"
    name_width = min(name_width, 80)  # cap at 80

    header = (
        f"{'Name':<{name_width}}  "
        f"{'Calls':>8}  "
        f"{'Total':>12}  "
        f"{'Avg':>12}  "
        f"{'Min':>12}  "
        f"{'Max':>12}"
    )
    separator = "-" * len(header)

    lines = [separator, header, separator]

    for name, s in sorted_items:
        avg_us = s["total_us"] / s["count"] if s["count"] > 0 else 0
        display_name = name[:name_width] if len(name) > name_width else name
        line = (
            f"{display_name:<{name_width}}  "
            f"{s['count']:>8}  "
            f"{format_time(s['total_us']):>12}  "
            f"{format_time(avg_us):>12}  "
            f"{format_time(s['min_us']):>12}  "
            f"{format_time(s['max_us']):>12}"
        )
        lines.append(line)

    lines.append(separator)
    lines.append(f"Total entries: {len(stats)}, showing top {len(sorted_items)}")
    return "\n".join(lines) + "\n"


def process_trace_file(filepath, output_path=None, row_limit=100, device_categories=DEVICE_CATEGORIES):
    """Process a single trace file and write a summary .txt."""
    print(f"Loading: {filepath}")
    events = load_trace(filepath)
    print(f"  Total events: {len(events)}")

    cpu_stats, cuda_stats, unknown_stats = aggregate_events(events, device_categories)
    print(f"  CPU activities: {len(cpu_stats)}, device activities: {len(cuda_stats)}, unclassified: {len(unknown_stats)}")

    # Determine output path
    if output_path is None:
        base = filepath
        for ext in (".json.gz", ".gz", ".json"):
            if base.endswith(ext):
                base = base[: -len(ext)]
                break
        output_path = base + "_summary.txt"

    # Generate summary
    lines = []
    lines.append("=" * 80)
    lines.append(f"Trace Summary: {os.path.basename(filepath)}")
    lines.append(f"Total events parsed: {len(events)}")
    lines.append("=" * 80)

    lines.append("")
    lines.append("Device Activity Summary (cumulative durations)")
    lines.append("")
    lines.append(generate_table(cuda_stats, sort_by="total_us", row_limit=row_limit))

    lines.append("")
    lines.append("CPU Activity Summary (inclusive durations)")
    lines.append("")
    lines.append(generate_table(cpu_stats, sort_by="total_us", row_limit=row_limit))

    lines.append("\nUnclassified Activity Summary (supply --device-category only after verifying platform semantics)")
    lines.append(generate_table(unknown_stats, sort_by="total_us", row_limit=row_limit))
    lines.append("Durations are sums of events, may overlap across streams/threads or nesting, and are not elapsed/self time.")

    # Overall stats
    total_cuda_us = sum(s["total_us"] for s in cuda_stats.values())
    total_cpu_us = sum(s["total_us"] for s in cpu_stats.values())
    total_cuda_calls = sum(s["count"] for s in cuda_stats.values())
    total_cpu_calls = sum(s["count"] for s in cpu_stats.values())

    lines.append("")
    lines.append("-" * 80)
    lines.append("Overall Statistics:")
    lines.append(f"  Summed device time: {format_time(total_cuda_us)} ({total_cuda_calls} calls)")
    lines.append(f"  Summed CPU time:  {format_time(total_cpu_us)} ({total_cpu_calls} calls)")
    lines.append("-" * 80)

    content = "\n".join(lines) + "\n"

    with open(output_path, "x", encoding="utf-8") as f:
        f.write(content)

    print(f"  Summary written to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate summary .txt from vLLM torch profiler trace files"
    )
    parser.add_argument(
        "path",
        help="Path to a .json.gz trace file or a directory containing trace files",
    )
    parser.add_argument(
        "--row-limit",
        type=int,
        default=100,
        help="Max rows per table (default: 100, 0 for unlimited)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output .txt path (only for single file input)",
    )
    parser.add_argument("--device-category", action="append", default=[], help="Additional verified device event category")
    args = parser.parse_args()
    if args.row_limit < 0:
        parser.error("row-limit must be nonnegative")
    if set(args.device_category) & CPU_CATEGORIES:
        parser.error("known CPU runtime categories cannot be reclassified as device execution")
    device_categories = DEVICE_CATEGORIES | set(args.device_category)

    row_limit = args.row_limit if args.row_limit > 0 else None

    if os.path.isdir(args.path):
        if args.output:
            parser.error("--output is only valid for a single input file")
        # Process all trace files in directory
        patterns = ["*.json.gz", "*.json"]
        files = []
        for pat in patterns:
            files.extend(glob.glob(os.path.join(args.path, pat)))

        if not files:
            print(f"No trace files found in: {args.path}")
            raise SystemExit(1)

        files.sort()
        print(f"Found {len(files)} trace file(s) in {args.path}\n")

        failed = False
        for f in files:
            try:
                process_trace_file(f, row_limit=row_limit, device_categories=device_categories)
            except Exception as e:
                failed = True
                print(f"  ERROR processing {f}: {e}")
            print()
        if failed:
            raise SystemExit(1)
    else:
        # Single file
        process_trace_file(args.path, output_path=args.output, row_limit=row_limit, device_categories=device_categories)


if __name__ == "__main__":
    main()
