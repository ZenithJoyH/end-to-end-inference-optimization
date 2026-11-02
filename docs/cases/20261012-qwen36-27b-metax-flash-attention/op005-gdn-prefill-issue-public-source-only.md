## Summary

Please document and validate the state-layout contract of `chunk_gated_delta_rule_fwd` across the generic implementation and the MetaX runtime replacement.

The public source at commit [29e80363b43bce4a25929989641015c1e734c9e3](https://github.com/flagos-ai/FlagGems-vllm/commit/29e80363b43bce4a25929989641015c1e734c9e3) exposes the same operator name with different initial/final-state layouts:

- Generic chunk implementation: K-major, `[N, HV, K, V]`.
- MetaX chunk implementation: V-major, `[N, HV, V, K]`.

This report concerns ABI discoverability and validation. It does **not** assert that a correctly adapted MetaX prefill kernel has an arithmetic defect.

## Public source evidence

1. [Generic FLA exports](https://github.com/flagos-ai/FlagGems-vllm/blob/29e80363b43bce4a25929989641015c1e734c9e3/src/flaggems_vllm/ops/FLA/__init__.py) export `chunk_gated_delta_rule_fwd` from [ops/FLA/chunk.py](https://github.com/flagos-ai/FlagGems-vllm/blob/29e80363b43bce4a25929989641015c1e734c9e3/src/flaggems_vllm/ops/FLA/chunk.py). Its [chunk_delta_h.py](https://github.com/flagos-ai/FlagGems-vllm/blob/29e80363b43bce4a25929989641015c1e734c9e3/src/flaggems_vllm/ops/FLA/chunk_delta_h.py) interprets the initial state with a K-major layout.
2. [MetaX fused/gdn_chunk.py](https://github.com/flagos-ai/FlagGems-vllm/blob/29e80363b43bce4a25929989641015c1e734c9e3/src/flaggems_vllm/runtime/backend/_metax/fused/gdn_chunk.py) implements the same function name using `chunk_gated_delta_rule_fwd_h_vmajor`. Its entrypoint normalizes contiguity but does not explicitly validate the trailing initial-state dimensions.
3. The [package initialization](https://github.com/flagos-ai/FlagGems-vllm/blob/29e80363b43bce4a25929989641015c1e734c9e3/src/flaggems_vllm/__init__.py) applies runtime-specific replacements. Therefore callers should not infer the active state ABI solely from the generic source.

## Why this matters

A caller adapting a V-major cache to the generic K-major convention may transpose its gathered state before calling the runtime export. That conversion is inappropriate when the resolved MetaX function already expects V-major.

When `K == V`, both arrangements have the same shape and can be contiguous, so shape inspection alone cannot reveal that a non-symmetric initial state represents different values after transposition. Correct input interpretation is essential before attributing an output/reference mismatch to numerical precision.

## Requested changes

- Define one canonical state ABI for the public export, or expose and document explicit backend-specific layout information.
- Document both initial-state and returned final-state layouts at the public entrypoint, including a vLLM V-major integration example.
- Validate state dimensions and supported strides where detectable, especially for `K != V`; explain the equal-dimension ambiguity.
- Add tests of the **resolved runtime export** with nonzero, non-symmetric initial states, unequal K/V dimensions, variable-length sequences and final-state comparisons against a sequential reference.

Related public validation tracking: #557, superseded by #549.

This issue includes only public repository source analysis; no private environment metadata, raw diagnostic outputs or internal reproducer code are attached.