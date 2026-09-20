#!/usr/bin/env python3
"""Benchmark direct strided gather for HY4 paged Indexer keys."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import torch
import triton
import triton.language as tl

from vllm_fl.models import hy_v4


NUM_BLOCKS = 6640
BLOCK_SIZE = 64
HEAD_DIM = 128
WARMUP = 5
RUNS = 10
REPEATS = 9


@triton.jit
def _paged_sequence_gather_kernel(
    kv_cache,
    block_table,
    output,
    seq_len,
    stride_cache_block,
    stride_cache_token,
    stride_cache_dim,
    stride_output_token,
    BLOCK_SIZE: tl.constexpr,
    HEAD_DIM: tl.constexpr,
    BLOCK_T: tl.constexpr,
    BLOCK_D: tl.constexpr,
):
    token_offsets = (
        tl.program_id(0) * BLOCK_T + tl.arange(0, BLOCK_T)
    )[:, None]
    dim_offsets = tl.arange(0, BLOCK_D)[None, :]
    token_mask = token_offsets < seq_len
    dim_mask = dim_offsets < HEAD_DIM
    logical_blocks = token_offsets // BLOCK_SIZE
    token_in_block = token_offsets % BLOCK_SIZE
    physical_blocks = tl.load(
        block_table + logical_blocks,
        mask=token_mask,
        other=0,
    )
    values = tl.load(
        kv_cache
        + physical_blocks * stride_cache_block
        + token_in_block * stride_cache_token
        + dim_offsets * stride_cache_dim,
        mask=token_mask & dim_mask,
        other=0.0,
    )
    tl.store(
        output + token_offsets * stride_output_token + dim_offsets,
        values,
        mask=token_mask & dim_mask,
    )


def candidate(
    kv_cache: torch.Tensor,
    block_table: torch.Tensor,
    seq_len: int,
    *,
    block_t: int,
    num_warps: int,
) -> torch.Tensor:
    output = torch.empty(
        (seq_len, kv_cache.shape[-1]),
        device=kv_cache.device,
        dtype=kv_cache.dtype,
    )
    _paged_sequence_gather_kernel[(triton.cdiv(seq_len, block_t),)](
        kv_cache,
        block_table,
        output,
        seq_len,
        kv_cache.stride(0),
        kv_cache.stride(1),
        kv_cache.stride(2),
        output.stride(0),
        BLOCK_SIZE=kv_cache.shape[1],
        HEAD_DIM=kv_cache.shape[2],
        BLOCK_T=block_t,
        BLOCK_D=triton.next_power_of_2(kv_cache.shape[2]),
        num_warps=num_warps,
        num_stages=1,
    )
    return output


def elapsed_us(fn) -> list[float]:
    for _ in range(WARMUP):
        fn()
    torch.cuda.synchronize()
    samples = []
    for _ in range(REPEATS):
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        for _ in range(RUNS):
            fn()
        end.record()
        end.synchronize()
        samples.append(start.elapsed_time(end) * 1000.0 / RUNS)
    return samples


def timing(samples: list[float]) -> dict[str, object]:
    return {
        "median_us": statistics.median(samples),
        "min_us": min(samples),
        "max_us": max(samples),
        "samples_us": samples,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")
    assert torch.cuda.is_available()
    assert hy_v4.current_platform.vendor_name == "thead"

    torch.manual_seed(20260919)
    kv_cache = torch.randn(
        (NUM_BLOCKS, BLOCK_SIZE, HEAD_DIM),
        device="cuda",
        dtype=torch.bfloat16,
    )
    block_table = torch.randperm(
        NUM_BLOCKS, device="cuda", dtype=torch.int64
    )[:128].to(torch.int32)
    configurations = ((1, 4), (2, 4), (4, 4), (8, 4), (8, 8))
    rows = []
    for seq_len in (2041, 3987, 4096):
        expected = hy_v4._paged_sequence(kv_cache, block_table, seq_len)
        torch.cuda.synchronize()
        baseline_stats = timing(
            elapsed_us(
                lambda: hy_v4._paged_sequence(
                    kv_cache, block_table, seq_len
                )
            )
        )
        candidates = []
        for block_t, num_warps in configurations:
            actual = candidate(
                kv_cache,
                block_table,
                seq_len,
                block_t=block_t,
                num_warps=num_warps,
            )
            torch.cuda.synchronize()
            exact = bool(torch.equal(expected, actual))
            assert exact
            candidate_stats = timing(
                elapsed_us(
                    lambda block_t=block_t, num_warps=num_warps: candidate(
                        kv_cache,
                        block_table,
                        seq_len,
                        block_t=block_t,
                        num_warps=num_warps,
                    )
                )
            )
            candidates.append(
                {
                    "block_t": block_t,
                    "num_warps": num_warps,
                    "exact": exact,
                    "timing": candidate_stats,
                    "speedup": baseline_stats["median_us"]
                    / candidate_stats["median_us"],
                    "delta_us": baseline_stats["median_us"]
                    - candidate_stats["median_us"],
                }
            )
        rows.append(
            {
                "seq_len": seq_len,
                "baseline": baseline_stats,
                "candidates": candidates,
            }
        )

    graph_seq_len = 4096
    graph_output = candidate(
        kv_cache,
        block_table,
        graph_seq_len,
        block_t=4,
        num_warps=4,
    )
    graph = torch.cuda.CUDAGraph()
    torch.cuda.synchronize()
    with torch.cuda.graph(graph):
        graph_output = candidate(
            kv_cache,
            block_table,
            graph_seq_len,
            block_t=4,
            num_warps=4,
        )
    graph_replays = []
    for replay in range(2):
        kv_cache[block_table[0].long(), 0, 0].add_(1)
        expected = hy_v4._paged_sequence(
            kv_cache, block_table, graph_seq_len
        )
        graph.replay()
        torch.cuda.synchronize()
        graph_replays.append(
            {
                "replay": replay + 1,
                "exact": bool(torch.equal(expected, graph_output)),
            }
        )
    assert all(row["exact"] for row in graph_replays)

    result = {
        "schema_version": 1,
        "device": torch.cuda.get_device_name(0),
        "vendor": hy_v4.current_platform.vendor_name,
        "cache_shape": list(kv_cache.shape),
        "cache_stride": list(kv_cache.stride()),
        "block_table_dtype": str(block_table.dtype),
        "rows": rows,
        "graph_capture": "passed",
        "graph_replays": graph_replays,
        "conclusion_boundary": (
            "isolated `_paged_sequence` gather at trace-observed cache and "
            "sequence shapes; not a full Indexer or end-to-end result"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
