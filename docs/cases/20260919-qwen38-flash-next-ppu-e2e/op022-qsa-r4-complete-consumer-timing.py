#!/usr/bin/env python3
"""op022 correctness-first timing of generic QSA vs the complete R4 consumer.

This experiment consumes immutable selected indices from one verified op021
rows4096 fixture.  It excludes the producer from both timing arms.  The R4 arm
includes output clear, workspace clear, membership build, and attention with
fallback on every eager call or graph replay.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import statistics
import sys
from pathlib import Path
from types import ModuleType
from typing import Callable

import numpy as np
import torch


EXPERIMENT_ID = "op-022-qsa-r4-complete-consumer-timing"
EXPECTED_OP020_SHA256 = "13bf633180074fb578bc99897ab645b922fc5e63efccb0ae585417b78aa08fd5"
EXPECTED_OP019_SHA256 = "7a2dd94e2918a2cf88be803235a62d9362d9a71bb6da13a49cc9d0dd7fc36acc"
EXPECTED_BASELINE_SOURCE_SHA256 = "e18fbb229d9c4a5c2b06a6858ae4679596e1a6f971a4ff8878acbbc4f469db23"
ROWS = 4096
GAIN_GATE_PCT = 8.0
WARMUP = 5
REPEAT = 5
MINIMUM_SAMPLES = 7
MAXIMUM_SAMPLES = 11
MAX_MAD_RATIO = 0.03
ATOL = 0.05
RTOL = 0.05


class ExperimentBlocker(RuntimeError):
    """A frozen prerequisite is absent or incompatible."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_module(path: Path, expected_sha: str, name: str) -> ModuleType:
    path = path.resolve()
    if not path.is_file():
        raise ExperimentBlocker(f"dependency is missing: {path}")
    actual = _sha256(path)
    if actual != expected_sha:
        raise ExperimentBlocker(
            f"dependency SHA mismatch for {path}: {actual} != {expected_sha}"
        )
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ExperimentBlocker(f"cannot import dependency: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _selected_sha(op020: ModuleType, workload: object) -> str:
    return op020._tensor_sha(workload.selected)


def _expected_structure(op020: ModuleType, workload: object) -> dict[str, np.ndarray]:
    selected = workload.selected.detach().cpu().clone()
    return op020._expected_structure(workload, selected)


def _assert_workspace(
    workload: object, expected: dict[str, np.ndarray]
) -> dict[str, object]:
    checks = {
        "membership": workload.membership.detach().cpu().numpy(),
        "group_base": workload.group_base.detach().cpu().numpy(),
        "overflow": workload.overflow.detach().cpu().numpy(),
    }
    for name, actual in checks.items():
        if not np.array_equal(actual, expected[name]):
            mismatches = int(np.count_nonzero(actual != expected[name]))
            raise AssertionError(f"complete {name} mismatch: {mismatches} cells")
    write_count = workload.write_count.detach().cpu()
    if not bool(torch.all(write_count == 1)):
        wrong = torch.nonzero(write_count != 1, as_tuple=False)[:16].tolist()
        raise AssertionError(f"candidate writer marker mismatch: {wrong}")
    return {
        "membership_sha256": hashlib.sha256(
            memoryview(checks["membership"].view(np.uint8)).cast("B")
        ).hexdigest(),
        "group_base_sha256": hashlib.sha256(
            memoryview(checks["group_base"].view(np.uint8)).cast("B")
        ).hexdigest(),
        "overflow_sha256": hashlib.sha256(
            memoryview(checks["overflow"].view(np.uint8)).cast("B")
        ).hexdigest(),
        "membership_cells_checked": int(workload.membership.numel()),
        "group_slots_checked": int(workload.group_base.numel()),
        "write_count_all_one": True,
    }


def _assert_theoretical_unique_writers(workload: object) -> dict[str, object]:
    counts = np.zeros(ROWS, dtype=np.int32)
    starts = workload.fixture.run_starts
    for begin, end in zip(starts[:-1], starts[1:]):
        for base in range(begin, end, 4):
            counts[base : min(base + 4, end)] += 1
    if not np.all(counts == 1):
        wrong = np.flatnonzero(counts != 1)[:16].tolist()
        raise AssertionError(f"CPU row-writer ownership is not unique: {wrong}")
    return {
        "request_run_starts": starts,
        "rows_with_one_owner": int(np.count_nonzero(counts == 1)),
        "rows_with_multiple_owners": int(np.count_nonzero(counts > 1)),
        "status": "passed",
    }


def _assert_outputs(
    generic: torch.Tensor, candidate: torch.Tensor
) -> dict[str, object]:
    if not bool(torch.isfinite(generic).all()) or not bool(torch.isfinite(candidate).all()):
        raise AssertionError("generic or candidate output contains NaN/Inf")
    torch.testing.assert_close(
        candidate.float(), generic.float(), atol=ATOL, rtol=RTOL
    )
    delta = (candidate.float() - generic.float()).abs()
    return {
        "generic_sha256": hashlib.sha256(
            memoryview(generic.cpu().contiguous().view(torch.uint8).numpy()).cast("B")
        ).hexdigest(),
        "candidate_sha256": hashlib.sha256(
            memoryview(candidate.cpu().contiguous().view(torch.uint8).numpy()).cast("B")
        ).hexdigest(),
        "max_abs_candidate_vs_generic": float(delta.max().item()),
        "mean_abs_candidate_vs_generic": float(delta.mean().item()),
    }


@torch.inference_mode()
def _correctness_gate(
    op020: ModuleType,
    op019: ModuleType,
    workload: object,
) -> tuple[dict[str, object], dict[str, np.ndarray], torch.Tensor, torch.Tensor]:
    selected_before = _selected_sha(op020, workload)
    captured_sha = op020._tensor_sha(workload.captured_selected_cpu)
    if selected_before != captured_sha:
        raise AssertionError("device selected does not equal immutable captured selected")
    shape_similarity = op020._shape_metrics(workload, workload.captured_selected_cpu)
    writer_ownership = _assert_theoretical_unique_writers(workload)

    op020._generic(workload)
    generic = workload.generic_output.detach().clone()
    op020._candidate(workload, op019)
    torch.cuda.synchronize()
    candidate = workload.candidate_output.detach().clone()
    output_summary = _assert_outputs(generic, candidate)
    expected = _expected_structure(op020, workload)
    workspace_summary = _assert_workspace(workload, expected)

    sample_rows = op020._sample_rows(workload)
    reference = op020._fp32_reference(
        workload, workload.captured_selected_cpu, sample_rows
    )
    torch.testing.assert_close(
        generic[sample_rows].float(), reference.float(), atol=ATOL, rtol=RTOL
    )
    torch.testing.assert_close(
        candidate[sample_rows].float(), reference.float(), atol=ATOL, rtol=RTOL
    )
    selected_after = _selected_sha(op020, workload)
    if selected_after != selected_before:
        raise AssertionError("selected changed during eager correctness")
    workspace_bytes = sum(
        tensor.numel() * tensor.element_size()
        for tensor in (
            workload.membership,
            workload.group_base,
            workload.overflow,
            workload.write_count,
        )
    )
    return (
        {
            "selected_sha256": selected_before,
            "shape_similarity": shape_similarity,
            "writer_ownership": writer_ownership,
            "outputs": output_summary,
            "workspace": workspace_summary,
            "sampled_fp32_rows": sample_rows,
            "workspace_bytes": workspace_bytes,
            "status": "passed",
        },
        expected,
        generic,
        candidate,
    )


def _capture_static_graph(fn: Callable[[], object]) -> torch.cuda.CUDAGraph:
    for _ in range(3):
        fn()
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, capture_error_mode="thread_local"):
        fn()
    torch.cuda.synchronize()
    return graph


