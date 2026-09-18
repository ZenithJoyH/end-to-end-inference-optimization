#!/usr/bin/env python3
"""Validate and benchmark the active fused reduction in the full Indexer block."""

from __future__ import annotations

import json
import statistics

import torch

from vllm_fl.models import hy_v4


ROWS = 128
KEYS = 4096
HEADS = 32
HEAD_DIM = 128
TOPK = 2048
WARMUP = 3
RUNS = 5
REPEATS = 5


def baseline(q, weights, keys, row_starts, row_ends, output) -> None:
    output.fill_(-1)
    scores = torch.matmul(keys.unsqueeze(0), q.transpose(1, 2))
    logits = (
        torch.relu(scores) * weights.to(scores.dtype).unsqueeze(1)
    ).sum(dim=-1).float()
    selected = output[:, :TOPK]
    hy_v4._top_k_per_row_prefill(
        logits,
        row_starts,
        row_ends,
        selected,
    )
    valid = selected >= 0
    selected.add_(row_starts.unsqueeze(1))
    selected.masked_fill_(~valid, -1)


def candidate(q, weights, keys, row_starts, row_ends, output) -> None:
    hy_v4._select_topk_block(
        q,
        weights,
        keys,
        row_starts,
        row_ends,
        key_start=0,
        key_end=KEYS,
        request_start=0,
        topk=TOPK,
        output=output,
    )


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


def main() -> None:
    torch.manual_seed(20260916)
    q = torch.randn(
        (ROWS, HEADS, HEAD_DIM), device="cuda", dtype=torch.bfloat16
    )
    weights = torch.randn((ROWS, HEADS), device="cuda", dtype=torch.float32)
    keys = torch.randn((KEYS, HEAD_DIM), device="cuda", dtype=torch.bfloat16)
    row_starts = torch.zeros(ROWS, device="cuda", dtype=torch.int32)
    row_ends = torch.linspace(TOPK + 1, KEYS, ROWS, device="cuda").to(
        torch.int32
    )
    baseline_output = torch.empty((ROWS, TOPK), device="cuda", dtype=torch.int32)
    candidate_output = torch.empty_like(baseline_output)

    baseline(q, weights, keys, row_starts, row_ends, baseline_output)
    candidate(q, weights, keys, row_starts, row_ends, candidate_output)
    torch.cuda.synchronize()
    baseline_mask = torch.zeros((ROWS, KEYS), device="cuda", dtype=torch.bool)
    candidate_mask = torch.zeros_like(baseline_mask)
    baseline_mask.scatter_(1, baseline_output.to(torch.long), True)
    candidate_mask.scatter_(1, candidate_output.to(torch.long), True)
    intersection = (baseline_mask & candidate_mask).sum(dim=1)
    correctness = {
        "mean_selected_set_overlap_fraction": float(
            intersection.sum().item() / (ROWS * TOPK)
        ),
        "minimum_row_overlap_fraction": float(intersection.min().item() / TOPK),
        "exact_row_count": int((intersection == TOPK).sum().item()),
        "candidate_indices_in_range": bool(
            (
                (candidate_output >= 0)
                & (candidate_output < row_ends.unsqueeze(1))
            ).all().item()
        ),
    }
    if not correctness["candidate_indices_in_range"]:
        raise AssertionError("candidate emitted out-of-range indices")

    baseline_samples = elapsed_us(
        lambda: baseline(
            q, weights, keys, row_starts, row_ends, baseline_output
        )
    )
    candidate_samples = elapsed_us(
        lambda: candidate(
            q, weights, keys, row_starts, row_ends, candidate_output
        )
    )
    baseline_median = statistics.median(baseline_samples)
    candidate_median = statistics.median(candidate_samples)

    candidate(q, weights, keys, row_starts, row_ends, candidate_output)
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        candidate(q, weights, keys, row_starts, row_ends, candidate_output)
    for _ in range(2):
        graph.replay()
    q.add_(torch.tensor(0.25, device="cuda", dtype=torch.bfloat16))
    graph.replay()
    torch.cuda.synchronize()

    print(
        "SUMMARY="
        + json.dumps(
            {
                "status": "passed",
                "shape": {
                    "rows": ROWS,
                    "keys": KEYS,
                    "heads": HEADS,
                    "head_dim": HEAD_DIM,
                    "topk": TOPK,
                },
                "baseline_samples_us": baseline_samples,
                "candidate_samples_us": candidate_samples,
                "baseline_median_us": baseline_median,
                "candidate_median_us": candidate_median,
                "speedup": baseline_median / candidate_median,
                "correctness": correctness,
                "graph": {
                    "capture": "passed",
                    "replays": 3,
                    "changed_input_replay": True,
                },
                "boundary": (
                    "operator-only full Indexer scoring block; formal accuracy "
                    "and profiler-off service validation required"
                ),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
