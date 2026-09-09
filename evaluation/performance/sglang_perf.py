#!/usr/bin/env python3

"""Parameterized diagnostic SGLang benchmark; not a formal accuracy gate.

Native format: sgl-project/sglang v0.5.11, python/sglang/bench_serving.py.
The maintained workload uses fixed random lengths, infinite arrival rate and
an explicit concurrency cap. Original imported scripts remain under test/.
"""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vllm_perf

HOST = "127.0.0.1"
PORT = 30000
RUNS = 3
SKIP_FIRST = 1
COMMON_ARGS = None  # Callers must supply an explicit target.


def build_common_args(args):
    return [sys.executable, "-m", "sglang.bench_serving", "--backend", "sglang",
            "--model", args.model, "--tokenizer", args.tokenizer,
            "--host", args.host, "--port", str(args.port), "--dataset-name", "random",
            "--random-range-ratio", "0", "--request-rate", "inf",
            "--seed", str(args.seed)]


DEFAULT_TEST_CASES = [
    (1024, 1024, 64, 128),
    # (4096, 1024, 64, 128),
    # (16384, 1024, 64, 128),
    # (32768, 1024, 64, 128),
    # (65536, 1024, 64, 128),
]

ALL_TEST_CASES = [
    *DEFAULT_TEST_CASES,
    (4096, 1024, 1, 256),
    (4096, 1024, 4, 256),
    (4096, 1024, 16, 256),
    (4096, 1024, 256, 256),
    (131072, 1024, 64, 64),
    (262144, 1024, 64, 64),
]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default="benchmark_results")
    parser.add_argument("--timeout", type=float, default=3600)
    parser.add_argument("--enable-all", action="store_true", help="Run the extended diagnostic matrix")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not 0 < args.port <= 65535 or not 0 <= args.seed < 2**32 or not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("invalid port, seed or timeout")
    return args


PATTERNS = {
    "failed_requests": r"Failed requests:\s+([0-9.]+)",
    "successful_requests": r"Successful requests:\s+([0-9.]+)",
    "benchmark_duration": r"Benchmark duration \(s\):\s+([0-9.]+)",
    "total_input_tokens": r"Total input tokens:\s+([0-9.]+)",
    "total_output_tokens": r"Total generated tokens:\s+([0-9.]+)",
    "request_throughput": r"Request throughput \(req/s\):\s+([0-9.]+)",
    "output_throughput": r"Output token throughput \(tok/s\):\s+([0-9.]+)",
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
    "mean_e2el_ms": r"Mean E2EL \(ms\):\s+([0-9.]+)",
    "median_e2el_ms": r"Median E2EL \(ms\):\s+([0-9.]+)",
    "p99_e2el_ms": r"P99 E2EL \(ms\):\s+([0-9.]+)",
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
    "Mean E2EL (ms)",
    "Median E2EL (ms)",
    "P99 E2EL (ms)",
]


def extract_metrics(output_text):
    result = {}
    for key, pattern in PATTERNS.items():
        match = re.search(pattern, output_text, re.IGNORECASE)
        result[key] = float(match.group(1)) if match else None
    return result


