#!/usr/bin/env python3
"""Compare the current M64 MoE transaction with FlagGems FUSE_SILU.

This is an isolated accelerator microbenchmark; it does not start or call a
vLLM service.  Baseline and candidate share inputs, routing/alignment,
BM16/BN64/BK128/warps4/stages3 config, GEMM2, and moe_sum.  The only semantic
change is whether GEMM1 stores gate/up to BF16 and invokes a separate
silu_and_mul kernel, or performs SiLU in the GEMM1 FP32 accumulator and stores
the activated BF16 tensor directly with FUSE_SILU=True.
"""

from __future__ import annotations

import argparse
import inspect
import json
import math
import statistics
import traceback
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
MIN_FULL_TRANSACTION_SPEEDUP = 1.08
ATOL = 0.02
RTOL = 0.02

CONFIG = {
    "BLOCK_SIZE_M": 16,
    "BLOCK_SIZE_N": 64,
    "BLOCK_SIZE_K": 128,
    "GROUP_SIZE_M": 1,
    "SPLIT_K": 1,
    "num_warps": 4,
    "num_stages": 3,
}


def make_inputs(seed: int, device: torch.device) -> dict[str, torch.Tensor]:
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
    values, topk_ids = torch.topk(router, TOP_K, dim=-1, sorted=True)
    return {
        "hidden": hidden.contiguous(),
        "w1": w1.contiguous(),
        "w2": w2.contiguous(),
        "topk_weights": torch.softmax(values, dim=-1).contiguous(),
        "topk_ids": topk_ids.to(torch.int32).contiguous(),
    }


class Transaction:
    def __init__(self, inputs: dict[str, torch.Tensor]) -> None:
        self.inputs = inputs
        self.sorted_ids, self.expert_ids, self.num_tokens_post_pad = (
            moe_align_block_size(
                inputs["topk_ids"], CONFIG["BLOCK_SIZE_M"], NUM_EXPERTS
            )
        )
        device = inputs["hidden"].device
        self.baseline_gemm1 = torch.empty(
            (TOKENS, TOP_K, W1_OUT), device=device, dtype=torch.bfloat16
        )
        self.baseline_activated = torch.empty(
            (TOKENS * TOP_K, LOCAL_INTERMEDIATE),
            device=device,
            dtype=torch.bfloat16,
        )
        self.fused_activated = torch.empty_like(self.baseline_activated)
        self.baseline_gemm2 = torch.empty(
            (TOKENS, TOP_K, HIDDEN_SIZE), device=device, dtype=torch.bfloat16
        )
        self.fused_gemm2 = torch.empty_like(self.baseline_gemm2)
        self.baseline_final = torch.empty(
            (TOKENS, HIDDEN_SIZE), device=device, dtype=torch.bfloat16
        )
        self.fused_final = torch.empty_like(self.baseline_final)

    def baseline_gemm1_activation(self) -> None:
        invoke_fused_moe_triton_kernel(
            self.inputs["hidden"],
            self.inputs["w1"],
            self.baseline_gemm1,
            None,
            None,
            self.inputs["topk_weights"],
            self.sorted_ids,
            self.expert_ids,
            self.num_tokens_post_pad,
            False,
            TOP_K,
            CONFIG,
            tl.bfloat16,
            FUSE_SILU=False,
        )
        flat = self.baseline_gemm1.view(-1, W1_OUT)
        silu_and_mul_out(
            flat[:, :LOCAL_INTERMEDIATE],
            flat[:, LOCAL_INTERMEDIATE:],
            self.baseline_activated,
        )

    def fused_gemm1_activation(self) -> None:
        invoke_fused_moe_triton_kernel(
            self.inputs["hidden"],
            self.inputs["w1"],
            self.fused_activated.view(TOKENS, TOP_K, LOCAL_INTERMEDIATE),
            None,
            None,
            self.inputs["topk_weights"],
            self.sorted_ids,
            self.expert_ids,
            self.num_tokens_post_pad,
            False,
            TOP_K,
            CONFIG,
            tl.bfloat16,
            FUSE_SILU=True,
        )

    def baseline_gemm2_sum(self) -> None:
        invoke_fused_moe_triton_kernel(
            self.baseline_activated,
            self.inputs["w2"],
            self.baseline_gemm2,
            None,
            None,
            self.inputs["topk_weights"],
            self.sorted_ids,
            self.expert_ids,
            self.num_tokens_post_pad,
            True,
            1,
            CONFIG,
            tl.bfloat16,
        )
        moe_sum(self.baseline_gemm2, self.baseline_final)

    def fused_gemm2_sum(self) -> None:
        invoke_fused_moe_triton_kernel(
            self.fused_activated,
            self.inputs["w2"],
            self.fused_gemm2,
            None,
            None,
            self.inputs["topk_weights"],
            self.sorted_ids,
            self.expert_ids,
            self.num_tokens_post_pad,
            True,
            1,
            CONFIG,
            tl.bfloat16,
        )
        moe_sum(self.fused_gemm2, self.fused_final)

    def baseline(self) -> None:
        self.baseline_gemm1_activation()
        self.baseline_gemm2_sum()

    def fused(self) -> None:
        self.fused_gemm1_activation()
        self.fused_gemm2_sum()


