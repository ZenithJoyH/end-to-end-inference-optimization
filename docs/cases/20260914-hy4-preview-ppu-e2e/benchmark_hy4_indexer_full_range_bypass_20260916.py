#!/usr/bin/env python3
"""Benchmark bypassing Indexer scoring when every valid key is selected."""

from __future__ import annotations

import json
import statistics

import torch

from vllm_fl.models import hy_v4

TOPK = 2048
HEADS = 32
HEAD_DIM = 128
WARMUP, RUNS, REPEATS = 3, 5, 5


def candidate(output, row_starts, row_ends, request_start):
    hy_v4._fill_hyv4_full_range_indices(
        row_starts,
        row_ends,
        request_start,
        output,
    )


def dense_reference(
    q,
    weights,
    keys,
    row_starts,
    row_ends,
    *,
    key_start,
    key_end,
    request_start,
    topk,
    output,
):
    """Pre-provider implementation retained as the correctness oracle."""
    output.fill_(-1)
    block_keys = keys[key_start:key_end]
    scores = torch.matmul(block_keys.unsqueeze(0), q.transpose(1, 2))
    logits = (
        torch.relu(scores) * weights.to(scores.dtype).unsqueeze(1)
    ).sum(dim=-1).float()
    positions = torch.arange(
        block_keys.shape[0], device=keys.device, dtype=row_starts.dtype
    )
    local_starts = row_starts - key_start
    local_ends = row_ends - key_start
    valid_positions = (positions.unsqueeze(0) >= local_starts.unsqueeze(1)) & (
        positions.unsqueeze(0) < local_ends.unsqueeze(1)
    )
    logits.masked_fill_(~valid_positions, float("-inf"))
    count = min(topk, output.shape[1], block_keys.shape[0])
    selected = torch.topk(logits, count, dim=-1, sorted=True).indices.to(
        output.dtype
    )
    valid_counts = (row_ends - row_starts).clamp(min=0, max=count)
    selected_ranks = torch.arange(
        count, device=output.device, dtype=valid_counts.dtype
    )
    valid_selections = selected_ranks.unsqueeze(0) < valid_counts.unsqueeze(1)
    selected.add_(key_start - request_start)
    selected.masked_fill_(~valid_selections, -1)
    output[:, :count].copy_(selected)


def elapsed(fn):
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


def one_case(rows, width, request_start):
    torch.manual_seed(rows * 10000 + width + request_start)
    q = torch.randn((rows, HEADS, HEAD_DIM), device="cuda", dtype=torch.bfloat16)
    weights = torch.randn((rows, HEADS), device="cuda", dtype=torch.bfloat16)
    keys = torch.randn((request_start + width, HEAD_DIM), device="cuda", dtype=torch.bfloat16)
    starts = torch.full((rows,), request_start, device="cuda", dtype=torch.int32)
    ends = request_start + torch.linspace(1, width, rows, device="cuda").to(torch.int32)
    baseline_out = torch.empty((rows, TOPK), device="cuda", dtype=torch.int32)
    candidate_out = torch.empty_like(baseline_out)
    kwargs = dict(
        key_start=request_start,
        key_end=request_start + width,
        request_start=request_start,
        topk=TOPK,
    )

    dense_reference(
        q, weights, keys, starts, ends, output=baseline_out, **kwargs
    )
    candidate_out.fill_(-1)
    candidate(candidate_out, starts, ends, request_start)
    torch.cuda.synchronize()
    for row in range(rows):
        valid_count = int((ends[row] - starts[row]).item())
        expected = torch.arange(valid_count, device="cuda", dtype=torch.int32)
        torch.testing.assert_close(
            baseline_out[row, :valid_count].sort().values, expected, atol=0, rtol=0
        )
        torch.testing.assert_close(
            candidate_out[row, :valid_count],
            expected,
            atol=0,
            rtol=0,
        )

    baseline_samples = elapsed(
        lambda: dense_reference(
            q, weights, keys, starts, ends, output=baseline_out, **kwargs
        )
    )

    def run_candidate():
        candidate_out.fill_(-1)
        candidate(candidate_out, starts, ends, request_start)

    candidate_samples = elapsed(run_candidate)
    baseline_median = statistics.median(baseline_samples)
    candidate_median = statistics.median(candidate_samples)
    return {
        "rows": rows,
        "width": width,
        "request_start": request_start,
        "baseline_samples_us": baseline_samples,
        "candidate_samples_us": candidate_samples,
        "baseline_median_us": baseline_median,
        "candidate_median_us": candidate_median,
        "speedup": baseline_median / candidate_median,
        "exact_valid_prefix_indices": True,
    }


def graph_check():
    rows, width, request_start = 128, 2048, 17
    starts = torch.full((rows,), request_start, device="cuda", dtype=torch.int32)
    ends = request_start + torch.linspace(1, width, rows, device="cuda").to(torch.int32)
    output = torch.full((rows, TOPK), -1, device="cuda", dtype=torch.int32)
    candidate(output, starts, ends, request_start)
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        output.fill_(-1)
        candidate(output, starts, ends, request_start)
    for _ in range(2):
        graph.replay()
    changed_ends = request_start + torch.linspace(2, width, rows, device="cuda").to(torch.int32)
    ends.copy_(changed_ends)
    graph.replay()
    torch.cuda.synchronize()
    expected_last = request_start + width - 1 - request_start
    assert int(output[-1, width - 1].item()) == expected_last
    return {"capture": "passed", "replays": 3, "changed_input_observed": True}


def main():
    rows = [one_case(*case) for case in ((128, 128, 0), (128, 1024, 0), (128, 2048, 0), (113, 2048, 17))]
    for row in rows:
        print(json.dumps(row), flush=True)
    summary = {
        "status": "passed",
        "semantic_guard": "max(row_end-row_start)<=topk",
        "graph": graph_check(),
        "min_speedup": min(row["speedup"] for row in rows),
        "rows": rows,
    }
    print("SUMMARY=" + json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
