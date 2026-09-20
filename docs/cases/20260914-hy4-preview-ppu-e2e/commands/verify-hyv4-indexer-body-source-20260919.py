#!/usr/bin/env python3
"""Verify the applied HY4 Indexer body optimizations from imported source."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from vllm_fl.models import hy_v4


def reference_paged_sequence(
    kv_cache: torch.Tensor,
    block_table: torch.Tensor,
    seq_len: int,
) -> torch.Tensor:
    block_size = kv_cache.shape[1]
    num_blocks = (seq_len + block_size - 1) // block_size
    blocks = block_table[:num_blocks].to(torch.long)
    offsets = torch.arange(seq_len, device=kv_cache.device, dtype=torch.long)
    slots = blocks.index_select(0, offsets // block_size) * block_size
    slots = slots + offsets.remainder(block_size)
    return kv_cache.reshape(-1, kv_cache.shape[-1]).index_select(0, slots)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")
    assert torch.cuda.is_available()
    assert hy_v4.current_platform.vendor_name == "thead"
    torch.manual_seed(20260919)

    cache = torch.randn(
        (6640, 64, 128), device="cuda", dtype=torch.bfloat16
    )
    block_table = torch.randperm(
        6640, device="cuda", dtype=torch.int64
    )[:128].to(torch.int32)
    gather_rows = []
    for seq_len in (2041, 3987, 4096):
        expected = reference_paged_sequence(cache, block_table, seq_len)
        actual = hy_v4._paged_sequence(cache, block_table, seq_len)
        torch.cuda.synchronize()
        row = {
            "seq_len": seq_len,
            "exact": bool(torch.equal(expected, actual)),
        }
        gather_rows.append(row)
        assert row["exact"]

    graph_seq_len = 4096
    graph = torch.cuda.CUDAGraph()
    torch.cuda.synchronize()
    with torch.cuda.graph(graph):
        graph_output = hy_v4._paged_sequence(
            cache, block_table, graph_seq_len
        )
    graph_replays = []
    for replay in range(2):
        cache[block_table[0].long(), 0, 0].add_(1)
        expected = reference_paged_sequence(
            cache, block_table, graph_seq_len
        )
        graph.replay()
        torch.cuda.synchronize()
        graph_replays.append({
            "replay": replay + 1,
            "exact": bool(torch.equal(expected, graph_output)),
        })
    assert all(row["exact"] for row in graph_replays)

    selected_source = torch.randint(
        -1, 4096, (128, 2048), device="cuda", dtype=torch.int32
    )
    selected_source[:, ::7] = -1
    row_starts = torch.arange(
        128, device="cuda", dtype=torch.int32
    ).mul_(4096)
    translated_expected = selected_source.clone()
    valid = translated_expected >= 0
    translated_expected.add_((row_starts - 1024).unsqueeze(1))
    translated_expected.masked_fill_(~valid, -1)
    translated_actual = selected_source.clone()
    hy_v4._translate_hyv4_selected_block(
        translated_actual, row_starts, 1024
    )
    torch.cuda.synchronize()
    translation_exact = bool(
        torch.equal(translated_expected, translated_actual)
    )
    assert translation_exact

    score_source = torch.randn(
        (128, 2048, 32), device="cuda", dtype=torch.bfloat16
    )
    weights = torch.randn(
        (128, 32), device="cuda", dtype=torch.bfloat16
    )
    expected_products = (
        torch.relu(score_source)
        * weights.to(score_source.dtype).unsqueeze(1)
    )
    expected_logits = expected_products.sum(dim=-1).float()
    score_actual = score_source.clone()
    actual_logits = hy_v4._hyv4_weighted_relu_reduce(
        score_actual, weights
    )
    torch.cuda.synchronize()
    pointwise_exact = bool(torch.equal(expected_products, score_actual))
    logits_exact = bool(torch.equal(expected_logits, actual_logits))
    assert pointwise_exact and logits_exact

    result = {
        "schema_version": 1,
        "device": torch.cuda.get_device_name(0),
        "vendor": hy_v4.current_platform.vendor_name,
        "paged_sequence": gather_rows,
        "paged_sequence_graph_capture": "passed",
        "paged_sequence_graph_replays": graph_replays,
        "block_translation_exact": translation_exact,
        "inplace_pointwise_exact": pointwise_exact,
        "inplace_logits_exact": logits_exact,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
