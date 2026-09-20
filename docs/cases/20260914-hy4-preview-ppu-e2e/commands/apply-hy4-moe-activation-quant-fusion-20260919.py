#!/usr/bin/env python3
"""Apply exact T-Head SiLU-mul plus per-token INT8 quant fusion."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> dict[str, str]:
    original = path.read_text()
    matches = original.count(old)
    if matches != 1:
        raise RuntimeError(f"expected one match in {path}, got {matches}")
    updated = original.replace(old, new, 1)
    path.write_text(updated)
    return {
        "path": str(path),
        "before_sha256": hashlib.sha256(original.encode()).hexdigest(),
        "after_sha256": hashlib.sha256(updated.encode()).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("--reverse", action="store_true")
    args = parser.parse_args()
    source = args.repo / "src/flaggems_vllm/runtime/backend/_thead/ops/fused_moe.py"
    test = args.repo / "tests/test_thead_hy4_ops.py"

    quant_anchor = '''def _int8_quantize(
    A: torch.Tensor,
'''
    quant_fusion = '''@libentry()
@triton.jit
def _silu_mul_dynamic_per_token_int8_quant_kernel(
    input_ptr,
    output_ptr,
    scale_ptr,
    hidden_size: tl.constexpr,
    BLOCK_SIZE: tl.constexpr,
):
    row = tl.program_id(0)
    offsets = tl.arange(0, BLOCK_SIZE)
    mask = offsets < hidden_size
    input_base = row * hidden_size * 2
    gate = tl.load(
        input_ptr + input_base + offsets, mask=mask, other=0.0
    ).to(tl.float32)
    up = tl.load(
        input_ptr + input_base + hidden_size + offsets,
        mask=mask,
        other=0.0,
    )
    # Preserve the old two-kernel semantics: activation is stored as BF16
    # before the FP32 absmax and quantization reduction.
    activated = (
        tl.fdiv(gate, 1.0 + tl.exp(-gate)) * up
    ).to(tl.bfloat16).to(tl.float32)
    absmax = tl.maximum(tl.max(tl.abs(activated), axis=0), 1e-10)
    scale = absmax / 127.0
    quantized = libdevice.rint(libdevice.div_rn(activated, scale))
    quantized = tl.minimum(tl.maximum(quantized, -128.0), 127.0)
    tl.store(
        output_ptr + row * hidden_size + offsets,
        quantized.to(tl.int8),
        mask=mask,
    )
    tl.store(scale_ptr + row, scale)


def _silu_mul_dynamic_per_token_int8_quant(
    A: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    assert A.is_contiguous()
    assert A.ndim == 2 and A.shape[-1] % 2 == 0
    hidden_size = A.shape[-1] // 2
    output = torch.empty(
        (A.shape[0], hidden_size), device=A.device, dtype=torch.int8
    )
    scale = torch.empty((A.shape[0], 1), device=A.device, dtype=torch.float32)
    _silu_mul_dynamic_per_token_int8_quant_kernel[(A.shape[0],)](
        A,
        output,
        scale,
        hidden_size=hidden_size,
        BLOCK_SIZE=triton.next_power_of_2(hidden_size),
        num_warps=4,
        num_stages=1,
    )
    return output, scale


def _can_fuse_silu_mul_int8_quant(
    activation: MoEActivation,
    use_int8_w8a8: bool,
    per_act_token_quant: bool,
    block_shape: Optional[list[int]],
) -> bool:
    return (
        activation in (MoEActivation.SILU, MoEActivation.SWIGLUOAI)
        and use_int8_w8a8
        and per_act_token_quant
        and block_shape is None
    )


def _int8_quantize(
    A: torch.Tensor,
'''

    flow_old = '''        # 4. Apply activation separately if the fused path was not taken
        if not do_fuse_silu:
            apply_moe_activation(
                activation_enum, intermediate_cache2, intermediate_cache1.view(-1, N)
            )

        # 5. Quantize activated intermediate for GEMM2
        qintermediate_cache2, a2q_scale = moe_kernel_quantize_input(
            A=intermediate_cache2,
            A_scale=a2_scale,
            quant_dtype=quant_dtype,
            per_act_token_quant=per_channel_quant,
            block_shape=block_shape,
            ocp_mx_scheme=ocp_mx_scheme,
        )
'''
    flow_new = '''        # 4/5. Fuse SiLU-mul with exact per-token INT8 quantization when
        # the T-Head W8A8 path would otherwise materialize a BF16 cache.
        fuse_activation_quant = (
            not do_fuse_silu
            and _can_fuse_silu_mul_int8_quant(
                activation_enum,
                use_int8_w8a8,
                per_channel_quant,
                block_shape,
            )
        )
        if fuse_activation_quant:
            qintermediate_cache2, a2q_scale = (
                _silu_mul_dynamic_per_token_int8_quant(
                    intermediate_cache1.view(-1, N)
                )
            )
        else:
            if not do_fuse_silu:
                apply_moe_activation(
                    activation_enum,
                    intermediate_cache2,
                    intermediate_cache1.view(-1, N),
                )
            qintermediate_cache2, a2q_scale = moe_kernel_quantize_input(
                A=intermediate_cache2,
                A_scale=a2_scale,
                quant_dtype=quant_dtype,
                per_act_token_quant=per_channel_quant,
                block_shape=block_shape,
                ocp_mx_scheme=ocp_mx_scheme,
            )
'''
    test_anchor = '''@pytest.mark.parametrize("dtype", [torch.float16, torch.bfloat16, torch.float32])
@pytest.mark.parametrize("hidden_size", [128, 256, 6144])
def test_hy4_dynamic_per_token_int8_quant_is_exact(dtype, hidden_size):
'''
    test_insert = '''def test_hy4_silu_mul_dynamic_per_token_int8_quant_is_exact():
    torch.manual_seed(20260919)
    source = torch.randn((17, 256), device="cuda", dtype=torch.bfloat16)
    intermediate = torch.empty((17, 128), device="cuda", dtype=torch.bfloat16)
    thead_fused_moe._silu_and_mul_kernel(
        source[:, :128], source[:, 128:], out0=intermediate
    )
    expected_q, expected_scale = thead_fused_moe._dynamic_per_token_int8_quant(
        intermediate
    )
    actual_q, actual_scale = (
        thead_fused_moe._silu_mul_dynamic_per_token_int8_quant(source)
    )
    assert torch.equal(actual_q, expected_q)
    assert torch.equal(actual_scale, expected_scale)


@pytest.mark.parametrize("dtype", [torch.float16, torch.bfloat16, torch.float32])
@pytest.mark.parametrize("hidden_size", [128, 256, 6144])
def test_hy4_dynamic_per_token_int8_quant_is_exact(dtype, hidden_size):
'''

    pairs = [
        (source, quant_anchor, quant_fusion),
        (source, flow_old, flow_new),
        (test, test_anchor, test_insert),
    ]
    if args.reverse:
        pairs = [(path, new, old) for path, old, new in pairs]
    changes = [replace_once(path, old, new) for path, old, new in pairs]
    print(json.dumps({"changes": changes}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
