BF16 GDN prefill can return an FP32 final state outside `atol=2e-3, rtol=2e-2` because the inverse, WY representation, state projection and innovation are rounded during chunk propagation. Weak decay exposes accumulated error even when BF16 outputs pass.

For MetaX BF16 Q/K/V, keep the intermediate state chain in FP32 and use IEEE state dot products. Allocate the output directly in BF16, preserving the seven-value return protocol and V-major state ABI. Auxiliary inverse/WY/state intermediates intentionally become FP32; backward/recompute consumers are outside this inference-only validation. Other backends and the non-BF16 route retain their selection and precision. Bound compilation using validated FP32 configurations; these are not claimed to be optimal performance settings.

Fixes #923.

Validation:

- 11 synthetic MetaX tests passed; coverage includes non-square K/V, empty segments, chunk tails, nonzero/zero/padded initial states, slow decay, no-final-state output dtype, and changed-input graph replays.
- The upstream seed-100 weak-decay case reproduces a final-state assertion failure (7,870 / 393,216 elements outside tolerance).
- Same-input CPU recurrence checks retain `atol=2e-3, rtol=2e-2`.
- Formatting/lint: Black 24.8.0, isort 5.12.0 and flake8 7.1.0.

This is an accuracy fix submitted as a draft. FP32 workspace/compute cost has not passed performance acceptance; no end-to-end speedup or full model accuracy result is claimed. Other hardware and the full legacy dtype/shape matrix remain unmeasured. Existing entrypoint contiguity normalization is unchanged; no new Torch compute fallback is introduced.
