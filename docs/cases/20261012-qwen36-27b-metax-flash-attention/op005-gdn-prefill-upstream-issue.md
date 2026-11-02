## Summary

While integrating GDN prefill on MetaX C550, a BF16-vs-CPU-FP32 check failed. On auditing the actual function object, we found a state-layout mismatch in our adapter: it assumed the **generic K-major** contract and transposed vLLM's V-major state, but the **MetaX runtime export already consumes V-major**.

**This is not currently a confirmed arithmetic defect in the MetaX prefill kernel.** The observed numerical failure is confounded by the adapter's incorrect state conversion. This issue requests a clear, discoverable runtime state-layout contract, validation and regression coverage so callers do not infer the ABI from the generic source and silently pass the wrong state.

## Version and environment

- FlagGems-vllm: `0.3.0.dev1`, commit [`29e80363b43bce4a25929989641015c1e734c9e3`](https://github.com/flagos-ai/FlagGems-vllm/commit/29e80363b43bce4a25929989641015c1e734c9e3).
- GPU: MetaX C550; Python `3.12.11`; PyTorch `2.8.0+metax3.7.0.7`.
- Triton/FlagTree: `0.7.0+metax.gitc39f1b1b`; MACA runtime/compiler `3.7.0.38`; driver `3.8.1`.
- The checkout has unrelated experimental FlashAttention/decode changes. The **selected MetaX prefill file is byte-identical to this upstream commit**, SHA256 `f4a6bd6cf6db191439fa3bdc1e6b25d432b739c1a0700b85a2da78e427a3d75a`. Those unrelated changes are not presented as a clean-checkout prefill validation.

## ABI discrepancy

The top-level call is `flaggems_vllm.chunk_gated_delta_rule_fwd`:

- On MetaX it resolves to [`runtime/backend/_metax/fused/gdn_chunk.py`](https://github.com/flagos-ai/FlagGems-vllm/blob/29e80363b43bce4a25929989641015c1e734c9e3/src/flaggems_vllm/runtime/backend/_metax/fused/gdn_chunk.py). This calls `chunk_gated_delta_rule_fwd_h_vmajor` and uses `[N, HV, V, K]` states. Its signature also accepts `chunk_indices`, `chunk_offsets` and `**kwargs`.
- The generic [`ops/FLA/chunk.py`](https://github.com/flagos-ai/FlagGems-vllm/blob/29e80363b43bce4a25929989641015c1e734c9e3/src/flaggems_vllm/ops/FLA/chunk.py), with [`ops/FLA/chunk_delta_h.py`](https://github.com/flagos-ai/FlagGems-vllm/blob/29e80363b43bce4a25929989641015c1e734c9e3/src/flaggems_vllm/ops/FLA/chunk_delta_h.py), uses `[N, HV, K, V]` states.

Both are exposed under the same runtime operator name. The MetaX entrypoint checks contiguity but does not explicitly validate/document the trailing state dimensions in its public function docstring. When `K == V`, a transposed, contiguous state has the same shape, so shape inspection alone cannot reveal that its values represent a different initial state.

## Observed integration failure

- `q/k`: `[1, 160, 8, 128]`, BF16, already L2-normalized.
- `v`: `[1, 160, 24, 128]`, BF16; `g`: FP32; `beta`: BF16.
- Variable-length sequences: `cu_seqlens=[0,64,160]` (64 and 96 tokens).
- Original initial state: nonzero/non-symmetric FP32 `[2,24,128,128]` in **V-major**.
- The erroneous adapter passed `initial_state.transpose(-1,-2).contiguous()` to the MetaX export, and intended to transpose the returned final state back.
- Output was cast to BF16 and compared against a CPU FP32 sequential recurrence starting from the **original V-major state**, with `atol=0.002, rtol=0.02`.

```text
Mismatched elements: 159 / 491520
Greatest absolute difference: 0.003936767578125 at index (0, 64, 1, 4)
Greatest relative difference: 74.5 at index (0, 64, 16, 21)
```

These numbers were observed in the integration probe; they must not be interpreted as the error of a correctly adapted MetaX call. The output assertion failed before final-state or prefill graph validation completed.

An attempted comparison with the installed vLLM generic chunk reference was also inconclusive: it failed with `OutOfResources: shared memory Required: 69632, Hardware limit: 65536`. That is a separate reference-path limitation, not evidence of a FlagGems defect.

## Self-contained diagnostic candidate

The following script was extracted from the probe and calls the resolved FlagGems export directly, without vLLM, model weights or requests. It preserves the RNG draw sequence before the observed failing prefill case. **It has been syntax-checked but not rerun as a standalone clean-checkout GPU test.** The correct V-major call is included for a follow-up comparison; no passing result for it is claimed here.

Run in the described MetaX environment with `FLAGGEMS_VENDOR=metax python repro.py` on an idle GPU:

```python
"""Diagnostic candidate from the integration probe; no vLLM/model required.
Prepared but not rerun as a standalone clean-checkout reproducer.
"""
import inspect
import torch
import flaggems_vllm

DEVICE = "cuda"
torch.manual_seed(42)

# Preserve the random draws that preceded the failing prefill case in the
# integration probe. No decode kernels or model requests are run here.
def consume_previous_draws(B, H, HV, K, V):
    _storage = torch.randn(B * 4 + 4, HV * V * K + 512, device=DEVICE) * .01
    _mixed = torch.randn(B, 2 * H * K + HV * V + 64,
                        device=DEVICE, dtype=torch.bfloat16)
    _a = torch.randn(B, HV + 4, device=DEVICE, dtype=torch.bfloat16)[:, :HV]
    _b = torch.randn_like(_a)
    _A = torch.randn(HV, device=DEVICE)
    _dt = torch.randn_like(_A)

for shape in [(1, 8, 24, 128, 128), (8, 8, 24, 128, 128),
              (64, 8, 24, 128, 128), (4, 2, 4, 96, 80)]:
    consume_previous_draws(*shape)
for _ in range(4):
    consume_previous_draws(4, 4, 8, 128, 96)

H, HV, K, V, T = 8, 24, 128, 128, 160
q = torch.randn(1, T, H, K, device=DEVICE, dtype=torch.bfloat16)
k = torch.randn_like(q)
q = (q.float() / (q.float().square().sum(-1, keepdim=True) + 1e-6).sqrt()).to(q.dtype)
k = (k.float() / (k.float().square().sum(-1, keepdim=True) + 1e-6).sqrt()).to(k.dtype)
v = torch.randn(1, T, HV, V, device=DEVICE, dtype=torch.bfloat16)
g = -torch.rand(1, T, HV, device=DEVICE)
beta = torch.rand(1, T, HV, device=DEVICE, dtype=torch.bfloat16)
state_vm = torch.randn(2, HV, V, K, device=DEVICE) * .01
cu = torch.tensor([0, 64, T], device=DEVICE, dtype=torch.int32)

# CPU FP32 reference starts from the original, non-symmetric V-major states.
qq = q.cpu().float().repeat_interleave(HV // H, dim=2)
kk = k.cpu().float().repeat_interleave(HV // H, dim=2)
vv, gg, bb = v.cpu().float(), g.cpu().float(), beta.cpu().float()
ref = torch.zeros_like(vv)
initial = state_vm.cpu().clone()
for n, (begin, end) in enumerate([(0, 64), (64, T)]):
    state = initial[n].clone()
    for t in range(begin, end):
        state *= gg[0, t].exp()[:, None, None]
        delta = (vv[0, t] - (state * kk[0, t, :, None, :]).sum(-1)) * bb[0, t, :, None]
        state += delta[:, :, None] * kk[0, t, :, None, :]
        ref[0, t] = (state * qq[0, t, :, None, :]).sum(-1) * K ** -.5
ref = ref.to(torch.bfloat16)

f = flaggems_vllm.chunk_gated_delta_rule_fwd
print("resolved export:", f.__module__, inspect.signature(f))

def diagnose(label, initial_state):
    _, out, _, final_state, _, _, _ = f(
        q=q, k=k, v=v, g=g, beta=beta, scale=K ** -.5,
        initial_state=initial_state, output_final_state=True, cu_seqlens=cu,
    )
    torch.cuda.synchronize()
    out = out.to(q.dtype).cpu()
    err = (out.float() - ref.float()).abs()
    tol = .002 + .02 * ref.float().abs()
    print(label, "max_abs=", err.max().item(),
          "over_tolerance=", (err > tol).sum().item(), "/", out.numel(),
          "final_state_shape=", tuple(final_state.shape))

with torch.inference_mode():
    # Proposed correct MetaX call, not yet verified as a separate GPU test.
    diagnose("MetaX V-major input", state_vm)
    # Mirrors the erroneous adapter used in the observed integration test.
    # This passes a K-major value arrangement to the V-major runtime export.
    diagnose("generic-style transpose (wrong for MetaX)",
             state_vm.transpose(-1, -2).contiguous())
```

## Requested resolution

1. Document one canonical initial/final-state ABI for `chunk_gated_delta_rule_fwd`, or expose explicit backend-specific layout information when runtime replacement changes it.
2. Validate state shape/layout where detectable, especially `K != V`, and document the square-state ambiguity.
3. Add nonzero, non-symmetric initial-state tests with `K != V`, variable-length sequences and final-state checks against a sequential FP32 reference; test the **resolved runtime export**, not just the generic import.
4. Provide a vLLM V-major integration example that selects the correct conversion for the actual backend.

Related validation tracking: #557 (superseded by #549). This report is a concrete ABI/integration failure scenario rather than a claim that all MetaX GDN prefill arithmetic is incorrect.
