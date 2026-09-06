#!/usr/bin/env python3
"""
Benchmark vLLM with official --profile flag (vllm bench serve --profile).

Usage:
 1. Start the vLLM server with --profiler-config to enable profiling:

    vllm serve /data/Qwen3.6-27B \
      --tensor-parallel-size 2 --port 8010 --trust-remote-code --dtype bfloat16 \
      --served-model-name qwen36-plugin-somegems-opt2 \
      --profiler-config '{"profiler":"torch","torch_profiler_dir":"./vllm_profile","torch_profiler_with_stack":true,"torch_profiler_record_shapes":true}'

    NOTE: --profiler-config is REQUIRED for profiling. Without it, the server
    won't register /start_profile and /stop_profile endpoints, and the
    --profile flag in vllm bench serve will fail with 404.

    profiler-config options:
      - profiler: "torch" (required)
      - torch_profiler_dir: path to save trace files (required)

 2. Run this profiling script:
    python perf_test/vllm_profile.py

    Options:
      --no-profile        Run without profiling (pure benchmark, no --profile flag)
      --profile-runs all  Profile all non-warmup runs (default: only last run)
      --profile-dir DIR   Where to look for trace files (default: ./vllm_profile)

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

MODEL = "hy3-preview-native"
TOKENIZER_PATH = "/mnt/common/models/Hy3-preview"
HOST = "127.0.0.1"
PORT = 8010
RUNS = 3
SKIP_FIRST = 2

TEST_CASES = [
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
    "peak_output_throughput": r"Peak output token throughput \(tok/s\):\s+([0-9.]+)",
    "total_token_throughput": r"Total token throughput \(tok/s\):\s+([0-9.]+)",
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
    "Num Prompts",
    "Run",
    "Successful Requests",
    "Benchmark Duration (s)",
    "Total Input Tokens",
    "Total Output Tokens",
    "Req/s",
    "Output tok/s",
    "Peak Output tok/s",
    "Total tok/s",
    "Mean TTFT (ms)",
    "Median TTFT (ms)",
    "P99 TTFT (ms)",
    "Mean TPOT (ms)",
    "Median TPOT (ms)",
    "P99 TPOT (ms)",
    "Mean ITL (ms)",
    "Median ITL (ms)",
    "P99 ITL (ms)",
]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile-dir", type=str, default="./vllm_profile",
        help="Directory where vLLM server writes profiling traces.",
    )
    parser.add_argument("--host", type=str, default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument(
        "--no-profile", action="store_true",
        help="Run benchmark without profiling (same as vllm_perf.py behavior).",
    )
    parser.add_argument(
        "--profile-runs", type=str, default="last",
        choices=["all", "last", "first"],
        help="Which non-warmup runs to profile: 'all', 'last' (default), or 'first'. "
        "Warmup runs (first SKIP_FIRST runs) are never profiled.",
    )
    return parser.parse_args()


def build_common_args(host, port):
    """Build base args for vllm bench serve."""
    return [
        "vllm", "bench", "serve",
        "--backend", "vllm",
        "--model", MODEL,
        "--tokenizer", TOKENIZER_PATH,
        "--endpoint", "/v1/completions",
        "--host", host,
        "--port", str(port),
        "--dataset-name", "random",
        "--ignore-eos",
    ]


def get_trace_files(profile_dir):
    """Get list of trace files sorted by modification time."""
    patterns = [
        os.path.join(profile_dir, "*.pt.trace.json.gz"),
        os.path.join(profile_dir, "*.pt.trace.json"),
        os.path.join(profile_dir, "*.json.gz"),
    ]
    files = []
    for pat in patterns:
        files.extend(glob.glob(pat))
    return sorted(set(files), key=os.path.getmtime)


def should_profile_run(run_id, total_runs, profile_runs_mode):
    """Determine if this run should have profiling enabled.

    Warmup runs (first SKIP_FIRST runs) are never profiled.
    For non-warmup runs, profile_runs_mode controls which ones get profiled.
    """
    if run_id <= SKIP_FIRST:
        return False

    if profile_runs_mode == "all":
        return True
    elif profile_runs_mode == "first":
        return run_id == SKIP_FIRST + 1
    else:  # "last"
        return run_id == total_runs


def extract_metrics(output_text):
    result = {}
    for key, pattern in PATTERNS.items():
        match = re.search(pattern, output_text, re.IGNORECASE)
        result[key] = float(match.group(1)) if match else None
    return result


def format_result(case, metrics, run_label=""):
    input_len, output_len, concurrency, num_prompts = case

    result = {
        "Prefill": input_len,
        "Decode": output_len,
        "Conc": concurrency,
        "Num Prompts": num_prompts,
        "Run": run_label,
        "Successful Requests": metrics.get("successful_requests"),
        "Benchmark Duration (s)": metrics.get("benchmark_duration"),
        "Total Input Tokens": metrics.get("total_input_tokens"),
        "Total Output Tokens": metrics.get("total_output_tokens"),
        "Req/s": metrics.get("request_throughput"),
        "Output tok/s": metrics.get("output_throughput"),
        "Peak Output tok/s": metrics.get("peak_output_throughput"),
        "Total tok/s": metrics.get("total_token_throughput"),
        "Mean TTFT (ms)": metrics.get("mean_ttft_ms"),
        "Median TTFT (ms)": metrics.get("median_ttft_ms"),
        "P99 TTFT (ms)": metrics.get("p99_ttft_ms"),
        "Mean TPOT (ms)": metrics.get("mean_tpot_ms"),
        "Median TPOT (ms)": metrics.get("median_tpot_ms"),
        "P99 TPOT (ms)": metrics.get("p99_tpot_ms"),
        "Mean ITL (ms)": metrics.get("mean_itl_ms"),
        "Median ITL (ms)": metrics.get("median_itl_ms"),
        "P99 ITL (ms)": metrics.get("p99_itl_ms"),
    }

    return result


def append_csv(row, filename, columns):
    file_exists = os.path.exists(filename)

    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=columns,
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


def average_metrics(results):
    avg_result = {}

    keys = results[0].keys()

    for key in keys:
        values = [r[key] for r in results if isinstance(r.get(key), (int, float))]

        if values:
            avg_result[key] = round(mean(values), 2)

    return avg_result


# ---------------------------------------------------------------------------
# Benchmark execution
# ---------------------------------------------------------------------------

def run_once(case, run_id, enable_profile, common_args):
    """Run a single benchmark. If enable_profile, append --profile to the cmd."""
    input_len, output_len, concurrency, num_prompts = case

    name = f"{input_len}_{output_len}_c{concurrency}"

    print("=" * 80)
    print(f"Running: {name} | Run {run_id}/{RUNS} | Profile: {enable_profile}")
    print("=" * 80)

    cmd = common_args + [
        "--random-input-len", str(input_len),
        "--random-output-len", str(output_len),
        "--max-concurrency", str(concurrency),
        "--num-prompts", str(num_prompts),
    ]

    # Use vllm bench serve --profile to trigger start/stop profiling automatically
    if enable_profile:
        cmd.append("--profile")

    print(" ".join(cmd))
    print()

    start_time = time.time()

    process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    elapsed = time.time() - start_time

    output = process.stdout

    print(output)

    metrics = extract_metrics(output)

    metrics["elapsed_sec"] = round(elapsed, 2)

    return metrics


def run_test_case(case, csv_file, no_profile, profile_runs, common_args):
    """Run all rounds for one test case, write per-run rows + SUMMARY to csv_file."""
    all_runs = []

    for run_id in range(1, RUNS + 1):
        enable_profile = (
            not no_profile and should_profile_run(run_id, RUNS, profile_runs)
        )

        metrics = run_once(case, run_id, enable_profile, common_args)

        expected_successful_requests = case[3]
        status = (
            "SUCCESS"
            if metrics.get("successful_requests") == expected_successful_requests
            else "FAILED"
        )

        profiled_tag = "+profile" if enable_profile else ""
        run_label = f"Run{run_id}({status}){profiled_tag}"

        raw_row = format_result(case, metrics, run_label=run_label)
        append_csv(raw_row, csv_file, CSV_COLUMNS)

        all_runs.append(metrics)

    # Compute summary from non-warmup runs
    valid_runs = all_runs[SKIP_FIRST:]

    expected_successful_requests = case[3]
    has_failed_run = any(
        run.get("successful_requests") != expected_successful_requests
        for run in valid_runs
    )

    avg_metrics = average_metrics(valid_runs)

    summary_row = format_result(case, avg_metrics, run_label="SUMMARY")
    append_csv(summary_row, csv_file, CSV_COLUMNS)

    return summary_row, has_failed_run


def print_summary(results):
    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)

    for r in results:
        print(
            f"Prefill={r['Prefill']} "
            f"Decode={r['Decode']} "
            f"Conc={r['Conc']} "
            f"NumPrompts={r['Num Prompts']} "
            f"Req/s={r['Req/s']} "
            f"Total tok/s={r['Total tok/s']} "
            f"TTFT={r['Mean TTFT (ms)']}ms"
        )


def main():
    args = parse_args()
    test_cases = TEST_CASES
    common_args = build_common_args(args.host, str(args.port))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir = os.path.join("benchmark_results", MODEL)
    os.makedirs(output_dir, exist_ok=True)

    all_summary = []

    print()
    print(f"RUNS={RUNS}")
    print(f"SKIP_FIRST={SKIP_FIRST}")
    print(f"PROFILING={'DISABLED' if args.no_profile else 'ENABLED'}")
    print(f"PROFILE_RUNS={args.profile_runs}")
    print(f"PROFILE_DIR={args.profile_dir}")
    print(f"TOTAL_CASES={len(test_cases)}")
    print(f"TEST_CASES={test_cases}")
    print()

    csv_files = []

    for case in test_cases:
        input_len, output_len, concurrency, num_prompts = case
        scenario_name = f"{input_len}in_{output_len}out_c{concurrency}_n{num_prompts}"
        csv_file = os.path.join(
            output_dir, f"{MODEL}_{scenario_name}_{timestamp}.csv"
        )

        try:
            summary_row, has_failed_run = run_test_case(
                case, csv_file,
                args.no_profile, args.profile_runs, common_args,
            )

            csv_files.append(csv_file)

            if has_failed_run:
                print(f"SKIP SUMMARY ROW (failed case): {case}")
                continue

            all_summary.append(summary_row)

        except Exception as e:
            print(f"ERROR: {e}")

    print_summary(all_summary)

    print()
    print("CSV files:")
    for f in csv_files:
        print(f"  {f}")

    if not args.no_profile:
        traces = get_trace_files(args.profile_dir)
        if traces:
            print(f"\nProfile traces ({len(traces)} files) in: {args.profile_dir}")
            for t in traces[-10:]:
                size_mb = os.path.getsize(t) / (1024 * 1024)
                print(f"  {t} ({size_mb:.1f} MB)")
            print("\nView with: https://ui.perfetto.dev/")


if __name__ == "__main__":
    main()
