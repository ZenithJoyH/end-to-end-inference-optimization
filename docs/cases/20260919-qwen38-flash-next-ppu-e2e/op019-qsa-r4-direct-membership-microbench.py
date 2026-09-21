#!/usr/bin/env python3
"""op-019 R4 direct-membership complete-transaction microbenchmark.

This is a standalone target-hardware experiment.  It imports the current
FlagGems generic QSA sparse attention as the baseline and defines the bounded
R4 candidate locally; it does not patch a service or an installed package.

The timed candidate transaction includes:

* clearing the direct-address membership/group metadata workspace;
* rebuilding membership from the current selected-index tensor;
* grouped sparse attention for eligible full groups; and
* the per-row fallback performed by the same grouped kernel for tails or
  rejected groups.

The default ``first`` scope runs the two frozen rows4096 valid fixtures.  The
``full`` scope additionally runs deterministic rows64 guards and derived
invalid/non-contiguous correctness cases.  Only Prefill and Mixed rows4096
valid eager+graph measurements can pass the 8 percent promotion gate.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import torch
import triton
import triton.language as tl

from flag_gems.fused.qsa import qsa_sparse_paged_attention


EXPERIMENT_ID = "op-019-qsa-r4-direct-membership"
GROUP_ROWS = 4
QUERY_HEADS = 3
KV_HEADS = 1
HEAD_DIM = 256
PAGE_SIZE = 16
TOPK = 2051
TOKEN_BUCKET = 8192
BLOCK_M = 16
BLOCK_N = 16
BLOCK_D = 256
BLOCK_BUILD = 256
BLOCK_CLEAR = 256
ATOL = 0.05
RTOL = 0.05
PRIMARY_GAIN_GATE_PCT = 8.0
ROWS64_EAGER_REGRESSION_LIMIT_PCT = 5.0
ROWS64_GRAPH_REGRESSION_LIMIT_PCT = 2.0

DEFAULT_PREFILL_FIXTURE = Path(
    "/mnt/nfs/users/jinghao/qwen3.8-flash/"
    "20260919-qwen38-flash-next-ppu-e2e/profiling/"
    "op019-qsa-exact-prefill-001/op019-p4k-prefill-fixture-001"
)
DEFAULT_MIXED_FIXTURE = Path(
    "/mnt/nfs/users/jinghao/qwen3.8-flash/"
    "20260919-qwen38-flash-next-ppu-e2e/profiling/"
    "op019-qsa-exact-mixed-001/op019-p4k-mixed-fixture-001"
)
EXPECTED_FIXTURES = {
    "prefill": {
        "manifest_sha256": (
            "480def84c7d2c17cb86fac9e2e340caa28806f89cd3bfe05ca7885e0378daf64"
        ),
        "selected_sha256": (
            "3a0d49fd904d074afde80c007027259cd1ee7a1dafc001fe15baf939c19ba4ed"
        ),
    },
    "mixed": {
        "manifest_sha256": (
            "07fb120403a6af733417feb9db48af7fca8d0869b2ec18cbb1e9698c70455dd6"
        ),
        "selected_sha256": (
            "f99873bc244fad551ef1d25be3f07ced896c717bcbaa28e9b82e7b2660cdaac5"
        ),
    },
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@triton.jit
def _copy_int32_buffer_kernel(src_ptr, dst_ptr, numel, BLOCK: tl.constexpr):
    offsets = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
    values = tl.load(src_ptr + offsets, mask=offsets < numel, other=0)
    tl.store(dst_ptr + offsets, values, mask=offsets < numel)


def _copy_selected_device(dst: torch.Tensor, src: torch.Tensor) -> None:
    if dst.shape != src.shape or dst.dtype != torch.int32 or src.dtype != torch.int32:
        raise ValueError("selected device-copy tensors must be shape-equal int32")
    if not dst.is_contiguous() or not src.is_contiguous():
        raise ValueError("selected device-copy tensors must be contiguous")
    block = 256
    _copy_int32_buffer_kernel[(triton.cdiv(dst.numel(), block),)](
        src, dst, dst.numel(), BLOCK=block, num_warps=4
    )


@triton.jit
def _affine_selected_inplace_kernel(
    selected_ptr,
    numel,
    LOGICAL_TOKENS: tl.constexpr,
    MULTIPLIER: tl.constexpr,
    OFFSET: tl.constexpr,
    INVERSE_MULTIPLIER: tl.constexpr,
    INVERSE: tl.constexpr,
    BLOCK: tl.constexpr,
):
    offsets = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
    token = tl.load(selected_ptr + offsets, mask=offsets < numel, other=-1)
    valid = (offsets < numel) & (token >= 0) & (token < LOGICAL_TOKENS)
    if INVERSE:
        transformed = (
            ((token - OFFSET + LOGICAL_TOKENS) % LOGICAL_TOKENS)
            * INVERSE_MULTIPLIER
        ) % LOGICAL_TOKENS
    else:
        transformed = (token * MULTIPLIER + OFFSET) % LOGICAL_TOKENS
    tl.store(selected_ptr + offsets, transformed, mask=valid)


def _transform_selected_inplace(
    selected: torch.Tensor, logical_tokens: int, *, inverse: bool
) -> None:
    multiplier = _coprime_multiplier(logical_tokens)
    inverse_multiplier = pow(multiplier, -1, logical_tokens)
    offset = logical_tokens // 2 + 1
    block = 256
    _affine_selected_inplace_kernel[(triton.cdiv(selected.numel(), block),)](
        selected,
        selected.numel(),
        LOGICAL_TOKENS=logical_tokens,
        MULTIPLIER=multiplier,
        OFFSET=offset,
        INVERSE_MULTIPLIER=inverse_multiplier,
        INVERSE=inverse,
        BLOCK=block,
        num_warps=4,
    )


@triton.jit
def _clear_qsa_group_workspace_kernel(
    membership_ptr,
    group_base_ptr,
    overflow_ptr,
    write_count_ptr,
    total_membership_cells,
    num_group_slots,
    num_output_lanes,
    BLOCK: tl.constexpr,
):
    offsets = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
    tl.store(
        membership_ptr + offsets,
        0,
        mask=offsets < total_membership_cells,
    )
    tl.store(group_base_ptr + offsets, -1, mask=offsets < num_group_slots)
    tl.store(overflow_ptr + offsets, 0, mask=offsets < num_group_slots)
    tl.store(write_count_ptr + offsets, 0, mask=offsets < num_output_lanes)


@triton.jit
def _build_qsa_group_membership_kernel(
    indices_ptr,
    token_to_req_ptr,
    query_start_loc_ptr,
    membership_ptr,
    group_base_ptr,
    overflow_ptr,
    stride_indices_row,
    stride_indices_column,
    num_rows,
    num_requests,
    num_group_slots,
    TOPK_VALUE: tl.constexpr,
    TOKEN_BUCKET_VALUE: tl.constexpr,
    GROUP_ROWS_VALUE: tl.constexpr,
    BLOCK: tl.constexpr,
):
    row = tl.program_id(0)
    request = tl.load(token_to_req_ptr + row, mask=row < num_rows, other=-1)
    request_valid = (request >= 0) & (request < num_requests)
    safe_request = tl.minimum(tl.maximum(request, 0), num_requests - 1)
    segment_start = tl.load(
        query_start_loc_ptr + safe_request, mask=request_valid, other=0
    )
    segment_end = tl.load(
        query_start_loc_ptr + safe_request + 1, mask=request_valid, other=0
    )
    in_segment = (
        (row < num_rows)
        & request_valid
        & (row >= segment_start)
        & (row < segment_end)
    )
    segment_offset = row - segment_start
    base_row = segment_start + (segment_offset // GROUP_ROWS_VALUE) * GROUP_ROWS_VALUE
    # Request ids are required to be contiguous run ids [0, num_requests).
    # Adding request makes compact segment-aligned group ids collision-free
    # even when a request boundary is not divisible by GROUP_ROWS.
    group_id = base_row // GROUP_ROWS_VALUE + safe_request
    group_valid = in_segment & (group_id >= 0) & (group_id < num_group_slots)
    safe_group_id = tl.minimum(tl.maximum(group_id, 0), num_group_slots - 1)
    row_in_group = segment_offset % GROUP_ROWS_VALUE
    tl.store(
        group_base_ptr + safe_group_id,
        base_row,
        mask=group_valid & (row_in_group == 0),
    )

    any_reject = tl.zeros((), dtype=tl.int32)
    for column_start in tl.range(0, TOPK_VALUE, BLOCK):
        columns = column_start + tl.arange(0, BLOCK)
        token = tl.load(
            indices_ptr
            + row * stride_indices_row
            + columns * stride_indices_column,
            mask=(row < num_rows) & (columns < TOPK_VALUE),
            other=-1,
        )
        selected = group_valid & (columns < TOPK_VALUE) & (token >= 0)
        in_bucket = selected & (token < TOKEN_BUCKET_VALUE)
        safe_token = tl.minimum(tl.maximum(token, 0), TOKEN_BUCKET_VALUE - 1)
        old_membership = tl.atomic_or(
            membership_ptr + safe_group_id * TOKEN_BUCKET_VALUE + safe_token,
            1 << row_in_group,
            mask=in_bucket,
        )
        duplicate_in_row = in_bucket & (
            (old_membership & (1 << row_in_group)) != 0
        )
        any_reject += tl.sum(
            ((selected & ~in_bucket) | duplicate_in_row).to(tl.int32), axis=0
        )
    tl.atomic_or(
        overflow_ptr + safe_group_id,
        1,
        mask=group_valid & (any_reject > 0),
    )


@triton.jit
def _qsa_sparse_paged_gqa_group4_kernel(
    q_ptr,
    k_cache_ptr,
    v_cache_ptr,
    indices_ptr,
    block_table_ptr,
    token_to_req_ptr,
    logical_positions_ptr,
    membership_ptr,
    group_base_ptr,
    overflow_ptr,
    write_count_ptr,
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
    num_group_slots,
    softmax_scale,
    TOPK_VALUE: tl.constexpr,
    TOKEN_BUCKET_VALUE: tl.constexpr,
    PAGE_SIZE_VALUE: tl.constexpr,
    PAGE_TABLE_WIDTH: tl.constexpr,
    GROUP_ROWS_VALUE: tl.constexpr,
    GROUP_SIZE: tl.constexpr,
    HEAD_DIM_VALUE: tl.constexpr,
    BLOCK_M_VALUE: tl.constexpr,
    BLOCK_N_VALUE: tl.constexpr,
    BLOCK_D_VALUE: tl.constexpr,
):
    group_id = tl.program_id(0)
    kv_head = tl.program_id(1)
    base_row = tl.load(
        group_base_ptr + group_id,
        mask=group_id < num_group_slots,
        other=-1,
    )
    group_exists = (group_id < num_group_slots) & (base_row >= 0)
    safe_base = tl.maximum(base_row, 0)

    group_rows = tl.arange(0, GROUP_ROWS_VALUE)
    source_rows = safe_base + group_rows
    row_exists = group_exists & (source_rows < num_rows)
    safe_source_rows = tl.minimum(tl.maximum(source_rows, 0), num_rows - 1)
    requests = tl.load(
        token_to_req_ptr + safe_source_rows,
        mask=row_exists,
        other=-1,
    )
    positions = tl.load(
        logical_positions_ptr + safe_source_rows,
        mask=row_exists,
        other=-1,
    )
    request0 = tl.load(
        token_to_req_ptr + safe_base,
        mask=group_exists & (safe_base < num_rows),
        other=-1,
    )
    row_exists &= requests == request0
    position0 = tl.load(
        logical_positions_ptr + safe_base,
        mask=group_exists & (safe_base < num_rows),
        other=-1,
    )
    overflow = tl.load(
        overflow_ptr + group_id,
        mask=group_id < num_group_slots,
        other=1,
    )
    full_group = (
        group_exists
        & (tl.sum(row_exists.to(tl.int32), axis=0) == GROUP_ROWS_VALUE)
        & (request0 >= 0)
        & (request0 < num_requests)
        & (position0 >= 0)
        & (
            tl.sum(
                ((requests == request0) & row_exists).to(tl.int32), axis=0
            )
            == GROUP_ROWS_VALUE
        )
        & (
            tl.sum(
                ((positions == position0 + group_rows) & row_exists).to(tl.int32),
                axis=0,
            )
            == GROUP_ROWS_VALUE
        )
        & (overflow == 0)
    )

    head_lanes = tl.arange(0, BLOCK_M_VALUE)
    dims = tl.arange(0, BLOCK_D_VALUE)
    lane_row = head_lanes // GROUP_SIZE
    lane_head = head_lanes % GROUP_SIZE
    query_rows = safe_base + lane_row
    safe_query_rows = tl.minimum(tl.maximum(query_rows, 0), num_rows - 1)
    query_requests = tl.load(
        token_to_req_ptr + safe_query_rows,
        mask=(
            group_exists
            & (head_lanes < GROUP_ROWS_VALUE * GROUP_SIZE)
            & (query_rows < num_rows)
        ),
        other=-1,
    )
    lane_valid = (
        group_exists
        & (head_lanes < GROUP_ROWS_VALUE * GROUP_SIZE)
        & (query_rows < num_rows)
        & (query_requests == request0)
    )
    query = tl.load(
        q_ptr
        + safe_query_rows[:, None] * stride_q_row
        + (kv_head * GROUP_SIZE + lane_head[:, None]) * stride_q_head
        + dims[None, :] * stride_q_dim,
        mask=lane_valid[:, None] & (dims[None, :] < HEAD_DIM_VALUE),
        other=0.0,
    )
    query = (query * softmax_scale * 1.4426950408889634).to(query.dtype)

    max_value = tl.full((BLOCK_M_VALUE,), -1.0e20, dtype=tl.float32)
    normalizer = tl.zeros((BLOCK_M_VALUE,), dtype=tl.float32)
    accumulator = tl.zeros((BLOCK_M_VALUE, BLOCK_D_VALUE), dtype=tl.float32)
    columns_in_tile = tl.arange(0, BLOCK_N_VALUE)

    for group_row in tl.static_range(0, GROUP_ROWS_VALUE):
        source_row = safe_base + group_row
        source_exists = group_exists & (source_row < num_rows)
        safe_source_row = tl.minimum(tl.maximum(source_row, 0), num_rows - 1)
        source_request = tl.load(
            token_to_req_ptr + safe_source_row, mask=source_exists, other=-1
        )
        source_exists &= source_request == request0
        lookup_request = tl.where(full_group, request0, source_request)
        request_valid = (
            source_exists & (lookup_request >= 0) & (lookup_request < num_requests)
        )
        safe_request = tl.minimum(tl.maximum(lookup_request, 0), num_requests - 1)
        for column_start in tl.range(0, TOPK_VALUE, BLOCK_N_VALUE):
            columns = column_start + columns_in_tile
            token = tl.load(
                indices_ptr
                + safe_source_row * stride_indices_row
                + columns * stride_indices_column,
                mask=source_exists & (columns < TOPK_VALUE),
                other=-1,
            )
            token_valid = source_exists & (columns < TOPK_VALUE) & (token >= 0)
            in_bucket = token_valid & (token < TOKEN_BUCKET_VALUE)
            safe_bucket_token = tl.minimum(
                tl.maximum(token, 0), TOKEN_BUCKET_VALUE - 1
            )
            membership = tl.load(
                membership_ptr
                + group_id * TOKEN_BUCKET_VALUE
                + safe_bucket_token,
                mask=group_exists & in_bucket,
                other=0,
            )
            owns_union_token = (
                in_bucket
                & ((membership & (1 << group_row)) != 0)
                & ((membership & ((1 << group_row) - 1)) == 0)
            )
            read_token = token_valid & tl.where(
                full_group, owns_union_token, token_valid
            )
            logical_page = tl.maximum(token, 0) // PAGE_SIZE_VALUE
            page_offset = tl.maximum(token, 0) % PAGE_SIZE_VALUE
            valid = (
                read_token
                & request_valid
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
            safe_page = tl.minimum(
                tl.maximum(physical_page, 0), num_cache_blocks - 1
            ).to(tl.int64)
            keys = tl.load(
                k_cache_ptr
                + safe_page[None, :] * stride_k_block
                + page_offset[None, :] * stride_k_token
                + kv_head * stride_k_head
                + dims[:, None] * stride_k_dim,
                mask=(dims[:, None] < HEAD_DIM_VALUE) & valid[None, :],
                other=0.0,
            )
            values = tl.load(
                v_cache_ptr
                + safe_page[:, None] * stride_v_block
                + page_offset[:, None] * stride_v_token
                + kv_head * stride_v_head
                + dims[None, :] * stride_v_dim,
                mask=valid[:, None] & (dims[None, :] < HEAD_DIM_VALUE),
                other=0.0,
            )
            head_membership = (
                membership[None, :] & (1 << lane_row[:, None])
            ) != 0
            fallback_head = lane_row[:, None] == group_row
            head_uses_token = tl.where(
                full_group, head_membership, fallback_head
            )
            score_valid = (
                valid[None, :]
                & head_uses_token
                & lane_valid[:, None]
            )
            scores = tl.dot(query, keys)
            scores = tl.where(score_valid, scores, -1.0e20)
            next_max = tl.maximum(max_value, tl.max(scores, axis=1))
            alpha = tl.math.exp2(max_value - next_max)
            probabilities = tl.where(
                score_valid,
                tl.math.exp2(scores - next_max[:, None]),
                0.0,
            )
            accumulator = tl.dot(
                probabilities.to(values.dtype),
                values,
                acc=accumulator * alpha[:, None],
            )
            normalizer = normalizer * alpha + tl.sum(probabilities, axis=1)
            max_value = next_max

    result = tl.where(
        normalizer[:, None] > 0,
        accumulator / tl.maximum(normalizer[:, None], 1.0e-20),
        0.0,
    )
    tl.store(
        output_ptr
        + safe_query_rows[:, None] * stride_output_row
        + (kv_head * GROUP_SIZE + lane_head[:, None]) * stride_output_head
        + dims[None, :] * stride_output_dim,
        result,
        mask=lane_valid[:, None] & (dims[None, :] < HEAD_DIM_VALUE),
    )
    # group_base is a segment-aligned one-to-one map (validated against the
    # CPU fixture below), so no two active programs may own the same row/head.
    # Use a plain coverage marker here: the PPU backend's vector atomic-add
    # diagnostic produced false counts even though the full output already
    # matched the generic oracle.  Collision/uniqueness is proven separately
    # from the complete group_base map instead of relying on debug atomics.
    tl.store(
        write_count_ptr
        + safe_query_rows * GROUP_SIZE
        + lane_head,
        1,
        mask=lane_valid,
    )


def qsa_sparse_paged_attention_group4_direct(
    q: torch.Tensor,
    k_cache: torch.Tensor,
    v_cache: torch.Tensor,
    logical_indices: torch.Tensor,
    block_table: torch.Tensor,
    token_to_req: torch.Tensor,
    logical_positions: torch.Tensor,
    query_start_loc: torch.Tensor,
    membership_workspace: torch.Tensor,
    group_base_workspace: torch.Tensor,
    overflow_workspace: torch.Tensor,
    write_count_workspace: torch.Tensor,
    softmax_scale: float | None = None,
    out: torch.Tensor | None = None,
) -> torch.Tensor:
    """Run the complete R4 transaction or raise before launch."""

    if q.device.type in ("cpu", "meta"):
        raise RuntimeError("op019 candidate requires an accelerator Triton backend")
    if q.ndim != 3 or q.shape[1:] != (QUERY_HEADS, HEAD_DIM):
        raise ValueError("op019 candidate requires q [rows,3,256]")
    if (
        k_cache.ndim != 4
        or k_cache.shape[1:] != (PAGE_SIZE, KV_HEADS, HEAD_DIM)
        or v_cache.shape != k_cache.shape
    ):
        raise ValueError("op019 candidate requires K/V [blocks,16,1,256]")
    if not all(t.dtype == torch.bfloat16 for t in (q, k_cache, v_cache)):
        raise TypeError("op019 candidate requires BF16 Q/K/V")
    rows = q.shape[0]
    if logical_indices.shape != (rows, TOPK) or logical_indices.dtype != torch.int32:
        raise ValueError("op019 candidate requires int32 indices [rows,2051]")
    if token_to_req.shape != (rows,) or token_to_req.dtype != torch.int32:
        raise ValueError("op019 candidate requires int32 token_to_req [rows]")
    if logical_positions.shape != (rows,) or logical_positions.dtype not in (
        torch.int32,
        torch.int64,
    ):
        raise ValueError("op019 candidate requires integer positions [rows]")
    if query_start_loc.ndim != 1 or query_start_loc.dtype != torch.int32:
        raise ValueError("op019 candidate requires int32 query_start_loc")
    num_requests = query_start_loc.numel() - 1
    if num_requests <= 0 or block_table.shape[0] != num_requests:
        raise ValueError("request metadata and block table disagree")
    minimum_group_slots = triton.cdiv(rows, GROUP_ROWS) + num_requests
    if membership_workspace.ndim != 2 or membership_workspace.shape[1] != TOKEN_BUCKET:
        raise ValueError("membership workspace has the wrong token bucket")
    if membership_workspace.shape[0] < minimum_group_slots:
        raise ValueError("membership workspace has too few group slots")
    if membership_workspace.dtype != torch.int32:
        raise TypeError("membership workspace must be int32")
    group_slots = membership_workspace.shape[0]
    if group_base_workspace.shape != (group_slots,) or overflow_workspace.shape != (
        group_slots,
    ):
        raise ValueError("group metadata workspace shape mismatch")
    if group_base_workspace.dtype != torch.int32 or overflow_workspace.dtype != torch.int32:
        raise TypeError("group metadata workspaces must be int32")
    if write_count_workspace.shape != (rows, QUERY_HEADS):
        raise ValueError("write-count workspace must be [rows,3]")
    if write_count_workspace.dtype != torch.int32:
        raise TypeError("write-count workspace must be int32")
    tensors = (
        q,
        k_cache,
        v_cache,
        logical_indices,
        block_table,
        token_to_req,
        logical_positions,
        query_start_loc,
        membership_workspace,
        group_base_workspace,
        overflow_workspace,
        write_count_workspace,
    )
    if any(t.device != q.device for t in tensors):
        raise ValueError("all op019 candidate tensors must share one device")
    if out is None:
        out = torch.empty_like(q)
    if out.shape != q.shape or out.dtype != q.dtype or out.device != q.device:
        raise ValueError("op019 output must match q")
    if not rows:
        return out
    scale = HEAD_DIM**-0.5 if softmax_scale is None else float(softmax_scale)
    if scale <= 0:
        raise ValueError("softmax scale must be positive")

    # Required because invalid/padding requests do not own a group descriptor.
    # It is deliberately inside the candidate transaction and graph capture.
    out.zero_()
    total_cells = membership_workspace.numel()
    _clear_qsa_group_workspace_kernel[
        (triton.cdiv(total_cells, BLOCK_CLEAR),)
    ](
        membership_workspace,
        group_base_workspace,
        overflow_workspace,
        write_count_workspace,
        total_cells,
        group_slots,
        rows * QUERY_HEADS,
        BLOCK=BLOCK_CLEAR,
        num_warps=4,
    )
    _build_qsa_group_membership_kernel[(rows,)](
        logical_indices,
        token_to_req,
        query_start_loc,
        membership_workspace,
        group_base_workspace,
        overflow_workspace,
        logical_indices.stride(0),
        logical_indices.stride(1),
        rows,
        num_requests,
        group_slots,
        TOPK_VALUE=TOPK,
        TOKEN_BUCKET_VALUE=TOKEN_BUCKET,
        GROUP_ROWS_VALUE=GROUP_ROWS,
        BLOCK=BLOCK_BUILD,
        num_warps=4,
    )
    _qsa_sparse_paged_gqa_group4_kernel[(group_slots, KV_HEADS)](
        q,
        k_cache,
        v_cache,
        logical_indices,
        block_table,
        token_to_req,
        logical_positions,
        membership_workspace,
        group_base_workspace,
        overflow_workspace,
        write_count_workspace,
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
        rows,
        k_cache.shape[0],
        num_requests,
        group_slots,
        scale,
        TOPK_VALUE=TOPK,
        TOKEN_BUCKET_VALUE=TOKEN_BUCKET,
        PAGE_SIZE_VALUE=PAGE_SIZE,
        PAGE_TABLE_WIDTH=block_table.shape[1],
        GROUP_ROWS_VALUE=GROUP_ROWS,
        GROUP_SIZE=QUERY_HEADS,
        HEAD_DIM_VALUE=HEAD_DIM,
        BLOCK_M_VALUE=BLOCK_M,
        BLOCK_N_VALUE=BLOCK_N,
        BLOCK_D_VALUE=BLOCK_D,
        num_warps=4,
        num_stages=2,
    )
    return out


@dataclass
class FrozenFixture:
    phase: str
    root: Path
    manifest: dict
    manifest_sha256: str
    selected_sha256: str
    selected: np.ndarray
    token_to_req: np.ndarray
    logical_positions: np.ndarray
    query_start_loc: np.ndarray
    request_run_ids: np.ndarray
    seq_lens: np.ndarray


@dataclass
class Workload:
    phase: str
    rows: int
    mode: str
    fixture_origin: tuple[int, int]
    fixture_manifest_sha256: str
    fixture_selected_sha256: str
    q: torch.Tensor
    k_cache: torch.Tensor
    v_cache: torch.Tensor
    selected: torch.Tensor
    selected_a: torch.Tensor
    selected_b: torch.Tensor
    block_table: torch.Tensor
    token_to_req: torch.Tensor
    logical_positions: torch.Tensor
    query_start_loc: torch.Tensor
    membership: torch.Tensor
    group_base: torch.Tensor
    overflow: torch.Tensor
    write_count: torch.Tensor
    cpu_selected: np.ndarray
    cpu_token_to_req: np.ndarray
    cpu_positions: np.ndarray
    cpu_starts: np.ndarray


def _load_raw(root: Path, entry: dict) -> np.ndarray:
    path = root / entry["path"]
    if not path.is_file() or path.stat().st_size != int(entry["nbytes"]):
        raise RuntimeError(f"raw fixture size mismatch: {path}")
    if _sha256(path) != entry["sha256"]:
        raise RuntimeError(f"raw fixture SHA mismatch: {path}")
    array = np.memmap(path, mode="r", dtype=np.dtype(entry["dtype"]))
    expected = int(np.prod(entry["shape"], dtype=np.int64))
    if array.size != expected:
        raise RuntimeError(f"raw fixture element count mismatch: {path}")
    return np.asarray(array.reshape(entry["shape"])).copy()


def load_fixture(root: Path, phase: str) -> FrozenFixture:
    root = root.resolve()
    manifest_path = root / "manifest.json"
    manifest_sha = _sha256(manifest_path)
    expected = EXPECTED_FIXTURES[phase]
    if manifest_sha != expected["manifest_sha256"]:
        raise RuntimeError(
            f"{phase} manifest SHA mismatch: {manifest_sha} != "
            f"{expected['manifest_sha256']}"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("observed_phase") != phase or int(manifest.get("rows", -1)) != 4096:
        raise RuntimeError(f"{phase} manifest phase/rows mismatch")
    files = manifest["files"]
    selected = _load_raw(root, files["selected"])
    if files["selected"]["sha256"] != expected["selected_sha256"]:
        raise RuntimeError(f"{phase} selected SHA is not the frozen input")
    arrays = {
        name: _load_raw(root, files[name])
        for name in (
            "token_to_req",
            "logical_positions",
            "query_start_loc",
            "request_run_ids",
            "seq_lens",
        )
    }
    if selected.shape != (4096, TOPK) or selected.dtype != np.dtype("<i4"):
        raise RuntimeError(f"{phase} selected shape/dtype mismatch")
    run_ids = arrays["request_run_ids"].astype(np.int64, copy=False)
    if not np.array_equal(run_ids, np.arange(run_ids.size, dtype=np.int64)):
        raise RuntimeError(
            "first-round direct group-id mapping requires contiguous request run ids"
        )
    starts = arrays["query_start_loc"].astype(np.int64, copy=False)
    if starts.size != run_ids.size + 1 or starts[0] != 0 or starts[-1] != 4096:
        raise RuntimeError("fixture request boundaries do not span rows4096")
    duplicate_rows = 0
    for values in selected:
        valid = values[values >= 0]
        if np.unique(valid).size != valid.size:
            duplicate_rows += 1
    if duplicate_rows:
        raise RuntimeError(
            f"producer-unique gate failed in {duplicate_rows} fixture rows"
        )
    if selected[selected >= 0].max(initial=-1) >= TOKEN_BUCKET:
        raise RuntimeError("frozen valid fixture exceeds TOKEN_BUCKET=8192")
    return FrozenFixture(
        phase=phase,
        root=root,
        manifest=manifest,
        manifest_sha256=manifest_sha,
        selected_sha256=files["selected"]["sha256"],
        selected=selected,
        token_to_req=arrays["token_to_req"],
        logical_positions=arrays["logical_positions"],
        query_start_loc=arrays["query_start_loc"],
        request_run_ids=arrays["request_run_ids"],
        seq_lens=arrays["seq_lens"],
    )


def _rows64_window(fixture: FrozenFixture) -> tuple[int, int]:
    starts = fixture.query_start_loc.astype(np.int64)
    lengths = np.diff(starts)
    run = int(np.argmax(lengths))
    begin, end = int(starts[run]), int(starts[run + 1])
    if end - begin < 64:
        raise RuntimeError("fixture has no request segment long enough for rows64")
    candidates = np.arange(begin, end - 64 + 1, dtype=np.int64)
    aligned = candidates[candidates % 16 == 0]
    if not aligned.size:
        raise RuntimeError("fixture has no 16-aligned rows64 window")
    center = (begin + end - 64) / 2.0
    start = int(aligned[np.argmin(np.abs(aligned - center))])
    return start, start + 64


def _coprime_multiplier(size: int) -> int:
    for value in range(3, max(4, size), 2):
        if math.gcd(value, size) == 1:
            return value
    return 1


def _selected_b_affine(selected: torch.Tensor, logical_tokens: int) -> torch.Tensor:
    """Make a cardinality-preserving but materially different graph input."""

    multiplier = _coprime_multiplier(logical_tokens)
    offset = logical_tokens // 2 + 1
    in_domain = (selected >= 0) & (selected < logical_tokens)
    return torch.where(
        in_domain,
        (selected * multiplier + offset) % logical_tokens,
        selected,
    )


def _selected_b_affine_cpu(selected: np.ndarray, logical_tokens: int) -> np.ndarray:
    multiplier = _coprime_multiplier(logical_tokens)
    offset = logical_tokens // 2 + 1
    output = selected.copy()
    valid = (output >= 0) & (output < logical_tokens)
    output[valid] = (output[valid] * multiplier + offset) % logical_tokens
    return output.astype(np.int32, copy=False)


def make_workload(
    fixture: FrozenFixture,
    rows: int,
    mode: str,
    device: torch.device,
) -> Workload:
    if rows == 4096:
        origin = (0, 4096)
        selected = fixture.selected.copy()
        requests = fixture.token_to_req.copy().astype(np.int32)
        positions = fixture.logical_positions.copy().astype(np.int64)
        starts = fixture.query_start_loc.copy().astype(np.int32)
    elif rows == 64:
        origin = _rows64_window(fixture)
        selected = fixture.selected[origin[0] : origin[1]].copy()
        positions = fixture.logical_positions[origin[0] : origin[1]].copy().astype(np.int64)
        requests = np.zeros(rows, dtype=np.int32)
        starts = np.asarray([0, rows], dtype=np.int32)
    else:
        raise ValueError("op019 fixture runner supports rows64 or rows4096")
    if mode not in ("valid", "invalid_noncontiguous"):
        raise ValueError(f"unsupported mode: {mode}")

    num_requests = starts.size - 1
    nonnegative = selected[selected >= 0]
    max_token = int(nonnegative.max(initial=0))
    table_width = max(1, math.ceil((max_token + 1) / PAGE_SIZE))
    logical_tokens = table_width * PAGE_SIZE
    logical_pages = np.arange(table_width, dtype=np.int32)
    block_table = np.empty((num_requests, table_width), dtype=np.int32)
    if mode == "valid":
        for request in range(num_requests):
            block_table[request] = logical_pages
    else:
        multiplier = _coprime_multiplier(table_width)
        physical = (logical_pages * multiplier + 17) % table_width
        for request in range(num_requests):
            block_table[request] = np.roll(physical, request)
        block_table[:, 29::31] = -1
        selected[:, 11::17] = -1
        selected[:, 23::97] = logical_tokens + PAGE_SIZE
        requests[-1] = -1
        if rows > 1:
            requests[-2] = num_requests
        if rows >= 8:
            positions[1] = positions[0] + 3
            positions[-1] = -1

    seed_material = (
        f"{fixture.selected_sha256}:{fixture.phase}:{rows}:{mode}"
    ).encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "little")
    torch.manual_seed(seed)
    q = torch.randn((rows, QUERY_HEADS, HEAD_DIM), dtype=torch.bfloat16, device=device)
    k_cache = torch.randn(
        (table_width, PAGE_SIZE, KV_HEADS, HEAD_DIM),
        dtype=torch.bfloat16,
        device=device,
    )
    v_cache = torch.randn_like(k_cache)
    selected_tensor = torch.from_numpy(selected).to(device=device, dtype=torch.int32)
    selected_a = selected_tensor.clone()
    selected_b = torch.from_numpy(
        _selected_b_affine_cpu(selected, logical_tokens)
    ).to(device=device, dtype=torch.int32)
    token_to_req = torch.from_numpy(requests).to(device=device, dtype=torch.int32)
    logical_positions = torch.from_numpy(positions).to(device=device, dtype=torch.int64)
    query_start_loc = torch.from_numpy(starts).to(device=device, dtype=torch.int32)
    block_table_tensor = torch.from_numpy(block_table).to(device=device, dtype=torch.int32)
    group_slots = triton.cdiv(rows, GROUP_ROWS) + num_requests
    membership = torch.empty(
        (group_slots, TOKEN_BUCKET), dtype=torch.int32, device=device
    )
    group_base = torch.empty(group_slots, dtype=torch.int32, device=device)
    overflow = torch.empty(group_slots, dtype=torch.int32, device=device)
    write_count = torch.empty((rows, QUERY_HEADS), dtype=torch.int32, device=device)
    return Workload(
        phase=fixture.phase,
        rows=rows,
        mode=mode,
        fixture_origin=origin,
        fixture_manifest_sha256=fixture.manifest_sha256,
        fixture_selected_sha256=fixture.selected_sha256,
        q=q,
        k_cache=k_cache,
        v_cache=v_cache,
        selected=selected_tensor,
        selected_a=selected_a,
        selected_b=selected_b,
        block_table=block_table_tensor,
        token_to_req=token_to_req,
        logical_positions=logical_positions,
        query_start_loc=query_start_loc,
        membership=membership,
        group_base=group_base,
        overflow=overflow,
        write_count=write_count,
        cpu_selected=selected,
        cpu_token_to_req=requests,
        cpu_positions=positions,
        cpu_starts=starts,
    )


def make_order_stress_workload(
    fixture: FrozenFixture, device: torch.device
) -> Workload:
    """Create opposite/rotated selected orders and near-tie signed values."""

    workload = make_workload(fixture, 64, "valid", device)
    source = workload.cpu_selected[0]
    valid = source[source >= 0].copy()
    if valid.size < 64:
        raise RuntimeError("order stress needs at least 64 selected tokens")
    rows = []
    orders = (
        valid,
        valid[::-1],
        np.roll(valid, valid.size // 3),
        np.roll(valid[::-1], valid.size // 5),
    )
    for order in orders:
        row = np.full(TOPK, -1, dtype=np.int32)
        row[: order.size] = order
        rows.append(row)
    workload.cpu_selected[:GROUP_ROWS] = np.stack(rows)
    workload.selected = torch.from_numpy(workload.cpu_selected).to(
        device=device, dtype=torch.int32
    )
    workload.selected_a = workload.selected.clone()
    logical_tokens = workload.block_table.shape[1] * PAGE_SIZE
    workload.selected_b = torch.from_numpy(
        _selected_b_affine_cpu(workload.cpu_selected, logical_tokens)
    ).to(device=device, dtype=torch.int32)
    # Scores are deliberately close; signed V magnifies accumulation-order
    # sensitivity without changing the exact mathematical token set.
    workload.q.fill_(0.015625)
    key_pattern = torch.arange(
        workload.k_cache.numel(), device=device, dtype=torch.int64
    ).reshape(workload.k_cache.shape)
    workload.k_cache.copy_(
        (((key_pattern % 7) - 3).float() * 2.0e-4).to(torch.bfloat16)
    )
    value_pattern = torch.arange(
        workload.v_cache.numel(), device=device, dtype=torch.int64
    ).reshape(workload.v_cache.shape)
    signs = torch.where((value_pattern % 2) == 0, 1.0, -1.0)
    magnitudes = 0.5 + (value_pattern % 17).float() / 32.0
    workload.v_cache.copy_((signs * magnitudes).to(torch.bfloat16))
    workload.mode = "order_stress_reverse_rotate_near_tie_signed_v"
    return workload


def make_duplicate_fallback_workload(
    fixture: FrozenFixture, device: torch.device
) -> Workload:
    """Inject a same-row duplicate; device build must reject the whole group."""

    workload = make_workload(fixture, 64, "valid", device)
    valid_columns = np.flatnonzero(workload.cpu_selected[1] >= 0)
    if valid_columns.size < 2:
        raise RuntimeError("duplicate stress needs two valid selected columns")
    workload.cpu_selected[1, valid_columns[1]] = workload.cpu_selected[
        1, valid_columns[0]
    ]
    workload.selected = torch.from_numpy(workload.cpu_selected).to(
        device=device, dtype=torch.int32
    )
    workload.selected_a = workload.selected.clone()
    logical_tokens = workload.block_table.shape[1] * PAGE_SIZE
    workload.selected_b = torch.from_numpy(
        _selected_b_affine_cpu(workload.cpu_selected, logical_tokens)
    ).to(device=device, dtype=torch.int32)
    workload.mode = "duplicate_same_row_requires_group_fallback"
    return workload


def make_bucket_overflow_fallback_workload(
    fixture: FrozenFixture, device: torch.device
) -> Workload:
    """Write normal membership first, then force whole-group overflow fallback."""

    workload = make_workload(fixture, 64, "valid", device)
    valid_columns = np.flatnonzero(workload.cpu_selected[3] >= 0)
    if not valid_columns.size:
        raise RuntimeError("overflow stress needs one valid selected column")
    workload.cpu_selected[3, valid_columns[-1]] = TOKEN_BUCKET
    workload.selected = torch.from_numpy(workload.cpu_selected).to(
        device=device, dtype=torch.int32
    )
    workload.selected_a = workload.selected.clone()
    # Keep B in range for normal tokens while retaining one overflow token.
    logical_tokens = workload.block_table.shape[1] * PAGE_SIZE
    workload.selected_b = torch.from_numpy(
        _selected_b_affine_cpu(workload.cpu_selected, logical_tokens)
    ).to(device=device, dtype=torch.int32)
    workload.mode = "bucket_overflow_requires_whole_group_fallback"
    return workload


def _group_metrics(workload: Workload) -> dict[str, object]:
    selected = workload.cpu_selected
    requests = workload.cpu_token_to_req
    positions = workload.cpu_positions
    starts = workload.cpu_starts
    row_sizes = np.count_nonzero(selected >= 0, axis=1).astype(np.int64)
    denominator = int(row_sizes[(requests >= 0) & (positions >= 0)].sum())
    covered = 0
    union_sum = 0
    full_groups = 0
    fallback_rows = 0
    for request in range(starts.size - 1):
        begin, end = int(starts[request]), int(starts[request + 1])
        row = begin
        while row < end:
            count = min(GROUP_ROWS, end - row)
            ids = np.arange(row, row + count)
            eligible = (
                count == GROUP_ROWS
                and np.all(requests[ids] == request)
                and np.all(positions[ids] == positions[row] + np.arange(GROUP_ROWS))
                and np.all(positions[ids] >= 0)
            )
            if eligible:
                values = np.concatenate([selected[item][selected[item] >= 0] for item in ids])
                covered += int(row_sizes[ids].sum())
                union_sum += int(np.unique(values).size)
                full_groups += 1
            else:
                fallback_rows += count
            row += GROUP_ROWS
    return {
        "B_all_eligible_occurrences": denominator,
        "A_R_covered_occurrences": covered,
        "U_R_union_sum": union_sum,
        "rho": (covered - union_sum) / denominator if denominator else None,
        "coverage": covered / denominator if denominator else None,
        "mask_density": covered / (GROUP_ROWS * union_sum) if union_sum else None,
        "eligible_full_groups": full_groups,
        "fallback_rows": fallback_rows,
    }


def _sample_reference_rows(workload: Workload) -> list[int]:
    rows: set[int] = {0, workload.rows - 1}
    for request in range(workload.cpu_starts.size - 1):
        begin = int(workload.cpu_starts[request])
        end = int(workload.cpu_starts[request + 1])
        if begin < end:
            rows.update((begin, (begin + end - 1) // 2, end - 1))
            rows.update(range(begin, min(begin + GROUP_ROWS + 1, end)))
            rows.update(range(max(begin, end - GROUP_ROWS - 1), end))
    return sorted(row for row in rows if 0 <= row < workload.rows)[:32]


def _fp32_reference(workload: Workload, row_ids: list[int]) -> torch.Tensor:
    reference = torch.zeros(
        (len(row_ids), QUERY_HEADS, HEAD_DIM),
        dtype=torch.bfloat16,
        device=workload.q.device,
    )
    table_cpu = workload.block_table.cpu()
    requests_cpu = workload.token_to_req.cpu()
    selected_cpu = workload.selected[row_ids].cpu().long()
    scale = HEAD_DIM**-0.5
    for output_row, source_row in enumerate(row_ids):
        request = int(requests_cpu[source_row])
        if not 0 <= request < table_cpu.shape[0]:
            continue
        tokens = selected_cpu[output_row]
        pages = torch.div(tokens.clamp_min(0), PAGE_SIZE, rounding_mode="floor")
        offsets = tokens.clamp_min(0) % PAGE_SIZE
        valid = (tokens >= 0) & (pages < table_cpu.shape[1])
        safe_pages = pages.clamp(0, table_cpu.shape[1] - 1)
        physical = table_cpu[request, safe_pages]
        valid &= (physical >= 0) & (physical < workload.k_cache.shape[0])
        if not bool(valid.any()):
            continue
        physical_device = physical[valid].to(workload.q.device)
        offset_device = offsets[valid].to(workload.q.device)
        keys = workload.k_cache[physical_device, offset_device, 0].float()
        values = workload.v_cache[physical_device, offset_device, 0].float()
        for head in range(QUERY_HEADS):
            scores = torch.matmul(keys, workload.q[source_row, head].float()) * scale
            reference[output_row, head] = torch.matmul(
                torch.softmax(scores, dim=0), values
            ).to(torch.bfloat16)
    return reference


def _tensor_sha(tensor: torch.Tensor) -> str:
    value = tensor.detach().to("cpu").contiguous().view(torch.uint8).numpy()
    return hashlib.sha256(memoryview(value).cast("B")).hexdigest()


def _correctness(
    workload: Workload,
    generic_output: torch.Tensor,
    candidate_output: torch.Tensor,
) -> dict[str, object]:
    if not bool(torch.isfinite(generic_output).all()) or not bool(
        torch.isfinite(candidate_output).all()
    ):
        raise AssertionError("generic or candidate output contains NaN/Inf")
    torch.testing.assert_close(
        candidate_output.float(), generic_output.float(), atol=ATOL, rtol=RTOL
    )
    row_ids = _sample_reference_rows(workload)
    reference = _fp32_reference(workload, row_ids)
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
        if int(torch.count_nonzero(generic_output[invalid]).item()) != 0:
            raise AssertionError("generic invalid-request output is not exact zero")
        if int(torch.count_nonzero(candidate_output[invalid]).item()) != 0:
            raise AssertionError("candidate invalid-request output is not exact zero")
    write_count = workload.write_count.cpu()
    if not bool(torch.all(write_count == 1)):
        wrong_indices = torch.nonzero(write_count != 1, as_tuple=False)[:16]
        wrong = [
            [int(row), int(head), int(write_count[row, head])]
            for row, head in wrong_indices.tolist()
        ]
        raise AssertionError(f"candidate row/head coverage marker is not one: {wrong}")
    difference = (candidate_output.float() - generic_output.float()).abs()
    return {
        "sampled_fp32_rows": row_ids,
        "max_abs_candidate_vs_generic": float(difference.max().item()),
        "mean_abs_candidate_vs_generic": float(difference.mean().item()),
        "generic_output_sha256": _tensor_sha(generic_output),
        "candidate_output_sha256": _tensor_sha(candidate_output),
    }


def _structure_reference(workload: Workload, maximum_groups: int = 8) -> dict[str, object]:
    group_base = workload.group_base.cpu().numpy()
    overflow = workload.overflow.cpu().numpy()
    expected_group_map: dict[int, int] = {}
    for request in range(workload.cpu_starts.size - 1):
        begin, end = (
            int(workload.cpu_starts[request]),
            int(workload.cpu_starts[request + 1]),
        )
        for base in range(begin, end, GROUP_ROWS):
            group_id = base // GROUP_ROWS + request
            if group_id in expected_group_map:
                raise AssertionError(f"CPU group-id collision gid={group_id}")
            expected_group_map[group_id] = base
    actual_group_map = {
        int(group_id): int(base)
        for group_id, base in enumerate(group_base.tolist())
        if int(base) >= 0
    }
    if actual_group_map != expected_group_map:
        raise AssertionError(
            "device group-base map has a collision, missing group, or extra writer"
        )
    if len(set(actual_group_map.values())) != len(actual_group_map):
        raise AssertionError("multiple device group slots own the same base row")
    checked = 0
    for request in range(workload.cpu_starts.size - 1):
        begin, end = (
            int(workload.cpu_starts[request]),
            int(workload.cpu_starts[request + 1]),
        )
        for base in range(begin, end, GROUP_ROWS):
            group_id = base // GROUP_ROWS + request
            if int(group_base[group_id]) != base:
                raise AssertionError(
                    f"group base mismatch gid={group_id}: {group_base[group_id]} != {base}"
                )
            expected: dict[int, int] = {}
            for row in range(base, min(base + GROUP_ROWS, end)):
                bit = 1 << (row - base)
                for token in workload.cpu_selected[row]:
                    if 0 <= int(token) < TOKEN_BUCKET:
                        expected[int(token)] = expected.get(int(token), 0) | bit
            actual = workload.membership[group_id].cpu().numpy()
            actual_tokens = np.flatnonzero(actual)
            if actual_tokens.tolist() != sorted(expected):
                raise AssertionError(f"membership token set mismatch gid={group_id}")
            for token, bits in expected.items():
                if int(actual[token]) != bits:
                    raise AssertionError(
                        f"membership bits mismatch gid={group_id} token={token}"
                    )
            group_selected = workload.cpu_selected[
                base : min(base + GROUP_ROWS, end)
            ]
            high_token = bool(np.any(group_selected >= TOKEN_BUCKET))
            duplicate = any(
                np.unique(row[row >= 0]).size != np.count_nonzero(row >= 0)
                for row in group_selected
            )
            expected_overflow = int(high_token or duplicate)
            if int(overflow[group_id] != 0) != expected_overflow:
                raise AssertionError(f"overflow mismatch gid={group_id}")
            checked += 1
            if checked >= maximum_groups:
                return {
                    "checked_groups": checked,
                    "all_group_bases_checked": len(actual_group_map),
                    "group_base_bijection": "passed",
                    "status": "passed",
                }
    return {
        "checked_groups": checked,
        "all_group_bases_checked": len(actual_group_map),
        "group_base_bijection": "passed",
        "status": "passed",
    }


def _capture_graph(
    fn: Callable[[], torch.Tensor], output: torch.Tensor
) -> torch.cuda.CUDAGraph:
    for _ in range(5):
        fn()
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, capture_error_mode="thread_local"):
        fn()
    torch.cuda.synchronize()
    return graph


def _graph_dynamic_aba(
    workload: Workload,
    fn: Callable[[], torch.Tensor],
    output: torch.Tensor,
    eager_oracle: Callable[[], torch.Tensor],
) -> tuple[torch.cuda.CUDAGraph, dict[str, object]]:
    original_selected = workload.selected
    workload.selected = workload.selected_a
    oracle_a = eager_oracle().clone()
    torch.cuda.synchronize()
    graph_a = _capture_graph(fn, output)

    workload.selected = workload.selected_b
    oracle_b = eager_oracle().clone()
    torch.cuda.synchronize()
    graph_b = _capture_graph(fn, output)

    workload.selected = original_selected
    graph_a.replay()
    torch.cuda.synchronize()
    replay_a_first = output.clone()
    torch.testing.assert_close(
        replay_a_first.float(), oracle_a.float(), atol=ATOL, rtol=RTOL
    )
    graph_b.replay()
    torch.cuda.synchronize()
    replay_b = output.clone()
    torch.testing.assert_close(replay_b.float(), oracle_b.float(), atol=ATOL, rtol=RTOL)
    replay_a_first_sha = _tensor_sha(replay_a_first)
    replay_b_sha = _tensor_sha(replay_b)
    if replay_b_sha == replay_a_first_sha:
        oracle_b_sha = _tensor_sha(oracle_b)
        raise AssertionError(
            "graph B replay did not change from graph A; "
            f"selected_a_sha={_tensor_sha(workload.selected_a)} "
            f"selected_b_sha={_tensor_sha(workload.selected_b)} "
            f"replay_a_sha={replay_a_first_sha} oracle_b_sha={oracle_b_sha}"
        )
    graph_a.replay()
    torch.cuda.synchronize()
    replay_a_second = output.clone()
    torch.testing.assert_close(
        replay_a_second.float(), oracle_a.float(), atol=ATOL, rtol=RTOL
    )
    return graph_a, {
        "method": "dual_graph_shared_workspace_A_B_A",
        "replay_a_first_sha256": replay_a_first_sha,
        "replay_b_sha256": replay_b_sha,
        "replay_a_second_sha256": _tensor_sha(replay_a_second),
        "replays": 3,
        "changed_selected_pointer_only": True,
        "shared_candidate_workspace": True,
        "status": "passed",
    }


def _time_once(fn: Callable[[], object], repeat: int) -> float:
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    start.record()
    for _ in range(repeat):
        fn()
    end.record()
    torch.cuda.synchronize()
    return float(start.elapsed_time(end)) / repeat


def _summary(values: list[float]) -> dict[str, float | list[float]]:
    median = statistics.median(values)
    deviations = [abs(value - median) for value in values]
    return {
        "raw_ms": values,
        "median_ms": median,
        "p25_ms": float(np.percentile(values, 25)),
        "p75_ms": float(np.percentile(values, 75)),
        "mad_ms": statistics.median(deviations),
        "min_ms": min(values),
        "max_ms": max(values),
    }


def _interleaved_timing(
    baseline: Callable[[], object],
    candidate: Callable[[], object],
    repeat: int,
    minimum_samples: int,
    maximum_samples: int,
) -> dict[str, object]:
    for _ in range(5):
        baseline()
        candidate()
    torch.cuda.synchronize()
    baseline_values: list[float] = []
    candidate_values: list[float] = []
    orders: list[str] = []
    target = minimum_samples
    sample = 0
    while sample < target:
        if sample % 2 == 0:
            baseline_values.append(_time_once(baseline, repeat))
            candidate_values.append(_time_once(candidate, repeat))
            orders.append("baseline,candidate")
        else:
            candidate_values.append(_time_once(candidate, repeat))
            baseline_values.append(_time_once(baseline, repeat))
            orders.append("candidate,baseline")
        sample += 1
        if sample == minimum_samples:
            summaries = (_summary(baseline_values), _summary(candidate_values))
            unstable = any(
                item["median_ms"] > 0
                and item["mad_ms"] / item["median_ms"] > 0.03
                for item in summaries
            )
            if unstable:
                target = maximum_samples
    baseline_summary = _summary(baseline_values)
    candidate_summary = _summary(candidate_values)
    gain = (
        baseline_summary["median_ms"] / candidate_summary["median_ms"] - 1.0
    ) * 100.0
    return {
        "baseline": baseline_summary,
        "candidate": candidate_summary,
        "gain_pct": gain,
        "orders": orders,
        "repeat": repeat,
        "samples": len(orders),
    }


@torch.inference_mode()
def run_case(
    workload: Workload,
    repeat: int,
    minimum_samples: int,
    maximum_samples: int,
    measure_performance: bool,
) -> dict[str, object]:
    generic_output = torch.empty_like(workload.q)
    candidate_output = torch.empty_like(workload.q)
    oracle_output = torch.empty_like(workload.q)

    def generic_fn() -> torch.Tensor:
        return qsa_sparse_paged_attention(
            workload.q,
            workload.k_cache,
            workload.v_cache,
            workload.selected,
            workload.block_table,
            workload.token_to_req,
            out=generic_output,
        )

    def candidate_fn() -> torch.Tensor:
        return qsa_sparse_paged_attention_group4_direct(
            workload.q,
            workload.k_cache,
            workload.v_cache,
            workload.selected,
            workload.block_table,
            workload.token_to_req,
            workload.logical_positions,
            workload.query_start_loc,
            workload.membership,
            workload.group_base,
            workload.overflow,
            workload.write_count,
            out=candidate_output,
        )

    def generic_oracle() -> torch.Tensor:
        return qsa_sparse_paged_attention(
            workload.q,
            workload.k_cache,
            workload.v_cache,
            workload.selected,
            workload.block_table,
            workload.token_to_req,
            out=oracle_output,
        )

    original_selected = workload.selected
    generic_fn()
    candidate_fn()
    torch.cuda.synchronize()
    structure = _structure_reference(workload)
    correctness = _correctness(workload, generic_output, candidate_output)

    eager_a = generic_output.clone()
    workload.selected = workload.selected_b
    generic_fn()
    torch.cuda.synchronize()
    eager_b = generic_output.clone()
    eager_a_sha = _tensor_sha(eager_a)
    eager_b_sha = _tensor_sha(eager_b)
    if eager_a_sha == eager_b_sha:
        raise AssertionError(
            "eager generic output did not change for selected B; "
            f"selected_a_sha={_tensor_sha(workload.selected_a)} "
            f"selected_b_sha={_tensor_sha(workload.selected_b)} "
            f"eager_a_sha={eager_a_sha} eager_b_sha={eager_b_sha}"
        )
    workload.selected = original_selected

    candidate_graph, candidate_aba = _graph_dynamic_aba(
        workload, candidate_fn, candidate_output, generic_oracle
    )
    generic_graph, generic_aba = _graph_dynamic_aba(
        workload, generic_fn, generic_output, generic_oracle
    )
    workload.selected = original_selected
    generic_fn()
    candidate_fn()
    torch.cuda.synchronize()
    _correctness(workload, generic_output, candidate_output)

    eager_timing = None
    graph_timing = None
    if measure_performance:
        eager_timing = _interleaved_timing(
            generic_fn,
            candidate_fn,
            repeat,
            minimum_samples,
            maximum_samples,
        )
        graph_timing = _interleaved_timing(
            generic_graph.replay,
            candidate_graph.replay,
            repeat,
            minimum_samples,
            maximum_samples,
        )

    workspace_bytes = (
        workload.membership.numel() * workload.membership.element_size()
        + workload.group_base.numel() * workload.group_base.element_size()
        + workload.overflow.numel() * workload.overflow.element_size()
        + workload.write_count.numel() * workload.write_count.element_size()
    )
    result = {
        "phase": workload.phase,
        "rows": workload.rows,
        "mode": workload.mode,
        "fixture_origin": list(workload.fixture_origin),
        "fixture_manifest_sha256": workload.fixture_manifest_sha256,
        "fixture_selected_sha256": workload.fixture_selected_sha256,
        "q_shape": list(workload.q.shape),
        "kv_shape": list(workload.k_cache.shape),
        "selected_shape": list(workload.selected.shape),
        "block_table_shape": list(workload.block_table.shape),
        "workspace": {
            "membership_shape": list(workload.membership.shape),
            "membership_dtype": str(workload.membership.dtype),
            "group_base_shape": list(workload.group_base.shape),
            "overflow_shape": list(workload.overflow.shape),
            "write_count_shape": list(workload.write_count.shape),
            "total_bytes": workspace_bytes,
        },
        "launch": {
            "R": GROUP_ROWS,
            "TOKEN_BUCKET": TOKEN_BUCKET,
            "BLOCK_M": BLOCK_M,
            "BLOCK_N": BLOCK_N,
            "BLOCK_D": BLOCK_D,
            "candidate_transaction": [
                "output_zero",
                "workspace_clear",
                "membership_build",
                "group4_attention_with_fallback",
                "diagnostic_write_coverage_marker_plus_group_base_bijection",
            ],
        },
        "fixture_metrics": _group_metrics(workload),
        "correctness": correctness,
        "structure_reference": structure,
        "graph_dynamic_aba": {
            "generic": generic_aba,
            "candidate": candidate_aba,
        },
        "eager_timing": eager_timing,
        "graph_timing": graph_timing,
        "performance_measured": measure_performance,
    }
    if eager_timing is not None and graph_timing is not None:
        result["passes_eight_percent_eager_gate"] = (
            eager_timing["gain_pct"] >= PRIMARY_GAIN_GATE_PCT
        )
        result["passes_eight_percent_graph_gate"] = (
            graph_timing["gain_pct"] >= PRIMARY_GAIN_GATE_PCT
        )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefill-fixture", type=Path, default=DEFAULT_PREFILL_FIXTURE)
    parser.add_argument("--mixed-fixture", type=Path, default=DEFAULT_MIXED_FIXTURE)
    parser.add_argument("--scope", choices=("first", "full"), default="first")
    parser.add_argument("--repeat-4096", type=int, default=5)
    parser.add_argument("--repeat-64", type=int, default=20)
    parser.add_argument("--minimum-samples", type=int, default=7)
    parser.add_argument("--maximum-samples", type=int, default=11)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if sys.byteorder != "little":
        raise RuntimeError("op019 raw fixture reader requires a little-endian host")
    if not torch.cuda.is_available():
        raise RuntimeError("an accelerator exposed through torch.cuda is required")
    if args.minimum_samples < 3 or args.maximum_samples < args.minimum_samples:
        raise ValueError("invalid sample counts")

    fixtures = (
        load_fixture(args.prefill_fixture, "prefill"),
        load_fixture(args.mixed_fixture, "mixed"),
    )
    cases: list[tuple[FrozenFixture, int, str, bool]] = []
    for fixture in fixtures:
        cases.append((fixture, 4096, "valid", True))
        if args.scope == "full":
            cases.extend(
                (
                    (fixture, 64, "valid", True),
                    (fixture, 4096, "invalid_noncontiguous", False),
                    (fixture, 64, "invalid_noncontiguous", False),
                )
            )

    results = []
    for fixture, rows, mode, measure in cases:
        workload = make_workload(fixture, rows, mode, torch.device("cuda"))
        repeat = args.repeat_4096 if rows == 4096 else args.repeat_64
        results.append(
            run_case(
                workload,
                repeat=repeat,
                minimum_samples=args.minimum_samples,
                maximum_samples=args.maximum_samples,
                measure_performance=measure,
            )
        )
    # Mandatory semantic stress, independent of the promotion timing arms.
    # The first case changes every non-owner row's effective traversal order;
    # the second proves that a same-row duplicate sets the device reject flag
    # and forces the whole group through exact per-row fallback.
    for stress_workload in (
        make_order_stress_workload(fixtures[0], torch.device("cuda")),
        make_duplicate_fallback_workload(fixtures[0], torch.device("cuda")),
        make_bucket_overflow_fallback_workload(fixtures[0], torch.device("cuda")),
    ):
        results.append(
            run_case(
                stress_workload,
                repeat=args.repeat_64,
                minimum_samples=args.minimum_samples,
                maximum_samples=args.maximum_samples,
                measure_performance=False,
            )
        )

    primary = [
        result
        for result in results
        if result["rows"] == 4096 and result["mode"] == "valid"
    ]
    primary_gate_passed = len(primary) == 2 and all(
        result.get("passes_eight_percent_eager_gate", False)
        and result.get("passes_eight_percent_graph_gate", False)
        for result in primary
    )
    rows64 = [
        result
        for result in results
        if result["rows"] == 64 and result["mode"] == "valid"
    ]
    rows64_guard_passed = None
    if args.scope == "full":
        rows64_guard_passed = len(rows64) == 2 and all(
            result["eager_timing"]["gain_pct"]
            >= -ROWS64_EAGER_REGRESSION_LIMIT_PCT
            and result["graph_timing"]["gain_pct"]
            >= -ROWS64_GRAPH_REGRESSION_LIMIT_PCT
            for result in rows64
        )

    baseline_source = Path(inspect.getsourcefile(qsa_sparse_paged_attention) or "")
    payload = {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "scope": args.scope,
        "candidate": "R4 direct-address membership TOKEN_BUCKET=8192",
        "baseline": "current imported flag_gems.fused.qsa_sparse_paged_attention",
        "baseline_source": str(baseline_source),
        "baseline_source_sha256": (
            _sha256(baseline_source) if baseline_source.is_file() else None
        ),
        "fixture_expectations": EXPECTED_FIXTURES,
        "atol": ATOL,
        "rtol": RTOL,
        "primary_gain_gate_pct": PRIMARY_GAIN_GATE_PCT,
        "primary_gate_passed": primary_gate_passed,
        "rows64_guard_passed": rows64_guard_passed,
        "full_correctness_gate_complete": args.scope == "full",
        "promotion_allowed": bool(
            args.scope == "full" and primary_gate_passed and rows64_guard_passed
        ),
        "stop_conditions": [
            "either frozen fixture fails SHA, rows, dtype, or producer-unique validation",
            "generic/candidate or sampled FP32 correctness exceeds atol=rtol=0.05",
            "device membership differs from the CPU structure reference",
            "invalid request output is not exact zero",
            "generic or candidate graph selected-only A/B/A replay fails",
            "Prefill or Mixed rows4096 valid eager/graph gain is below 8 percent",
            "full scope rows64 eager regresses over 5 percent or graph over 2 percent",
        ],
        "conclusion_boundary": (
            "Standalone operator microbenchmark only; no service source was changed, "
            "no end-to-end gain or formal accuracy acceptance is proven."
        ),
        "results": results,
    }
    script_path = Path(__file__).resolve()
    payload["script_sha256"] = _sha256(script_path)
    encoded = json.dumps(payload, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
