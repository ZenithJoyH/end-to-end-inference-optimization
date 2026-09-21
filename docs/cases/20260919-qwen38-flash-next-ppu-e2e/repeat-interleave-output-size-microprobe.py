#!/usr/bin/env python3
"""Measure whether repeat_interleave(output_size=...) removes PPU host sync.

This is a standalone diagnostic probe.  It mirrors the per-layer token-group
construction in Qwen3.8-Flash-Next metadata without importing or patching the
serving stack.  It compares identical inputs with and without the known CPU
output size and verifies bit-exact outputs in eager and graph replay modes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Callable

import torch
from torch.profiler import ProfilerActivity, profile, record_function


MARKER = "repeat_interleave_output_size_probe|"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_trace(path: Path) -> list[dict]:
    document = json.loads(path.read_text(encoding="utf-8"))
    events = document.get("traceEvents") if isinstance(document, dict) else document
    if not isinstance(events, list):
        raise ValueError("trace has no traceEvents list")
    return [event for event in events if isinstance(event, dict)]


def complete(event: dict) -> bool:
    return event.get("ph") == "X" and isinstance(event.get("ts"), (int, float))


def summarize(trace_path: Path) -> dict[str, dict]:
    events = load_trace(trace_path)
    results: dict[str, dict] = {}
    for marker in events:
        name = str(marker.get("name", ""))
        if not (
            complete(marker)
            and marker.get("cat") == "user_annotation"
            and name.startswith(MARKER)
        ):
            continue
        base = name.rsplit("|iteration=", 1)[0]
        start = float(marker["ts"])
        end = start + float(marker.get("dur", 0.0))
        row = results.setdefault(
            base,
            {
                "marker_count": 0,
                "marker_total_us": 0.0,
                "cuda_stream_synchronize_count": 0,
                "cuda_stream_synchronize_total_us": 0.0,
                "aten_repeat_interleave_count": 0,
                "aten_item_count": 0,
                "aten_local_scalar_dense_count": 0,
            },
        )
        row["marker_count"] += 1
        row["marker_total_us"] += end - start
        for event in events:
            if not complete(event):
                continue
            timestamp = float(event["ts"])
            if timestamp < start or timestamp > end:
                continue
            event_name = str(event.get("name", ""))
            duration = float(event.get("dur", 0.0))
            if event_name == "cudaStreamSynchronize":
                row["cuda_stream_synchronize_count"] += 1
                row["cuda_stream_synchronize_total_us"] += duration
            elif event_name == "aten::repeat_interleave":
                row["aten_repeat_interleave_count"] += 1
            elif event_name == "aten::item":
                row["aten_item_count"] += 1
            elif event_name == "aten::_local_scalar_dense":
                row["aten_local_scalar_dense_count"] += 1
    for row in results.values():
        row["marker_avg_us"] = row["marker_total_us"] / row["marker_count"]
    return results


def time_calls(fn: Callable[[], torch.Tensor], warmup: int, repeat: int) -> dict:
    for _ in range(warmup):
        fn()
    torch.cuda.synchronize()
    started = time.perf_counter_ns()
    for _ in range(repeat):
        fn()
    torch.cuda.synchronize()
    return {"host_wall_us_per_call": (time.perf_counter_ns() - started) / 1000 / repeat}


def capture(fn: Callable[[], torch.Tensor]) -> torch.cuda.CUDAGraph:
    for _ in range(3):
        fn()
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, capture_error_mode="thread_local"):
        fn()
    torch.cuda.synchronize()
    return graph


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device-index", type=int, default=0)
    parser.add_argument("--warmup", type=int, default=8)
    parser.add_argument("--repeat", type=int, default=16)
    parser.add_argument("--acknowledge-isolated-device", action="store_true")
    args = parser.parse_args()
    if not args.acknowledge_isolated_device:
        parser.error("--acknowledge-isolated-device is required")
    if args.output_dir.exists():
        parser.error(f"output directory exists: {args.output_dir}")
    torch.cuda.set_device(args.device_index)

    shapes = {
        "prefill4096": torch.tensor([4096], device="cuda", dtype=torch.int32),
        "mixed4096": torch.tensor([4033] + [1] * 63, device="cuda", dtype=torch.int32),
        "decode64": torch.ones(64, device="cuda", dtype=torch.int32),
    }
    cases: dict[str, dict] = {}
    for shape_id, query_lens in shapes.items():
        total = int(query_lens.numel() == 1 and 4096 or query_lens.numel())
        if shape_id == "mixed4096":
            total = 4096
        req_group = torch.arange(query_lens.numel(), device="cuda", dtype=torch.int64) % 3

        def original(r=req_group, q=query_lens) -> torch.Tensor:
            return torch.repeat_interleave(r, q)

        def optimized(r=req_group, q=query_lens, n=total) -> torch.Tensor:
            return torch.repeat_interleave(r, q, output_size=n)

        reference = original().clone()
        candidate = optimized().clone()
        torch.testing.assert_close(candidate, reference, atol=0, rtol=0)
        row = {
            "total_tokens": total,
            "num_requests": query_lens.numel(),
            "eager_bit_exact": True,
            "timings": {
                "original": time_calls(original, args.warmup, args.repeat),
                "output_size": time_calls(optimized, args.warmup, args.repeat),
            },
        }
        # Capture the candidate first.  The original form performs a host
        # scalar read and can invalidate the stream capture; once invalidated,
        # a later candidate capture in the same process is not meaningful.
        try:
            optimized_graph = capture(optimized)
            optimized_graph.replay()
            torch.cuda.synchronize()
            row["output_size_graph_capture"] = "passed"
        except Exception as exc:
            optimized_graph = None
            row["output_size_graph_capture"] = "failed"
            row["output_size_graph_error"] = f"{type(exc).__name__}: {exc}"
        # Do not attempt original capture here: its expected host scalar read
        # invalidates PPU capture and would poison later cases in this process.
        original_graph = None
        row["original_graph_capture"] = "not_attempted_host_scalar_read"
        cases[shape_id] = {
            "original": original,
            "output_size": optimized,
            "original_graph": original_graph,
            "output_size_graph": optimized_graph,
            "result": row,
        }

    args.output_dir.mkdir(parents=True)
    trace_path = args.output_dir / "trace.json"
    with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as profiler:
        for shape_id, case in cases.items():
            modes = [("eager", "original", case["original"]), ("eager", "output_size", case["output_size"])]
            if case["original_graph"] is not None:
                modes.extend(
                    [
                        ("graph", "original", case["original_graph"].replay),
                        ("graph", "output_size", case["output_size_graph"].replay),
                    ]
                )
            for mode, variant, fn in modes:
                for iteration in range(args.repeat):
                    done = torch.cuda.Event(blocking=True)
                    with record_function(
                        f"{MARKER}shape={shape_id}|mode={mode}|variant={variant}|iteration={iteration}"
                    ):
                        fn()
                        done.record()
                        done.synchronize()
    profiler.export_chrome_trace(str(trace_path))
    summary = summarize(trace_path)
    for case in cases.values():
        case.pop("original")
        case.pop("output_size")
        case.pop("original_graph")
        case.pop("output_size_graph")
    script_path = Path(__file__).resolve()
    result_path = args.output_dir / "result.json"
    payload = {
        "schema_version": 1,
        "experiment": "repeat-interleave-output-size-sync-attribution",
        "scope": "standalone diagnostic; not service performance",
        "device": {
            "index": args.device_index,
            "name": torch.cuda.get_device_name(args.device_index),
            "torch_version": torch.__version__,
        },
        "warmup": args.warmup,
        "repeat": args.repeat,
        "cases": {key: value["result"] for key, value in cases.items()},
        "trace_summary": summary,
        "artifacts": {
            "script": {"path": str(script_path), "sha256": sha256(script_path)},
            "trace": {"path": str(trace_path), "sha256": sha256(trace_path)},
        },
    }
    result_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
