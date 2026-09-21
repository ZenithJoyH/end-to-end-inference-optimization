#!/usr/bin/env python3
"""Compatibility wrapper for a SHA-pinned historical workload matrix.

The historical source file is parsed as data after a fixed SHA check; it is
never imported or executed. New experiments should call the maintained runner
directly with a frozen plan.
"""

import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


SOURCE_RUNNER_SHA256 = "c3dc6d8f9405a62fc51081086e7347d828fb63917ce956f04c8d21cc4001bfab"
REQUIRED_METRICS = [
    "request_throughput",
    "output_throughput",
    "total_token_throughput",
    "p99_ttft_ms",
    "p99_tpot_ms",
    "p99_itl_ms",
    "p99_e2el_ms",
]


def repository_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "evaluation/performance/vllm_perf.py").is_file():
            return parent
    raise RuntimeError("repository root is unavailable")


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_source_cases(path: Path) -> list[tuple[int, int, int, int]]:
    path = Path(path)
    digest = sha256(path)
    if digest != SOURCE_RUNNER_SHA256:
        raise ValueError(f"source runner SHA mismatch: {digest}")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    value = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "DEFAULT_TEST_CASES"
            for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            break
    if not isinstance(value, list) or not value:
        raise ValueError("DEFAULT_TEST_CASES is missing")
    cases = []
    for item in value:
        if (
            not isinstance(item, tuple)
            or len(item) != 4
            or any(type(number) is not int or number <= 0 for number in item)
        ):
            raise ValueError("DEFAULT_TEST_CASES contains an invalid workload")
        cases.append(item)
    return cases


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--runner", type=Path, required=True, help="frozen historical source matrix")
    result.add_argument("--model", required=True)
    result.add_argument("--tokenizer", required=True)
    result.add_argument("--host", required=True)
    result.add_argument("--port", type=int, required=True)
    result.add_argument("--max-model-len", type=int, required=True)
    result.add_argument("--output-dir", type=Path, required=True)
    result.add_argument("--service-manifest", required=True)
    result.add_argument("--comparison-contract")
    result.add_argument("--accuracy-gate")
    result.add_argument("--acceptance-tools", type=Path)
    result.add_argument("--role", choices=("baseline", "candidate", "revert"), default="candidate")
    result.add_argument("--run-id")
    result.add_argument("--input-lengths", type=int, nargs="+")
    result.add_argument("--output-length", type=int, default=1024)
    result.add_argument("--concurrency", type=int, default=64)
    result.add_argument("--requests", type=int, default=128)
    result.add_argument("--seed", type=int, default=42)
    result.add_argument("--timeout", type=float, default=3600)
    result.add_argument("--performance-only", action="store_true")
    result.add_argument("--dry-run", action="store_true")
    result.add_argument("--trust-remote-code", action=argparse.BooleanOptionalAction, default=True)
    return result


def build_plan(args) -> dict:
    source_cases = read_source_cases(args.runner)
    if args.output_length <= 0 or args.concurrency <= 0 or args.requests <= 0:
        raise ValueError("output length, concurrency, and requests must be positive")
    if args.input_lengths is None:
        cases = source_cases
    else:
        requested = set(args.input_lengths)
        known_order = [case[0] for case in source_cases]
        if len(requested) != len(args.input_lengths) or requested - set(known_order):
            raise ValueError("input lengths must be distinct members of the frozen source matrix")
        cases = [
            (input_tokens, args.output_length, args.concurrency, args.requests)
            for input_tokens in known_order
            if input_tokens in requested
        ]
    if args.max_model_len <= 0 or any(input_tokens + output_tokens > args.max_model_len for input_tokens, output_tokens, _, _ in cases):
        raise ValueError("workload exceeds --max-model-len")
    if args.port <= 0 or args.port > 65535 or args.seed < 0 or args.timeout <= 0:
        raise ValueError("port, seed, or timeout is invalid")

    return {
        "schema_version": 1,
        "target": {
            "model": args.model,
            "tokenizer": args.tokenizer,
            "host": args.host,
            "port": args.port,
            "endpoint": "/v1/completions",
            "trust_remote_code": args.trust_remote_code,
        },
        "generation": {
            "seed": args.seed,
            "temperature": 0,
            "ignore_eos": True,
            "random_range_ratio": 0,
        },
        "measurement": {
            "warmup_rounds": 1,
            "measured_rounds": 2,
            "timeout_s": args.timeout,
            "required_metrics": list(REQUIRED_METRICS),
            "slo": {},
            "warmup_stability": None,
        },
        "cases": [
            {
                "id": f"p{input_tokens}-d{output_tokens}-c{concurrency}-n{requests}",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "concurrency": concurrency,
                "requests": requests,
                "load_mode": "finite_batch",
                "stage": "mixed",
                "request_rate": None,
                "burstiness": 1,
            }
            for input_tokens, output_tokens, concurrency, requests in cases
        ],
    }


def shared_runner(args) -> Path:
    root = repository_root()
    accuracy = (args.acceptance_tools or root / "evaluation/accuracy").resolve()
    performance = accuracy.parent / "performance"
    runner = performance / "vllm_perf.py"
    if accuracy.name != "accuracy" or performance.name != "performance" or not runner.is_file():
        raise ValueError("acceptance tools must have a maintained sibling performance runner")
    return runner


def _command(args, config: Path, *, dry_run: bool) -> list[str]:
    command = [
        sys.executable,
        str(shared_runner(args)),
        "--config", str(config),
        "--service-manifest", args.service_manifest,
        "--role", args.role,
        "--run-id", args.run_id or f"{args.role}-01",
        "--scope", "performance_only" if args.performance_only else "diagnostic",
        "--output-dir", str(args.output_dir),
    ]
    if args.comparison_contract:
        command.extend(("--comparison-contract", args.comparison_contract))
    if args.accuracy_gate:
        command.extend(("--accuracy-gate", args.accuracy_gate))
    if dry_run:
        command.append("--dry-run")
    return command


def main(argv=None) -> int:
    argument_parser = parser()
    args = argument_parser.parse_args(argv)
    if args.output_dir.exists():
        argument_parser.error(f"output already exists: {args.output_dir}")
    if args.performance_only and args.accuracy_gate:
        argument_parser.error("--performance-only cannot be combined with --accuracy-gate")
    if not args.performance_only and not args.accuracy_gate:
        argument_parser.error("formal candidate mode requires --accuracy-gate")
    if args.accuracy_gate and args.role != "candidate":
        argument_parser.error("an accuracy gate can only admit a candidate run")
    try:
        plan = build_plan(args)
        shared_runner(args)
    except ValueError as exc:
        argument_parser.error(str(exc))

    with tempfile.TemporaryDirectory(prefix="xingchen4-perf-plan-") as temporary:
        config = Path(temporary) / "plan.json"
        config.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        preflight = subprocess.run(_command(args, config, dry_run=True), capture_output=True, text=True)
        if preflight.returncode != 0:
            if preflight.stderr:
                print(preflight.stderr, file=sys.stderr, end="")
            return preflight.returncode
        if args.dry_run:
            if preflight.stdout:
                print(preflight.stdout, end="")
            return 0

        args.output_dir.mkdir(parents=True, exist_ok=False)
        metadata = dict(plan)
        metadata["source_runner"] = str(args.runner.resolve())
        metadata["source_runner_sha256"] = SOURCE_RUNNER_SHA256
        (args.output_dir / "wrapper-plan.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        result = subprocess.run(_command(args, config, dry_run=False))
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