@torch.inference_mode()
def _graph_correctness_gate(
    op020: ModuleType,
    workload: object,
    baseline_graph: torch.cuda.CUDAGraph,
    candidate_graph: torch.cuda.CUDAGraph,
    eager_generic: torch.Tensor,
    expected_workspace: dict[str, np.ndarray],
) -> dict[str, object]:
    selected_sha = _selected_sha(op020, workload)
    baseline_hashes: list[str] = []
    candidate_hashes: list[str] = []
    workspace_hashes: list[str] = []
    baseline_first: torch.Tensor | None = None
    candidate_first: torch.Tensor | None = None
    for _ in range(3):
        baseline_graph.replay()
        torch.cuda.synchronize()
        current = workload.generic_output.detach().clone()
        if baseline_first is None:
            baseline_first = current
        else:
            torch.testing.assert_close(current, baseline_first, atol=0, rtol=0)
        torch.testing.assert_close(current, eager_generic, atol=0, rtol=0)
        baseline_hashes.append(op020._tensor_sha(current))
    for _ in range(3):
        candidate_graph.replay()
        torch.cuda.synchronize()
        current = workload.candidate_output.detach().clone()
        if candidate_first is None:
            candidate_first = current
        else:
            torch.testing.assert_close(current, candidate_first, atol=0, rtol=0)
        _assert_outputs(eager_generic, current)
        workspace = _assert_workspace(workload, expected_workspace)
        candidate_hashes.append(op020._tensor_sha(current))
        workspace_hashes.append(workspace["membership_sha256"])
    if _selected_sha(op020, workload) != selected_sha:
        raise AssertionError("selected changed during graph correctness")
    return {
        "baseline_graph_count": 1,
        "candidate_graph_count": 1,
        "replays_per_arm": 3,
        "external_input_updates_between_replays": False,
        "baseline_output_sha256": baseline_hashes,
        "candidate_output_sha256": candidate_hashes,
        "candidate_membership_sha256": workspace_hashes,
        "baseline_replays_bit_exact": len(set(baseline_hashes)) == 1,
        "candidate_replays_bit_exact": len(set(candidate_hashes)) == 1,
        "candidate_workspace_replays_bit_exact": len(set(workspace_hashes)) == 1,
        "status": "passed",
    }


