#!/usr/bin/env python3
"""Microbenchmark Qwen3.8 QSA sparse GQA with a literal four-head tile.

This is an isolated experiment artifact.  It does not patch FlagGems or the
live service.  Run it only inside the cloned optimization container after the
selected accelerator has been released by every service.

The current FlagGems kernel receives ``BLOCK_M=16`` for the production
``GROUP_SIZE=3`` shape.  The candidate below keeps the same online-softmax and
two ``tl.dot`` operations, but expresses the smallest legal Triton head tensor
as the literal ``tl.arange(0, 4)``.  ``BLOCK_M`` is deliberately absent from
the candidate signature so the PPU automatic block-size adjustment cannot
rewrite a launch meta-parameter back to 16.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import torch
import triton
import triton.language as tl

from flag_gems.fused.qsa import qsa_sparse_paged_attention


PAGE_SIZE = 16
QUERY_HEADS = 3
KV_HEADS = 1
HEAD_DIM = 256
TOPK = 2051
BLOCK_N = 16
ATOL = 0.05
RTOL = 0.05
TRANSACTION_GAIN_GATE_PCT = 8.0


@triton.jit
def _qsa_sparse_paged_gqa3_literal4_kernel(
    q_ptr,
    k_cache_ptr,
    v_cache_ptr,
    indices_ptr,
    block_table_ptr,
    token_to_req_ptr,
    output_ptr,
    stride_q_row,
    stride_q_head,
    stride_q_dim,
    stride_k_block,
    stride_k_token,
    stride_k_head,
    stride_k_dim,
    stride_v_block,
    stride_v_token,
    stride_v_head,
    stride_v_dim,
    stride_indices_row,
    stride_indices_column,
    stride_table_req,
    stride_table_page,
    stride_output_row,
    stride_output_head,
    stride_output_dim,
    num_rows,
    num_cache_blocks,
    num_requests,
    softmax_scale,
    TOPK_VALUE: tl.constexpr,
    PAGE_SIZE_VALUE: tl.constexpr,
    PAGE_TABLE_WIDTH: tl.constexpr,
) -> None:
    """Exact group-3 specialization with no configurable BLOCK_M.

    The PPU backend may still pad small ``tl.dot`` M/N dimensions internally.
    This candidate only claims to remove the twelve extra *logical* lanes from
    query/state/softmax/accumulator tensors; generated IR must be inspected
    before interpreting a timing result as reduced tensor-core work.
    """

    row = tl.program_id(0)
    # tl.arange(0, 3) is illegal in Triton 3.6 because the end must be a power
    # of two.  Four is the smallest legal tensor extent; lane 3 is masked.
    head_offsets = tl.arange(0, 4)
    dim_offsets = tl.arange(0, 256)
    column_offsets = tl.arange(0, 16)

    request = tl.load(token_to_req_ptr + row)
    safe_request = tl.minimum(tl.maximum(request, 0), num_requests - 1)
    query = tl.load(
        q_ptr
        + row * stride_q_row
        + head_offsets[:, None] * stride_q_head
        + dim_offsets[None, :] * stride_q_dim,
        mask=(head_offsets[:, None] < 3),
        other=0.0,
    )
    # Preserve the live kernel's BF16 rounding point exactly.
    query = (query * softmax_scale * 1.4426950408889634).to(query.dtype)

    max_value = tl.full((4,), -1.0e20, dtype=tl.float32)
    normalizer = tl.zeros((4,), dtype=tl.float32)
    accumulator = tl.zeros((4, 256), dtype=tl.float32)

    for start in tl.range(0, TOPK_VALUE, 16):
        columns = start + column_offsets
        logical_token = tl.load(
            indices_ptr
            + row * stride_indices_row
            + columns * stride_indices_column,
            mask=columns < TOPK_VALUE,
            other=-1,
        )
        logical_page = tl.maximum(logical_token, 0) // PAGE_SIZE_VALUE
        page_offset = tl.maximum(logical_token, 0) % PAGE_SIZE_VALUE
        valid = (
            (row < num_rows)
            & (request >= 0)
            & (request < num_requests)
            & (logical_token >= 0)
            & (logical_page < PAGE_TABLE_WIDTH)
        )
        physical_page = tl.load(
            block_table_ptr
            + safe_request * stride_table_req
            + tl.minimum(logical_page, PAGE_TABLE_WIDTH - 1)
            * stride_table_page,
            mask=valid,
            other=-1,
        )
        valid &= (physical_page >= 0) & (physical_page < num_cache_blocks)
        # Match the live overflow guard for large cache strides.
        safe_page = tl.maximum(physical_page, 0).to(tl.int64)
        keys = tl.load(
            k_cache_ptr
            + safe_page[None, :] * stride_k_block
            + page_offset[None, :] * stride_k_token
            + 0 * stride_k_head
            + dim_offsets[:, None] * stride_k_dim,
            mask=valid[None, :],
            other=0.0,
        )
        values = tl.load(
            v_cache_ptr
            + safe_page[:, None] * stride_v_block
            + page_offset[:, None] * stride_v_token
            + 0 * stride_v_head
            + dim_offsets[None, :] * stride_v_dim,
            mask=valid[:, None],
            other=0.0,
        )
        scores = tl.dot(query, keys)
        scores = tl.where(valid[None, :], scores, -1.0e20)
        next_max = tl.maximum(max_value, tl.max(scores, axis=1))
        alpha = tl.math.exp2(max_value - next_max)
        probabilities = tl.where(
            valid[None, :], tl.math.exp2(scores - next_max[:, None]), 0.0
        )
        accumulator = tl.dot(
            probabilities.to(values.dtype),
            values,
            acc=accumulator * alpha[:, None],
        )
        normalizer = normalizer * alpha + tl.sum(probabilities, axis=1)
        max_value = next_max

    output = tl.where(
        normalizer[:, None] > 0,
        accumulator / tl.maximum(normalizer[:, None], 1.0e-20),
        0.0,
    )
    tl.store(
        output_ptr
        + row * stride_output_row
        + head_offsets[:, None] * stride_output_head
        + dim_offsets[None, :] * stride_output_dim,
        output,
        mask=(row < num_rows) & (head_offsets[:, None] < 3),
    )


def qsa_sparse_paged_attention_group3_literal4(
    q: torch.Tensor,
    k_cache: torch.Tensor,
    v_cache: torch.Tensor,
    logical_indices: torch.Tensor,
    block_table: torch.Tensor,
    token_to_req: torch.Tensor,
    softmax_scale: float | None = None,
    out: torch.Tensor | None = None,
) -> torch.Tensor:
    """Launch the exact production specialization or fail before launch."""

    if q.device.type in ("cpu", "meta"):
        raise RuntimeError("literal4 QSA requires an accelerator Triton backend")
    if q.ndim != 3 or q.shape[1:] != (QUERY_HEADS, HEAD_DIM):
        raise ValueError("literal4 QSA requires query [rows, 3, 256]")
    expected_cache_tail = (PAGE_SIZE, KV_HEADS, HEAD_DIM)
    if (
        k_cache.ndim != 4
        or k_cache.shape[1:] != expected_cache_tail
        or v_cache.shape != k_cache.shape
    ):
        raise ValueError("literal4 QSA requires K/V [blocks, 16, 1, 256]")
    if not all(t.dtype == torch.bfloat16 for t in (q, k_cache, v_cache)):
        raise TypeError("literal4 QSA requires BF16 Q/K/V")
    if logical_indices.shape != (q.shape[0], TOPK):
        raise ValueError("literal4 QSA requires indices [rows, 2051]")
    if logical_indices.dtype != torch.int32:
        raise TypeError("literal4 QSA requires int32 indices")
    if block_table.ndim != 2 or block_table.dtype != torch.int32:
        raise TypeError("literal4 QSA requires a rank-2 int32 block table")
    if token_to_req.shape != (q.shape[0],) or token_to_req.dtype != torch.int32:
        raise TypeError("literal4 QSA requires int32 token_to_req [rows]")
    tensors = (q, k_cache, v_cache, logical_indices, block_table, token_to_req)
    if any(t.device != q.device for t in tensors):
        raise ValueError("literal4 QSA tensors must share one accelerator device")
    if not all(k_cache.shape[:3]) or not all(block_table.shape):
        raise ValueError("literal4 QSA cache and block table must be nonempty")

    if out is None:
        out = torch.empty_like(q)
    if out.shape != q.shape or out.dtype != torch.bfloat16 or out.device != q.device:
        raise ValueError("literal4 QSA output must be BF16 and match query")
    if not q.shape[0]:
        return out
    scale = HEAD_DIM**-0.5 if softmax_scale is None else float(softmax_scale)
    if scale <= 0:
        raise ValueError("literal4 QSA softmax scale must be positive")

    _qsa_sparse_paged_gqa3_literal4_kernel[(q.shape[0],)](
        q,
        k_cache,
        v_cache,
        logical_indices,
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
        logical_indices.stride(0),
        logical_indices.stride(1),
        block_table.stride(0),
        block_table.stride(1),
        out.stride(0),
        out.stride(1),
        out.stride(2),
        q.shape[0],
        k_cache.shape[0],
        block_table.shape[0],
        scale,
        TOPK_VALUE=TOPK,
        PAGE_SIZE_VALUE=PAGE_SIZE,
        PAGE_TABLE_WIDTH=block_table.shape[1],
        num_warps=4,
        num_stages=2,
    )
    return out


@dataclass
class Workload:
    mode: str
    q: torch.Tensor
    k_cache: torch.Tensor
    v_cache: torch.Tensor
    logical_indices: torch.Tensor
    block_table: torch.Tensor
    token_to_req: torch.Tensor


def _make_workload(rows: int, mode: str, device: torch.device) -> Workload:
    if rows <= 0:
        raise ValueError("rows must be positive")
    if mode not in ("valid", "invalid_noncontiguous"):
        raise ValueError(f"unknown mode: {mode}")

    torch.manual_seed(15000 + rows + (0 if mode == "valid" else 1))
    if rows == 4096:
        num_requests = 4
        token_to_req = torch.arange(
            num_requests, dtype=torch.int32, device=device
        ).repeat_interleave(1024)
    else:
        num_requests = rows
        token_to_req = torch.arange(rows, dtype=torch.int32, device=device)

    # 4096 logical tokens cover every valid value generated below and match
    # the P4K primary graph bucket.  256 physical pages keep the cache compact.
    logical_tokens = 4096
    num_pages = math.ceil(logical_tokens / PAGE_SIZE)
    logical_pages = torch.arange(num_pages, dtype=torch.int32, device=device)
    if mode == "valid":
        block_table = logical_pages.expand(num_requests, -1).contiguous()
    else:
        # 73 is coprime with 256: this is a full, non-contiguous permutation.
        physical = (logical_pages * 73 + 17) % num_pages
        block_table = torch.stack(
            [torch.roll(physical, shifts=request) for request in range(num_requests)]
        )
        # Exercise invalid physical pages in addition to invalid logical tokens.
        block_table[:, 29::31] = -1

    k_cache = torch.randn(
        (num_pages, PAGE_SIZE, KV_HEADS, HEAD_DIM),
        dtype=torch.bfloat16,
        device=device,
    )
    v_cache = torch.randn_like(k_cache)
    q = torch.randn(
        (rows, QUERY_HEADS, HEAD_DIM), dtype=torch.bfloat16, device=device
    )

    columns = torch.arange(TOPK, dtype=torch.int32, device=device)
    row_offsets = torch.arange(rows, dtype=torch.int32, device=device)[:, None]
    # 37 is odd, hence coprime with 4096.  Each row gets 2051 unique logical
    # tokens in a deterministic selection-like order.
    logical_indices = (columns[None, :] * 37 + row_offsets * 13) % logical_tokens
    if mode == "invalid_noncontiguous":
        logical_indices[:, 11::17] = -1
        logical_indices[:, 23::97] = logical_tokens + PAGE_SIZE
        # Cover both negative and too-large request sentinels.  The rows must
        # produce exact zeros and must not read page zero accidentally.
        token_to_req[-1] = -1
        if rows > 1:
            token_to_req[-2] = num_requests

    return Workload(
        mode=mode,
        q=q,
        k_cache=k_cache,
        v_cache=v_cache,
        logical_indices=logical_indices.contiguous(),
        block_table=block_table.contiguous(),
        token_to_req=token_to_req.contiguous(),
    )


def _torch_reference_rows(workload: Workload, row_ids: list[int]) -> torch.Tensor:
    """Independent FP32 reference for a small set of BF16 input rows."""

    refs = torch.zeros(
        (len(row_ids), QUERY_HEADS, HEAD_DIM),
        dtype=torch.bfloat16,
        device=workload.q.device,
    )
    table_cpu = workload.block_table.cpu()
    requests_cpu = workload.token_to_req.cpu()
    indices_cpu = workload.logical_indices[row_ids].cpu().long()
    scale = HEAD_DIM**-0.5
    for output_row, source_row in enumerate(row_ids):
        request = int(requests_cpu[source_row])
        if not 0 <= request < table_cpu.shape[0]:
            continue
        positions = indices_cpu[output_row]
        logical_pages = torch.div(positions.clamp_min(0), PAGE_SIZE, rounding_mode="floor")
        offsets = positions.clamp_min(0) % PAGE_SIZE
        valid = (positions >= 0) & (logical_pages < table_cpu.shape[1])
        safe_logical_pages = logical_pages.clamp(0, table_cpu.shape[1] - 1)
        physical_pages = table_cpu[request, safe_logical_pages]
        valid &= (physical_pages >= 0) & (physical_pages < workload.k_cache.shape[0])
        if not bool(valid.any()):
            continue
        physical_device = physical_pages[valid].to(workload.q.device)
        offsets_device = offsets[valid].to(workload.q.device)
        keys = workload.k_cache[physical_device, offsets_device, 0].float()
        values = workload.v_cache[physical_device, offsets_device, 0].float()
        for head in range(QUERY_HEADS):
            scores = torch.matmul(keys, workload.q[source_row, head].float()) * scale
            refs[output_row, head] = torch.matmul(
                torch.softmax(scores, dim=0), values
            ).to(torch.bfloat16)
    return refs


def _assert_reference(
    workload: Workload,
    generic_output: torch.Tensor,
    candidate_output: torch.Tensor,
) -> dict[str, float]:
    torch.testing.assert_close(
        candidate_output.float(), generic_output.float(), atol=ATOL, rtol=RTOL
    )
    row_ids = [0]
    if workload.q.shape[0] > 1:
        row_ids.append(workload.q.shape[0] - 1)
    reference = _torch_reference_rows(workload, row_ids)
    generic_rows = generic_output[row_ids]
    candidate_rows = candidate_output[row_ids]
    torch.testing.assert_close(
        generic_rows.float(), reference.float(), atol=ATOL, rtol=RTOL
    )
    torch.testing.assert_close(
        candidate_rows.float(), reference.float(), atol=ATOL, rtol=RTOL
    )

    invalid = (workload.token_to_req < 0) | (
        workload.token_to_req >= workload.block_table.shape[0]
    )
    if bool(invalid.any()):
        assert torch.count_nonzero(generic_output[invalid]).item() == 0
        assert torch.count_nonzero(candidate_output[invalid]).item() == 0
    difference = (candidate_output.float() - generic_output.float()).abs()
    return {
        "max_abs_candidate_vs_generic": float(difference.max().item()),
        "mean_abs_candidate_vs_generic": float(difference.mean().item()),
        "reference_rows": len(row_ids),
    }


def _event_median_ms(
    fn: Callable[[], object], warmup: int, repeat: int, samples: int
) -> tuple[float, list[float]]:
    for _ in range(warmup):
        fn()
    torch.cuda.synchronize()
    values = []
    for _ in range(samples):
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        for _ in range(repeat):
            fn()
        end.record()
        torch.cuda.synchronize()
        values.append(float(start.elapsed_time(end)) / repeat)
    return statistics.median(values), values


def _capture_and_replay_twice(
    fn: Callable[[], object], output: torch.Tensor
) -> tuple[torch.cuda.CUDAGraph, torch.Tensor, torch.Tensor, torch.Tensor]:
    for _ in range(3):
        fn()
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, capture_error_mode="thread_local"):
        fn()
    torch.cuda.synchronize()
    captured = output.clone()
    graph.replay()
    torch.cuda.synchronize()
    replay_one = output.clone()
    graph.replay()
    torch.cuda.synchronize()
    replay_two = output.clone()
    torch.testing.assert_close(captured, replay_one, atol=0, rtol=0)
    torch.testing.assert_close(captured, replay_two, atol=0, rtol=0)
    return graph, captured, replay_one, replay_two


def _graph_median_ms(
    graph: torch.cuda.CUDAGraph, repeat: int, samples: int
) -> tuple[float, list[float]]:
    values = []
    for _ in range(samples):
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        for _ in range(repeat):
            graph.replay()
        end.record()
        torch.cuda.synchronize()
        values.append(float(start.elapsed_time(end)) / repeat)
    return statistics.median(values), values


@torch.inference_mode()
def run_case(
    rows: int,
    mode: str,
    warmup: int,
    repeat: int,
    samples: int,
) -> dict[str, object]:
    workload = _make_workload(rows, mode, torch.device("cuda"))
    generic_output = torch.empty_like(workload.q)
    candidate_output = torch.empty_like(workload.q)

    def generic_fn() -> torch.Tensor:
        return qsa_sparse_paged_attention(
            workload.q,
            workload.k_cache,
            workload.v_cache,
            workload.logical_indices,
            workload.block_table,
            workload.token_to_req,
            out=generic_output,
        )

    def candidate_fn() -> torch.Tensor:
        return qsa_sparse_paged_attention_group3_literal4(
            workload.q,
            workload.k_cache,
            workload.v_cache,
            workload.logical_indices,
            workload.block_table,
            workload.token_to_req,
            out=candidate_output,
        )

    generic_fn()
    candidate_fn()
    torch.cuda.synchronize()
    correctness = _assert_reference(workload, generic_output, candidate_output)

    generic_ms, generic_samples = _event_median_ms(
        generic_fn, warmup, repeat, samples
    )
    candidate_ms, candidate_samples = _event_median_ms(
        candidate_fn, warmup, repeat, samples
    )

    generic_graph, generic_capture, _, _ = _capture_and_replay_twice(
        generic_fn, generic_output
    )
    candidate_graph, candidate_capture, _, _ = _capture_and_replay_twice(
        candidate_fn, candidate_output
    )
    torch.testing.assert_close(
        candidate_capture.float(), generic_capture.float(), atol=ATOL, rtol=RTOL
    )
    _assert_reference(workload, generic_capture, candidate_capture)
    generic_graph_ms, generic_graph_samples = _graph_median_ms(
        generic_graph, repeat, samples
    )
    candidate_graph_ms, candidate_graph_samples = _graph_median_ms(
        candidate_graph, repeat, samples
    )

    eager_gain_pct = (generic_ms / candidate_ms - 1.0) * 100.0
    graph_gain_pct = (generic_graph_ms / candidate_graph_ms - 1.0) * 100.0
    return {
        "rows": rows,
        "mode": mode,
        "dtype": "bfloat16",
        "query_shape": list(workload.q.shape),
        "cache_shape": list(workload.k_cache.shape),
        "indices_shape": list(workload.logical_indices.shape),
        "generic_block_m": 16,
        "candidate_head_block_literal": 4,
        "candidate_valid_heads": 3,
        "correctness": correctness,
        "graph_capture_replays": 2,
        "generic_median_ms": generic_ms,
        "candidate_median_ms": candidate_ms,
        "eager_gain_pct": eager_gain_pct,
        "generic_graph_median_ms": generic_graph_ms,
        "candidate_graph_median_ms": candidate_graph_ms,
        "graph_gain_pct": graph_gain_pct,
        "generic_samples_ms": generic_samples,
        "candidate_samples_ms": candidate_samples,
        "generic_graph_samples_ms": generic_graph_samples,
        "candidate_graph_samples_ms": candidate_graph_samples,
        "passes_eight_percent_eager_gate": eager_gain_pct
        >= TRANSACTION_GAIN_GATE_PCT,
        "passes_eight_percent_graph_gate": graph_gain_pct
        >= TRANSACTION_GAIN_GATE_PCT,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", default="1,64,4096")
    parser.add_argument(
        "--modes", default="valid,invalid_noncontiguous"
    )
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--repeat", type=int, default=20)
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("an accelerator exposed through torch.cuda is required")
    rows_values = [int(value) for value in args.rows.split(",")]
    modes = [value.strip() for value in args.modes.split(",") if value.strip()]
    if not rows_values or not modes:
        raise ValueError("rows and modes must be nonempty")
    results = [
        run_case(rows, mode, args.warmup, args.repeat, args.samples)
        for rows in rows_values
        for mode in modes
    ]
    primary = [
        result
        for result in results
        if result["rows"] == 4096 and result["mode"] == "valid"
    ]
    payload = {
        "schema_version": 1,
        "experiment": "op015-qsa-sparse-group3-literal4",
        "comparison": "current generic BLOCK_M=16 versus literal HEAD_BLOCK=4",
        "rows": rows_values,
        "modes": modes,
        "warmup": args.warmup,
        "repeat": args.repeat,
        "samples": args.samples,
        "atol": ATOL,
        "rtol": RTOL,
        "transaction_gain_gate_pct": TRANSACTION_GAIN_GATE_PCT,
        "primary_gate_passed": bool(primary)
        and bool(primary[0]["passes_eight_percent_eager_gate"])
        and bool(primary[0]["passes_eight_percent_graph_gate"]),
        "stop_conditions": [
            "candidate fails to compile or generated code restores logical M=16",
            "candidate/reference mismatch exceeds BF16 atol=rtol=0.05",
            "invalid request output is not exactly zero",
            "capture differs from either of two graph replays",
            "rows4096 valid eager or graph gain is below 8 percent",
        ],
        "results": results,
    }
    script_path = Path(__file__).resolve()
    payload["script_sha256"] = hashlib.sha256(script_path.read_bytes()).hexdigest()
    encoded = json.dumps(payload, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