def error_metrics(reference: torch.Tensor, actual: torch.Tensor) -> dict[str, object]:
    ref32 = reference.float()
    act32 = actual.float()
    delta = (ref32 - act32).abs()
    denom = ref32.norm().clamp_min(1e-12)
    cosine = torch.nn.functional.cosine_similarity(
        ref32.flatten(), act32.flatten(), dim=0
    )
    finite = bool(torch.isfinite(act32).all().item())
    close = bool(torch.allclose(actual, reference, atol=ATOL, rtol=RTOL))
    equal_fraction = float((reference == actual).float().mean().item())
    return {
        "finite": finite,
        "allclose": close,
        "atol": ATOL,
        "rtol": RTOL,
        "bitwise_equal_fraction": equal_fraction,
        "max_abs": float(delta.max().item()),
        "mean_abs": float(delta.mean().item()),
        "relative_l2": float((delta.norm() / denom).item()),
        "cosine": float(cosine.item()),
    }


def event_ms(fn: Callable[[], None], warmup: int, repeat: int) -> float:
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


def summarize(samples: list[float]) -> dict[str, object]:
    ordered = sorted(samples)
    mean = statistics.fmean(samples)
    p95_index = min(len(ordered) - 1, math.ceil(0.95 * len(ordered)) - 1)
    return {
        "round_ms": samples,
        "median_ms": statistics.median(samples),
        "mean_ms": mean,
        "p95_ms": ordered[p95_index],
        "cv": statistics.pstdev(samples) / mean if mean else 0.0,
    }