def _event_ms(fn: Callable[[], object], repeat: int) -> float:
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    start.record()
    for _ in range(repeat):
        fn()
    end.record()
    torch.cuda.synchronize()
    return float(start.elapsed_time(end)) / repeat


def _summary(values: list[float]) -> dict[str, object]:
    median = statistics.median(values)
    mad = statistics.median(abs(value - median) for value in values)
    return {
        "raw_ms": values,
        "median_ms": median,
        "p25_ms": float(np.percentile(values, 25)),
        "p75_ms": float(np.percentile(values, 75)),
        "mad_ms": mad,
        "mad_over_median": mad / median if median > 0 else None,
        "min_ms": min(values),
        "max_ms": max(values),
    }


def _paired_timing(
    baseline: Callable[[], object], candidate: Callable[[], object]
) -> dict[str, object]:
    for _ in range(WARMUP):
        baseline()
        candidate()
    torch.cuda.synchronize()
    baseline_values: list[float] = []
    candidate_values: list[float] = []
    orders: list[str] = []
    target = MINIMUM_SAMPLES
    sample = 0
    while sample < target:
        if sample % 2 == 0:
            baseline_values.append(_event_ms(baseline, REPEAT))
            candidate_values.append(_event_ms(candidate, REPEAT))
            orders.append("baseline,candidate")
        else:
            candidate_values.append(_event_ms(candidate, REPEAT))
            baseline_values.append(_event_ms(baseline, REPEAT))
            orders.append("candidate,baseline")
        sample += 1
        if sample == MINIMUM_SAMPLES:
            interim = (_summary(baseline_values), _summary(candidate_values))
            if any(
                item["mad_over_median"] is None
                or item["mad_over_median"] > MAX_MAD_RATIO
                for item in interim
            ):
                target = MAXIMUM_SAMPLES
    baseline_summary = _summary(baseline_values)
    candidate_summary = _summary(candidate_values)
    stable = all(
        item["mad_over_median"] is not None
        and item["mad_over_median"] <= MAX_MAD_RATIO
        for item in (baseline_summary, candidate_summary)
    )
    gain = (
        baseline_summary["median_ms"] / candidate_summary["median_ms"] - 1.0
    ) * 100.0
    paired_gain = [
        (base / candidate - 1.0) * 100.0
        for base, candidate in zip(baseline_values, candidate_values)
    ]
    return {
        "baseline": baseline_summary,
        "candidate": candidate_summary,
        "gain_pct": gain,
        "paired_gain_pct": paired_gain,
        "orders": orders,
        "warmup": WARMUP,
        "repeat": REPEAT,
        "samples": len(orders),
        "maximum_mad_over_median": MAX_MAD_RATIO,
        "measurement_stable": stable,
        "passes_eight_percent_gate": stable and gain >= GAIN_GATE_PCT,
    }


