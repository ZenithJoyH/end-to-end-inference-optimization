#!/usr/bin/env python3
"""Run the P16K benchmark against the integrated FlagGems-vllm entry point."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from flaggems_vllm.runtime.backend._thead.fused.flashmla_sparse import (
    flash_mla_sparse_cached_prefill_fwd,
)


BASE = Path(
    "/mnt/nfs/users/jinghao/hy4-preview/optimize/"
    "20260914-hy4-preview-ppu-e2e/commands/"
    "benchmark-hy4-p16k-cached-prefill-sparse-mla-hybrid-20260921.py"
)


def main() -> int:
    spec = importlib.util.spec_from_file_location("p16k_sparse_hybrid_benchmark", BASE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load benchmark: {BASE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    def integrated(q, kv, indices, sink, lengths):
        return flash_mla_sparse_cached_prefill_fwd(
            q=q,
            kv=kv,
            indices=indices,
            sm_scale=module.SCALE,
            d_v=module.DV,
            attn_sink=sink,
            topk_length=lengths,
        )

    module.hybrid = integrated
    return module.main()


if __name__ == "__main__":
    raise SystemExit(main())
