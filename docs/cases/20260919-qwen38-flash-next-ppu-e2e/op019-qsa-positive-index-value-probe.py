#!/usr/bin/env python3
"""Minimal proof that QSA consumes the value of a nonnegative logical index."""

from __future__ import annotations

import hashlib
import json

import torch

from flag_gems.fused.qsa import qsa_sparse_paged_attention


def sha(tensor: torch.Tensor) -> str:
    raw = tensor.detach().to("cpu").contiguous().view(torch.uint8).numpy()
    return hashlib.sha256(memoryview(raw).cast("B")).hexdigest()


@torch.inference_mode()
def main() -> None:
    torch.manual_seed(20260921)
    q = torch.randn((1, 3, 256), dtype=torch.bfloat16, device="cuda")
    k = torch.randn((129, 16, 1, 256), dtype=torch.bfloat16, device="cuda")
    v = torch.randn_like(k)
    table = torch.arange(129, dtype=torch.int32, device="cuda").reshape(1, 129)
    requests = torch.zeros(1, dtype=torch.int32, device="cuda")
    index0 = torch.tensor([[0]], dtype=torch.int32, device="cuda")
    index2049 = torch.tensor([[2049]], dtype=torch.int32, device="cuda")
    index_invalid = torch.tensor([[-1]], dtype=torch.int32, device="cuda")
    out0 = qsa_sparse_paged_attention(q, k, v, index0, table, requests)
    out2049 = qsa_sparse_paged_attention(q, k, v, index2049, table, requests)
    out_invalid = qsa_sparse_paged_attention(q, k, v, index_invalid, table, requests)
    torch.cuda.synchronize()

    expected0 = v[0, 0, 0].expand(3, 256)
    expected2049 = v[128, 1, 0].expand(3, 256)
    payload = {
        "out0_sha256": sha(out0),
        "out2049_sha256": sha(out2049),
        "out_invalid_sha256": sha(out_invalid),
        "expected0_sha256": sha(expected0),
        "expected2049_sha256": sha(expected2049),
        "out0_equals_expected0": sha(out0) == sha(expected0),
        "out2049_equals_expected2049": sha(out2049) == sha(expected2049),
        "positive_outputs_differ": sha(out0) != sha(out2049),
        "invalid_is_zero": sha(out_invalid) == sha(torch.zeros_like(out_invalid)),
        "expected_values_differ": sha(expected0) != sha(expected2049),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not all(
        payload[key]
        for key in (
            "out0_equals_expected0",
            "out2049_equals_expected2049",
            "positive_outputs_differ",
            "invalid_is_zero",
            "expected_values_differ",
        )
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
