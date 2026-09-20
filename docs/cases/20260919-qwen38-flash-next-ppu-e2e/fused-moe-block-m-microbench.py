#!/usr/bin/env python3
"""Falsify a BLOCK_SIZE_M-only tuning hypothesis for Qwen3.8 Flash MoE.

This is an offline accelerator microbenchmark.  It calls the same public
FlagGems alignment and fused-MoE kernel interfaces selected by the live Plugin,
but it neither starts nor sends traffic to a vLLM service.

Production rank-local BF16 shapes (TP=8):
  W1 [512, 160, 2560], W2 [512, 2560, 80], top-k=10.

Only BLOCK_SIZE_M differs between baseline and candidate:
  decode M=64:          32 -> 16
  prefill M=4096/4153: 128 -> 64
All other Triton config fields are asserted equal before execution.
"""

from __future__ import annotations

import argparse
import inspect
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import torch
from vllm.triton_utils import tl

from flag_gems.fused.fused_moe import invoke_fused_moe_triton_kernel
from flag_gems.fused.moe_align_block_size import moe_align_block_size
from flag_gems.fused.silu_and_mul import silu_and_mul_out


NUM_EXPERTS = 512
TOP_K = 10
HIDDEN_SIZE = 2560
LOCAL_INTERMEDIATE = 80
W1_OUT = 2 * LOCAL_INTERMEDIATE

CASES = {
    "decode": {
        "tokens": 64,
        "baseline": {
            "BLOCK_SIZE_M": 32,
            "BLOCK_SIZE_N": 64,
            "BLOCK_SIZE_K": 128,
            "GROUP_SIZE_M": 1,
            "SPLIT_K": 1,
            "num_warps": 4,
            "num_stages": 3,
        },
        "candidate_block_m": 16,
    },
    "prefill": {
        "tokens": 4096,
        "baseline": {
            "BLOCK_SIZE_M": 128,
            "BLOCK_SIZE_N": 128,
            "BLOCK_SIZE_K": 64,
            "GROUP_SIZE_M": 1,
            "SPLIT_K": 1,
            "num_warps": 8,
            "num_stages": 3,
        },
        "candidate_block_m": 64,
    },
    "prefill_guard": {
        "tokens": 4153,
        "baseline": {
            "BLOCK_SIZE_M": 128,
            "BLOCK_SIZE_N": 128,
            "BLOCK_SIZE_K": 64,
            "GROUP_SIZE_M": 1,
            "SPLIT_K": 1,
            "num_warps": 8,
            "num_stages": 3,
        },
        "candidate_block_m": 64,
    },
}


@dataclass
class Inputs:
    hidden: torch.Tensor
    w1: torch.Tensor
    w2: torch.Tensor
    topk_weights: torch.Tensor
    topk_ids: torch.Tensor


@dataclass
class Variant:
    name: str
    config: dict[str, int]
    sorted_token_ids: torch.Tensor
    expert_ids: torch.Tensor
    num_tokens_post_pad: torch.Tensor
    gemm1_out: torch.Tensor
    activated: torch.Tensor
    gemm2_out: torch.Tensor


def _candidate_config(
    baseline: dict[str, int], candidate_block_m: int
) -> dict[str, int]:
    candidate = baseline.copy()
    candidate["BLOCK_SIZE_M"] = candidate_block_m
    for key, value in baseline.items():
        if key != "BLOCK_SIZE_M" and candidate[key] != value:
            raise AssertionError(f"candidate unexpectedly changes {key}")
    changed = {key for key in baseline if baseline[key] != candidate[key]}
    if changed != {"BLOCK_SIZE_M"}:
        raise AssertionError(f"expected BLOCK_SIZE_M-only change, got {changed}")
    return candidate


def _make_inputs(tokens: int, seed: int, device: torch.device) -> Inputs:
    generator = torch.Generator(device=device)
    generator.manual_seed(seed)
    hidden = torch.randn(
        (tokens, HIDDEN_SIZE),
        generator=generator,
        device=device,
        dtype=torch.bfloat16,
    ) * 0.02
    w1 = torch.randn(
        (NUM_EXPERTS, W1_OUT, HIDDEN_SIZE),
        generator=generator,
        device=device,
        dtype=torch.bfloat16,
    ) * 0.02
    w2 = torch.randn(
        (NUM_EXPERTS, HIDDEN_SIZE, LOCAL_INTERMEDIATE),
        generator=generator,
        device=device,
        dtype=torch.bfloat16,
    ) * 0.02
    # Deterministic router values give unique top-k IDs without allocating a
    # model.  The same routing tensors are reused by baseline and candidate.
    router = torch.randn(
        (tokens, NUM_EXPERTS),
        generator=generator,
        device=device,
        dtype=torch.float32,
    )
    router_values, topk_ids = torch.topk(router, TOP_K, dim=-1, sorted=True)
    topk_weights = torch.softmax(router_values, dim=-1).contiguous()
    return Inputs(
        hidden=hidden.contiguous(),
        w1=w1.contiguous(),
        w2=w2.contiguous(),
        topk_weights=topk_weights,
        topk_ids=topk_ids.to(torch.int32).contiguous(),
    )


