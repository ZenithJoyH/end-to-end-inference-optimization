## Describe the bug

On T-Head PPU, the generic FlagGems `conv3d` kernel crashes with `CUDA error: an illegal memory access was encountered` for the large leading dimension used by MiniMax-M3 video patch embedding during vLLM memory profiling.

The failure is reproducible without loading vLLM or model weights. The failing tensors are:

- input: `[522240, 3, 2, 14, 14]`, BF16
- weight: `[1280, 3, 2, 14, 14]`, BF16
- bias: `None`
- stride: `(2, 14, 14)`
- padding: `0`
- dilation: `1`
- groups: `1`
- `FLAGTREE_AABS=0`

This shape comes from a 340-frame MiniMax-M3 dummy video: `170 * 48 * 64 = 522240` flattened patches.

### Minimal reproducer

Run this only on an otherwise idle device. The failing call can poison the device context for the current process.

```python
import os
import torch
from flag_gems.ops.conv3d import conv3d

assert os.environ.get("FLAGTREE_AABS") == "0"

n = 522240
x = torch.empty((n, 3, 2, 14, 14), device="cuda:0", dtype=torch.bfloat16)
w = torch.empty((1280, 3, 2, 14, 14), device="cuda:0", dtype=torch.bfloat16)

y = conv3d(
    x,
    w,
    bias=None,
    stride=(2, 14, 14),
    padding=0,
    dilation=1,
    groups=1,
)
torch.cuda.synchronize()
print(y.shape)
```

Command:

```bash
source /usr/local/PPU_SDK/envsetup.sh
export FLAGTREE_AABS=0
python repro_conv3d_large_n.py
```

### Observed result

The first invocation enters Triton autotuning and fails during benchmark synchronization:

```text
File "flag_gems/ops/conv3d.py", line 384, in conv3d
  conv3d_forward_kernel[grid](...)
File "triton/runtime/autotuner.py", line 207, in _bench
  rett = self.do_bench(kernel_call, quantiles=(0.5, 0.2, 0.8))
File "triton/testing.py", line 209, in do_bench
  di.synchronize()
File "torch/cuda/__init__.py", line 1108, in synchronize
  return torch._C._cuda_synchronize()
torch.AcceleratorError: CUDA error: an illegal memory access was encountered
```

In the original vLLM trigger this happens in `determine_available_memory -> profile_run -> MiniMax-M3 vision patch_embedding -> torch.nn.functional.conv3d -> flag_gems.ops.conv3d` and prevents the server from becoming ready.

### Expected result

The operator should complete and return `[522240, 1280, 1, 1, 1]`, or reject the unsupported shape before launching a kernel. It should not cause an illegal memory access during autotuning.

### Likely cause

`conv3d()` pads `weight_c < 16` from 3 to 16. After padding, the input N-stride is:

```text
16 * 2 * 14 * 14 = 6272 elements
```

For `N=522240`, the largest input element offset is:

```text
(522240 - 1) * 6272 = 3,275,483,008 > INT32_MAX (2,147,483,647)
```

By contrast, the known-good service configuration generates `N=261120`, whose corresponding offset is `1,637,738,368 < INT32_MAX`.

In `conv3d_forward_kernel`, `in_n_point_value` originates from `tl.arange`, and pointer offsets are formed with expressions such as `input_n_stride * in_n_point_value`. This looks like a 32-bit index overflow after the channel-padding expansion. Please confirm whether the input/output pointer arithmetic needs explicit `tl.int64` promotion and whether autotuning should exclude configurations that cannot safely index the tensor.

### Environment

| Component | Version |
|---|---|
| Hardware | T-Head PPU-ZW810E |
| `ppu-smi` | v1.28, build 2026-06-17 |
| Python | 3.12.3 |
| PyTorch | 2.10.0 |
| Triton / FlagTree | `triton.__version__ == 3.6.0`, target `cuda`, arch 80 |
| FlagGems source | `flagos-ai/FlagGems@3c6f7537d2d5d3aa680c55bbee5c70f2100c5b85` |
| FlagGems reported version | `5.4.0rc2.post1+g4d9c34775` |

The working tree had no modification to `src/flag_gems/ops/conv3d.py` when the failure was captured.

### Additional context

The same MiniMax-M3 service starts successfully with `max_model_len=65536`, which produces the smaller `N=261120` patch-embedding shape. Increasing it to `131072` deterministically reaches the large Conv3d shape above and fails before API readiness.
