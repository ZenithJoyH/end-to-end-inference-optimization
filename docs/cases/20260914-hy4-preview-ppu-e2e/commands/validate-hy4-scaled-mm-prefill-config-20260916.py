#!/usr/bin/env python3
"""Validate the T-Head scaled-mm config set and CUDA-graph replay."""

from __future__ import annotations

import json

import torch

from flag_gems import runtime
from flag_gems.ops.scaled_mm import scaled_mm_out


REQUIRED = {
    (128, 64, 64, 3, 4),
    (128, 128, 64, 3, 4),
    (64, 256, 64, 3, 4),
}
SHAPES = (
    (2048, 6144, 576),
    (16, 6144, 576),
)


def config_signature(row) -> tuple[int, int, int, int, int]:
    kwargs = row.kwargs
    return (
        kwargs["BLOCK_M"],
        kwargs["BLOCK_N"],
        kwargs["BLOCK_K"],
        row.num_stages,
        row.num_warps,
    )


def validate_graph(m: int, k: int, n: int) -> dict:
    a = torch.randint(-127, 128, (m, k), device="cuda", dtype=torch.int8)
    b = torch.randint(-127, 128, (k, n), device="cuda", dtype=torch.int8)
    scale_a = torch.rand((m, 1), device="cuda", dtype=torch.float32) * 0.02
    scale_b = torch.rand((n,), device="cuda", dtype=torch.float32) * 0.02
    out = torch.empty((m, n), device="cuda", dtype=torch.bfloat16)

    def op() -> None:
        scaled_mm_out(
            a,
            b,
            scale_a,
            scale_b,
            out_dtype=torch.bfloat16,
            out=out,
        )

    for _ in range(3):
        op()
    torch.cuda.synchronize()
    expected = out.clone()

    stream = torch.cuda.Stream()
    stream.wait_stream(torch.cuda.current_stream())
    with torch.cuda.stream(stream):
        for _ in range(2):
            op()
    stream.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        op()
    for _ in range(2):
        graph.replay()
    torch.cuda.synchronize()

    exact_fraction = float((out == expected).float().mean().item())
    max_abs_diff = float((out.float() - expected.float()).abs().max().item())
    assert exact_fraction == 1.0, (m, k, n, exact_fraction, max_abs_diff)
    return {
        "M": m,
        "N": n,
        "K": k,
        "capture": "passed",
        "replays": 2,
        "exact_fraction": exact_fraction,
        "max_abs_diff": max_abs_diff,
    }


def main() -> None:
    configs = runtime.get_tuned_config("scaled_mm")
    signatures = {config_signature(row) for row in configs}
    assert len(configs) == 7, len(configs)
    assert REQUIRED <= signatures, (REQUIRED, signatures)
    report = {
        "schema_version": 1,
        "config_count": len(configs),
        "required_configs_present": True,
        "config_signatures": sorted(signatures),
        "graph_results": [validate_graph(*shape) for shape in SHAPES],
    }
    print("SUMMARY=" + json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    torch.manual_seed(20260916)
    main()
