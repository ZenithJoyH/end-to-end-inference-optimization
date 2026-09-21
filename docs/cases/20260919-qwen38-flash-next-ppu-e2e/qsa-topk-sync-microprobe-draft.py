#!/usr/bin/env python3
"""Attribute PPU cudaStreamSynchronize calls to QSA's native torch.topk.

This is an isolated diagnostic microprobe, not a service benchmark.  It never
imports or patches vLLM/Plugin/FlagGems.  Run it only after an operator has
reserved one otherwise-idle device for this process.

The QSA transaction performs one ``torch.topk`` for every score chunk emitted
by ``qsa_mqa_paged``.  P4K widths 1024 and 1280 both fit in one 128-MiB logits
workspace chunk for rows 64 and 4096, so one probe call represents one QSA
score-chunk TopK.  The probe records eager and CUDA-graph-replay paths plus an
elementwise control with the same tensor shape and event wait.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import torch
from torch.profiler import ProfilerActivity, profile, record_function


DEFAULT_ROWS = (64, 4096)
DEFAULT_COLUMNS = (1024, 1280)
DEFAULT_K = 512  # QSA token_topk=2048 / compression_ratio=4.
MARKER_PREFIX = "qsa_topk_sync_probe|"
MBTOPK_NAME_PARTS = (
    "mbtopk",
    "computeBlockDigitCounts",
    "computeBlockwiseWithinKCounts",
    "computeDigitCumSum",
    "gatherTopK",
    "radixSortKVInPlace",
    "DeviceScanByKeyKernel",
)


@dataclass
class ProbeCase:
    rows: int
    columns: int
    k: int
    logits: torch.Tensor
    topk_values: torch.Tensor
    topk_indices: torch.Tensor
    control_output: torch.Tensor
    topk_graph: torch.cuda.CUDAGraph | None = None
    control_graph: torch.cuda.CUDAGraph | None = None
    graph_error: str | None = None

    @property
    def shape_id(self) -> str:
        return f"rows={self.rows}|columns={self.columns}|k={self.k}"

    def topk_eager(self) -> None:
        torch.topk(
            self.logits,
            self.k,
            dim=-1,
            largest=True,
            sorted=True,
            out=(self.topk_values, self.topk_indices),
        )

    def control_eager(self) -> None:
        torch.add(self.logits, 0.0, out=self.control_output)

    def topk_replay(self) -> None:
        if self.topk_graph is None:
            raise RuntimeError(f"TopK graph unavailable for {self.shape_id}")
        self.topk_graph.replay()

    def control_replay(self) -> None:
        if self.control_graph is None:
            raise RuntimeError(f"control graph unavailable for {self.shape_id}")
        self.control_graph.replay()


def _csv_ints(value: str) -> tuple[int, ...]:
    values = tuple(int(item) for item in value.split(",") if item.strip())
    if not values or any(item <= 0 for item in values):
        raise argparse.ArgumentTypeError("expected comma-separated positive integers")
    return values


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _make_case(rows: int, columns: int, k: int) -> ProbeCase:
    if k > columns:
        raise ValueError(f"k={k} exceeds columns={columns}")
    # QSA qsa_mqa_paged returns FP32 logits.  A tiny deterministic row/column
    # offset avoids accidental tie-heavy inputs without changing the TopK path.
    logits = torch.randn((rows, columns), device="cuda", dtype=torch.float32)
    logits.add_(
        torch.arange(columns, device="cuda", dtype=torch.float32).mul_(1.0e-7)
    )
    return ProbeCase(
        rows=rows,
        columns=columns,
        k=k,
        logits=logits,
        topk_values=torch.empty((rows, k), device="cuda", dtype=torch.float32),
        topk_indices=torch.empty((rows, k), device="cuda", dtype=torch.int64),
        control_output=torch.empty_like(logits),
    )


def _capture_graph(fn: Callable[[], None]) -> torch.cuda.CUDAGraph:
    for _ in range(3):
        fn()
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, capture_error_mode="thread_local"):
        fn()
    torch.cuda.synchronize()
    return graph


def _prepare_graphs(case: ProbeCase) -> None:
    try:
        case.topk_eager()
        eager_values = case.topk_values.clone()
        eager_indices = case.topk_indices.clone()
        case.topk_graph = _capture_graph(case.topk_eager)
        case.control_graph = _capture_graph(case.control_eager)
        case.topk_replay()
        done = torch.cuda.Event(blocking=True)
        done.record()
        done.synchronize()
        torch.testing.assert_close(case.topk_values, eager_values, atol=0, rtol=0)
        torch.testing.assert_close(case.topk_indices, eager_indices, atol=0, rtol=0)
    except Exception as exc:  # Preserve eager evidence if graph capture is unsupported.
        case.topk_graph = None
        case.control_graph = None
        case.graph_error = f"{type(exc).__name__}: {exc}"


def _measure_without_profiler(
    fn: Callable[[], None], warmup: int, repeat: int
) -> dict[str, float]:
    for _ in range(warmup):
        fn()
    torch.cuda.synchronize()
    start_event = torch.cuda.Event(enable_timing=True)
    end_event = torch.cuda.Event(enable_timing=True)
    started_ns = time.perf_counter_ns()
    start_event.record()
    for _ in range(repeat):
        fn()
    end_event.record()
    torch.cuda.synchronize()
    elapsed_ns = time.perf_counter_ns() - started_ns
    return {
        "host_wall_us_per_call": elapsed_ns / 1000.0 / repeat,
        "device_event_us_per_call": float(start_event.elapsed_time(end_event))
        * 1000.0
        / repeat,
    }


def _marker(operation: str, mode: str, case: ProbeCase, iteration: int) -> str:
    return (
        f"{MARKER_PREFIX}operation={operation}|mode={mode}|{case.shape_id}"
        f"|iteration={iteration}"
    )


def _run_profile_block(
    operation: str,
    mode: str,
    case: ProbeCase,
    fn: Callable[[], None],
    repeat: int,
) -> None:
    # Event synchronization bounds asynchronous device activity inside each
    # record_function interval.  It maps to cudaEventSynchronize, not the
    # cudaStreamSynchronize event under test.
    done_events = [torch.cuda.Event(blocking=True) for _ in range(repeat)]
    for iteration, done in enumerate(done_events):
        with record_function(_marker(operation, mode, case, iteration)):
            fn()
            done.record()
            done.synchronize()


def _load_trace(path: Path) -> list[dict]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(document, dict):
        events = document.get("traceEvents")
    else:
        events = document
    if not isinstance(events, list):
        raise ValueError("Chrome trace has no traceEvents list")
    return [event for event in events if isinstance(event, dict)]


def _is_complete_event(event: dict) -> bool:
    return event.get("ph") == "X" and isinstance(event.get("ts"), (int, float))


def _base_marker(marker_name: str) -> str:
    return re.sub(r"\|iteration=\d+$", "", marker_name)


def _summarize_trace(trace_path: Path, repeat: int) -> dict[str, dict]:
    events = _load_trace(trace_path)
    markers: list[tuple[str, float, float]] = []
    for event in events:
        name = str(event.get("name", ""))
        # PPU profiler exports every record_function as both a CPU
        # user_annotation and a GPU annotation.  The CPU interval encloses the
        # host runtime calls under test; counting both duplicates every marker
        # and can associate the same runtime event twice.
        if (
            _is_complete_event(event)
            and event.get("cat") == "user_annotation"
            and name.startswith(MARKER_PREFIX)
        ):
            start = float(event["ts"])
            markers.append((_base_marker(name), start, start + float(event.get("dur", 0))))

    grouped: dict[str, dict] = {}
    for base, start, end in markers:
        row = grouped.setdefault(
            base,
            {
                "marker_count": 0,
                "marker_total_us": 0.0,
                "cuda_stream_synchronize_count": 0,
                "cuda_stream_synchronize_total_us": 0.0,
                "cuda_event_synchronize_count": 0,
                "cuda_event_synchronize_total_us": 0.0,
                "aten_topk_count": 0,
                "aten_topk_total_us": 0.0,
                "mbtopk_kernel_count": 0,
                "mbtopk_kernel_total_us": 0.0,
                "mbtopk_kernel_counts_by_name": {},
            },
        )
        row["marker_count"] += 1
        row["marker_total_us"] += end - start
        for event in events:
            if not _is_complete_event(event):
                continue
            timestamp = float(event["ts"])
            if timestamp < start or timestamp > end:
                continue
            name = str(event.get("name", ""))
            duration = float(event.get("dur", 0.0))
            if name == "cudaStreamSynchronize":
                row["cuda_stream_synchronize_count"] += 1
                row["cuda_stream_synchronize_total_us"] += duration
            elif name == "cudaEventSynchronize":
                row["cuda_event_synchronize_count"] += 1
                row["cuda_event_synchronize_total_us"] += duration
            elif name == "aten::topk":
                row["aten_topk_count"] += 1
                row["aten_topk_total_us"] += duration
            if any(part in name for part in MBTOPK_NAME_PARTS):
                row["mbtopk_kernel_count"] += 1
                row["mbtopk_kernel_total_us"] += duration
                counts = row["mbtopk_kernel_counts_by_name"]
                counts[name] = counts.get(name, 0) + 1

    for row in grouped.values():
        marker_count = row["marker_count"]
        row["marker_avg_us"] = row["marker_total_us"] / max(marker_count, 1)
        row["planned_repeat"] = repeat
    return grouped


def _parse_marker_fields(marker: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for item in marker.removeprefix(MARKER_PREFIX).split("|"):
        key, value = item.split("=", 1)
        fields[key] = value
    return fields


def _evaluate(grouped: dict[str, dict], repeat: int) -> list[dict]:
    indexed: dict[tuple[str, str, str, str], tuple[str, dict]] = {}
    for marker, counters in grouped.items():
        fields = _parse_marker_fields(marker)
        key = (fields["mode"], fields["rows"], fields["columns"], fields["k"])
        indexed[(fields["operation"], *key)] = (marker, counters)

    evaluations = []
    topk_keys = [key for key in indexed if key[0] == "topk"]
    for topk_key in sorted(topk_keys):
        _, mode, rows, columns, k = topk_key
        control_key = ("control", mode, rows, columns, k)
        marker, topk = indexed[topk_key]
        if control_key not in indexed:
            evaluations.append(
                {"marker": marker, "decision": "inconclusive_missing_control"}
            )
            continue
        _, control = indexed[control_key]
        topk_sync = topk["cuda_stream_synchronize_count"]
        control_sync = control["cuda_stream_synchronize_count"]
        adjusted = topk_sync - control_sync
        ratio = adjusted / repeat
        if topk["marker_count"] != repeat or control["marker_count"] != repeat:
            decision = "inconclusive_marker_count"
        elif control_sync != 0:
            decision = "inconclusive_control_has_stream_sync"
        elif adjusted == 3 * repeat:
            decision = "supports_exactly_three_stream_sync_per_topk"
        else:
            decision = "refutes_exactly_three_stream_sync_per_topk"
        evaluations.append(
            {
                "marker": marker,
                "mode": mode,
                "rows": int(rows),
                "columns": int(columns),
                "k": int(k),
                "topk_stream_sync_count": topk_sync,
                "control_stream_sync_count": control_sync,
                "adjusted_stream_sync_count": adjusted,
                "adjusted_stream_sync_per_topk": ratio,
                "topk_stream_sync_total_us": topk[
                    "cuda_stream_synchronize_total_us"
                ],
                "control_stream_sync_total_us": control[
                    "cuda_stream_synchronize_total_us"
                ],
                "aten_topk_count": topk["aten_topk_count"],
                "mbtopk_kernel_count": topk["mbtopk_kernel_count"],
                "mbtopk_kernel_counts_by_name": topk[
                    "mbtopk_kernel_counts_by_name"
                ],
                "decision": decision,
            }
        )
    return evaluations


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=_csv_ints, default=DEFAULT_ROWS)
    parser.add_argument("--columns", type=_csv_ints, default=DEFAULT_COLUMNS)
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--repeat", type=int, default=8)
    parser.add_argument("--device-index", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--acknowledge-isolated-device",
        action="store_true",
        help="required acknowledgement that the selected device is idle/reserved",
    )
    args = parser.parse_args()
    if not args.acknowledge_isolated_device:
        parser.error("refusing to run without --acknowledge-isolated-device")
    if args.k <= 0 or args.repeat <= 0 or args.warmup < 0:
        parser.error("k/repeat must be positive and warmup non-negative")
    if args.output_dir.exists():
        parser.error(f"output directory already exists: {args.output_dir}")
    if not torch.cuda.is_available():
        parser.error("CUDA-compatible accelerator is unavailable")

    torch.cuda.set_device(args.device_index)
    torch.manual_seed(74284)
    torch.cuda.manual_seed_all(74284)
    cases = [
        _make_case(rows, columns, args.k)
        for rows in args.rows
        for columns in args.columns
    ]
    for case in cases:
        _prepare_graphs(case)

    timings: dict[str, dict] = {}
    for case in cases:
        timings[f"topk|eager|{case.shape_id}"] = _measure_without_profiler(
            case.topk_eager, args.warmup, args.repeat
        )
        timings[f"control|eager|{case.shape_id}"] = _measure_without_profiler(
            case.control_eager, args.warmup, args.repeat
        )
        if case.topk_graph is not None and case.control_graph is not None:
            timings[f"topk|graph|{case.shape_id}"] = _measure_without_profiler(
                case.topk_replay, args.warmup, args.repeat
            )
            timings[f"control|graph|{case.shape_id}"] = _measure_without_profiler(
                case.control_replay, args.warmup, args.repeat
            )

    args.output_dir.mkdir(parents=True, exist_ok=False)
    trace_path = args.output_dir / "trace.json"
    with profile(
        activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
        record_shapes=False,
        profile_memory=False,
        with_stack=False,
    ) as profiler:
        for case in cases:
            _run_profile_block(
                "control", "eager", case, case.control_eager, args.repeat
            )
            _run_profile_block("topk", "eager", case, case.topk_eager, args.repeat)
            if case.topk_graph is not None and case.control_graph is not None:
                _run_profile_block(
                    "control", "graph", case, case.control_replay, args.repeat
                )
                _run_profile_block(
                    "topk", "graph", case, case.topk_replay, args.repeat
                )
    profiler.export_chrome_trace(str(trace_path))

    grouped = _summarize_trace(trace_path, args.repeat)
    evaluations = _evaluate(grouped, args.repeat)
    script_path = Path(__file__).resolve()
    payload = {
        "schema_version": 1,
        "experiment": "qsa-topk-cuda-stream-sync-attribution",
        "scope": "standalone_microprobe_not_service_performance",
        "shape_rationale": {
            "rows_64": "P4K decode concurrency",
            "rows_4096": "one max-num-batched-tokens P4K prefill scheduling step",
            "columns_1024": "4096 visible tokens / compression_ratio 4",
            "columns_1280": "5120 visible tokens / compression_ratio 4",
            "k": "token_topk 2048 / compression_ratio 4",
            "boundary": (
                "1024/1280 are semantic P4K visible widths. If live metadata shows "
                "the actual torch.topk logits width is static 8448 or full capacity "
                "20000, rerun with that value via --columns."
            ),
        },
        "device": {
            "index": args.device_index,
            "name": torch.cuda.get_device_name(args.device_index),
            "torch_version": torch.__version__,
        },
        "warmup": args.warmup,
        "repeat": args.repeat,
        "rows": list(args.rows),
        "columns": list(args.columns),
        "k": args.k,
        "graph_capture": [
            {
                "rows": case.rows,
                "columns": case.columns,
                "captured": case.graph_error is None,
                "error": case.graph_error,
            }
            for case in cases
        ],
        "no_profiler_timings": timings,
        "trace_groups": grouped,
        "evaluations": evaluations,
        "artifacts": {
            "script": {"path": str(script_path), "sha256": _sha256(script_path)},
            "trace": {"path": str(trace_path), "sha256": _sha256(trace_path)},
        },
    }
    result_path = args.output_dir / "result.json"
    result_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
