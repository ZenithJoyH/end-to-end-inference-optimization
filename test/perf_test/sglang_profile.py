#!/usr/bin/env python3
"""
Benchmark SGLang (v0.5.11) with profiling via bench_serving --profile.

Profiling mechanism:
  - Set SGLANG_TORCH_PROFILER_DIR env var to specify trace output directory.
  - The env var must be set BEFORE the server starts (read at server init).
  - bench_serving --profile triggers the server to start/stop torch profiling
    around the benchmark run automatically.

Usage:
 1. Set the trace output directory and start the SGLang server:

    export SGLANG_TORCH_PROFILER_DIR=./sglang_profile

    python -m sglang.launch_server \
      --model-path /data/Qwen3.6-27B \
      --tp 2 --port 30000 --trust-remote-code --dtype bfloat16 \
      --served-model-name qwen36-plugin-somegems-opt2

    NOTE: SGLANG_TORCH_PROFILER_DIR must be set in the server's environment.
    Without it, --profile in bench_serving will have no effect.

 2. Run this profiling script:
    python perf_test/sglang_profile.py

    Options:
      --no-profile        Run without profiling (pure benchmark, no --profile flag)
      --profile-runs all  Profile all non-warmup runs (default: only last run)
      --profile-dir DIR   Where trace files are saved (default: ./sglang_profile)

 3. View traces in Perfetto UI (https://ui.perfetto.dev/) or chrome://tracing
"""

import argparse
import csv
import glob
import os
import re
import subprocess
import time
from datetime import datetime
from statistics import mean

MODEL = "minicpm-sglang-profile"
TOKENIZER_PATH = "/data/jinghao/minicpm5-2.6/MiniCPM5-2.6B-0426_job_327123_step_24000_fusion_think_512k"
SHAREGPT_PATH = "/data/jinghao/minicpm5-2.6/ShareGPT_V3_unfiltered_cleaned_split.json"
HOST = "127.0.0.1"
PORT = 8000
RUNS = 2
SKIP_FIRST = 1

TEST_CASES = [
    # (input_len, output_len, concurrency, num_prompts)
    # (1024, 1024, 64, 64),
    (4096, 1024, 64, 64),
    # (16384, 1024, 64, 64),
    # (32768, 1024, 64, 64),
    # (65536, 1024, 64, 64),
]

PATTERNS = {
    "successful_requests": r"Successful requests:\s+([0-9.]+)",
    "benchmark_duration": r"Benchmark duration \(s\):\s+([0-9.]+)",
    "total_input_tokens": r"Total input tokens:\s+([0-9.]+)",
    "total_output_tokens": r"Total generated tokens:\s+([0-9.]+)",
    "request_throughput": r"Request throughput \(req/s\):\s+([0-9.]+)",
    "output_throughput": r"Output token throughput \(tok/s\):\s+([0-9.]+)",
    "total_token_throughput": r"Total [Tt]oken throughput \(tok/s\):\s+([0-9.]+)",
    "mean_ttft_ms": r"Mean TTFT \(ms\):\s+([0-9.]+)",
    "median_ttft_ms": r"Median TTFT \(ms\):\s+([0-9.]+)",
    "p99_ttft_ms": r"P99 TTFT \(ms\):\s+([0-9.]+)",
    "mean_tpot_ms": r"Mean TPOT \(ms\):\s+([0-9.]+)",
    "median_tpot_ms": r"Median TPOT \(ms\):\s+([0-9.]+)",
    "p99_tpot_ms": r"P99 TPOT \(ms\):\s+([0-9.]+)",
    "mean_itl_ms": r"Mean ITL \(ms\):\s+([0-9.]+)",
    "median_itl_ms": r"Median ITL \(ms\):\s+([0-9.]+)",
    "p99_itl_ms": r"P99 ITL \(ms\):\s+([0-9.]+)",
}

CSV_COLUMNS = [
    "Prefill",
    "Decode",
    "Conc",
    "NumPrompts",
    "Run",
    "Profiled",
    "Duration(s)",
    "OutputThroughput(tok/s)",
    "TotalThroughput(tok/s)",
    "MeanTTFT(ms)",
    "MedianTTFT(ms)",
    "P99TTFT(ms)",
    "MeanTPOT(ms)",
    "MedianTPOT(ms)",
    "P99TPOT(ms)",
    "MeanITL(ms)",
    "MedianITL(ms)",
    "P99ITL(ms)",
]

SUMMARY_COLUMNS = [
    "Prefill",
    "Decode",
    "Conc",
    "NumPrompts",
    "AvgDuration(s)",
    "AvgOutputThroughput(tok/s)",
    "AvgTotalThroughput(tok/s)",
    "AvgMeanTTFT(ms)",
    "AvgP99TTFT(ms)",
    "AvgMeanTPOT(ms)",
    "AvgP99TPOT(ms)",
    "AvgMeanITL(ms)",
    "AvgP99ITL(ms)",
]


