#!/usr/bin/env python3
"""Apply the validated T-Head W8A8 MoE padding/tile specialization."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> dict[str, str]:
    original = path.read_text()
    if original.count(old) != 1:
        raise RuntimeError(f"expected exactly one match in {path}, got {original.count(old)}")
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
    args = parser.parse_args()
    source = args.repo / "src/flaggems_vllm/runtime/backend/_thead/ops/fused_moe.py"
    test = args.repo / "tests/test_thead_hy4_ops.py"

    config_old = '''    if dtype == "int8_w8a8":
        tokens_per_expert = M // max(E, 1)
        if tokens_per_expert <= 2:
            block_m = 16
        elif tokens_per_expert <= 4:
            block_m = 32
        elif tokens_per_expert <= 16:
            block_m = 64
        else:
            block_m = 128

        if N >= 4096:
            block_n = 128 if M <= 128 else 256
        else:
            block_n = 64 if M <= 64 else 128
        block_k = 128 if M <= 64 else 64
'''
    config_new = '''    if dtype == "int8_w8a8":
        tokens_per_expert = M // max(E, 1)
        routed_tokens_per_expert = M * topk // max(E, 1)
        if M >= 1024 and 48 <= routed_tokens_per_expert <= 96:
            # At this routing density BM64 pads most experts to two blocks.
            # BM32 reduces wasted expert rows enough to offset the extra
            # programs on PPU (M2048/E256/top8: about 20% full-MoE speedup).
            block_m = 32
        elif tokens_per_expert <= 2:
            block_m = 16
        elif tokens_per_expert <= 4:
            block_m = 32
        elif tokens_per_expert <= 16:
            block_m = 64
        else:
            block_m = 128

        if M >= 1024 and 48 <= routed_tokens_per_expert <= 96:
            # The same target density prefers BN128 in both stages; BN256
            # loses parallelism in the wide down projection.
            block_n = 128
        elif N >= 4096:
            block_n = 128 if M <= 128 else 256
        else:
            block_n = 64 if M <= 64 else 128
        block_k = (
            128
            if M >= 2048 and gemm_stage == "gemm1" and K % 128 == 0
            else 128
            if M <= 64
            else 64
        )
'''
    gemm2_old = '''        if use_half_gemm_fast_paths:
            gemm2_config, _ = get_moe_config(
                tokens_in_chunk,
                gemm_stage="gemm2",
                enable_gemm_fast_path=True,
            )
        use_direct_sum = (
'''
    gemm2_new = '''        if use_half_gemm_fast_paths:
            gemm2_config, _ = get_moe_config(
                tokens_in_chunk,
                gemm_stage="gemm2",
                enable_gemm_fast_path=True,
            )
        elif config_dtype == "int8_w8a8":
            gemm2_config, _ = get_moe_config(
                tokens_in_chunk,
                gemm_stage="gemm2",
            )
        use_direct_sum = (
'''
    test_old = '''    assert config == {
        "BLOCK_SIZE_M": 64,
        "BLOCK_SIZE_N": 128,
        "BLOCK_SIZE_K": 64,
        "GROUP_SIZE_M": 1,
        "num_warps": 4,
        "num_stages": 3,
        "USE_INT32_OFFSETS": False,
    }
'''
    test_new = '''    assert config == {
        "BLOCK_SIZE_M": 32,
        "BLOCK_SIZE_N": 128,
        "BLOCK_SIZE_K": 128,
        "GROUP_SIZE_M": 1,
        "num_warps": 4,
        "num_stages": 3,
        "USE_INT32_OFFSETS": False,
    }
    gemm2_config = thead_fused_moe.get_default_config(
        2048, 256, 6144, 128, 8, dtype, gemm_stage="gemm2"
    )
    assert gemm2_config == {
        "BLOCK_SIZE_M": 32,
        "BLOCK_SIZE_N": 128,
        "BLOCK_SIZE_K": 64,
        "GROUP_SIZE_M": 1,
        "num_warps": 4,
        "num_stages": 3,
        "USE_INT32_OFFSETS": False,
    }
'''

    changes = [
        replace_once(source, config_old, config_new),
        replace_once(source, gemm2_old, gemm2_new),
        replace_once(test, test_old, test_new),
    ]
    print(json.dumps({"changes": changes}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
