#!/usr/bin/env python3
"""Test smaller BLOCK_M tiles for the live QSA GROUP_SIZE=3 sparse GQA call."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import torch
from flag_gems.fused.qsa import _qsa_sparse_paged_gqa_kernel


TOPK = 2051
PAGE_SIZE = 16
HEAD_DIM = 256
GROUP_SIZE = 3
BLOCK_N = 16
BLOCK_D = 256


def launch(
    q: torch.Tensor,
    k_cache: torch.Tensor,
    v_cache: torch.Tensor,
    indices: torch.Tensor,
    block_table: torch.Tensor,
    token_to_req: torch.Tensor,
    out: torch.Tensor,
    block_m: int,
) -> None:
    _qsa_sparse_paged_gqa_kernel[(q.shape[0], 1)](
        q,
        k_cache,
        v_cache,
        indices,
        block_table,
        token_to_req,
        out,
        q.stride(0),
        q.stride(1),
        q.stride(2),
        k_cache.stride(0),
        k_cache.stride(1),
        k_cache.stride(2),
        k_cache.stride(3),
        v_cache.stride(0),
        v_cache.stride(1),
        v_cache.stride(2),
        v_cache.stride(3),
        indices.stride(0),
        indices.stride(1),
        block_table.stride(0),
        block_table.stride(1),
        out.stride(0),
        out.stride(1),
        out.stride(2),
        q.shape[0],
        k_cache.shape[0],
        block_table.shape[0],
        float(HEAD_DIM**-0.5),
        TOPK=TOPK,
        PAGE_SIZE=PAGE_SIZE,
        PAGE_TABLE_WIDTH=block_table.shape[1],
        NUM_KV_HEADS=1,
        GROUP_SIZE=GROUP_SIZE,
        HEAD_DIM=HEAD_DIM,
        BLOCK_M=block_m,
        BLOCK_N=BLOCK_N,
        BLOCK_D=BLOCK_D,
        num_warps=4,
        num_stages=2,
    )


def event_ms(fn, warmup: int, repeat: int) -> float:
    for _ in range(warmup):
        fn()
    torch.cuda.synchronize()
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    start.record()
    for _ in range(repeat):
        fn()
    end.record()
    torch.cuda.synchronize()
    return float(start.elapsed_time(end)) / repeat


def capture_and_replay(fn, output: torch.Tensor) -> dict:
    for _ in range(3):
        fn()
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, capture_error_mode="thread_local"):
        fn()
    torch.cuda.synchronize()
    captured = output.clone()
    snapshots = []
    for _ in range(2):
        graph.replay()
        torch.cuda.synchronize()
        snapshots.append(output.clone())
    torch.testing.assert_close(captured, snapshots[0], atol=0, rtol=0)
    torch.testing.assert_close(captured, snapshots[1], atol=0, rtol=0)
    return {"capture": True, "replays": 2, "stable": True}


def make_case(rows: int, invalid_indices: bool, noncontiguous_pages: bool):
    device = torch.device("cuda")
    if rows == 4096:
        num_requests = 4
        token_to_req = torch.arange(
            num_requests, device=device, dtype=torch.int32
        ).repeat_interleave(rows // num_requests)
    else:
        num_requests = rows
        token_to_req = torch.arange(rows, device=device, dtype=torch.int32)
    max_sequence_length = 4096
    pages = math.ceil(max_sequence_length / PAGE_SIZE)
    page_ids = torch.arange(pages, device=device, dtype=torch.int32)
    if noncontiguous_pages:
        page_ids = (page_ids * 73) % pages
    block_table = page_ids.expand(num_requests, -1).contiguous()
    k_cache = torch.randn(
        (pages, PAGE_SIZE, 1, HEAD_DIM), device=device, dtype=torch.bfloat16
    )
    v_cache = torch.randn_like(k_cache)
    q = torch.randn((rows, GROUP_SIZE, HEAD_DIM), device=device, dtype=torch.bfloat16)
    base = torch.arange(TOPK, device=device, dtype=torch.int32)
    indices = base.expand(rows, -1).contiguous()
    if invalid_indices:
        indices[:, 256::257] = -1
    return q, k_cache, v_cache, indices, block_table, token_to_req


@torch.inference_mode()
def run_case(
    rows: int,
    invalid_indices: bool,
    noncontiguous_pages: bool,
    warmup: int,
    repeat: int,
) -> dict:
    tensors = make_case(rows, invalid_indices, noncontiguous_pages)
    outputs = {
        block_m: torch.empty_like(tensors[0]) for block_m in (16, 8, 4)
    }
    functions = {
        block_m: (
            lambda block_m=block_m: launch(*tensors, outputs[block_m], block_m)
        )
        for block_m in outputs
    }
    result = {
        "rows": rows,
        "invalid_indices": invalid_indices,
        "noncontiguous_pages": noncontiguous_pages,
        "dtype": "bfloat16",
        "group_size": GROUP_SIZE,
        "head_dim": HEAD_DIM,
        "topk": TOPK,
        "variants": {},
    }
    reference = None
    for block_m in (16, 8, 4):
        try:
            functions[block_m]()
            torch.cuda.synchronize()
            if block_m == 16:
                reference = outputs[block_m].clone()
            else:
                assert reference is not None
                torch.testing.assert_close(
                    outputs[block_m], reference, atol=0.05, rtol=0.05
                )
            elapsed = event_ms(functions[block_m], warmup, repeat)
            graph = capture_and_replay(functions[block_m], outputs[block_m])
            max_abs = 0.0
            if reference is not None:
                max_abs = float(
                    (outputs[block_m].float() - reference.float()).abs().max().item()
                )
            result["variants"][str(block_m)] = {
                "status": "passed",
                "event_ms": elapsed,
                "speedup_vs_block_m16": None,
                "max_abs_vs_block_m16": max_abs,
                "graph": graph,
            }
        except Exception as exc:
            torch.cuda.synchronize()
            result["variants"][str(block_m)] = {
                "status": "failed",
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
    baseline = result["variants"]["16"]
    if baseline["status"] != "passed":
        raise RuntimeError("BLOCK_M=16 baseline failed")
    for block_m in (8, 4):
        row = result["variants"][str(block_m)]
        if row["status"] == "passed":
            row["speedup_vs_block_m16"] = baseline["event_ms"] / row["event_ms"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", default="1,8,64,4096")
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--repeat", type=int, default=20)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    torch.manual_seed(20260920)
    torch.cuda.set_device(0)
    rows_values = [int(value) for value in args.rows.split(",")]
    cases = []
    for rows in rows_values:
        for invalid_indices, noncontiguous_pages in (
            (False, False),
            (True, True),
        ):
            cases.append(
                run_case(
                    rows,
                    invalid_indices,
                    noncontiguous_pages,
                    args.warmup,
                    args.repeat,
                )
            )
    candidate_speedups = [
        case["variants"][str(block_m)]["speedup_vs_block_m16"]
        for case in cases
        for block_m in (8, 4)
        if case["variants"][str(block_m)]["status"] == "passed"
    ]
    payload = {
        "schema_version": 1,
        "experiment": "op015-qsa-sparse-gqa-group3-block-m",
        "warmup": args.warmup,
        "repeat": args.repeat,
        "cases": cases,
        "gate": {
            "required_complete_call_speedup": 1.08,
            "any_candidate_compiled": bool(candidate_speedups),
            "all_passing_candidate_speedups_ge_1_08": bool(candidate_speedups)
            and all(value >= 1.08 for value in candidate_speedups),
        },
        "boundary": (
            "Standalone exact sparse-call test only. A passing 8% operator gate "
            "still requires source integration, focused tests, service graph/canonical, "
            "and same-device no-profiler performance screening."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