def save_error_log(cmd, case, run_id, stdout, stderr, returncode, output_dir):
    """当测试出现服务端报错时，保存完整的请求信息到错误日志文件"""
    error_log_dir = os.path.join(output_dir, "error_logs")
    os.makedirs(error_log_dir, exist_ok=True)
    input_len, output_len, concurrency, num_prompts = case
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
    filename = f"error_in{input_len}_out{output_len}_c{concurrency}_run{run_id}_{timestamp}.json"
    filepath = os.path.join(error_log_dir, filename)
    error_record = {
        "timestamp": datetime.now().isoformat(),
        "request_params": {
            "input_len": input_len,
            "output_len": output_len,
            "concurrency": concurrency,
            "num_prompts": num_prompts,
            "run_id": run_id,
        },
        "command": " ".join(cmd),
        "command_list": cmd,
        "returncode": returncode,
        "stdout": stdout,
        "stderr": stderr,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(error_record, f, ensure_ascii=False, indent=2)
    print(f"[ERROR LOG] saved to: {filepath}")


def format_result(case, metrics, run_label=""):
    input_len, output_len, concurrency, num_prompts = case
    return {
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
        "Mean E2EL (ms)": metrics.get("mean_e2el_ms"),
        "Median E2EL (ms)": metrics.get("median_e2el_ms"),
        "P99 E2EL (ms)": metrics.get("p99_e2el_ms"),
    }


def append_csv(row, filename, columns):
    file_exists = os.path.exists(filename)
    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def build_round_command(case, run_id, common_args, raw_path):
    input_len, output_len, concurrency, num_prompts = case
    if any(type(x) is not int or x <= 0 for x in case) or output_len <= 1:
        raise ValueError("diagnostic cases require positive integers and output length > 1")
    if not common_args:
        raise ValueError("explicit model/tokenizer/host command is required")
    cmd = list(common_args)
    if "--seed" in cmd:
        index = cmd.index("--seed") + 1
        seed = int(cmd[index]) + input_len * 10 + concurrency * 1000 + run_id
        if not 0 <= seed < 2**32:
            raise ValueError("derived seed is outside the client range")
        cmd[index] = str(seed)
    return cmd + ["--random-input-len", str(input_len), "--random-output-len", str(output_len),
                  "--max-concurrency", str(concurrency), "--num-prompts", str(num_prompts),
                  "--output-file", str(raw_path), "--output-details"]


def validate_result(case, raw, stdout):
    if not isinstance(raw, dict):
        return {}, {"schema": "unknown", "errors": ["native SGLang result must be an object"]}
    inputs = raw.get("input_lens")
    adapted = dict(raw)
    # SGLang has no num_prompts field; derive it from independently saved
    # per-request inputs, never from the requested case or success counter.
    adapted["num_prompts"] = len(inputs) if isinstance(inputs, list) else None
    adapted["total_token_throughput"] = raw.get("total_throughput")
    metrics, validation = vllm_perf.validate_native_result(case, adapted, vllm_perf.extract_metrics(stdout))
    validation["schema"] = "sglang_detailed_v0.5.11"
    for key, expected in (("backend", "sglang"), ("dataset_name", "random"),
                          ("random_input_len", case[0]), ("random_output_len", case[1]),
                          ("random_range_ratio", 0), ("max_concurrency", case[2])):
        if isinstance(raw.get(key), bool) or raw.get(key) != expected:
            validation["errors"].append(f"native {key} differs from the requested workload")
    if raw.get("request_rate") != float("inf"):
        validation["errors"].append("native request_rate differs from finite-batch inf arrival")
    if (not isinstance(inputs, list) or len(inputs) != case[3]
            or any(type(n) is not int or n != case[0] for n in inputs)):
        validation["errors"].append("native input_lens differ from fixed input length")
    for stat in ("mean", "median", "p99"):
        key = f"{stat}_e2e_latency_ms"
        value = raw.get(key)
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            validation["errors"].append(f"missing or invalid native {key}")
        metrics[f"{stat}_e2el_ms"] = value
    return metrics, validation


def run_once(case, run_id, output_dir, common_args=None, timeout_s=3600):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / f"p{case[0]}-d{case[1]}-c{case[2]}-r{run_id}-{uuid.uuid4().hex}.jsonl"
    cmd = build_round_command(case, run_id, common_args or COMMON_ARGS, raw_path)
    start = time.monotonic()
    def as_text(value):
        return value.decode(errors="replace") if isinstance(value, bytes) else value or ""
    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as exc:
        process = subprocess.CompletedProcess(cmd, 124, as_text(exc.stdout), as_text(exc.stderr) + "\nbenchmark timed out")
    except OSError as exc:
        process = subprocess.CompletedProcess(cmd, 127, "", str(exc))
    print(process.stdout)
    raw, raw_error = {}, None
    try:
        lines = [line for line in raw_path.read_text().splitlines() if line.strip()]
        if len(lines) != 1:
            raise ValueError("expected exactly one native JSONL result")
        def unique_pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    raise ValueError(f"duplicate native JSON key: {key}")
                result[key] = value
            return result
        raw = json.loads(lines[0], object_pairs_hook=unique_pairs)
    except (OSError, ValueError) as exc:
        raw_error = str(exc)
    metrics, validation = validate_result(case, raw, process.stdout)
    if raw_error:
        validation["errors"].append(raw_error)
    if process.returncode != 0:
        validation["errors"].append(f"benchmark exited with status {process.returncode}")
    metrics.update(elapsed_sec=time.monotonic()-start, returncode=process.returncode,
                   valid=not validation["errors"])
    # Preserve successful output as well: profiling acknowledgement is evidence,
    # and native JSON alone cannot explain an export/start/stop failure.
    evidence = dict(command=cmd, returncode=process.returncode, valid=metrics["valid"],
                    raw_result=str(raw_path), stdout=process.stdout, stderr=process.stderr, **validation)
    with raw_path.with_suffix(".validation.json").open("x") as stream:
        json.dump(evidence, stream, indent=2, allow_nan=False)
    if not metrics["valid"]:
        save_error_log(cmd, case, run_id, process.stdout, process.stderr, process.returncode, str(output_dir))
    return metrics


def average_metrics(results):
    avg_result = {}
    if not results or any(not r.get("valid") for r in results):
        raise ValueError("Cannot aggregate incomplete or failed rounds")
    keys = results[0].keys()
    for key in keys:
        if key in ("returncode", "valid"):
            continue
        values = [r[key] for r in results if isinstance(r.get(key), (int, float))]
        # Missing metrics stay unavailable; do not report a mean from fewer rounds.
        avg_result[key] = round(mean(values), 2) if len(values) == len(results) else None
    return avg_result


def run_test_case(case, csv_file, output_dir, common_args=None, timeout_s=3600):
    all_runs = []

    for run_id in range(1, RUNS + 1):
        metrics = run_once(case, run_id, output_dir, common_args, timeout_s=timeout_s)

        expected_successful_requests = case[3]
        status = (
            "SUCCESS"
            if metrics.get("valid") is True
            else "FAILED"
        )

        raw_row = format_result(case, metrics, run_label=f"Run{run_id}({status})")
        append_csv(raw_row, csv_file, CSV_COLUMNS)

        all_runs.append(metrics)

    valid_runs = all_runs[SKIP_FIRST:]

    expected_successful_requests = case[3]
    # A failed warmup also invalidates the case; never average surviving rounds.
    has_failed_run = any(run.get("valid") is not True for run in all_runs)
    if has_failed_run or not valid_runs:
        return None, True

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

    test_cases = ALL_TEST_CASES if args.enable_all else DEFAULT_TEST_CASES

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]

    model_label = re.sub(r"[^A-Za-z0-9_.-]+", "_", args.model).strip("_") or "model"
    output_dir = os.path.join(args.output_dir, model_label, timestamp)
    common_args = build_common_args(args)
    if args.dry_run:
        for case in test_cases:
            for run_id in range(1, RUNS + 1):
                print(json.dumps(build_round_command(case, run_id, common_args, Path(output_dir) / f"round-{run_id}.jsonl")))
        return
    os.makedirs(output_dir, exist_ok=True)

    all_summary = []
    failed_cases = []

    print()
    print(f"RUNS={RUNS}")
    print(f"SKIP_FIRST={SKIP_FIRST}")
    print(f"ENABLE_ALL={args.enable_all}")
    print(f"TOTAL_CASES={len(test_cases)}")
    print(f"TEST_CASES={test_cases}")
    print()

    csv_files = []

    for case in test_cases:
        input_len, output_len, concurrency, num_prompts = case
        scenario_name = f"{input_len}in_{output_len}out_c{concurrency}_n{num_prompts}"
        csv_file = os.path.join(
            output_dir, f"{model_label}_{scenario_name}_{timestamp}.csv"
        )

        try:
            summary_row, has_failed_run = run_test_case(
                case,
                csv_file,
                output_dir, common_args, timeout_s=args.timeout,
            )

            csv_files.append(csv_file)

            if has_failed_run:
                failed_cases.append(case)
                print(f"SKIP SUMMARY ROW (failed case): {case}")
                continue

            all_summary.append(summary_row)

        except Exception as e:
            failed_cases.append(case)
            print(f"ERROR: {e}")

    print_summary(all_summary)

    print()
    print("CSV files:")
    for f in csv_files:
        print(f"  {f}")

    if failed_cases or not all_summary:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
