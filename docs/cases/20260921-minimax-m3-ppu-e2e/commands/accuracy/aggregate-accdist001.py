#!/usr/bin/env python3
"""Validate and aggregate three full GPQA request-seed runs."""

import argparse
import hashlib
import json
from pathlib import Path
import random


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values, probability):
    values = sorted(values)
    position = probability * (len(values) - 1)
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    fraction = position - lower
    return values[lower] * (1 - fraction) + values[upper] * fraction


def load_seed(root, seed):
    sample_files = list((root / f"seed-{seed}" / "native").rglob("samples_*.jsonl"))
    result_files = list((root / f"seed-{seed}" / "native").rglob("results_*.json"))
    if len(sample_files) != 1 or len(result_files) != 1:
        raise ValueError(f"seed {seed}: expected one samples/results pair")
    rows = [json.loads(line) for line in sample_files[0].open(encoding="utf-8") if line.strip()]
    strict = [row for row in rows if row.get("filter") == "strict-match"]
    by_doc = {int(row["doc_id"]): row for row in strict}
    if len(strict) != 198 or set(by_doc) != set(range(198)):
        raise ValueError(f"seed {seed}: strict-match coverage is not exactly doc_id 0..197")
    if any(row.get("timeout") for row in strict):
        raise ValueError(f"seed {seed}: timeout observed")
    outcomes = {doc: float(row["exact_match"]) for doc, row in by_doc.items()}
    if any(value not in (0.0, 1.0) for value in outcomes.values()):
        raise ValueError(f"seed {seed}: non-binary exact_match")
    truncations = sum(
        (row.get("usage") or {}).get("completion_tokens") == 30000
        for row in strict
    )
    result = json.loads(result_files[0].read_text(encoding="utf-8"))
    return {
        "seed": seed,
        "score": sum(outcomes.values()) / 198,
        "correct": int(sum(outcomes.values())),
        "truncations": truncations,
        "truncation_rate": truncations / 198,
        "outcomes": outcomes,
        "samples": {"path": str(sample_files[0]), "sha256": sha256(sample_files[0])},
        "results": {"path": str(result_files[0]), "sha256": sha256(result_files[0])},
        "native_result_task": result.get("results", {}).get("gpqa_diamond_generative_cot"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite {args.output}")
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    seeds = contract["request_seeds"]
    runs = [load_seed(args.root, seed) for seed in seeds]
    vectors = [[run["outcomes"][doc] for run in runs] for doc in range(198)]
    per_doc_means = [sum(vector) / len(vector) for vector in vectors]
    rng = random.Random(contract["aggregation"]["random_seed"])
    estimates = []
    for _ in range(10000):
        sampled = [per_doc_means[rng.randrange(198)] for _ in range(198)]
        estimates.append(sum(sampled) / 198)
    scores = [run["score"] for run in runs]
    lower = percentile(estimates, 0.025)
    upper = percentile(estimates, 0.975)
    threshold = contract["reference_threshold"]
    output_runs = [{k: v for k, v in run.items() if k != "outcomes"} for run in runs]
    output = {
        "schema_version": 1,
        "experiment_id": contract["experiment_id"],
        "contract": {"path": str(args.contract.resolve()), "sha256": sha256(args.contract)},
        "runs": output_runs,
        "aggregate": {
            "mean": sum(scores) / len(scores),
            "min": min(scores),
            "max": max(scores),
            "bootstrap_95_percent_interval": [lower, upper],
            "all_correct_questions": sum(sum(vector) == len(seeds) for vector in vectors),
            "all_wrong_questions": sum(sum(vector) == 0 for vector in vectors),
            "mixed_questions": sum(0 < sum(vector) < len(seeds) for vector in vectors),
            "point_estimate_meets_reference": sum(scores) / len(scores) >= threshold,
            "conservative_confidence_meets_reference": lower >= threshold,
            "formal_gate": False,
        },
    }
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(output["aggregate"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
