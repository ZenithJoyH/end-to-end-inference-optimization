#!/usr/bin/env python3
"""Verify the applied no-refill Indexer block under graph replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from vllm_fl.models import hy_v4


ROWS = 128
KEYS = 2048
HEADS = 32
HEAD_DIM = 128
TOPK = 2048
SENTINEL = 123456789


def invoke(q, weights, keys, starts, ends, output) -> None:
    hy_v4._select_topk_block(
        q,
        weights,
        keys,
        starts,
        ends,
        key_start=0,
        key_end=KEYS,
        request_start=0,
        topk=TOPK,
        output=output,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")
    assert torch.cuda.is_available()
    assert hy_v4.current_platform.vendor_name == "thead"
    source = Path(hy_v4.__file__)
    source_text = source.read_text()
    function_text = source_text.split("def _select_topk_block(", 1)[1].split(
        "def _translate_hyv4_selected_prefix(", 1
    )[0]
    assert "output.fill_(-1)" not in function_text

    torch.manual_seed(20260919)
    q = torch.randn(
        (ROWS, HEADS, HEAD_DIM), device="cuda", dtype=torch.bfloat16
    )
    keys = torch.randn((KEYS, HEAD_DIM), device="cuda", dtype=torch.bfloat16)
    weights = torch.randn((ROWS, HEADS), device="cuda", dtype=torch.bfloat16)
    starts = torch.zeros((ROWS,), device="cuda", dtype=torch.int32)
    ends = torch.arange(
        KEYS - ROWS + 1, KEYS + 1, device="cuda", dtype=torch.int32
    )
    output = torch.full(
        (ROWS, TOPK), SENTINEL, device="cuda", dtype=torch.int32
    )
    invoke(q, weights, keys, starts, ends, output)
    torch.cuda.synchronize()
    expected_counts = torch.minimum(
        ends - starts, torch.full_like(ends, TOPK)
    )
    eager = {
        "sentinel_remaining": int((output == SENTINEL).sum().item()),
        "valid_counts_exact": bool(
            torch.equal((output >= 0).sum(dim=1), expected_counts)
        ),
    }
    assert eager["sentinel_remaining"] == 0
    assert eager["valid_counts_exact"]

    graph = torch.cuda.CUDAGraph()
    output.fill_(SENTINEL)
    torch.cuda.synchronize()
    with torch.cuda.graph(graph):
        invoke(q, weights, keys, starts, ends, output)
    replays = []
    for replay in range(2):
        output.fill_(SENTINEL)
        graph.replay()
        torch.cuda.synchronize()
        row = {
            "replay": replay + 1,
            "sentinel_remaining": int((output == SENTINEL).sum().item()),
            "valid_counts_exact": bool(
                torch.equal((output >= 0).sum(dim=1), expected_counts)
            ),
        }
        assert row["sentinel_remaining"] == 0
        assert row["valid_counts_exact"]
        replays.append(row)

    result = {
        "schema_version": 1,
        "source": str(source),
        "source_contains_block_fill": False,
        "shape": {"rows": ROWS, "keys": KEYS, "topk": TOPK},
        "eager": eager,
        "graph_capture": "passed",
        "graph_replays": replays,
        "conclusion_boundary": "applied-source operator validation only",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
