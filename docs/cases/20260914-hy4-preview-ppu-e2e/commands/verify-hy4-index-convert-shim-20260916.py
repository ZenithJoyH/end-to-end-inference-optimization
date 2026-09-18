#!/usr/bin/env python3
"""Verify the applied HY4 sparse-index BLOCK_N shim and graph replay."""

from __future__ import annotations

import json
import statistics
import time

import torch

import vllm_fl.models.hy_v4  # noqa: F401 - installs the idempotent shim
from vllm.v1.attention.backends.mla import flashmla_sparse


TOPK, BLOCK_SIZE, NUM_REQUESTS, MAX_BLOCKS = 2048, 64, 64, 128


def sync() -> None:
    torch.cuda.synchronize()


def measure(fn):
    out = fn()
    for _ in range(5):
        out = fn()
    sync()
    samples = []
    for _ in range(80):
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
    candidate = flashmla_sparse.triton_convert_req_index_to_global_index
    baseline = candidate._vllm_fl_original
    results = {}
    graph_args = None
    eager_output = None
    for m in (256, 2048):
        req_ids = (torch.arange(m, device=dev, dtype=torch.int32) % NUM_REQUESTS).contiguous()
        token_indices = torch.randint(
            0, MAX_BLOCKS * BLOCK_SIZE, (m, TOPK), device=dev, dtype=torch.int32
        )
        columns = torch.arange(TOPK, device=dev).view(1, -1)
        lengths = torch.tensor(
            [TOPK if i % 3 == 0 else (1024 if i % 3 == 1 else 128) for i in range(m)],
            device=dev,
            dtype=torch.int32,
        )
        token_indices.masked_fill_(columns >= lengths.view(-1, 1), -1)
        common = dict(
            BLOCK_SIZE=BLOCK_SIZE,
            NUM_TOPK_TOKENS=TOPK,
            return_valid_counts=True,
        )
        baseline_timing, reference = measure(
            lambda: baseline(req_ids, block_table, token_indices, BLOCK_N=128, **common)
        )
        candidate_timing, output = measure(
            lambda: candidate(req_ids, block_table, token_indices, **common)
        )
        results[str(m)] = {
            "baseline": baseline_timing,
            "candidate": candidate_timing,
            "speedup": baseline_timing["median_us"] / candidate_timing["median_us"],
            "indices_exact": bool(torch.equal(reference[0], output[0])),
            "counts_exact": bool(torch.equal(reference[1], output[1])),
        }
        if m == 2048:
            graph_args = (req_ids, block_table, token_indices, common)
            eager_output = output

    req_ids, block_table, token_indices, common = graph_args
    for _ in range(3):
        candidate(req_ids, block_table, token_indices, **common)
    sync()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        graph_output = candidate(req_ids, block_table, token_indices, **common)
    graph.replay()
    sync()
    replay_one = tuple(x.clone() for x in graph_output)
    graph.replay()
    sync()
    replay_two = tuple(x.clone() for x in graph_output)
    results["graph"] = {
        "capture": "passed",
        "replays": 2,
        "replays_exact": all(torch.equal(a, b) for a, b in zip(replay_one, replay_two)),
        "eager_vs_replay_exact": all(
            torch.equal(a, b) for a, b in zip(eager_output, replay_two)
        ),
    }
    print(json.dumps({"shape": {"topk": TOPK}, "results": results}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
