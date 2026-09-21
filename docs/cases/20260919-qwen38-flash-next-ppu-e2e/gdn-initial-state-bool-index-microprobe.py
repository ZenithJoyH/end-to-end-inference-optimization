#!/usr/bin/env python3
"""Probe the real prof005 GDN bool-index synchronization callsite."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Callable

import torch
from torch.profiler import ProfilerActivity, profile, record_function

import flag_gems


# Reproduce the serving process's FlagGems path for the exact operators under
# test without enabling unrelated ATen overrides in this standalone process.
flag_gems.only_enable(
    include=[
        "index_put_",
        "_index_put_impl_",
        "nonzero_numpy",
        "masked_fill_",
        "index_fill_",
    ]
)


MARKER = "gdn_initial_state_bool_index_probe|"
EVENT_NAMES = {
    "cudaStreamSynchronize",
    "aten::index_put_",
    "aten::_index_put_impl_",
    "aten::masked_fill_",
    "aten::index_fill_",
    "aten::nonzero",
    "aten::nonzero_numpy",
    "aten::item",
    "aten::_local_scalar_dense",
    "aten::copy_",
    "aten::to",
    "aten::_to_copy",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_events(path: Path) -> list[dict]:
    value = json.loads(path.read_text(encoding="utf-8"))
    events = value.get("traceEvents") if isinstance(value, dict) else value
    if not isinstance(events, list):
        raise ValueError("trace has no traceEvents")
    return [event for event in events if isinstance(event, dict)]


def complete(event: dict) -> bool:
    return event.get("ph") == "X" and isinstance(event.get("ts"), (int, float))


def summarize(path: Path) -> dict[str, dict]:
    events = load_events(path)
    result: dict[str, dict] = {}
    for marker in events:
        name = str(marker.get("name", ""))
        if not (
            complete(marker)
            and marker.get("cat") == "user_annotation"
            and name.startswith(MARKER)
        ):
            continue
        key = name.rsplit("|iteration=", 1)[0]
        start = float(marker["ts"])
        end = start + float(marker.get("dur", 0.0))
        row = result.setdefault(
            key, {"marker_count": 0, "marker_total_us": 0.0, "events": {}}
        )
        row["marker_count"] += 1
        row["marker_total_us"] += end - start
        for event in events:
            if not complete(event):
                continue
            timestamp = float(event["ts"])
            event_name = str(event.get("name", ""))
            if timestamp < start or timestamp > end or event_name not in EVENT_NAMES:
                continue
            bucket = row["events"].setdefault(
                event_name, {"count": 0, "total_us": 0.0}
            )
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


def graph_two_replays(fn: Callable[[], torch.Tensor]) -> str:
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
    parser.add_argument("--warmup", type=int, default=8)
    parser.add_argument("--repeat", type=int, default=16)
    parser.add_argument("--acknowledge-isolated-device", action="store_true")
    args = parser.parse_args()
    if not args.acknowledge_isolated_device:
        parser.error("--acknowledge-isolated-device is required")
    if args.output_dir.exists():
        parser.error(f"output directory exists: {args.output_dir}")
    torch.cuda.set_device(args.device_index)

    case_masks = {
        "b1_no_initial": [False],
        "b1_has_initial": [True],
        "b4_mixed": [False, True, False, True],
        "b64_mixed": [value % 3 != 0 for value in range(64)],
    }
    cases: dict[str, dict] = {}
    callables: dict[tuple[str, str], Callable[[], torch.Tensor]] = {}
    for case_id, mask_values in case_masks.items():
        batch = len(mask_values)
        mask_cpu = torch.tensor(mask_values, dtype=torch.bool)
        mask = mask_cpu.to("cuda")
        no_initial_indices = (~mask_cpu).nonzero(as_tuple=True)[0].to("cuda")
        expanded_no_initial = (~mask).view(batch, 1, 1, 1)
        seed = torch.randn(batch, 6, 128, 128, dtype=torch.bfloat16, device="cuda")
        if no_initial_indices.numel():
            seed[no_initial_indices, 0, 0, 0] = float("nan")
        original_buffer = seed.clone()
        masked_buffer = seed.clone()
        index_fill_buffer = seed.clone()

        def original(output=original_buffer, has_initial=mask) -> torch.Tensor:
            output[~has_initial, ...] = 0
            return output

        def masked_fill(output=masked_buffer, no_initial=expanded_no_initial) -> torch.Tensor:
            output.masked_fill_(no_initial, 0)
            return output

        def index_fill(output=index_fill_buffer, indices=no_initial_indices) -> torch.Tensor:
            output.index_fill_(0, indices, 0)
            return output

        reference = original().clone()
        masked = masked_fill().clone()
        indexed = index_fill().clone()
        torch.cuda.synchronize()
        torch.testing.assert_close(masked.cpu(), reference.cpu(), atol=0, rtol=0, equal_nan=True)
        torch.testing.assert_close(indexed.cpu(), reference.cpu(), atol=0, rtol=0, equal_nan=True)
        row = {
            "batch": batch,
            "state_shape": [batch, 6, 128, 128],
            "has_initial_state": mask_values,
            "eager_bit_exact_including_nan_rows": True,
            "host_wall_us_per_call": {
                "bool_index_put": time_calls(original, args.warmup, args.repeat),
                "masked_fill": time_calls(masked_fill, args.warmup, args.repeat),
                "cpu_index_fill": time_calls(index_fill, args.warmup, args.repeat),
            },
        }
        for name, fn in (("masked_fill", masked_fill), ("cpu_index_fill", index_fill)):
            try:
                row[f"{name}_graph_capture_two_replays"] = graph_two_replays(fn)
            except Exception as exc:
                row[f"{name}_graph_capture_two_replays"] = "failed"
                row[f"{name}_graph_error"] = f"{type(exc).__name__}: {exc}"
        cases[case_id] = row
        callables[(case_id, "bool_index_put")] = original
        callables[(case_id, "masked_fill")] = masked_fill
        callables[(case_id, "cpu_index_fill")] = index_fill

    args.output_dir.mkdir(parents=True)
    trace_path = args.output_dir / "trace.json"
    with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as profiler:
        for case_id in case_masks:
            for variant in ("bool_index_put", "masked_fill", "cpu_index_fill"):
                fn = callables[(case_id, variant)]
                for iteration in range(args.repeat):
                    done = torch.cuda.Event(blocking=True)
                    with record_function(
                        f"{MARKER}case={case_id}|variant={variant}|iteration={iteration}"
                    ):
                        fn()
                        done.record()
                        done.synchronize()
    profiler.export_chrome_trace(str(trace_path))
    script_path = Path(__file__).resolve()
    result_path = args.output_dir / "result.json"
    payload = {
        "schema_version": 1,
        "experiment": "qwen38-gdn-initial-state-bool-index-sync",
        "scope": "standalone diagnostic; not service performance",
        "dispatch": "FlagGems-only enable for index_put/nonzero_numpy/masked_fill/index_fill",
        "production_state_shape_per_request_tp8": [6, 128, 128],
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