def get_trace_files(profile_dir):
    """Find all trace files in the profile directory."""
    patterns = [
        os.path.join(profile_dir, "**", "*.json"),
        os.path.join(profile_dir, "**", "*.json.gz"),
        os.path.join(profile_dir, "**", "*.pt.trace.json"),
    ]
    files = []
    for pat in patterns:
        files.extend(glob.glob(pat, recursive=True))
    return sorted(set(files))


def build_bench_cmd(input_len, output_len, concurrency, num_prompts, profile=False):
    """Build the sglang.bench_serving command.

    When profile=True, appends --profile which triggers the server to
    start/stop torch profiling around the benchmark run.
    Traces are saved to SGLANG_TORCH_PROFILER_DIR (set in server env).
    """
    cmd = [
        "python3", "-m", "sglang.bench_serving",
        "--backend", "sglang",
        "--model", MODEL,
        "--tokenizer", TOKENIZER_PATH,
        "--host", HOST,
        "--port", str(PORT),
        "--dataset-name", "random",
        "--dataset-path", SHAREGPT_PATH,
        "--random-input-len", str(input_len),
        "--random-output-len", str(output_len),
        "--num-prompts", str(num_prompts),
        "--request-rate", str(concurrency),
    ]
    if profile:
        cmd.append("--profile")
    return cmd


def parse_output(output):
    """Parse benchmark output and extract metrics."""
    metrics = {}
    for key, pattern in PATTERNS.items():
        m = re.search(pattern, output)
        if m:
            metrics[key] = float(m.group(1))
    return metrics


def run_single_benchmark(cmd, run_idx, total_runs, profiled_flag):
    """Run a single benchmark iteration. Profiling is controlled by --profile in cmd."""
    print(f"  Run {run_idx}/{total_runs} (profile={'ON' if profiled_flag else 'OFF'})...")
    print(f"  CMD: {' '.join(cmd)}")

    start_time = time.time()
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=1800
    )
    elapsed = time.time() - start_time

    output = result.stdout + result.stderr
    print(f"  Completed in {elapsed:.1f}s (exit code: {result.returncode})")

    if result.returncode != 0:
        print(f"  STDERR (last 500 chars): ...{output[-500:]}")
        return None, profiled_flag

    metrics = parse_output(output)
    if not metrics:
        print(f"  WARNING: No metrics parsed from output")
        print(f"  OUTPUT (last 1000 chars): ...{output[-1000:]}")
        return None, profiled_flag

    return metrics, profiled_flag


def run_test_case(case, csv_file, no_profile, profile_runs):
    """Run all iterations for a single test case."""
    input_len, output_len, concurrency, num_prompts = case
    scenario = f"{input_len}in_{output_len}out_c{concurrency}_n{num_prompts}"
    print(f"\n{'='*70}")
    print(f"Test Case: {scenario}")
    print(f"{'='*70}")

    all_rows = []
    valid_rows = []
    has_failed_run = False

    for run_idx in range(1, RUNS + 1):
        # Determine if this run should be profiled
        if no_profile:
            profile_this_run = False
        elif profile_runs == "all":
            profile_this_run = (run_idx > SKIP_FIRST)
        else:
            # Default: only profile the last run
            profile_this_run = (run_idx == RUNS)

        cmd = build_bench_cmd(
            input_len, output_len, concurrency, num_prompts,
            profile=profile_this_run,
        )

        metrics, profiled = run_single_benchmark(
            cmd, run_idx, RUNS, profile_this_run
        )

        if metrics is None:
            has_failed_run = True
            row = {
                "Prefill": input_len,
                "Decode": output_len,
                "Conc": concurrency,
                "NumPrompts": num_prompts,
                "Run": run_idx,
                "Profiled": "FAILED",
            }
            all_rows.append(row)
            continue

        row = {
            "Prefill": input_len,
            "Decode": output_len,
            "Conc": concurrency,
            "NumPrompts": num_prompts,
            "Run": run_idx,
            "Profiled": "YES" if profiled else "NO",
            "Duration(s)": f"{metrics.get('benchmark_duration', 0):.2f}",
            "OutputThroughput(tok/s)": f"{metrics.get('output_throughput', 0):.2f}",
            "TotalThroughput(tok/s)": f"{metrics.get('total_token_throughput', 0):.2f}",
            "MeanTTFT(ms)": f"{metrics.get('mean_ttft_ms', 0):.2f}",
            "MedianTTFT(ms)": f"{metrics.get('median_ttft_ms', 0):.2f}",
            "P99TTFT(ms)": f"{metrics.get('p99_ttft_ms', 0):.2f}",
            "MeanTPOT(ms)": f"{metrics.get('mean_tpot_ms', 0):.2f}",
            "MedianTPOT(ms)": f"{metrics.get('median_tpot_ms', 0):.2f}",
            "P99TPOT(ms)": f"{metrics.get('p99_tpot_ms', 0):.2f}",
            "MeanITL(ms)": f"{metrics.get('mean_itl_ms', 0):.2f}",
            "MedianITL(ms)": f"{metrics.get('median_itl_ms', 0):.2f}",
            "P99ITL(ms)": f"{metrics.get('p99_itl_ms', 0):.2f}",
        }
        all_rows.append(row)

        # Only count non-warmup runs for summary
        if run_idx > SKIP_FIRST:
            valid_rows.append(metrics)

    # Write CSV
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)
    print(f"  CSV saved: {csv_file}")

    # Compute summary from valid (non-warmup) runs
    if not valid_rows:
        return None, has_failed_run

    def safe_mean(rows, key):
        vals = [r[key] for r in rows if key in r]
        return mean(vals) if vals else 0.0

    summary_row = {
        "Prefill": input_len,
        "Decode": output_len,
        "Conc": concurrency,
        "NumPrompts": num_prompts,
        "AvgDuration(s)": f"{safe_mean(valid_rows, 'benchmark_duration'):.2f}",
        "AvgOutputThroughput(tok/s)": f"{safe_mean(valid_rows, 'output_throughput'):.2f}",
        "AvgTotalThroughput(tok/s)": f"{safe_mean(valid_rows, 'total_token_throughput'):.2f}",
        "AvgMeanTTFT(ms)": f"{safe_mean(valid_rows, 'mean_ttft_ms'):.2f}",
        "AvgP99TTFT(ms)": f"{safe_mean(valid_rows, 'p99_ttft_ms'):.2f}",
        "AvgMeanTPOT(ms)": f"{safe_mean(valid_rows, 'mean_tpot_ms'):.2f}",
        "AvgP99TPOT(ms)": f"{safe_mean(valid_rows, 'p99_tpot_ms'):.2f}",
        "AvgMeanITL(ms)": f"{safe_mean(valid_rows, 'mean_itl_ms'):.2f}",
        "AvgP99ITL(ms)": f"{safe_mean(valid_rows, 'p99_itl_ms'):.2f}",
    }

    return summary_row, has_failed_run


