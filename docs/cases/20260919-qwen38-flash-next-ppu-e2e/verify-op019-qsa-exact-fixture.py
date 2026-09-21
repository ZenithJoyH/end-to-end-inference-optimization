#!/usr/bin/env python3
"""Verify raw op-019 fixture integrity and reproduce op-018 overlap counters."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


GROUP_ROWS = (2, 4, 8, 16)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_array(root: Path, entry: dict) -> np.ndarray:
    path = root / entry["path"]
    if path.stat().st_size != int(entry["nbytes"]):
        raise SystemExit(f"byte length mismatch: {path}")
    if sha256(path) != entry["sha256"]:
        raise SystemExit(f"SHA mismatch: {path}")
    array = np.memmap(path, mode="r", dtype=np.dtype(entry["dtype"]))
    expected = int(np.prod(entry["shape"], dtype=np.int64))
    if array.size != expected:
        raise SystemExit(f"element count mismatch: {path}")
    return array.reshape(entry["shape"])


def expected_phase_record(summary: dict, phase: str, group_rows: int) -> dict:
    for row in summary.get("rows", []):
        if int(row["R"]) == group_rows:
            return row[phase]
    raise SystemExit(f"op-018 summary has no R={group_rows}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture_dir", type=Path)
    parser.add_argument("--op018-summary", type=Path)
    args = parser.parse_args()
    root = args.fixture_dir.resolve()
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest["files"]
    selected = load_array(root, files["selected"])
    requests = load_array(root, files["token_to_req"])
    positions = load_array(root, files["logical_positions"])
    starts = load_array(root, files["query_start_loc"])
    run_ids = load_array(root, files["request_run_ids"])
    load_array(root, files["seq_lens"])

    actual_rows = int(manifest["actual_rows"])
    if starts.tolist()[-1] != actual_rows or starts.size != run_ids.size + 1:
        raise SystemExit("query_start_loc/run_ids shape mismatch")
    rebuilt = [0]
    rebuilt_ids = []
    if actual_rows:
        previous = int(requests[0])
        if previous < 0:
            raise SystemExit("active rows start with an invalid request")
        rebuilt_ids.append(previous)
        for row in range(1, actual_rows):
            current = int(requests[row])
            if current < 0:
                raise SystemExit("negative request inside active prefix")
            if current != previous:
                rebuilt.append(row)
                rebuilt_ids.append(current)
                previous = current
    rebuilt.append(actual_rows)
    if rebuilt != starts.tolist() or rebuilt_ids != run_ids.tolist():
        raise SystemExit("stored query_start_loc is not token_to_req run boundaries")
    if np.any(requests[actual_rows:] >= 0):
        raise SystemExit("nonnegative request after padding boundary")

    # Keep compact int32 unique arrays rather than millions of Python ints.
    row_values = []
    row_sizes = np.zeros(selected.shape[0], dtype=np.int64)
    duplicate_rows = []
    for row, values in enumerate(selected):
        valid = values[values >= 0]
        unique = np.unique(valid)
        if unique.size != valid.size:
            duplicate_rows.append(row)
        row_values.append(unique)
        row_sizes[row] = unique.size
    if duplicate_rows:
        raise SystemExit(
            f"selected tokens contain duplicates in {len(duplicate_rows)} rows; "
            f"first rows={duplicate_rows[:8]}"
        )

    eligible = (requests >= 0) & (positions >= 0)
    denominator = int(row_sizes[eligible].sum())
    metrics = {}
    for group_rows in GROUP_ROWS:
        covered = 0
        union_sum = 0
        groups = 0
        tails = 0
        union_sizes = []
        union_minus_leader = [[] for _ in range(group_rows)]
        for run_index, request in enumerate(run_ids.tolist()):
            begin = int(starts[run_index])
            end = int(starts[run_index + 1])
            row = begin
            while row + group_rows <= end:
                ids = np.arange(row, row + group_rows)
                expected_positions = positions[row] + np.arange(group_rows)
                valid_group = (
                    np.all(requests[ids] == request)
                    and np.all(positions[ids] == expected_positions)
                    and np.all(positions[ids] >= 0)
                    and request >= 0
                )
                if valid_group:
                    a_value = int(row_sizes[ids].sum())
                    union_values = np.unique(
                        np.concatenate([row_values[int(item)] for item in ids])
                    )
                    union_size = union_values.size
                    covered += a_value
                    union_sum += int(union_size)
                    groups += 1
                    union_sizes.append(int(union_size))
                    for leader in range(group_rows):
                        additions = np.setdiff1d(
                            union_values,
                            row_values[int(ids[leader])],
                            assume_unique=True,
                        ).size
                        union_minus_leader[leader].append(int(additions))
                else:
                    tails += 1
                row += group_rows
            tails += end - row
        reusable = covered - union_sum
        union_array = np.asarray(union_sizes, dtype=np.int64)
        percentiles = {
            name: (
                float(np.percentile(union_array, percentile, method="higher"))
                if union_array.size
                else None
            )
            for name, percentile in (("p50", 50), ("p90", 90), ("p99", 99))
        }
        leaders = {}
        for leader, values in enumerate(union_minus_leader):
            additions = np.asarray(values, dtype=np.int64)
            addition_sum = int(additions.sum())
            leaders[str(leader)] = {
                "union_minus_leader_sum": addition_sum,
                "leader_union_coverage": (
                    (union_sum - addition_sum) / union_sum if union_sum else None
                ),
                "groups_where_leader_equals_union": int(
                    np.count_nonzero(additions == 0)
                ),
                "max_union_minus_leader": (
                    int(additions.max()) if additions.size else None
                ),
            }
        metrics[str(group_rows)] = {
            "A_R_sum_row_cardinalities": covered,
            "U_R_sum_group_union_cardinalities": union_sum,
            "all_eligible_row_token_occurrences": denominator,
            "reusable_token_occurrences": reusable,
            "full_group_count": groups,
            "tail_or_rejected_count": tails,
            "rho": reusable / denominator if denominator else None,
            "coverage": covered / denominator if denominator else None,
            "mask_density": (
                covered / (group_rows * union_sum) if union_sum else None
            ),
            "union_size_distribution": {
                "min": int(union_array.min()) if union_array.size else None,
                "max": int(union_array.max()) if union_array.size else None,
                **percentiles,
            },
            "leader_analysis": leaders,
        }

    summary_comparison = None
    if args.op018_summary is not None:
        summary = json.loads(args.op018_summary.read_text(encoding="utf-8"))
        phase = manifest["observed_phase"]
        comparisons = {}
        for group_rows in GROUP_ROWS:
            actual = metrics[str(group_rows)]
            expected = expected_phase_record(summary, phase, group_rows)
            fields = (
                "A_R_sum_row_cardinalities",
                "U_R_sum_group_union_cardinalities",
                "all_eligible_row_token_occurrences",
                "reusable_token_occurrences",
                "full_group_count",
            )
            unequal = {
                field: {"fixture": actual[field], "op018": expected[field]}
                for field in fields
                if actual[field] != expected[field]
            }
            if unequal:
                raise SystemExit(
                    f"fixture counters differ from op-018 R={group_rows}: {unequal}"
                )
            comparisons[str(group_rows)] = "exact_integer_match"
        summary_comparison = {
            "path": str(args.op018_summary.resolve()),
            "sha256": sha256(args.op018_summary.resolve()),
            "phase": phase,
            "groups": comparisons,
        }

    result = {
        "schema_version": 1,
        "experiment_id": "op-019",
        "fixture_dir": str(root),
        "manifest_sha256": sha256(manifest_path),
        "integrity": "passed",
        "pickle_used": False,
        "query_start_loc_reconstruction": "passed",
        "duplicate_selected_rows": 0,
        "metrics": metrics,
        "op018_summary_comparison": summary_comparison,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
