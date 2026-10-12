#!/usr/bin/env python3
"""Reproduce FlagGems Conv3d illegal memory access on a large PPU tensor.

Run this only on an otherwise idle device. The failing invocation can poison the
accelerator context and requires the Python process to exit before another run.
"""

import argparse
import os

import torch

from flag_gems.ops.conv3d import conv3d


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=522240)
    args = parser.parse_args()

    if os.environ.get("FLAGTREE_AABS") != "0":
        raise SystemExit("set FLAGTREE_AABS=0 to match the reported environment")
    if not torch.cuda.is_available():
        raise SystemExit("an available PPU device is required")

    # MiniMax-M3 video patch embedding at max_model_len=131072:
    # 340 frames -> 170 temporal groups * 48 * 64 spatial patches = 522240.
    # Conv3d pads C=3 to C=16 internally, so the effective input N-stride is
    # 16 * 2 * 14 * 14 = 6272 elements.
    dtype = torch.bfloat16
    device = "cuda:0"
    x = torch.empty((args.n, 3, 2, 14, 14), device=device, dtype=dtype)
    weight = torch.empty((1280, 3, 2, 14, 14), device=device, dtype=dtype)

    effective_stride_n = 16 * 2 * 14 * 14
    print(
        {
            "input": tuple(x.shape),
            "weight": tuple(weight.shape),
            "stride": (2, 14, 14),
            "effective_padded_stride_n": effective_stride_n,
            "max_input_element_offset": (args.n - 1) * effective_stride_n,
            "int32_max": 2**31 - 1,
        },
        flush=True,
    )

    out = conv3d(
        x,
        weight,
        bias=None,
        stride=(2, 14, 14),
        padding=0,
        dilation=1,
        groups=1,
    )
    torch.cuda.synchronize()
    print({"output": tuple(out.shape), "status": "completed"}, flush=True)


if __name__ == "__main__":
    main()
