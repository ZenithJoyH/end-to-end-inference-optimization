# FlagGems depthwise convolution issue draft

Status: initial detailed draft was not published because automatic approval review required explicit payload disclosure authorization. The user subsequently explicitly allowed publication of model/hardware/runtime details, actual shapes, versions and full logs on 2026-10-13. The verified historical evidence plus a fresh current-container reproduction was published in [#7075 comment 6141950812](https://github.com/flagos-ai/FlagGems/issues/7075#issuecomment-6141950812). See `conv7075-current-env-repro-20261013.md` for exact fresh results and artifact SHAs; this older draft alone is not the final supplementary payload.

Target repository: `flagos-ai/FlagGems`

Title: `[Bug][T-Head] Generic depthwise conv expands input channels 16x and requests a 7.79 GiB temporary buffer`

---

### Describe the bug

The generic depthwise convolution path materializes 16 channels for every single-channel group to satisfy the `tl.dot` K-dimension requirement. For a production BF16 depthwise `conv1d` input of `[7, 10240, 3644]`, this expands the input temporary from **522,403,840 bytes (~498 MiB) to 8,358,461,440 bytes (7.79 GiB)** and causes OOM during Qwen3.8-Flash-Next PLE prefill.

In the original graph-serving sanity run, only 1/8 concurrent requests succeeded; the other seven returned HTTP 500, and a worker hit the 7.79 GiB allocation failure. A separate operator reproducer reproduced the same allocation failure without loading model weights. This is a historical, pinned-revision report; it is not a claim that the newest T-Head backend has been reproduced failing.

### Environment and exact input

- Observed FlagGems revision: [`8416e6dab471451cc437aac3896fdc382dce382e`](https://github.com/flagos-ai/FlagGems/commit/8416e6dab471451cc437aac3896fdc382dce382e), recorded by the failing standalone reproducer on 2026-09-04.
- Device: T-Head `PPU-ZW810E`, 96 GiB. This runtime exposes the `torch.cuda` API and reports CUDA-style error text.
- PyTorch: `2.10.0`; Python: `3.12`.
- Input: BF16, contiguous, shape `[7, 10240, 3644]`, strides `[37314560, 3644, 1]`.
- Weight: BF16, shape `[10240, 1, 4]`, strides `[4, 4, 1]`.
- `groups=10240`, `stride=1`, `padding=0`, `dilation=3`, `bias=None`.

### Minimal reproduction

The following is the shape-preserving version of the recorded standalone reproducer, with tokenizer/model dependencies removed. Use a fresh process on the pinned revision and select an available device externally.

```python
import torch
import flag_gems
from flag_gems.ops.conv1d import conv1d

torch.manual_seed(20260904)

# On the recorded 96-GiB PPU, this gives a 7.68-GiB allocator budget.
# It reproduces the live worker's memory pressure without loading a model
# or filling device memory with dummy allocations.
torch.cuda.set_per_process_memory_fraction(0.08)

x = torch.randn((7, 10240, 3644), device="cuda", dtype=torch.bfloat16)
w = torch.randn((10240, 1, 4), device="cuda", dtype=torch.bfloat16)

print("input bytes:", x.numel() * x.element_size())
print("padded input bytes:", x.numel() * x.element_size() * 16)

with flag_gems.use_gems(exclude=["slice"]):
    y = conv1d(x, w, groups=10240, stride=1, padding=0, dilation=3)
torch.cuda.synchronize()
```

The captured eager and graph reproducers both failed at this allocation. In the graph case, failure happened during the required eager warm-up **before capture**, so this particular OOM does not require graph replay.

Recorded allocator error:

```text
CUDA out of memory. Tried to allocate 7.79 GiB. GPU 0 has a total
capacity of 96.00 GiB of which 95.47 GiB is free. Including non-PyTorch
memory, this process has 540.00 MiB memory in use. 7.68 GiB allowed;
Of the allocated memory 498.28 MiB is allocated by PyTorch, and
9.72 MiB is reserved by PyTorch but unallocated.
```

### Allocation mechanism and dispatch path

At the failing revision, [`conv1d`](https://github.com/flagos-ai/FlagGems/blob/8416e6dab471451cc437aac3896fdc382dce382e/src/flag_gems/ops/conv1d.py) unsqueezes input/weight and calls the generic [`Conv2d.forward`](https://github.com/flagos-ai/FlagGems/blob/8416e6dab471451cc437aac3896fdc382dce382e/src/flag_gems/ops/conv2d.py#L392-L410). The latter uses `_MIN_DOT_K = 16`; when `weight_c == 1`, it reshapes the input by group and physically pads each group's channel dimension from 1 to 16:

```python
input = input.reshape(N, groups, weight_c, H, W)
input = torch.nn.functional.pad(input, (0, 0, 0, 0, 0, pad_c))
input = input.reshape(N, groups * (weight_c + pad_c), H, W)
```

This creates a tensor containing `7 * 10240 * 16 * 3644` BF16 elements, exactly matching the failed 7.79 GiB allocation.

There is also an important fallback/registration boundary: excluding only `conv1d` did not restore native execution, because `torch.nn.functional.conv1d` could still reach the registered ATen `_conv_depthwise2d` override. Excluding `conv2d` did not stop that override from directly calling the FlagGems Python `conv2d` implementation. The captured stack confirmed:

```text
torch.nn.functional.conv1d(..., groups=10240, dilation=3)
  -> flag_gems.ops.conv_depthwise2d._conv_depthwise2d
  -> flag_gems.ops.conv2d.conv2d
  -> Conv2d.apply / Conv2d.forward
```

A separate nested-dispatch probe also encountered an illegal memory access in `conv2d_forward_kernel` autotuning. That is an additional observed symptom; its causal relationship to the allocation expansion was not proven, so it should not be inferred from the OOM alone.

### Expected behavior and verified workaround

Depthwise convolution has one input channel per group and does not need a materialized 16-channel expansion. A direct depthwise kernel, a logical/masked K padding strategy, or a safe native fallback should keep temporary memory proportional to the real input/output size.

For comparison, native `torch.nn.functional.conv1d` on the exact long-prefill shape had **521,113,600 bytes (~497 MiB)** of additional peak allocation, equal to the output size. In the Plugin integration, excluding both `conv1d` and `_conv_depthwise2d` restored native execution. Eager/graph probes passed, and graph-serving sanity completed 8/8 requests without OOM. The workaround was revalidated on clean FlagGems `dcd0cfeae8187dee691656c0616c1ed95899c2ae` on 2026-09-07. These results validate the native fallback, not a fix to the generic FlagGems kernel.

### Current upstream status / requested follow-up

The newer upstream snapshot [`db69c06ed44b2e4f341c4d79bef32f9ff6b8ab75`](https://github.com/flagos-ai/FlagGems/blob/db69c06ed44b2e4f341c4d79bef32f9ff6b8ab75/src/flag_gems/runtime/backend/_thead/ops/conv_depthwise2d.py) already contains a direct T-Head depthwise specialization that explicitly discusses the generic channel-padding problem. I have inspected that source but have not rerun this production shape on it.

Please confirm whether the specialization and registered-op bridge cover this nested `F.conv1d` path, and add the BF16 `[7,10240,3644]` / `[10240,1,4]` / dilation-3 case to numerical and peak-memory regression coverage. If this is already fully addressed by an existing change, linking that change and regression coverage would resolve this report.

Related: #3021 tracks depthwise accuracy; this report specifically documents the temporary-memory expansion and the nested fallback boundary.
