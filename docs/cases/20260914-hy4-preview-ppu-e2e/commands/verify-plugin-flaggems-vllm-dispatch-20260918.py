#!/usr/bin/env python3
"""Verify Plugin dispatch to FlagGems-vLLM and W8A8 graph replay."""

from __future__ import annotations

import json

import torch

from vllm_fl.dispatch.backends.flaggems.impl.mla_sparse import (
    _resolve_flash_mla_sparse_fwd,
)
from vllm_fl.quantization.w8a8.moe_experts import (
    _flaggems_fused_experts_impl,
    _resolve_flaggems_fused_experts_impl,
)


def main() -> None:
    torch.manual_seed(20260918)
    m, experts, hidden, local_i, topk = 2048, 256, 6144, 128, 8
    hidden_states = torch.randn((m, hidden), device="cuda", dtype=torch.bfloat16)
    w1 = torch.randint(
        -8, 9, (experts, 2 * local_i, hidden), device="cuda", dtype=torch.int8
    )
    w2 = torch.randint(
        -8, 9, (experts, hidden, local_i), device="cuda", dtype=torch.int8
    )
    topk_ids = torch.randint(
        0, experts, (m, topk), device="cuda", dtype=torch.int32
    )
    topk_weights = torch.rand((m, topk), device="cuda", dtype=torch.float32)
    topk_weights /= topk_weights.sum(dim=-1, keepdim=True)
    kwargs = {
        "hidden_states": hidden_states,
        "w1": w1,
        "w2": w2,
        "topk_weights": topk_weights.contiguous(),
        "topk_ids": topk_ids.contiguous(),
        "inplace": False,
        "activation": "silu",
        "apply_router_weight_on_input": False,
        "use_fp8_w8a8": False,
        "use_int8_w8a8": True,
        "use_int8_w8a16": False,
        "use_int4_w4a16": False,
        "per_channel_quant": True,
        "global_num_experts": experts,
        "expert_map": None,
        "w1_scale": torch.full((experts, 2 * local_i, 1), 0.01, device="cuda"),
        "w2_scale": torch.full((experts, hidden, 1), 0.01, device="cuda"),
        "a1_scale": None,
        "a2_scale": None,
        "block_shape": None,
        "w1_bias": None,
        "w2_bias": None,
    }

    eager = _flaggems_fused_experts_impl(**kwargs)
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        captured = _flaggems_fused_experts_impl(**kwargs)
    graph.replay()
    torch.cuda.synchronize()
    replay1 = captured.clone()
    graph.replay()
    torch.cuda.synchronize()
    replay2 = captured.clone()

    moe_impl = _resolve_flaggems_fused_experts_impl()
    sparse_impl = _resolve_flash_mla_sparse_fwd()
    result = {
        "moe_impl": f"{moe_impl.__module__}.{moe_impl.__name__}",
        "sparse_mla_impl": f"{sparse_impl.__module__}.{sparse_impl.__name__}",
        "shape": "M2048/E256/TopK8/H6144/localI128",
        "graph_capture": "passed",
        "graph_replays": 2,
        "eager_vs_replay1_exact": bool(torch.equal(eager, replay1)),
        "replay1_vs_replay2_exact": bool(torch.equal(replay1, replay2)),
        "eager_vs_replay1_max_abs_diff": float(
            (eager.float() - replay1.float()).abs().max().item()
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
