#!/usr/bin/env python3
"""Report the LibTuner config selected for dominant Hy4 scaled-mm shapes."""

from __future__ import annotations

import importlib
import json

import torch


SHAPES = (
    (2048, 6144, 256),
    (2048, 2048, 1024),
    (2048, 1024, 6144),
    (2048, 6144, 576),
    (2048, 128, 6144),
    (2048, 6144, 2048),
)


def main() -> None:
    module = importlib.import_module("flag_gems.ops.scaled_mm")
    rows = []
    for m, k, n in SHAPES:
        a = torch.randint(-127, 128, (m, k), device="cuda", dtype=torch.int8)
        b = torch.randint(-127, 128, (k, n), device="cuda", dtype=torch.int8)
        scale_a = torch.rand((m, 1), device="cuda", dtype=torch.float32) * 0.02
        scale_b = torch.rand((n,), device="cuda", dtype=torch.float32) * 0.02
        out = torch.empty((m, n), device="cuda", dtype=torch.bfloat16)
        module.scaled_mm_out(
            a,
            b,
            scale_a,
            scale_b,
            out_dtype=torch.bfloat16,
            out=out,
        )
        torch.cuda.synchronize()
        config = module.scaled_mm_kernel.fn.best_config
        rows.append(
            {
                "M": m,
                "N": n,
                "K": k,
                "config": config.all_kwargs(),
            }
        )
        del a, b, scale_a, scale_b, out
    print("SUMMARY=" + json.dumps({"schema_version": 1, "shapes": rows}))


if __name__ == "__main__":
    torch.manual_seed(20260916)
    main()
