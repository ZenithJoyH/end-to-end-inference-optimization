# Public-source issue payload

Status: published. Issue: [flagos-ai/FlagGems #7075](https://github.com/flagos-ai/FlagGems/issues/7075), created 2026-10-13 16:34 +08:00. This is the public-source/synthetic-input payload; internal model, hardware configuration and raw failure logs were not published. The synthetic CPU padding reproduction was executed and confirmed `524288 -> 8388608 bytes`, ratio `16.0`.

Subsequent update: after the user explicitly authorized disclosure, actual input/environment details and complete historical/current logs were added in [comment 6141950812](https://github.com/flagos-ai/FlagGems/issues/7075#issuecomment-6141950812). The issue body now begins with the fresh actual-shape result and links that supplement. The original allocation-only payload below remains preserved as the initial publication record.

Title: `[Bug] Generic depthwise convolution materializes a 16x larger input buffer`

---

### Describe the bug

The generic grouped-convolution implementation physically pads each group's input channels to 16 before launching its Triton kernel. For depthwise convolution, `weight_c == 1`, so this creates an input buffer **16 times larger than the real input**. Large grouped/depthwise inputs can therefore exhaust memory due to preprocessing, even when the actual input and output fit.

This report is based on public source and the synthetic CPU reproduction below. It verifies the allocation expansion, rather than claiming a newly reproduced GPU-kernel failure on every backend.

### Source and mechanism

At public snapshot [`db69c06ed44b2e4f341c4d79bef32f9ff6b8ab75`](https://github.com/flagos-ai/FlagGems/blob/db69c06ed44b2e4f341c4d79bef32f9ff6b8ab75/src/flag_gems/ops/conv2d.py), `Conv2d.forward` uses `_MIN_DOT_K = 16` and performs the following materialized padding for `groups > 1`:

```python
input = input.reshape(N, groups, weight_c, H, W)
input = torch.nn.functional.pad(input, (0, 0, 0, 0, 0, pad_c))
input = input.reshape(N, groups * (weight_c + pad_c), H, W)
```

For depthwise input, `groups == C`, `weight_c == 1` and `pad_c == 15`; the intermediate contains `N * C * 16 * H * W` elements. This expansion is in the host-side preprocessing before the convolution kernel. The original input is also retained for backward, so allocating the padded input increases peak live storage.

The public [`ops/conv_depthwise2d.py`](https://github.com/flagos-ai/FlagGems/blob/db69c06ed44b2e4f341c4d79bef32f9ff6b8ab75/src/flag_gems/ops/conv_depthwise2d.py) wrapper calls this generic `conv2d` implementation with `groups = input.shape[1]`. The [`conv1d` wrapper](https://github.com/flagos-ai/FlagGems/blob/8416e6dab471451cc437aac3896fdc382dce382e/src/flag_gems/ops/conv1d.py) at the earlier public revision `8416e6da` also routes into this implementation by unsqueezing its input and weights.

### Minimal reproduction of the allocation

No model, tokenizer, accelerator, or private data is needed. This reproduces the padding branch with a small synthetic BF16 input on CPU:

```python
import torch
import torch.nn.functional as F

x = torch.zeros((1, 256, 1024, 1), dtype=torch.bfloat16)
N, C, H, W = x.shape
groups = C
weight_c = 1
pad_c = 16 - weight_c

padded = F.pad(
    x.reshape(N, groups, weight_c, H, W),
    (0, 0, 0, 0, 0, pad_c),
)
padded = padded.reshape(N, groups * (weight_c + pad_c), H, W)

input_bytes = x.numel() * x.element_size()
padded_bytes = padded.numel() * padded.element_size()
print(input_bytes, padded_bytes, padded_bytes / input_bytes)
assert padded_bytes == 16 * input_bytes
```

Verified output:

```text
524288 8388608 16.0
```

Thus even this small 512-KiB input creates an 8-MiB padded input, before accounting for the output or any other temporary buffers. The same code multiplies larger inputs by the same factor.

### Expected behavior / suggested follow-up

Depthwise convolution has no cross-channel reduction. It should avoid materializing 15 unused channels per group: a direct depthwise kernel, logical/masked K padding, or a validated fallback could keep workspace proportional to the actual input/output.

There is already a public [T-Head direct depthwise specialization](https://github.com/flagos-ai/FlagGems/blob/db69c06ed44b2e4f341c4d79bef32f9ff6b8ab75/src/flag_gems/runtime/backend/_thead/ops/conv_depthwise2d.py) that discusses this generic padding cost. Please confirm coverage of the registered `_conv_depthwise2d` entry and nested `F.conv1d` path, and consider a numerical plus peak-memory regression for the generic path and backend fallback. This report does not assert that the specialization itself has this defect.

Related: #3021 concerns depthwise accuracy; this report specifically tracks input-buffer amplification.