@torch.inference_mode()
def _post_timing_guard(
    op020: ModuleType,
    workload: object,
    baseline_graph: torch.cuda.CUDAGraph,
    candidate_graph: torch.cuda.CUDAGraph,
    expected_workspace: dict[str, np.ndarray],
    selected_sha: str,
) -> dict[str, object]:
    baseline_graph.replay()
    candidate_graph.replay()
    torch.cuda.synchronize()
    generic = workload.generic_output.detach().clone()
    candidate = workload.candidate_output.detach().clone()
    outputs = _assert_outputs(generic, candidate)
    workspace = _assert_workspace(workload, expected_workspace)
    if _selected_sha(op020, workload) != selected_sha:
        raise AssertionError("selected changed during timing")
    return {"outputs": outputs, "workspace": workspace, "status": "passed"}


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@torch.inference_mode()
def run(args: argparse.Namespace) -> dict[str, object]:
    if not torch.cuda.is_available():
        raise ExperimentBlocker("torch.cuda PPU-compatible API is unavailable")
    op020 = _load_module(args.op020_module, EXPECTED_OP020_SHA256, "op020_rows4096")
    op019 = _load_module(args.op019_module, EXPECTED_OP019_SHA256, "op019_boundary_fixed")
    baseline_source_text = inspect.getsourcefile(op020.qsa_sparse_paged_attention)
    if not baseline_source_text:
        raise ExperimentBlocker("cannot resolve imported baseline source")
    baseline_source = Path(baseline_source_text).resolve()
    if not baseline_source.is_file():
        raise ExperimentBlocker(f"imported baseline source is missing: {baseline_source}")
    baseline_source_sha = _sha256(baseline_source)
    if baseline_source_sha != EXPECTED_BASELINE_SOURCE_SHA256:
        raise ExperimentBlocker(
            "imported baseline source SHA mismatch: "
            f"{baseline_source_sha} != {EXPECTED_BASELINE_SOURCE_SHA256}"
        )
    fixture = op020.load_fixture(args.fixture, args.phase)
    workload = op020.make_workload(fixture, torch.device("cuda:0"))
    workload.selected.copy_(workload.captured_selected_cpu.to(workload.selected.device))
    torch.cuda.synchronize()

    correctness, expected_workspace, eager_generic, _eager_candidate = _correctness_gate(
        op020, op019, workload
    )
    selected_sha = correctness["selected_sha256"]

    baseline_fn = lambda: op020._generic(workload)
    candidate_fn = lambda: op020._candidate(workload, op019)
    baseline_graph = _capture_static_graph(baseline_fn)
    candidate_graph = _capture_static_graph(candidate_fn)
    graph_correctness = _graph_correctness_gate(
        op020,
        workload,
        baseline_graph,
        candidate_graph,
        eager_generic,
        expected_workspace,
    )

    eager_timing = _paired_timing(baseline_fn, candidate_fn)
    graph_timing = _paired_timing(baseline_graph.replay, candidate_graph.replay)
    post_guard = _post_timing_guard(
        op020,
        workload,
        baseline_graph,
        candidate_graph,
        expected_workspace,
        selected_sha,
    )
    phase_gate = bool(
        eager_timing["passes_eight_percent_gate"]
        and graph_timing["passes_eight_percent_gate"]
    )
    return {
        "experiment_id": EXPERIMENT_ID,
        "status": "passed",
        "phase": args.phase,
        "scope": "rows4096_consumer_only_complete_transaction",
        "script_sha256": _sha256(Path(__file__).resolve()),
        "dependencies": {
            "op020_path": str(args.op020_module.resolve()),
            "op020_sha256": EXPECTED_OP020_SHA256,
            "op019_boundary_fixed_path": str(args.op019_module.resolve()),
            "op019_boundary_fixed_sha256": EXPECTED_OP019_SHA256,
            "imported_baseline_source_path": str(baseline_source),
            "imported_baseline_source_sha256": baseline_source_sha,
        },
        "fixture": {
            "root": str(fixture.root),
            "manifest_sha256": fixture.manifest_sha256,
            "rows": fixture.manifest["rows"],
            "selected_shape": list(workload.selected.shape),
            "request_run_starts": fixture.run_starts,
        },
        "timing_boundary": {
            "baseline": ["current_generic_qsa_sparse_paged_attention"],
            "candidate": [
                "output_zero",
                "workspace_clear",
                "membership_build",
                "R4_attention_with_exact_fallback",
            ],
            "producer_included": False,
            "profiler_used": False,
        },
        "correctness": correctness,
        "graph_correctness": graph_correctness,
        "timing": {"eager": eager_timing, "graph": graph_timing},
        "post_timing_guard": post_guard,
        "phase_gate_passed": phase_gate,
        "four_way_gate": {
            "required": ["prefill_eager", "prefill_graph", "mixed_eager", "mixed_graph"],
            "threshold_pct_each": GAIN_GATE_PCT,
            "status": "pending_other_phase_aggregation",
            "single_phase_cannot_promote": True,
        },
        "service_or_source_modified": False,
        "endpoint_performance_proven": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("prefill", "mixed"), required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--op020-module", type=Path, required=True)
    parser.add_argument("--op019-module", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.output.exists():
        raise SystemExit(f"output already exists: {args.output}")
    try:
        payload = run(args)
    except ExperimentBlocker as exc:
        payload = {
            "experiment_id": EXPERIMENT_ID,
            "status": "blocked",
            "phase": args.phase,
            "script_sha256": _sha256(Path(__file__).resolve()),
            "error_type": type(exc).__name__,
            "message": str(exc),
            "service_or_source_modified": False,
        }
        _write_json(args.output, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        raise SystemExit(3)
    except AssertionError as exc:
        payload = {
            "experiment_id": EXPERIMENT_ID,
            "status": "failed",
            "phase": args.phase,
            "script_sha256": _sha256(Path(__file__).resolve()),
            "error_type": type(exc).__name__,
            "message": str(exc),
            "service_or_source_modified": False,
        }
        _write_json(args.output, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        raise SystemExit(1)
    except Exception as exc:
        payload = {
            "experiment_id": EXPERIMENT_ID,
            "status": "failed",
            "phase": args.phase,
            "script_sha256": _sha256(Path(__file__).resolve()),
            "error_type": type(exc).__name__,
            "message": str(exc),
            "service_or_source_modified": False,
        }
        _write_json(args.output, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        raise SystemExit(1)
    _write_json(args.output, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