def _make_variant(
    name: str, inputs: Inputs, config: dict[str, int]
) -> Variant:
    sorted_ids, expert_ids, num_tokens_post_pad = moe_align_block_size(
        inputs.topk_ids,
        config["BLOCK_SIZE_M"],
        NUM_EXPERTS,
    )
    tokens = inputs.hidden.shape[0]
    return Variant(
        name=name,
        config=config,
        sorted_token_ids=sorted_ids,
        expert_ids=expert_ids,
        num_tokens_post_pad=num_tokens_post_pad,
        gemm1_out=torch.empty(
            (tokens, TOP_K, W1_OUT), device=inputs.hidden.device, dtype=torch.bfloat16
        ),
        activated=torch.empty(
            (tokens * TOP_K, LOCAL_INTERMEDIATE),
            device=inputs.hidden.device,
            dtype=torch.bfloat16,
        ),
        gemm2_out=torch.empty(
            (tokens, TOP_K, HIDDEN_SIZE),
            device=inputs.hidden.device,
            dtype=torch.bfloat16,
        ),
    )


def _gemm1(inputs: Inputs, variant: Variant) -> None:
    invoke_fused_moe_triton_kernel(
        inputs.hidden,
        inputs.w1,
        variant.gemm1_out,
        None,
        None,
        inputs.topk_weights,
        variant.sorted_token_ids,
        variant.expert_ids,
        variant.num_tokens_post_pad,
        False,
        TOP_K,
        variant.config,
        tl.bfloat16,
    )


def _activation(variant: Variant) -> None:
    flat = variant.gemm1_out.view(-1, W1_OUT)
    silu_and_mul_out(
        flat[:, :LOCAL_INTERMEDIATE],
        flat[:, LOCAL_INTERMEDIATE:],
        variant.activated,
    )


def _gemm2(inputs: Inputs, variant: Variant) -> None:
    invoke_fused_moe_triton_kernel(
        variant.activated,
        inputs.w2,
        variant.gemm2_out,
        None,
        None,
        inputs.topk_weights,
        variant.sorted_token_ids,
        variant.expert_ids,
        variant.num_tokens_post_pad,
        True,
        1,
        variant.config,
        tl.bfloat16,
    )


def _pair(inputs: Inputs, variant: Variant) -> None:
    _gemm1(inputs, variant)
    _activation(variant)
    _gemm2(inputs, variant)


def _event_ms(fn: Callable[[], None], warmup: int, repeat: int) -> float:
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


def _error(reference: torch.Tensor, actual: torch.Tensor) -> dict[str, float]:
    delta = (reference.float() - actual.float()).abs()
    denom = reference.float().norm().clamp_min(1e-12)
    cosine = torch.nn.functional.cosine_similarity(
        reference.float().flatten(), actual.float().flatten(), dim=0
    )
    return {
        "max_abs": float(delta.max().item()),
        "mean_abs": float(delta.mean().item()),
        "relative_l2": float((delta.norm() / denom).item()),
        "cosine": float(cosine.item()),
    }


def _capture_and_replay(
    inputs: Inputs,
    variant: Variant,
    eager_reference: torch.Tensor,
    atol: float,
    rtol: float,
) -> dict[str, object]:
    for _ in range(3):
        _pair(inputs, variant)
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, capture_error_mode="thread_local"):
        _pair(inputs, variant)
    torch.cuda.synchronize()
    capture_output = variant.gemm2_out.clone()
    snapshots: list[torch.Tensor] = []
    replay_ms: list[float] = []
    for _ in range(2):
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        graph.replay()
        end.record()
        torch.cuda.synchronize()
        replay_ms.append(float(start.elapsed_time(end)))
        snapshots.append(variant.gemm2_out.clone())
    for output in (capture_output, *snapshots):
        torch.testing.assert_close(output, eager_reference, atol=atol, rtol=rtol)
    torch.testing.assert_close(snapshots[0], snapshots[1], atol=0, rtol=0)
    return {
        "capture_ok": True,
        "replay_count": 2,
        "replay_ms": replay_ms,
        "replay_bitwise_stable": True,
    }


def _summary(samples: list[float]) -> dict[str, object]:
    ordered = sorted(samples)
    p95_index = min(len(ordered) - 1, math.ceil(0.95 * len(ordered)) - 1)
    mean = statistics.fmean(samples)
    return {
        "round_ms": samples,
        "median_ms": statistics.median(samples),
        "mean_ms": mean,
        "p95_ms": ordered[p95_index],
        "cv": statistics.pstdev(samples) / mean if mean else 0.0,
    }


