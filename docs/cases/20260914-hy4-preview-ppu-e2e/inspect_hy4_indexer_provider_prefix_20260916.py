#!/usr/bin/env python3
"""Inspect valid-prefix coordinates returned by the active Indexer provider."""

import json

import torch

from vllm_fl.models import hy_v4


rows, width, topk = 128, 128, 2048
torch.manual_seed(1)
q = torch.randn((rows, 32, 128), device="cuda", dtype=torch.bfloat16)
weights = torch.randn((rows, 32), device="cuda", dtype=torch.bfloat16)
keys = torch.randn((width, 128), device="cuda", dtype=torch.bfloat16)
starts = torch.zeros((rows,), device="cuda", dtype=torch.int32)
ends = torch.linspace(1, width, rows, device="cuda").to(torch.int32)
output = torch.empty((rows, topk), device="cuda", dtype=torch.int32)
hy_v4._select_topk_block(
    q,
    weights,
    keys,
    starts,
    ends,
    key_start=0,
    key_end=width,
    request_start=0,
    topk=topk,
    output=output,
)
torch.cuda.synchronize()
for row in (0, 1, 8, 63, 127):
    valid_count = int((ends[row] - starts[row]).item())
    prefix = output[row, :valid_count].cpu().tolist()
    print(json.dumps({
        "row": row,
        "valid_count": valid_count,
        "prefix": prefix,
        "sorted_prefix": sorted(prefix),
        "expected": list(range(valid_count)),
        "tail_sample": output[row, valid_count:valid_count + 8].cpu().tolist(),
    }))
