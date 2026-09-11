#!/usr/bin/env python3

# Usage:
#  1. Start the server as follows (adjust model path and args as needed):
# vllm serve /models/Qwen3.6-27B --tensor-parallel-size 2 --max-model-len 262144 --no-enable-prefix-caching

#  2. Run this benchmark script (default workload matrix):
# python evaluation/performance/vllm_perf.py --model MODEL --tokenizer TOKENIZER
#
# [Optional] Run all 10 test cases:
# python evaluation/performance/vllm_perf.py --model MODEL --tokenizer TOKENIZER --enable-all


import argparse
import csv
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path
import time
import uuid
from datetime import datetime
from statistics import mean

HOST = "127.0.0.1"
PORT = 8010
RUNS = 3
SKIP_FIRST = 1

# Baseline cases used when --enable-all is not set.
# Each case is a tuple:
# (random_input_len, random_output_len, max_concurrency, num_prompts)
DEFAULT_TEST_CASES = [
    (1024, 1024, 64, 128),
    (4096, 1024, 64, 128),
    (16384, 1024, 64, 128),
    (32768, 1024, 64, 128),
    (65536, 1024, 64, 128),
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

    parser.add_argument("--model", help="服务暴露的模型名；legacy 模式必填")
    parser.add_argument("--tokenizer", help="tokenizer 路径或名称；legacy 模式必填")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--endpoint")
    parser.add_argument("--output-dir", default="benchmark_results")
    parser.add_argument("--seed", type=int, help="Legacy base seed (default 42)")
    parser.add_argument("--accuracy-gate", help="Formal gate issued by acceptance.py; omission means diagnostic scope")
    parser.add_argument("--service-manifest", help="Freshly verified current service identity")
    parser.add_argument("--config", help="Validated JSON performance plan (schema_version 1)")
    parser.add_argument("--role", choices=("baseline", "candidate", "revert"))
    parser.add_argument("--run-id", help="Unique output directory name; required with --config")
    parser.add_argument("--scope", choices=("diagnostic", "performance_only"), default="diagnostic")
    parser.add_argument("--comparison-contract", help="Pre-frozen comparison contract to bind by SHA")
    parser.add_argument("--dry-run", action="store_true", help="With --config, validate and print commands without running vLLM")

    parser.add_argument(
        "--enable-all",
        action="store_true",
        help="Enable the extended workload matrix.",
    )

    args = parser.parse_args()
    if args.config:
        if not args.service_manifest or not args.role or not args.run_id:
            parser.error("--config requires --service-manifest, --role and --run-id")
        if any(getattr(args, name) is not None for name in ("model", "tokenizer", "host", "port", "endpoint", "seed")) or args.enable_all:
            parser.error("Configure target, generation and cases in --config; legacy overrides are not accepted")
    else:
        if not args.model or not args.tokenizer:
            parser.error("legacy mode requires --model and --tokenizer")
        if args.role or args.run_id or args.dry_run or args.comparison_contract or args.scope != "diagnostic":
            parser.error("--role/--run-id/--dry-run/--comparison-contract/--scope require --config")
        args.host = args.host if args.host is not None else HOST
        args.port = args.port if args.port is not None else PORT
        args.endpoint = args.endpoint if args.endpoint is not None else "/v1/completions"
        args.seed = args.seed if args.seed is not None else 42
    return args


def build_common_args(args):
    return [
        "vllm",
        "bench",
        "serve",
        "--backend",
        "vllm",
        "--model",
        args.model,
        "--tokenizer",
        args.tokenizer,
        "--endpoint",
        args.endpoint,
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--dataset-name",
        "random",
        "--ignore-eos",
        "--random-range-ratio", "0",
        "--temperature", "0",
        "--seed", str(args.seed),
    ]


PATTERNS = {
    "failed_requests": r"Failed requests:\s+([0-9.]+)",
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


def extract_metrics(output_text):
    result = {}

    for key, pattern in PATTERNS.items():
        # Read the complete value, never a numeric prefix (e.g. 2 from 2oops).
        matches = re.findall(
            pattern.replace("([0-9.]+)", r"(\S+)"),
            output_text,
            re.IGNORECASE,
        )

        try:
            value = float(matches[0]) if len(matches) == 1 else None
        except ValueError:
            value = None
        result[key] = value if value is not None and math.isfinite(value) else None

    return result


REQUIRED_PERFORMANCE_METRICS = (
    "request_throughput", "output_throughput", "total_token_throughput",
    "mean_ttft_ms", "median_ttft_ms", "p99_ttft_ms",
    "mean_tpot_ms", "median_tpot_ms", "p99_tpot_ms",
    "mean_itl_ms", "median_itl_ms", "p99_itl_ms",
)
SUPPORTED_PERFORMANCE_METRICS = (
    "request_throughput", "output_throughput", "total_token_throughput", "request_goodput",
    *(f"{stat}_{metric}_ms" for metric in ("ttft", "tpot", "itl", "e2el")
      for stat in ("mean", "median", "p50", "p95", "p99")),
)


def validate_native_result(case, raw, stdout_metrics, required_metrics=None, ignore_eos=True, slo=None):
    """Validate the fixed-length generation schemas emitted with --save-detailed.

    v0.11.0 has completed + per-request errors/output_lens but no failed count;
    v0.12.0 adds failed. Do not infer zero failures from a missing field alone.
    Schema references: vllm-project/vllm, tags v0.11.0 and v0.12.0,
    vllm/benchmarks/serve.py (benchmark result and save-detailed handling).
    """
    input_len, output_len, _, num_prompts = case
    required_metrics = REQUIRED_PERFORMANCE_METRICS if required_metrics is None else required_metrics
    errors = []
    schema = "unknown"
    metrics = {key: raw.get(key) for key in PATTERNS}
    metrics.update({
        "successful_requests": raw.get("completed"),
        "benchmark_duration": raw.get("duration"),
        "peak_output_throughput": raw.get("max_output_tokens_per_s"),
    })
    metrics.update({key: raw.get(key) for key in required_metrics})

    # These tools measure multi-token streaming generation. Single-token output
    # needs a different contract because TPOT/ITL may not have any observations.
    if output_len <= 1 and any("_tpot_" in key or "_itl_" in key for key in required_metrics):
        errors.append("fixed generation schema requires output_len > 1 for TPOT/ITL")

    def expected_count(key, expected):
        value = raw.get(key)
        if type(value) is not int or value != expected:
            errors.append(f"native {key}: expected integer {expected}, got {value!r}")

    expected_count("num_prompts", num_prompts)
    expected_count("completed", num_prompts)
    expected_count("total_input_tokens", input_len * num_prompts)

    request_errors = raw.get("errors")
    output_lens = raw.get("output_lens")
    lengths_ok = (
        isinstance(output_lens, list) and len(output_lens) == num_prompts
        and all(type(length) is int and (length == output_len if ignore_eos else 1 <= length <= output_len)
                for length in output_lens)
    )
    expected_output = output_len * num_prompts if ignore_eos else sum(output_lens) if lengths_ok else None
    expected_count("total_output_tokens", expected_output)
    detailed_ok = (
        isinstance(request_errors, list) and len(request_errors) == num_prompts
        and all(error == "" for error in request_errors)
        and lengths_ok
    )
    if not detailed_ok:
        errors.append("native detailed errors/output_lens missing, incomplete, or inconsistent with workload")
    if "failed" in raw:
        schema = "vllm_generation_with_failed"
        expected_count("failed", 0)
        metrics["failed_requests"] = raw.get("failed")
    elif all(key in raw for key in ("num_prompts", "completed", "errors", "output_lens")):
        schema = "vllm_generation_legacy_detailed"
        # Only produce a failure count after all requested completions have
        # matching detailed records. Unknown/missing evidence remains missing.
        metrics["failed_requests"] = 0 if (
            detailed_ok and type(raw.get("completed")) is int
            and raw["completed"] == num_prompts
            and type(raw.get("num_prompts")) is int
            and raw["num_prompts"] == num_prompts
        ) else None
    else:
        errors.append("unsupported native result schema: no explicit failed count or complete legacy evidence")

    for key, expected in (
        ("successful_requests", num_prompts),
        ("total_input_tokens", input_len * num_prompts),
        ("total_output_tokens", expected_output),
    ):
        if stdout_metrics.get(key) != expected:
            errors.append(f"stdout {key}: expected {expected}, got {stdout_metrics.get(key)!r}")
    if stdout_metrics.get("failed_requests") not in (None, 0):
        errors.append("stdout reports failed requests")

    def finite_number(value):
        try:
            return type(value) in (int, float) and math.isfinite(value)
        except OverflowError:
            return False

    duration = raw.get("duration")
    if not finite_number(duration) or duration <= 0:
        errors.append("native duration must be finite and positive")
    reported_duration = stdout_metrics.get("benchmark_duration")
    if not finite_number(reported_duration) or reported_duration <= 0:
        errors.append("stdout benchmark duration must be finite and positive")
    elif finite_number(duration) and not math.isclose(duration, reported_duration, rel_tol=0, abs_tol=0.0051):
        errors.append("native duration disagrees with rounded stdout duration")

    if not required_metrics or any(key not in SUPPORTED_PERFORMANCE_METRICS for key in required_metrics):
        errors.append("required_metrics must contain supported performance metric names")
    for key in required_metrics:
        value = raw.get(key)
        valid_value = finite_number(value) and (
            value > 0 if "throughput" in key else value >= 0
        )
        if not valid_value:
            errors.append(f"required native metric {key} missing or invalid: {value!r}")
    peak = metrics["peak_output_throughput"]
    if peak is not None and (not finite_number(peak) or peak < 0):
        errors.append("optional native max_output_tokens_per_s is invalid")
    # The supported native schemas use this same unrounded duration for all
    # three throughput fields. Finite but inconsistent metrics are invalid too.
    if finite_number(duration) and duration > 0:
        for key, count_keys in (
            ("request_throughput", ("completed",)),
            ("output_throughput", ("total_output_tokens",)),
            ("total_token_throughput", ("total_input_tokens", "total_output_tokens")),
        ):
            if key in raw and all(type(raw.get(name)) is int for name in count_keys):
                count = sum(raw[name] for name in count_keys)
                expected = count / duration if finite_number(count) else None
                if (not finite_number(expected) or not finite_number(raw[key])
                        or not math.isclose(raw[key], expected, rel_tol=1e-6, abs_tol=1e-9)):
                    errors.append(f"native {key} disagrees with token/request counts divided by duration")
    if slo:
        goodput = raw.get("request_goodput")
        if not finite_number(goodput) or goodput < 0:
            errors.append("native request_goodput must be finite and nonnegative for SLO measurement")
        elif finite_number(duration) and duration > 0:
            count = goodput * duration
            if not finite_number(count) or count > num_prompts + 1e-6:
                errors.append("native request_goodput exceeds submitted request count / duration")
            elif abs(count - round(count)) > 1e-5:
                errors.append("native request_goodput does not encode an integer request count")

    return metrics, {"schema": schema, "errors": errors}


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

    print(f"[ERROR LOG] 错误信息已保存到: {filepath}")


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


def run_once(case, run_id, output_dir, common_args, timeout_s=3600):
    if type(timeout_s) not in (int, float) or not math.isfinite(timeout_s) or timeout_s <= 0:
        raise ValueError("timeout_s must be finite and positive")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    input_len, output_len, concurrency, num_prompts = case

    name = f"{input_len}_{output_len}_c{concurrency}"

    print("=" * 80)
    print(f"Running: {name} | Run {run_id}/{RUNS}")
    print("=" * 80)

    common_args = list(common_args)
    if "--seed" in common_args:
        index = common_args.index("--seed") + 1
        common_args[index] = str(int(common_args[index]) + input_len * 10 + concurrency * 1000 + run_id)
    raw_path = Path(output_dir) / f"p{input_len}-d{output_len}-c{concurrency}-r{run_id}-{uuid.uuid4().hex[:8]}.json"
    cmd = common_args + [
        "--save-result", "--save-detailed",
        "--percentile-metrics", "ttft,tpot,itl", "--metric-percentiles", "99",
        "--result-dir", str(raw_path.parent), "--result-filename", raw_path.name,
        "--random-input-len",
        str(input_len),
        "--random-output-len",
        str(output_len),
        "--max-concurrency",
        str(concurrency),
        "--num-prompts",
        str(num_prompts),
    ]

    print(" ".join(cmd))
    print()

    start_time = time.time()

    execution_error = None
    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as exc:
        def decoded(value):
            return value.decode(errors="replace") if isinstance(value, bytes) else value or ""
        process = subprocess.CompletedProcess(cmd, 124, decoded(exc.stdout), decoded(exc.stderr))
        execution_error = f"benchmark exceeded timeout_s={timeout_s}"
    except OSError as exc:
        process = subprocess.CompletedProcess(cmd, 127, "", str(exc))
        execution_error = f"benchmark could not execute: {exc}"
    except KeyboardInterrupt:
        process = subprocess.CompletedProcess(cmd, 130, "", "interrupted by user")
        execution_error = "benchmark interrupted; partial pipe output unavailable"

    elapsed = time.time() - start_time

    output = process.stdout

    print(output)
    if process.stderr:
        print(process.stderr)

    stdout_metrics = extract_metrics(output)

    raw = {}
    raw_error = None
    try:
        raw = json.loads(raw_path.read_text())
        if not isinstance(raw, dict):
            raise ValueError("native benchmark result is not an object")
    except (OSError, ValueError) as exc:
        raw_error = str(exc)
        raw = {}
    metrics, validation = validate_native_result(case, raw, stdout_metrics)
    if raw_error:
        validation["errors"].append(f"cannot read native result: {raw_error}")
    if execution_error:
        validation["errors"].append(execution_error)
    if process.returncode != 0:
        validation["errors"].append(f"benchmark exited with status {process.returncode}")
    metrics["elapsed_sec"] = round(elapsed, 2)
    metrics["returncode"] = process.returncode
    metrics["valid"] = not validation["errors"]
    output_path = raw_path.with_suffix(".output.json")
    with output_path.open("x", encoding="utf-8") as handle:
        json.dump({"stdout": process.stdout, "stderr": process.stderr}, handle, indent=2)
    with raw_path.with_suffix(".validation.json").open("x", encoding="utf-8") as handle:
        json.dump({"command": cmd, "returncode": process.returncode, "valid": metrics["valid"],
                   "raw_result": str(raw_path), "raw_error": raw_error,
                   "stdout_metrics": stdout_metrics, "output_path": str(output_path),
                   **validation}, handle, indent=2)
    has_error = not metrics["valid"]

    if has_error:
        save_error_log(
            cmd, case, run_id,
            stdout=process.stdout, stderr=process.stderr,
            returncode=process.returncode, output_dir=output_dir
        )
    if process.returncode == 130:
        raise KeyboardInterrupt("benchmark interrupted; failure evidence preserved")

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


def run_test_case(case, csv_file, output_dir, common_args):
    all_runs = []

    for run_id in range(1, RUNS + 1):
        metrics = run_once(case, run_id, output_dir, common_args)

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
    if args.config:
        # Loading this sibling by path also supports maintenance/test imports of
        # this script without relying on a caller's PYTHONPATH.
        import importlib.util
        spec = importlib.util.spec_from_file_location("performance_plan", Path(__file__).with_name("performance_plan.py"))
        plan_runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plan_runner)
        try:
            record = plan_runner.execute_plan(args)
        except (OSError, ValueError) as exc:
            raise SystemExit(str(exc)) from exc
        if record is not None:
            print(f"Run record: {record}")
            if json.loads(record.read_text())["status"] != "complete":
                raise SystemExit(1)
        return
    scope = "diagnostic"
    if args.accuracy_gate or args.service_manifest:
        if not args.accuracy_gate or not args.service_manifest:
            raise SystemExit("Provide both --accuracy-gate and --service-manifest")
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "accuracy"))
        from acceptance import check_gate
        check_gate(args.accuracy_gate, args.service_manifest, model=args.model,
                   host=args.host, port=args.port, tokenizer=args.tokenizer)
        if args.endpoint != "/v1/completions":
            raise SystemExit("This benchmark backend requires /v1/completions")
        scope = "formal_candidate"
    print(f"Acceptance scope: {scope}")

    test_cases = ALL_TEST_CASES if args.enable_all else DEFAULT_TEST_CASES
    common_args = build_common_args(args)
    model_label = re.sub(r"[^A-Za-z0-9_.-]+", "_", args.model).strip("_") or "model"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]

    output_dir = os.path.join(args.output_dir, model_label)
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, f"scope_{timestamp}.json"), "x", encoding="utf-8") as handle:
        json.dump({"scope": scope, "accuracy_gate": args.accuracy_gate,
                   "service_manifest": args.service_manifest}, handle, indent=2)
    all_summary = []
    failed_cases = []

    print()
    print(f"RUNS={RUNS}")
    print(f"SKIP_FIRST={SKIP_FIRST}")
    print(f"ENABLE_ALL={args.enable_all}")
    print(f"MODEL={args.model}")
    print(f"TOKENIZER={args.tokenizer}")
    print(f"SERVER={args.host}:{args.port}{args.endpoint}")
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
                output_dir,
                common_args,
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