@torch.inference_mode()
def run_case(
    case_name: str,
    warmup: int,
    repeat: int,
    rounds: int,
    seed: int,
    atol: float,
    rtol: float,
    device: torch.device,
) -> dict[str, object]:
    spec = CASES[case_name]
    baseline_config = dict(spec["baseline"])
    candidate_config = _candidate_config(
        baseline_config, int(spec["candidate_block_m"])
    )
    inputs = _make_inputs(int(spec["tokens"]), seed, device)
    variants = {
        "baseline": _make_variant("baseline", inputs, baseline_config),
        "candidate": _make_variant("candidate", inputs, candidate_config),
    }

    for variant in variants.values():
        _pair(inputs, variant)
    torch.cuda.synchronize()
    baseline_output = variants["baseline"].gemm2_out.clone()
    candidate_output = variants["candidate"].gemm2_out.clone()
    torch.testing.assert_close(
        candidate_output, baseline_output, atol=atol, rtol=rtol
    )
    correctness = _error(baseline_output, candidate_output)
    correctness.update({"passed": True, "atol": atol, "rtol": rtol})

    samples: dict[str, dict[str, list[float]]] = {
        name: {"gemm1": [], "gemm2": [], "pair": []} for name in variants
    }
    for round_index in range(rounds):
        order = ("baseline", "candidate")
        if round_index % 2:
            order = tuple(reversed(order))
        for name in order:
            variant = variants[name]
            # Exactly 20 warmups and 100 timed iterations per metric by
            # default.  CLI overrides are recorded in the JSON contract.
            samples[name]["gemm1"].append(
                _event_ms(lambda: _gemm1(inputs, variant), warmup, repeat)
            )
            _gemm1(inputs, variant)
            _activation(variant)
            samples[name]["gemm2"].append(
                _event_ms(lambda: _gemm2(inputs, variant), warmup, repeat)
            )
            samples[name]["pair"].append(
                _event_ms(lambda: _pair(inputs, variant), warmup, repeat)
            )

    timing = {
        name: {metric: _summary(values) for metric, values in metrics.items()}
        for name, metrics in samples.items()
    }
    base_pair = float(timing["baseline"]["pair"]["median_ms"])
    candidate_pair = float(timing["candidate"]["pair"]["median_ms"])
    speedup = base_pair / candidate_pair

    graph = {}
    for name, variant in variants.items():
        _pair(inputs, variant)
        torch.cuda.synchronize()
        eager_reference = variant.gemm2_out.clone()
        graph[name] = _capture_and_replay(
            inputs, variant, eager_reference, atol, rtol
        )

    return {
        "case": case_name,
        "tokens": int(spec["tokens"]),
        "shapes": {
            "hidden": list(inputs.hidden.shape),
            "topk_ids": list(inputs.topk_ids.shape),
            "w1": list(inputs.w1.shape),
            "w2": list(inputs.w2.shape),
        },
        "baseline_config": baseline_config,
        "candidate_config": candidate_config,
        "changed_fields": ["BLOCK_SIZE_M"],
        "correctness": correctness,
        "timing": timing,
        "pair_speedup": speedup,
        "pair_improvement_percent": (1.0 - candidate_pair / base_pair) * 100.0,
        "graph": graph,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cases", default="decode,prefill,prefill_guard",
        help="comma-separated subset of decode,prefill,prefill_guard",
    )
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--repeat", type=int, default=100)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--seed", type=int, default=74284)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--atol", type=float, default=0.02)
    parser.add_argument("--rtol", type=float, default=0.02)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("an accelerator exposed through torch.cuda is required")
    if args.warmup < 1 or args.repeat < 1 or args.rounds != 3:
        raise ValueError("warmup/repeat must be positive and rounds must remain 3")
    selected = [value.strip() for value in args.cases.split(",") if value.strip()]
    unknown = sorted(set(selected) - set(CASES))
    if unknown:
        raise ValueError(f"unknown cases: {unknown}")
    torch.cuda.set_device(args.device)
    device = torch.device("cuda", args.device)
    results = [
        run_case(
            case_name,
            args.warmup,
            args.repeat,
            args.rounds,
            args.seed,
            args.atol,
            args.rtol,
            device,
        )
        for case_name in selected
    ]
    payload = {
        "schema_version": 1,
        "experiment": "fused-moe-block-m-only-falsification",
        "dtype": "bfloat16",
        "device": args.device,
        "warmup": args.warmup,
        "iterations": args.repeat,
        "rounds": args.rounds,
        "graph_capture_replays": 2,
        "implementation": inspect.getsourcefile(invoke_fused_moe_triton_kernel),
        "results": results,
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
