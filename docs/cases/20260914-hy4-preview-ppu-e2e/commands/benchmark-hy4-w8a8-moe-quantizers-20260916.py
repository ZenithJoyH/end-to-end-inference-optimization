#!/usr/bin/env python3
"""Compare PyTorch, in-tree Triton, and T-Head native W8A8 quantizers.

The full MoE comparison monkey-patches only the private quantizer in the
already-selected FlagGems implementation; it does not modify source files.
"""

from __future__ import annotations

import json
import statistics
import time

import torch
import triton
import triton.language as tl
import triton.language.extra.libdevice as libdevice

import flag_gems.fused.fused_moe as fm
from flag_gems.runtime import torch_device_fn
from flag_gems.utils import libentry


M, E, HIDDEN, LOCAL_I, TOPK = 2048, 256, 6144, 128, 8


def sync() -> None:
    torch_device_fn.synchronize()


def pytorch_quant(x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    return fm._int8_quantize(x, None, True, None)


@triton.jit
def _round_half_to_even(x):
    floor = tl.floor(x)
    fraction = x - floor
    is_odd = tl.abs(floor - 2.0 * tl.floor(floor / 2.0)) > 0.5
    round_up = (fraction > 0.5) | ((tl.abs(fraction - 0.5) < 1e-10) & is_odd)
    return tl.where(round_up, floor + 1.0, floor)


@libentry()
@triton.jit
def _exact_dynamic_per_token_quant_int8_kernel(
    input_ptr,
    output_ptr,
    scale_ptr,
    hidden_size: tl.constexpr,
    BLOCK_SIZE: tl.constexpr,
):
    token_idx = tl.program_id(0)
    offsets = tl.arange(0, BLOCK_SIZE)
    mask = offsets < hidden_size
    values = tl.load(
        input_ptr + token_idx * hidden_size + offsets,
        mask=mask,
        other=0.0,
    ).to(tl.float32)
    absmax = tl.max(tl.abs(values), axis=0)
    absmax = tl.maximum(absmax, 1e-10)
    scale = absmax / 127.0
    # Match the current FlagGems expression rather than multiplying by a
    # reciprocal; the latter changes threshold-adjacent rounded values.
    quantized = libdevice.rint(libdevice.div_rn(values, scale))
    quantized = tl.minimum(tl.maximum(quantized, -128.0), 127.0)
    tl.store(
        output_ptr + token_idx * hidden_size + offsets,
        quantized.to(tl.int8),
        mask=mask,
    )
    tl.store(scale_ptr + token_idx, scale)


def triton_exact_quant(x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    x = x.contiguous()
    output = torch.empty_like(x, dtype=torch.int8)
    scale = torch.empty((x.shape[0], 1), device=x.device, dtype=torch.float32)
    block_size = triton.next_power_of_2(x.shape[1])
    with torch_device_fn.device(x.device):
        _exact_dynamic_per_token_quant_int8_kernel[(x.shape[0],)](
            x,
            output,
            scale,
            hidden_size=x.shape[1],
            BLOCK_SIZE=block_size,
        )
    return output, scale


QUANTIZERS = {
    "pytorch": pytorch_quant,
    "triton_exact": triton_exact_quant,
}


def summarize(samples: list[float]) -> dict[str, float]:
    return {
        "mean_us": statistics.fmean(samples),
        "median_us": statistics.median(samples),
        "min_us": min(samples),
        "max_us": max(samples),
    }


def measure_quant(name: str, x: torch.Tensor) -> tuple[dict[str, float], torch.Tensor, torch.Tensor]:
    fn = QUANTIZERS[name]
    q, scale = fn(x)
    for _ in range(5):
        q, scale = fn(x)
    sync()
    samples: list[float] = []
    for _ in range(100):
        start = time.perf_counter()
        q, scale = fn(x)
        sync()
        samples.append((time.perf_counter() - start) * 1_000_000)
    return summarize(samples), q, scale


def build_moe_inputs() -> dict[str, object]:
    device = torch.device("cuda")
    hidden = torch.randn((M, HIDDEN), device=device, dtype=torch.bfloat16)
    w1 = torch.randint(-8, 9, (E, 2 * LOCAL_I, HIDDEN), device=device, dtype=torch.int8)
    w2 = torch.randint(-8, 9, (E, HIDDEN, LOCAL_I), device=device, dtype=torch.int8)
    ids = torch.randint(0, E, (M, TOPK), device=device, dtype=torch.int32)
    weights = torch.rand((M, TOPK), device=device, dtype=torch.float32)
    weights /= weights.sum(dim=-1, keepdim=True)
    return {
        "hidden_states": hidden,
        "w1": w1,
        "w2": w2,
        "topk_weights": weights.contiguous(),
        "topk_ids": ids.contiguous(),
        "inplace": False,
        "activation": "silu",
        "apply_router_weight_on_input": False,
        "use_int8_w8a8": True,
        "per_channel_quant": True,
        "global_num_experts": E,
        "w1_scale": torch.full((E, 2 * LOCAL_I, 1), 0.01, device=device),
        "w2_scale": torch.full((E, HIDDEN, 1), 0.01, device=device),
    }


def run_moe(kwargs: dict[str, object], quantizer: str) -> torch.Tensor:
    if quantizer == "pytorch":
        return fm.fused_experts_impl(**kwargs)
    original = fm._int8_quantize

    def replacement(
        x: torch.Tensor,
        scale: torch.Tensor | None,
        per_act_token: bool,
        block_shape: list[int] | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if scale is not None or not per_act_token or block_shape is not None:
            return original(x, scale, per_act_token, block_shape)
        return QUANTIZERS[quantizer](x.reshape(-1, x.shape[-1]))

    try:
        fm._int8_quantize = replacement
        return fm.fused_experts_impl(**kwargs)
    finally:
        fm._int8_quantize = original


def measure_moe(kwargs: dict[str, object], quantizer: str) -> tuple[dict[str, float], torch.Tensor]:
    output = run_moe(kwargs, quantizer)
    for _ in range(5):
        output = run_moe(kwargs, quantizer)
    sync()
    samples: list[float] = []
    for _ in range(80):
        start = time.perf_counter()
        output = run_moe(kwargs, quantizer)
        sync()
        samples.append((time.perf_counter() - start) * 1000)
    return {
        "mean_ms": statistics.fmean(samples),
        "median_ms": statistics.median(samples),
        "min_ms": min(samples),
        "max_ms": max(samples),
    }, output


def tensor_diff(reference: torch.Tensor, candidate: torch.Tensor) -> dict[str, object]:
    diff = (reference.float() - candidate.float()).abs()
    return {
        "exact": bool(torch.equal(reference, candidate)),
        "max_abs_diff": float(diff.max().item()),
        "mean_abs_diff": float(diff.mean().item()),
        "different_elements": int(torch.count_nonzero(reference != candidate).item()),
    }


def main() -> None:
    torch.manual_seed(20260916)
    device = torch.device("cuda")
    quant_results: dict[str, object] = {}
    for label, shape in {
        "a1": (M, HIDDEN),
        "a2": (M * TOPK, LOCAL_I),
    }.items():
        x = torch.randn(shape, device=device, dtype=torch.bfloat16)
        outputs: dict[str, tuple[torch.Tensor, torch.Tensor]] = {}
        timings: dict[str, object] = {}
        for name in QUANTIZERS:
            timing, q, scale = measure_quant(name, x)
            timings[name] = timing
            outputs[name] = (q, scale)
        ref_q, ref_scale = outputs["pytorch"]
        quant_results[label] = {
            "shape": list(shape),
            "timings": timings,
            "correctness": {
                name: {
                    "q": tensor_diff(ref_q, q),
                    "scale": tensor_diff(ref_scale, scale),
                }
                for name, (q, scale) in outputs.items()
                if name != "pytorch"
            },
        }

    kwargs = build_moe_inputs()
    moe_timings: dict[str, object] = {}
    moe_outputs: dict[str, torch.Tensor] = {}
    for name in QUANTIZERS:
        timing, output = measure_moe(kwargs, name)
        moe_timings[name] = timing
        moe_outputs[name] = output
    ref = moe_outputs["pytorch"]
    print(json.dumps({
        "device_name": fm._get_device_name(),
        "quantizers": quant_results,
        "full_moe": {
            "shape": {"M": M, "E": E, "hidden": HIDDEN, "local_intermediate": LOCAL_I, "topk": TOPK},
            "timings": moe_timings,
            "speedup_vs_pytorch": {
                name: moe_timings["pytorch"]["median_ms"] / timing["median_ms"]
                for name, timing in moe_timings.items()
                if name != "pytorch"
            },
            "correctness": {
                name: tensor_diff(ref, output)
                for name, output in moe_outputs.items()
                if name != "pytorch"
            },
        },
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
