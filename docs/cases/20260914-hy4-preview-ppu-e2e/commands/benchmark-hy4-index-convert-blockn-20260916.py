#!/usr/bin/env python3
"""Sweep vLLM sparse-index conversion BLOCK_N for HY4's TopK=2048."""

from __future__ import annotations

import json
import statistics
import time

import torch

from vllm.v1.attention.backends.mla.sparse_utils import (
    triton_convert_req_index_to_global_index,
)


TOPK, BLOCK_SIZE, NUM_REQUESTS, MAX_BLOCKS = 2048, 64, 64, 128
BLOCK_NS = (64, 128, 256, 512, 1024, 2048)


def sync() -> None:
    torch.cuda.synchronize()


def measure(fn):
    out = fn()
    for _ in range(5):
        out = fn()
    sync()
    samples = []
    for _ in range(60):
        start = time.perf_counter()
        out = fn()
        sync()
        samples.append((time.perf_counter() - start) * 1_000_000)
    return {
        "mean_us": statistics.fmean(samples),
        "median_us": statistics.median(samples),
        "min_us": min(samples),
        "max_us": max(samples),
    }, out


def main() -> None:
    torch.manual_seed(20260916)
    dev = torch.device("cuda")
    block_table = torch.arange(
        NUM_REQUESTS * MAX_BLOCKS, device=dev, dtype=torch.int32
    ).view(NUM_REQUESTS, MAX_BLOCKS)
    results = {}
    for m in (1, 32, 64, 256, 2048):
        req_ids = (torch.arange(m, device=dev, dtype=torch.int32) % NUM_REQUESTS).contiguous()
        token_indices = torch.randint(
            0, MAX_BLOCKS * BLOCK_SIZE, (m, TOPK), device=dev, dtype=torch.int32
        )
        # Mix full, half-full and short rows to exercise valid-count atomics.
        columns = torch.arange(TOPK, device=dev).view(1, -1)
        lengths = torch.tensor(
            [TOPK if i % 3 == 0 else (1024 if i % 3 == 1 else 128) for i in range(m)],
            device=dev,
            dtype=torch.int32,
        )
        token_indices.masked_fill_(columns >= lengths.view(-1, 1), -1)

        base_timing, reference = measure(
            lambda: triton_convert_req_index_to_global_index(
                req_ids, block_table, token_indices,
                BLOCK_SIZE=BLOCK_SIZE, NUM_TOPK_TOKENS=TOPK,
                BLOCK_N=128, return_valid_counts=True,
            )
        )
        row = {"baseline": base_timing, "configs": {}}
        for block_n in BLOCK_NS:
            timing, output = measure(
                lambda b=block_n: triton_convert_req_index_to_global_index(
                    req_ids, block_table, token_indices,
                    BLOCK_SIZE=BLOCK_SIZE, NUM_TOPK_TOKENS=TOPK,
                    BLOCK_N=b, return_valid_counts=True,
                )
            )
            row["configs"][str(block_n)] = {
                "timing": timing,
                "speedup": base_timing["median_us"] / timing["median_us"],
                "indices_exact": bool(torch.equal(reference[0], output[0])),
                "counts_exact": bool(torch.equal(reference[1], output[1])),
            }
        results[str(m)] = row
    print(json.dumps({"shape": {"topk": TOPK}, "results": results}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
