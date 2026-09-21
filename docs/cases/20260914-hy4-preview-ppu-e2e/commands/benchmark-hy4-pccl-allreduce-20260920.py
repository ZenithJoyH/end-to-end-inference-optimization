#!/usr/bin/env python3
"""TP16 PCCl all-reduce microbenchmark for trace-observed HY4 tensor sizes."""

from __future__ import annotations

import json
import os
import statistics

import torch
import torch.distributed as dist


SIZES = (2048 * 6144, 2029 * 6144, 2048 * 2048, 2048 * 1024)
WARMUP = 10
RUNS = 40
REPEATS = 5


def main():
    local_rank = int(os.environ["LOCAL_RANK"])
    torch.cuda.set_device(local_rank)
    dist.init_process_group("nccl")
    rank = dist.get_rank()
    rows = []
    for numel in SIZES:
        tensor = torch.zeros(numel, device="cuda", dtype=torch.bfloat16)
        for _ in range(WARMUP):
            dist.all_reduce(tensor)
        torch.cuda.synchronize()
        dist.barrier()
        samples = []
        for _ in range(REPEATS):
            start = torch.cuda.Event(enable_timing=True)
            end = torch.cuda.Event(enable_timing=True)
            start.record()
            for _ in range(RUNS):
                dist.all_reduce(tensor)
            end.record()
            end.synchronize()
            samples.append(start.elapsed_time(end) * 1000.0 / RUNS)
        if rank == 0:
            rows.append(
                {
                    "numel": numel,
                    "bytes": numel * tensor.element_size(),
                    "samples_us": samples,
                    "median_us": statistics.median(samples),
                }
            )
        del tensor
    if rank == 0:
        print(
            "SUMMARY="
            + json.dumps(
                {
                    "schema_version": 1,
                    "world_size": dist.get_world_size(),
                    "nccl_algo": os.environ.get("NCCL_ALGO", "default"),
                    "nccl_proto": os.environ.get("NCCL_PROTO", "default"),
                    "rows": rows,
                }
            ),
            flush=True,
        )
    dist.destroy_process_group()


if __name__ == "__main__":
    main()

