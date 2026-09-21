#!/usr/bin/env python3
"""No-profiler TP8 PCCL all-reduce graph microbenchmark for fw-010.

The production model has 48 layers and performs one tensor-parallel reduction
after attention plus one after the MoE/MLP path, so one model step contains 96
hidden-state all-reduces.  The retained P4K service uses BF16 hidden size 2560,
4096 scheduled tokens for Prefill/Mixed, and at most 64 Decode rows.

Run this script in a fresh torchrun process for each PCCL environment variant.
Do not import vLLM and do not enable a profiler.  Each shape captures a graph
containing the 96-call sequence, verifies the capture and two changed-input
replays bit-for-bit, and then measures whole-chain graph replay latency on every
rank.  Buffer resets and barriers are outside the timed interval.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import statistics
import sys
from typing import Any

import torch
import torch.distributed as dist


WORLD_SIZE = 8
HIDDEN_SIZE = 2560
DEFAULT_ROWS = (1, 64, 4096)
DEFAULT_CALLS_PER_CHAIN = 96


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", default=",".join(map(str, DEFAULT_ROWS)))
    parser.add_argument("--hidden-size", type=int, default=HIDDEN_SIZE)
    parser.add_argument(
        "--calls-per-chain", type=int, default=DEFAULT_CALLS_PER_CHAIN
    )
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    args.rows = tuple(int(value) for value in args.rows.split(",") if value)
    if not args.rows or any(value <= 0 for value in args.rows):
        parser.error("--rows must contain positive comma-separated integers")
    if args.hidden_size <= 0 or args.calls_per_chain <= 0:
        parser.error("hidden size and calls per chain must be positive")
    if args.warmup < 2:
        parser.error("at least two graph warmups are required")
    if args.repeats < 5:
        parser.error("at least five measured repeats are required")
    return args


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(fraction * len(ordered)) - 1)
    return ordered[index]


def fill_rank_inputs(buffers: list[torch.Tensor], rank: int, offset: int) -> int:
    """Fill exact small BF16 integers and return the exact all-reduce sum."""
    value = rank + offset
    expected = sum(peer + offset for peer in range(WORLD_SIZE))
    for buffer in buffers:
        buffer.fill_(value)
    return expected


def assert_exact(buffers: list[torch.Tensor], expected: int, context: str) -> None:
    for index, buffer in enumerate(buffers):
        mismatches = torch.count_nonzero(buffer != expected).item()
        if mismatches:
            raise AssertionError(
                f"{context}: buffer={index}, expected={expected}, "
                f"mismatches={mismatches}"
            )


def benchmark_shape(
    *,
    rows: int,
    hidden_size: int,
    calls_per_chain: int,
    warmup: int,
    repeats: int,
    rank: int,
) -> tuple[dict[str, Any], tuple[Any, list[torch.Tensor]]]:
    shape = (rows, hidden_size)
    buffers = [
        torch.empty(shape, device="cuda", dtype=torch.bfloat16)
        for _ in range(calls_per_chain)
    ]

    # Initialize the lazy PCCL collective path outside capture.  On this PPU
    # runtime a captured collective is recorded but does not update its buffer
    # until graph.replay(), unlike ordinary kernels that also execute while
    # being captured.
    eager_probe = torch.full(
        shape, rank + 1, device="cuda", dtype=torch.bfloat16
    )
    dist.all_reduce(eager_probe, op=dist.ReduceOp.SUM)
    torch.cuda.synchronize()
    assert_exact([eager_probe], sum(peer + 1 for peer in range(WORLD_SIZE)), f"rows={rows} eager-init")

    # Capture the production-like 96-collective sequence.  Each call has its
    # own buffer so graph replay does not repeatedly reduce an already reduced
    # value.  Input refresh is deliberately outside the graph and timing.
    expected = fill_rank_inputs(buffers, rank, offset=1)
    dist.barrier()
    torch.cuda.synchronize()
    graph_stream = torch.cuda.Stream()
    graph_stream.wait_stream(torch.cuda.current_stream())
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, stream=graph_stream):
        for buffer in buffers:
            dist.all_reduce(buffer, op=dist.ReduceOp.SUM)
    torch.cuda.current_stream().wait_stream(graph_stream)
    torch.cuda.synchronize()

    graph.replay()
    torch.cuda.synchronize()
    assert_exact(buffers, expected, f"rows={rows} first-graph-replay")

    replay_checks = []
    for replay_index, offset in enumerate((2, 3), start=1):
        expected = fill_rank_inputs(buffers, rank, offset=offset)
        torch.cuda.synchronize()
        dist.barrier()
        graph.replay()
        torch.cuda.synchronize()
        assert_exact(buffers, expected, f"rows={rows} replay={replay_index}")
        replay_checks.append(
            {"replay": replay_index, "input_offset": offset, "expected": expected}
        )

    for warmup_index in range(warmup):
        fill_rank_inputs(buffers, rank, offset=10 + warmup_index)
        torch.cuda.synchronize()
        dist.barrier()
        graph.replay()
        torch.cuda.synchronize()

    samples_us = []
    for sample_index in range(repeats):
        expected = fill_rank_inputs(buffers, rank, offset=20 + sample_index)
        torch.cuda.synchronize()
        dist.barrier()
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        graph.replay()
        end.record()
        end.synchronize()
        elapsed_us = start.elapsed_time(end) * 1000.0
        assert_exact(buffers, expected, f"rows={rows} sample={sample_index}")
        samples_us.append(elapsed_us)

    median_chain_us = statistics.median(samples_us)
    local = {
        "rows": rows,
        "hidden_size": hidden_size,
        "numel": rows * hidden_size,
        "bytes_per_call": rows * hidden_size * 2,
        "calls_per_chain": calls_per_chain,
        "bytes_per_chain": rows * hidden_size * 2 * calls_per_chain,
        "capture_bit_exact": True,
        "initial_graph_replay_bit_exact": True,
        "changed_input_graph_replay_count_for_correctness": 2,
        "replay_checks": replay_checks,
        "samples_chain_us": samples_us,
        "median_chain_us": median_chain_us,
        "p90_chain_us": percentile(samples_us, 0.90),
        "median_per_call_us": median_chain_us / calls_per_chain,
    }
    # Keep graph and buffers alive through process exit.  The target PCCL has a
    # previously recorded post-graph communicator-destroy hang, so deleting
    # graph-owned resources before all ranks finish would be an extra variable.
    return local, (graph, buffers)


def main() -> None:
    args = parse_args()
    local_rank = int(os.environ["LOCAL_RANK"])
    torch.cuda.set_device(local_rank)
    dist.init_process_group("nccl")
    rank = dist.get_rank()
    world_size = dist.get_world_size()
    if world_size != WORLD_SIZE:
        raise RuntimeError(f"fw-010 requires TP8, got world_size={world_size}")

    local_rows = []
    retained_graph_resources = []
    for rows in args.rows:
        row, resources = benchmark_shape(
            rows=rows,
            hidden_size=args.hidden_size,
            calls_per_chain=args.calls_per_chain,
            warmup=args.warmup,
            repeats=args.repeats,
            rank=rank,
        )
        local_rows.append(row)
        retained_graph_resources.append(resources)

    # Fixed-size device gather avoids the pickling/device ambiguity of object
    # collectives under an NCCL/PCCL process group.
    local_samples = torch.tensor(
        [row["samples_chain_us"] for row in local_rows],
        device="cuda",
        dtype=torch.float32,
    )
    gathered = [torch.empty_like(local_samples) for _ in range(world_size)]
    dist.all_gather(gathered, local_samples)
    torch.cuda.synchronize()

    if rank == 0:
        gathered_cpu = [item.cpu().tolist() for item in gathered]
        result_rows = []
        for shape_index, local_row in enumerate(local_rows):
            by_rank = [values[shape_index] for values in gathered_cpu]
            rank_medians = [statistics.median(values) for values in by_rank]
            median_of_rank_medians = statistics.median(rank_medians)
            result_rows.append(
                {
                    **local_row,
                    "samples_chain_us_by_rank": by_rank,
                    "median_chain_us_by_rank": rank_medians,
                    "median_of_rank_medians_chain_us": median_of_rank_medians,
                    "median_of_rank_medians_per_call_us": (
                        median_of_rank_medians / args.calls_per_chain
                    ),
                    "max_over_median_rank_latency": (
                        max(rank_medians) / median_of_rank_medians
                    ),
                }
            )

        nccl_version = torch.cuda.nccl.version()
        payload = {
            "schema_version": 1,
            "experiment_id": "fw-010-ring-allreduce-causal-control",
            "status": "complete",
            "profiler_enabled": False,
            "backend": dist.get_backend(),
            "world_size": world_size,
            "dtype": "bfloat16",
            "torch_version": torch.__version__,
            "torch_cuda_nccl_version": (
                list(nccl_version)
                if isinstance(nccl_version, tuple)
                else nccl_version
            ),
            "device_name": torch.cuda.get_device_name(0),
            "environment": {
                "NCCL_ALGO": os.environ.get("NCCL_ALGO", "default"),
                "NCCL_PROTO": os.environ.get("NCCL_PROTO", "default"),
                "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
            },
            "shape_source": {
                "hidden_size": "Qwen3.8-Flash-Next text_config.hidden_size=2560",
                "rows_4096": "retained max_num_batched_tokens=4096 Prefill/Mixed",
                "rows_64": "retained max_num_seqs=64 full Decode batch",
                "rows_1": "Decode boundary/control only; excluded from weighted gate",
                "calls_per_chain": (
                    "48 layers times attention-output and MoE/MLP-output TP reduction"
                ),
            },
            "correctness_oracle": (
                "Every BF16 element is an exactly representable integer; each rank r "
                "uses r+offset and must equal sum(r+offset), with capture plus two "
                "changed-input graph replays checked by torch.equal semantics."
            ),
            "rows": result_rows,
            "boundary": (
                "Standalone PCCL/NCCL-interface transaction evidence only. It does not "
                "prove vLLM wrapper overhead, critical-path exposure, or end-to-end gain."
            ),
            "process_group_destroy": (
                "intentionally_skipped: this PCCL revision has a recorded post-graph "
                "destroy_process_group hang; all ranks perform a final barrier and exit"
            ),
        }
        rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(rendered)
        print("SUMMARY=" + json.dumps(payload, sort_keys=True), flush=True)

    dist.barrier()
    torch.cuda.synchronize()
    # See process_group_destroy above.  os._exit avoids the known PCCL graph
    # communicator destructor stall while preserving torchrun's success status.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
