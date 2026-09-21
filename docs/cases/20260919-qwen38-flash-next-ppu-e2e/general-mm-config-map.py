#!/usr/bin/env python3
"""Record the FlagGems autotuner choice for the op010 M=64 shape set."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import torch

from flag_gems.ops.mm import mm as gems_mm
from flag_gems.ops.mm import mm_kernel_general


SHAPES = (
    (64, 10240, 4),
    (64, 768, 2560),
    (64, 10240, 320),
    (64, 320, 10240),
    (64, 2560, 12),
    (64, 2560, 2048),
    (64, 2560, 10240),
    (64, 2560, 2560),
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", type=int, default=0)
    args = parser.parse_args()
    torch.cuda.set_device(args.device)
    device = torch.device("cuda", args.device)
    rows = []
    for m, k, n in SHAPES:
        a = torch.empty((m, k), device=device, dtype=torch.bfloat16)
        b = torch.empty((k, n), device=device, dtype=torch.bfloat16)
        output = gems_mm(a, b)
        torch.cuda.synchronize()
        tuner = mm_kernel_general.fn
        key = tuner.get_key(
            {
                "A": a,
                "B": b,
                "C": output,
                "M": m,
                "N": n,
                "K": k,
                "stride_am": a.stride(0),
                "stride_bk": b.stride(0),
            }
        )
        config = tuner.cache.get(key)
        if config is None:
            config = getattr(tuner, "best_config", None)
        if config is None:
            raise RuntimeError(f"no selected config found for {m=} {k=} {n=} {key=}")
        values = config.all_kwargs()
        block_m = int(values["BLOCK_M"])
        block_n = int(values["BLOCK_N"])
        rows.append(
            {
                "shape": {"m": m, "k": k, "n": n},
                "config": {
                    key: value
                    for key, value in values.items()
                    if isinstance(value, (bool, int, float, str))
                },
                "num_warps": int(config.num_warps),
                "num_stages": int(config.num_stages),
                "config_cache_key": [str(value) for value in key],
                "expected_grid": math.ceil(m / block_m) * math.ceil(n / block_n),
                "output_shape": list(output.shape),
            }
        )
    payload = {
        "schema_version": 1,
        "experiment": "op010-p4k-decode-general-mm-config-map",
        "dtype": "bfloat16",
        "rows": rows,
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True)
    args.output.parent.mkdir(parents=True, exist_ok=False)
    args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
