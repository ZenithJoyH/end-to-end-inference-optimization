#!/usr/bin/env python3
"""Isolate Qwen3.8 request-group index_put synchronization.

This diagnostic mirrors the two per-layer request-group assignments in
PleShortConvAttentionMetadataBuilder.  It compares advanced-index assignment
with index_fill_ on identical, fixed int64 request-index tensors.  It neither
imports nor patches the serving stack.
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


MARKER = "index_put_index_fill_probe|"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def trace_events(path: Path) -> list[dict]:
    value = json.loads(path.read_text(encoding="utf-8"))
    events = value.get("traceEvents") if isinstance(value, dict) else value
    if not isinstance(events, list):
        raise ValueError("trace has no traceEvents")
    return [event for event in events if isinstance(event, dict)]


def complete(event: dict) -> bool:
    return event.get("ph") == "X" and isinstance(event.get("ts"), (int, float))


def summarize(path: Path) -> dict[str, dict]:
    events = trace_events(path)
    names = (
        "cudaStreamSynchronize",
        "aten::index_put_",
        "aten::_index_put_impl_",
        "aten::index_fill_",
        "aten::nonzero",
        "aten::nonzero_numpy",
        "aten::item",
        "aten::_local_scalar_dense",
        "aten::copy_",
        "aten::to",
        "aten::_to_copy",
    )
    result: dict[str, dict] = {}
    for marker in events:
        marker_name = str(marker.get("name", ""))
        if not (
            complete(marker)
            and marker.get("cat") == "user_annotation"
            and marker_name.startswith(MARKER)
        ):
            continue
        key = marker_name.rsplit("|iteration=", 1)[0]
        start = float(marker["ts"])
        end = start + float(marker.get("dur", 0.0))
        row = result.setdefault(
            key,
            {"marker_count": 0, "marker_total_us": 0.0, "events": {}},
        )
        row["marker_count"] += 1
        row["marker_total_us"] += end - start
        for event in events:
            if not complete(event):
                continue
            timestamp = float(event["ts"])
            name = str(event.get("name", ""))
            if timestamp < start or timestamp > end or name not in names:
                continue
            bucket = row["events"].setdefault(name, {"count": 0, "total_us": 0.0})
            bucket["count"] += 1
            bucket["total_us"] += float(event.get("dur", 0.0))
    for row in result.values():
        row["marker_avg_us"] = row["marker_total_us"] / row["marker_count"]
    return result


def time_calls(fn: Callable[[], torch.Tensor], warmup: int, repeat: int) -> float:
    for _ in range(warmup):
        fn()
    torch.cuda.synchronize()
    started = time.perf_counter_ns()
    for _ in range(repeat):
        fn()
    torch.cuda.synchronize()
    return (time.perf_counter_ns() - started) / 1000 / repeat


def capture_and_replay_twice(fn: Callable[[], torch.Tensor]) -> str:
    for _ in range(3):
        fn()
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, capture_error_mode="thread_local"):
        fn()
    for _ in range(2):
        graph.replay()
        torch.cuda.synchronize()
    return "passed"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device-index", type=int, default=0)
    parser.add_argument("--warmup", type=int, default=16)
    parser.add_argument("--repeat", type=int, default=32)
    parser.add_argument("--acknowledge-isolated-device", action="store_true")
    args = parser.parse_args()
    if not args.acknowledge_isolated_device:
        parser.error("--acknowledge-isolated-device is required")
    if args.output_dir.exists():
        parser.error(f"output directory exists: {args.output_dir}")
    torch.cuda.set_device(args.device_index)

    shapes = {
        "prefill1": {"num_reqs": 1, "spec": [], "decode": []},
        "mixed64": {"num_reqs": 64, "spec": [], "decode": list(range(1, 64))},
        "decode64": {"num_reqs": 64, "spec": [], "decode": list(range(64))},
        "spec_mixed64": {
            "num_reqs": 64,
            "spec": [0, 4],
            "decode": [value for value in range(1, 12) if value != 4],
        },
    }
    cases: dict[str, dict] = {}
    callables: dict[tuple[str, str], Callable[[], torch.Tensor]] = {}
    for shape_id, shape in shapes.items():
        spec = torch.tensor(shape["spec"], dtype=torch.int64, device="cuda")
        decode = torch.tensor(shape["decode"], dtype=torch.int64, device="cuda")
        original_buffer = torch.empty(shape["num_reqs"], dtype=torch.int64, device="cuda")
        candidate_buffer = torch.empty_like(original_buffer)

        def original(
            output=original_buffer, spec_idx=spec, decode_idx=decode
        ) -> torch.Tensor:
            output.fill_(2)
            output[spec_idx] = 0
            output[decode_idx] = 1
            return output

        def index_fill(
            output=candidate_buffer, spec_idx=spec, decode_idx=decode
        ) -> torch.Tensor:
            output.fill_(2)
            output.index_fill_(0, spec_idx, 0)
            output.index_fill_(0, decode_idx, 1)
            return output

        reference = original().clone()
        candidate = index_fill().clone()
        torch.cuda.synchronize()
        torch.testing.assert_close(candidate.cpu(), reference.cpu(), atol=0, rtol=0)
        row = {
            "num_requests": shape["num_reqs"],
            "num_spec_indices": len(shape["spec"]),
            "num_decode_indices": len(shape["decode"]),
            "eager_bit_exact": True,
            "timings_host_wall_us_per_call": {
                "index_put": time_calls(original, args.warmup, args.repeat),
                "index_fill": time_calls(index_fill, args.warmup, args.repeat),
            },
        }
        try:
            row["index_fill_graph_capture_two_replays"] = capture_and_replay_twice(index_fill)
        except Exception as exc:
            row["index_fill_graph_capture_two_replays"] = "failed"
            row["index_fill_graph_error"] = f"{type(exc).__name__}: {exc}"
        cases[shape_id] = row
        callables[(shape_id, "index_put")] = original
        callables[(shape_id, "index_fill")] = index_fill

    args.output_dir.mkdir(parents=True)
    trace_path = args.output_dir / "trace.json"
    with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as profiler:
        for shape_id in shapes:
            for variant in ("index_put", "index_fill"):
                fn = callables[(shape_id, variant)]
                for iteration in range(args.repeat):
                    done = torch.cuda.Event(blocking=True)
                    with record_function(
                        f"{MARKER}shape={shape_id}|variant={variant}|iteration={iteration}"
                    ):
                        fn()
                        done.record()
                        done.synchronize()
    profiler.export_chrome_trace(str(trace_path))
    script_path = Path(__file__).resolve()
    result_path = args.output_dir / "result.json"
    payload = {
        "schema_version": 1,
        "experiment": "qwen38-request-group-index-put-vs-index-fill-sync",
        "scope": "standalone diagnostic; not service performance",
        "device": {
            "index": args.device_index,
            "name": torch.cuda.get_device_name(args.device_index),
            "torch_version": torch.__version__,
        },
        "warmup": args.warmup,
        "repeat": args.repeat,
        "cases": cases,
        "trace_summary": summarize(trace_path),
        "artifacts": {
            "script": {"path": str(script_path), "sha256": sha256(script_path)},
            "trace": {"path": str(trace_path), "sha256": sha256(trace_path)},
        },
    }
    result_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
