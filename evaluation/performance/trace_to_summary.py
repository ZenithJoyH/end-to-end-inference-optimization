#!/usr/bin/env python3
"""
Parse a vLLM torch profiler trace (.json.gz) and generate a summary .txt file
similar to PyTorch's profiler.key_averages().table().

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
        events = data.get("traceEvents", [])
    elif isinstance(data, list):
        events = data
    else:
        events = []

    return events


def categorize_event(event):
    """Categorize an event into CPU or CUDA based on its category."""
    cat = event.get("cat", "")
    # Common CUDA categories in PyTorch profiler traces
    if cat in ("kernel", "gpu_memcpy", "gpu_memset"):
        return "cuda"
    if "cuda" in cat.lower() or "gpu" in cat.lower():
        return "cuda"
    # Events on CUDA streams
    if "stream" in str(event.get("args", {})).lower():
        return "cuda"
    return "cpu"


def aggregate_events(events):
    """Aggregate duration events by name, separating CPU and CUDA."""
    cpu_stats = defaultdict(lambda: {"count": 0, "total_us": 0.0, "min_us": float("inf"), "max_us": 0.0})
    cuda_stats = defaultdict(lambda: {"count": 0, "total_us": 0.0, "min_us": float("inf"), "max_us": 0.0})

    for event in events:
        # Only process complete events (ph: "X") or duration events
        ph = event.get("ph", "")
        if ph not in ("X",):
            continue

        name = event.get("name", "")
        if not name:
            continue

        dur = event.get("dur", 0)  # duration in microseconds
        if dur <= 0:
            continue

        device = categorize_event(event)
        stats = cuda_stats if device == "cuda" else cpu_stats

        stats[name]["count"] += 1
        stats[name]["total_us"] += dur
        stats[name]["min_us"] = min(stats[name]["min_us"], dur)
        stats[name]["max_us"] = max(stats[name]["max_us"], dur)

    return cpu_stats, cuda_stats


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


def process_trace_file(filepath, output_path=None, row_limit=100):
    """Process a single trace file and write a summary .txt."""
    print(f"Loading: {filepath}")
    events = load_trace(filepath)
    print(f"  Total events: {len(events)}")

    cpu_stats, cuda_stats = aggregate_events(events)
    print(f"  CPU kernels: {len(cpu_stats)}, CUDA kernels: {len(cuda_stats)}")

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
    lines.append("CUDA Kernel Summary (sorted by total CUDA time)")
    lines.append("")
    lines.append(generate_table(cuda_stats, sort_by="total_us", row_limit=row_limit))

    lines.append("")
    lines.append("CPU Operation Summary (sorted by total CPU time)")
    lines.append("")
    lines.append(generate_table(cpu_stats, sort_by="total_us", row_limit=row_limit))

    # Overall stats
    total_cuda_us = sum(s["total_us"] for s in cuda_stats.values())
    total_cpu_us = sum(s["total_us"] for s in cpu_stats.values())
    total_cuda_calls = sum(s["count"] for s in cuda_stats.values())
    total_cpu_calls = sum(s["count"] for s in cpu_stats.values())

    lines.append("")
    lines.append("-" * 80)
    lines.append("Overall Statistics:")
    lines.append(f"  Total CUDA time: {format_time(total_cuda_us)} ({total_cuda_calls} calls)")
    lines.append(f"  Total CPU time:  {format_time(total_cpu_us)} ({total_cpu_calls} calls)")
    lines.append("-" * 80)

    content = "\n".join(lines) + "\n"

    with open(output_path, "w", encoding="utf-8") as f:
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
    args = parser.parse_args()

    row_limit = args.row_limit if args.row_limit > 0 else None

    if os.path.isdir(args.path):
        # Process all trace files in directory
        patterns = ["*.json.gz", "*.json"]
        files = []
        for pat in patterns:
            files.extend(glob.glob(os.path.join(args.path, pat)))

        if not files:
            print(f"No trace files found in: {args.path}")
            return

        files.sort()
        print(f"Found {len(files)} trace file(s) in {args.path}\n")

        for f in files:
            try:
                process_trace_file(f, row_limit=row_limit)
            except Exception as e:
                print(f"  ERROR processing {f}: {e}")
            print()
    else:
        # Single file
        process_trace_file(args.path, output_path=args.output, row_limit=row_limit)


if __name__ == "__main__":
    main()
