#!/usr/bin/env python3
# Historical results remain diagnostic; never upgrade them to formal gates.
"""Validate and summarize historical XingChen4 three-round measurements.

This compatibility tool never upgrades legacy results to formal acceptance.
"""

import argparse
import json
import math
from pathlib import Path
from statistics import median


METRICS = (
    "request_throughput",
    "output_throughput",
    "total_token_throughput",
    "mean_ttft_ms",
    "p99_ttft_ms",
    "p99_tpot_ms",
    "p99_e2el_ms",
)


def _number(value, *, positive=False) -> bool:
    return (
        type(value) in (int, float)
        and math.isfinite(value)
        and (value > 0 if positive else value >= 0)
    )


def validate_legacy_result(case, raw) -> None:
    input_tokens, output_tokens, _, requests = case
    for key, expected in (
        ("num_prompts", requests),
        ("completed", requests),
        ("failed", 0),
        ("total_input_tokens", input_tokens * requests),
        ("total_output_tokens", output_tokens * requests),
    ):
        if type(raw.get(key)) is not int or raw[key] != expected:
            raise ValueError(f"{key} is inconsistent with the workload")
    errors = raw.get("errors")
    lengths = raw.get("output_lens")
    if errors != [""] * requests:
        raise ValueError("request error evidence is incomplete")
    if lengths != [output_tokens] * requests:
        raise ValueError("output lengths are inconsistent with fixed generation")
    duration = raw.get("duration")
    if not _number(duration, positive=True):
        raise ValueError("duration must be finite and positive")
    for key in METRICS:
        if not _number(raw.get(key), positive="throughput" in key):
            raise ValueError(f"invalid metric: {key}")
    expected = {
        "request_throughput": requests / duration,
        "output_throughput": output_tokens * requests / duration,
        "total_token_throughput": (input_tokens + output_tokens) * requests / duration,
    }
    for key, value in expected.items():
        if not math.isclose(raw[key], value, rel_tol=1e-6, abs_tol=1e-9):
            raise ValueError(f"{key} disagrees with counts divided by duration")


def load_validator():
    """Return the frozen legacy validator used by the compatibility collector."""
    return validate_legacy_result


def collect(root: Path, validator=None) -> dict:
    root = Path(root)
    rounds = json.loads((root / "all-rounds.json").read_text(encoding="utf-8"))
    if not isinstance(rounds, list) or len(rounds) < 3:
        raise ValueError("historical summary requires at least three complete rounds")
    cases = [item.get("case") for item in rounds if isinstance(item, dict)]
    if len(cases) != len(rounds) or any(case != cases[0] for case in cases[1:]):
        raise ValueError("all rounds must use the same workload")
    case = cases[0]
    if (
        not isinstance(case, list)
        or len(case) != 4
        or any(type(value) is not int or value <= 0 for value in case)
    ):
        raise ValueError("round workload must contain four positive integers")

    validator = validator or load_validator()
    observed = []
    seen = set()
    input_tokens, output_tokens, concurrency, _ = case
    for item in rounds:
        run = item.get("run")
        if type(run) is not int or run <= 0 or run in seen:
            raise ValueError("round IDs must be unique positive integers")
        seen.add(run)
        path = root / f"p{input_tokens}-d{output_tokens}-c{concurrency}-r{run}.json"
        raw = json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda value: float(value))
        validator(case, raw)
        observed.append(raw)

    steady = observed[1:]
    return {
        "schema_version": 1,
        "scope": "historical_performance_only",
        "workload": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "concurrency": concurrency,
            "requests": case[3],
        },
        "warmup_rounds": 1,
        "measured_rounds": len(steady),
        "warmup_stability": "not_established_by_fixed_rounds",
        "steady": {
            key: {
                "round_values": [raw[key] for raw in steady],
                "median_of_rounds": median(raw[key] for raw in steady),
            }
            for key in METRICS
        },
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    summary = collect(args.root)
    encoded = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(encoded)
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