def print_summary(all_summary):
    """Print a formatted summary table."""
    if not all_summary:
        print("\nNo valid summary data.")
        return

    print(f"\n{'='*70}")
    print("SUMMARY (averaged over non-warmup runs)")
    print(f"{'='*70}")

    # Print header
    header = " | ".join(f"{col:>20s}" for col in SUMMARY_COLUMNS)
    print(header)
    print("-" * len(header))

    for row in all_summary:
        line = " | ".join(f"{str(row.get(col, '')):>20s}" for col in SUMMARY_COLUMNS)
        print(line)


def parse_script_args():
    parser = argparse.ArgumentParser(
        description="Benchmark SGLang with profiling support"
    )
    parser.add_argument(
        "--no-profile",
        action="store_true",
        help="Run without profiling (pure benchmark)",
    )
    parser.add_argument(
        "--profile-runs",
        choices=["last", "all"],
        default="last",
        help="Which runs to profile: 'last' (default) or 'all' non-warmup runs",
    )
    parser.add_argument(
        "--profile-dir",
        default="./sglang_profile",
        help="Directory for profile trace output (default: ./sglang_profile)",
    )
    parser.add_argument(
        "--host",
        default=HOST,
        help=f"Server host (default: {HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=PORT,
        help=f"Server port (default: {PORT})",
    )
    return parser.parse_args()


def main():
    args = parse_script_args()

    global HOST, PORT
    HOST = args.host
    PORT = args.port

    profile_dir = os.path.abspath(args.profile_dir)
    if not args.no_profile:
        os.makedirs(profile_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("benchmark_results", f"sglang_profile_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    print(f"SGLang Profile Benchmark")
    print(f"  Model: {MODEL}")
    print(f"  Server: {HOST}:{PORT}")
    print(f"  Runs per case: {RUNS} (skip first {SKIP_FIRST} as warmup)")
    print(f"  Profiling: {'DISABLED' if args.no_profile else 'ENABLED'}")
    if not args.no_profile:
        print(f"  Profile runs: {args.profile_runs}")
        print(f"  Profile dir: {profile_dir}")
    print(f"  Output dir: {output_dir}")
    print(f"  Test cases: {len(TEST_CASES)}")
    print()

    all_summary = []
    csv_files = []

    for case in TEST_CASES:
        input_len, output_len, concurrency, num_prompts = case
        scenario_name = f"{input_len}in_{output_len}out_c{concurrency}_n{num_prompts}"
        csv_file = os.path.join(
            output_dir, f"sglang_{scenario_name}_{timestamp}.csv"
        )

        try:
            summary_row, has_failed_run = run_test_case(
                case, csv_file,
                args.no_profile, args.profile_runs,
            )

            csv_files.append(csv_file)

            if has_failed_run:
                print(f"SKIP SUMMARY ROW (failed case): {case}")
                continue

            if summary_row:
                all_summary.append(summary_row)

        except Exception as e:
            print(f"ERROR: {e}")

    print_summary(all_summary)

    print()
    print("CSV files:")
    for f in csv_files:
        print(f"  {f}")

    if not args.no_profile:
        traces = get_trace_files(profile_dir)
        if traces:
            print(f"\nProfile traces ({len(traces)} files) in: {profile_dir}")
            for t in traces[-10:]:
                size_mb = os.path.getsize(t) / (1024 * 1024)
                print(f"  {t} ({size_mb:.1f} MB)")
            print("\nView with: https://ui.perfetto.dev/")


if __name__ == "__main__":
    main()