def capture_and_replay(
    fn: Callable[[], None], output: torch.Tensor
) -> dict[str, object]:
    for _ in range(3):
        fn()
    torch.cuda.synchronize()
    eager = output.clone()
    try:
        graph = torch.cuda.CUDAGraph()
        with torch.cuda.graph(graph, capture_error_mode="thread_local"):
            fn()
        torch.cuda.synchronize()
        captured = output.clone()
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
            snapshots.append(output.clone())
        eager_equal = bool(torch.equal(captured, eager)) and all(
            torch.equal(value, eager) for value in snapshots
        )
        replay_equal = bool(torch.equal(snapshots[0], snapshots[1]))
        return {
            "capture_ok": True,
            "replay_count": 2,
            "replay_ms": replay_ms,
            "eager_bitwise_equal": eager_equal,
            "replay_bitwise_stable": replay_equal,
            "passed": eager_equal and replay_equal,
        }
    except Exception as exc:  # Preserve a machine-readable graph failure.
        return {
            "capture_ok": False,
            "replay_count": 0,
            "passed": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


@torch.inference_mode()
def run(args: argparse.Namespace) -> dict[str, object]:
    device = torch.device("cuda", args.device)
    inputs = make_inputs(args.seed, device)
    tx = Transaction(inputs)

    tx.baseline()
    tx.fused()
    torch.cuda.synchronize()
    correctness = {
        "activated_bf16": error_metrics(tx.baseline_activated, tx.fused_activated),
        "gemm2_routed_bf16": error_metrics(tx.baseline_gemm2, tx.fused_gemm2),
        "final_reduced_bf16": error_metrics(tx.baseline_final, tx.fused_final),
    }
    correctness_passed = all(
        value["finite"] and value["allclose"] for value in correctness.values()
    )

    payload: dict[str, object] = {
        "schema_version": 1,
        "experiment": "op012-m64-gemm1-silu-fusion",
        "dtype": "bfloat16",
        "shape": {
            "hidden": list(inputs["hidden"].shape),
            "w1": list(inputs["w1"].shape),
            "w2": list(inputs["w2"].shape),
            "topk_ids": list(inputs["topk_ids"].shape),
        },
        "config": CONFIG,
        "single_variable": "gemm1 FUSE_SILU=False + separate silu_and_mul -> FUSE_SILU=True",
        "pair_gate_up_dot": False,
        "rounding_contract": {
            "baseline": "GEMM1 FP32 accumulate -> BF16 gate/up store -> FP32 SiLU -> BF16 activated store",
            "candidate": "GEMM1 FP32 accumulate -> FP32 SiLU -> BF16 activated store",
            "bitwise_candidate_vs_baseline_required": False,
            "finite_and_elementwise_allclose_required": True,
            "atol": ATOL,
            "rtol": RTOL,
        },
        "correctness": correctness,
        "correctness_passed": correctness_passed,
        "alignment": {
            "sorted_token_capacity": int(tx.sorted_ids.numel()),
            "num_tokens_post_pad": int(tx.num_tokens_post_pad.item()),
        },
        "expected_grids": {
            "baseline_gemm1": 1560,
            "fused_gemm1_silu": 1040,
            "gemm2_both": 20800,
        },
        "implementation": inspect.getsourcefile(invoke_fused_moe_triton_kernel),
        "gate": {
            "required_full_transaction_speedup": MIN_FULL_TRANSACTION_SPEEDUP,
            "passed": False,
        },
    }
    if not correctness_passed:
        payload["status"] = "stopped_correctness"
        payload["stop_reason"] = "BF16 finite/allclose contract failed before timing"
        return payload

    names = ("baseline", "fused")
    metrics = ("gemm1_activation", "gemm2_sum", "full_transaction")
    samples = {name: {metric: [] for metric in metrics} for name in names}
    for round_index in range(args.rounds):
        order = list(names)
        if round_index % 2:
            order.reverse()
        for name in order:
            if name == "baseline":
                first = tx.baseline_gemm1_activation
                second = tx.baseline_gemm2_sum
                full = tx.baseline
            else:
                first = tx.fused_gemm1_activation
                second = tx.fused_gemm2_sum
                full = tx.fused
            samples[name]["gemm1_activation"].append(
                event_ms(first, args.warmup, args.repeat)
            )
            first()
            samples[name]["gemm2_sum"].append(
                event_ms(second, args.warmup, args.repeat)
            )
            samples[name]["full_transaction"].append(
                event_ms(full, args.warmup, args.repeat)
            )

    timing = {
        name: {metric: summarize(values) for metric, values in result.items()}
        for name, result in samples.items()
    }
    base_ms = float(timing["baseline"]["full_transaction"]["median_ms"])
    fused_ms = float(timing["fused"]["full_transaction"]["median_ms"])
    speedup = base_ms / fused_ms
    graph = {
        "baseline": capture_and_replay(tx.baseline, tx.baseline_final),
        "fused": capture_and_replay(tx.fused, tx.fused_final),
    }
    graph_passed = all(value["passed"] for value in graph.values())
    passed = correctness_passed and graph_passed and speedup >= MIN_FULL_TRANSACTION_SPEEDUP
    payload.update(
        {
            "status": "passed" if passed else "stopped_gate",
            "timing": timing,
            "full_transaction_speedup": speedup,
            "full_transaction_improvement_percent": (1.0 - fused_ms / base_ms) * 100.0,
            "graph": graph,
            "measurement": {
                "warmup": args.warmup,
                "iterations": args.repeat,
                "rounds": args.rounds,
                "graph_replays": 2,
            },
            "gate": {
                "required_full_transaction_speedup": MIN_FULL_TRANSACTION_SPEEDUP,
                "correctness_passed": correctness_passed,
                "graph_passed": graph_passed,
                "performance_passed": speedup >= MIN_FULL_TRANSACTION_SPEEDUP,
                "passed": passed,
            },
        }
    )
    if not passed:
        failed = [key for key, value in payload["gate"].items() if key.endswith("_passed") and not value]
        payload["stop_reason"] = "failed gates: " + ", ".join(failed)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--seed", type=int, default=74284)
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--repeat", type=int, default=100)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def write_payload(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.warmup < 1 or args.repeat < 1 or args.rounds != 3:
        raise ValueError("warmup/repeat must be positive and rounds must remain 3")
    if not torch.cuda.is_available():
        raise RuntimeError("an accelerator exposed through torch.cuda is required")
    torch.cuda.set_device(args.device)
    try:
        payload = run(args)
    except Exception as exc:
        payload = {
            "schema_version": 1,
            "experiment": "op012-m64-gemm1-silu-fusion",
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
            "gate": {"passed": False},
        }
        write_payload(args.output, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        raise
    write_payload(args.output, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not payload["gate"]["passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
