#!/usr/bin/env python3
"""Offline falsification for a GEMM2-only BLOCK_SIZE_N=128 hypothesis.

This script does not start or call a vLLM service.  It exercises the same
FlagGems alignment, fused-MoE kernel, SiLU-and-mul, and top-k reduction used by
the retained Qwen3.8 Flash M64 path.

Production rank-local BF16 shapes (TP=8):
  hidden [64, 2560]
  W1     [512, 160, 2560]
  W2     [512, 2560, 80]
  top-k  10

The candidate changes exactly one field for GEMM2:
  BLOCK_SIZE_N: 64 -> 128

GEMM1 remains on the retained BM16/BN64/BK128/warps4/stages3 config.  The
promotion gate is bitwise BF16 equality, successful graph capture plus two
bitwise-stable replays for both variants, and >=8% median speedup for the full
GEMM1 + activation + GEMM2 + top-k reduction transaction.
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
from flag_gems.fused.moe_sum import moe_sum
from flag_gems.fused.silu_and_mul import silu_and_mul_out


NUM_EXPERTS = 512
TOP_K = 10
TOKENS = 64
HIDDEN_SIZE = 2560
LOCAL_INTERMEDIATE = 80
W1_OUT = 2 * LOCAL_INTERMEDIATE
MIN_FULL_MOE_SPEEDUP = 1.08

RETAINED_CONFIG = {
    "BLOCK_SIZE_M": 16,
    "BLOCK_SIZE_N": 64,
    "BLOCK_SIZE_K": 128,
    "GROUP_SIZE_M": 1,
    "SPLIT_K": 1,
    "num_warps": 4,
    "num_stages": 3,
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
    gemm1_config: dict[str, int]
    gemm2_config: dict[str, int]
    sorted_token_ids: torch.Tensor
    expert_ids: torch.Tensor
    num_tokens_post_pad: torch.Tensor
    gemm1_out: torch.Tensor
    activated: torch.Tensor
    gemm2_out: torch.Tensor
    final_out: torch.Tensor


def _candidate_gemm2_config() -> dict[str, int]:
    candidate = RETAINED_CONFIG.copy()
    candidate["BLOCK_SIZE_N"] = 128
    changed = {
        key
        for key in RETAINED_CONFIG
        if candidate.get(key) != RETAINED_CONFIG.get(key)
    }
    if changed != {"BLOCK_SIZE_N"}:
        raise AssertionError(f"expected BLOCK_SIZE_N-only change, got {changed}")
    return candidate


def _make_inputs(seed: int, device: torch.device) -> Inputs:
    generator = torch.Generator(device=device)
    generator.manual_seed(seed)
    hidden = torch.randn(
        (TOKENS, HIDDEN_SIZE),
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
    router = torch.randn(
        (TOKENS, NUM_EXPERTS),
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
    name: str,
    inputs: Inputs,
    gemm1_config: dict[str, int],
    gemm2_config: dict[str, int],
) -> Variant:
    # BLOCK_SIZE_M is unchanged, so both variants intentionally share the
    # same alignment semantics and differ only in GEMM2's N tile.
    if gemm1_config["BLOCK_SIZE_M"] != gemm2_config["BLOCK_SIZE_M"]:
        raise AssertionError("this experiment requires one shared BLOCK_SIZE_M")
    sorted_ids, expert_ids, num_tokens_post_pad = moe_align_block_size(
        inputs.topk_ids,
        gemm1_config["BLOCK_SIZE_M"],
        NUM_EXPERTS,
    )
    return Variant(
        name=name,
        gemm1_config=gemm1_config,
        gemm2_config=gemm2_config,
        sorted_token_ids=sorted_ids,
        expert_ids=expert_ids,
        num_tokens_post_pad=num_tokens_post_pad,
        gemm1_out=torch.empty(
            (TOKENS, TOP_K, W1_OUT), device=inputs.hidden.device, dtype=torch.bfloat16
        ),
        activated=torch.empty(
            (TOKENS * TOP_K, LOCAL_INTERMEDIATE),
            device=inputs.hidden.device,
            dtype=torch.bfloat16,
        ),
        gemm2_out=torch.empty(
            (TOKENS, TOP_K, HIDDEN_SIZE),
            device=inputs.hidden.device,
            dtype=torch.bfloat16,
        ),
        final_out=torch.empty(
            (TOKENS, HIDDEN_SIZE), device=inputs.hidden.device, dtype=torch.bfloat16
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
        variant.gemm1_config,
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
        variant.gemm2_config,
        tl.bfloat16,
    )


def _pair(inputs: Inputs, variant: Variant) -> None:
    _gemm1(inputs, variant)
    _activation(variant)
    _gemm2(inputs, variant)


def _full_moe(inputs: Inputs, variant: Variant) -> None:
    _pair(inputs, variant)
    moe_sum(variant.gemm2_out, variant.final_out)


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


def _error(reference: torch.Tensor, actual: torch.Tensor) -> dict[str, float | bool]:
    delta = (reference.float() - actual.float()).abs()
    denom = reference.float().norm().clamp_min(1e-12)
    cosine = torch.nn.functional.cosine_similarity(
        reference.float().flatten(), actual.float().flatten(), dim=0
    )
    return {
        "bitwise_equal": bool(torch.equal(reference, actual)),
        "max_abs": float(delta.max().item()),
        "mean_abs": float(delta.mean().item()),
        "relative_l2": float((delta.norm() / denom).item()),
        "cosine": float(cosine.item()),
    }


def _capture_and_replay(
    inputs: Inputs, variant: Variant, eager_reference: torch.Tensor
) -> dict[str, object]:
    for _ in range(3):
        _full_moe(inputs, variant)
    torch.cuda.synchronize()
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, capture_error_mode="thread_local"):
        _full_moe(inputs, variant)
    torch.cuda.synchronize()
    capture_output = variant.final_out.clone()
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
        snapshots.append(variant.final_out.clone())
    for output in (capture_output, *snapshots):
        if not torch.equal(output, eager_reference):
            raise AssertionError("graph output is not bitwise equal to eager BF16 output")
    if not torch.equal(snapshots[0], snapshots[1]):
        raise AssertionError("two graph replays are not bitwise stable")
    return {
        "capture_ok": True,
        "replay_count": 2,
        "replay_ms": replay_ms,
        "eager_bitwise_equal": True,
        "replay_bitwise_stable": True,
    }


@torch.inference_mode()
def run(args: argparse.Namespace) -> dict[str, object]:
    device = torch.device("cuda", args.device)
    inputs = _make_inputs(args.seed, device)
    candidate_gemm2 = _candidate_gemm2_config()
    variants = {
        "retained_bn64": _make_variant(
            "retained_bn64", inputs, RETAINED_CONFIG.copy(), RETAINED_CONFIG.copy()
        ),
        "candidate_gemm2_bn128": _make_variant(
            "candidate_gemm2_bn128",
            inputs,
            RETAINED_CONFIG.copy(),
            candidate_gemm2,
        ),
    }

    for variant in variants.values():
        _full_moe(inputs, variant)
    torch.cuda.synchronize()
    baseline = variants["retained_bn64"]
    candidate = variants["candidate_gemm2_bn128"]
    pair_error = _error(baseline.gemm2_out, candidate.gemm2_out)
    final_error = _error(baseline.final_out, candidate.final_out)
    if not pair_error["bitwise_equal"] or not final_error["bitwise_equal"]:
        raise AssertionError("candidate failed required bitwise BF16 equality")

    metrics = ("gemm1", "activation", "gemm2", "pair", "full_moe")
    samples = {
        name: {metric: [] for metric in metrics}
        for name in variants
    }
    for round_index in range(args.rounds):
        order = list(variants)
        if round_index % 2:
            order.reverse()
        for name in order:
            variant = variants[name]
            samples[name]["gemm1"].append(
                _event_ms(lambda: _gemm1(inputs, variant), args.warmup, args.repeat)
            )
            _gemm1(inputs, variant)
            samples[name]["activation"].append(
                _event_ms(lambda: _activation(variant), args.warmup, args.repeat)
            )
            _activation(variant)
            samples[name]["gemm2"].append(
                _event_ms(lambda: _gemm2(inputs, variant), args.warmup, args.repeat)
            )
            samples[name]["pair"].append(
                _event_ms(lambda: _pair(inputs, variant), args.warmup, args.repeat)
            )
            samples[name]["full_moe"].append(
                _event_ms(lambda: _full_moe(inputs, variant), args.warmup, args.repeat)
            )

    timing = {
        name: {metric: _summary(values) for metric, values in variant.items()}
        for name, variant in samples.items()
    }
    base_ms = float(timing["retained_bn64"]["full_moe"]["median_ms"])
    candidate_ms = float(
        timing["candidate_gemm2_bn128"]["full_moe"]["median_ms"]
    )
    speedup = base_ms / candidate_ms

    graph = {}
    for name, variant in variants.items():
        _full_moe(inputs, variant)
        torch.cuda.synchronize()
        eager_reference = variant.final_out.clone()
        graph[name] = _capture_and_replay(inputs, variant, eager_reference)

    em = int(baseline.sorted_token_ids.numel())
    num_pid_m = math.ceil(em / RETAINED_CONFIG["BLOCK_SIZE_M"])
    expected_grids = {
        "gemm1": num_pid_m * math.ceil(W1_OUT / RETAINED_CONFIG["BLOCK_SIZE_N"]),
        "retained_gemm2": num_pid_m
        * math.ceil(HIDDEN_SIZE / RETAINED_CONFIG["BLOCK_SIZE_N"]),
        "candidate_gemm2": num_pid_m
        * math.ceil(HIDDEN_SIZE / candidate_gemm2["BLOCK_SIZE_N"]),
    }

    passed = (
        bool(pair_error["bitwise_equal"])
        and bool(final_error["bitwise_equal"])
        and all(value["capture_ok"] for value in graph.values())
        and speedup >= MIN_FULL_MOE_SPEEDUP
    )
    return {
        "schema_version": 1,
        "experiment": "op011-m64-gemm2-block-n-only-falsification",
        "dtype": "bfloat16",
        "device": args.device,
        "shape": {
            "hidden": list(inputs.hidden.shape),
            "w1": list(inputs.w1.shape),
            "w2": list(inputs.w2.shape),
            "topk_ids": list(inputs.topk_ids.shape),
        },
        "retained_gemm1_config": RETAINED_CONFIG,
        "retained_gemm2_config": RETAINED_CONFIG,
        "candidate_gemm1_config": RETAINED_CONFIG,
        "candidate_gemm2_config": candidate_gemm2,
        "changed_fields": ["gemm2.BLOCK_SIZE_N"],
        "alignment": {
            "sorted_token_capacity": em,
            "num_tokens_post_pad": int(baseline.num_tokens_post_pad.item()),
            "expected_kernel_grids": expected_grids,
        },
        "correctness": {
            "gemm2_routed_output": pair_error,
            "final_reduced_output": final_error,
            "required": "bitwise_equal_bf16",
        },
        "timing": timing,
        "full_moe_speedup": speedup,
        "full_moe_improvement_percent": (1.0 - candidate_ms / base_ms) * 100.0,
        "graph": graph,
        "gate": {
            "required_speedup": MIN_FULL_MOE_SPEEDUP,
            "passed": passed,
            "stop_if_below_threshold": True,
        },
        "measurement": {
            "warmup": args.warmup,
            "iterations": args.repeat,
            "rounds": args.rounds,
            "graph_capture_replays": 2,
        },
        "implementation": inspect.getsourcefile(invoke_fused_moe_triton_kernel),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--repeat", type=int, default=100)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--seed", type=int, default=74284)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("an accelerator exposed through torch.cuda is required")
    if args.warmup < 1 or args.repeat < 1 or args.rounds != 3:
        raise ValueError("warmup/repeat must be positive and rounds must remain 3")
    torch.cuda.set_device(args.device)
    payload = run(args)
    encoded = json.dumps(payload, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    if not payload["gate"]["passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
