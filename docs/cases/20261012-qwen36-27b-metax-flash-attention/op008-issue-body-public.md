## Summary

The MetaX runtime `chunk_gated_delta_rule_fwd` can exceed `atol=2e-3, rtol=2e-2` for its FP32 final state on normalized BF16 inputs, particularly across multiple chunks with weak decay. The BF16 output can pass the same check while the carried state fails.

This replaces the earlier layout-only framing of this issue. The active MetaX ABI is V-major `[N, HV, V, K]`; the caller-side transpose was corrected before the precision investigation below. These failures use the correct layout.

## Reproduction and reference

Test the **resolved runtime export**, with normalized BF16 Q/K, BF16 V, FP32 gates/state, GQA `Hg=8, HV=24`, `K=V=128`, and a nonzero, non-symmetric initial state. A 257-token sequence with `g=-0.001` or `-0.01` is a useful regression case. Compare every output/state element against a CPU FP32 token-by-token recurrence on the **same already-quantized inputs**.

The related PR includes a self-contained synthetic test (`tests/test_FLA/test_metax_gdn_prefill_state_precision.py`), including seeds 100/101, weak decay, non-square K/V, an empty segment, a chunk tail, padded initial-state strides, and two graph replays with changed inputs. No external tensor snapshot or model is required. On the upstream base, the seed-100 weak-decay case fails the final-state assertion: 7,870 / 393,216 elements exceed tolerance (2.0%); the greatest reported absolute mismatch is approximately `1.025e-2`.

The investigated implementation is present at [29e80363](https://github.com/flagos-ai/FlagGems-vllm/commit/29e80363b43bce4a25929989641015c1e734c9e3); the MetaX chunk source is unchanged at the PR base [6123527f](https://github.com/flagos-ai/FlagGems-vllm/commit/6123527f05497e08bc677cb40e8364502c4f5a32).

## Precision diagnosis

- An exact FP64 chunk formulation agrees with the sequential recurrence on the quantized inputs. Explicitly simulating intermediate BF16 rounding reproduces a captured GPU failing element within approximately `9e-9`.
- In that case, the state error was approximately `2.556e-3`, exceeding its `2.295e-3` allowance. Removing the empty segment leaves the active final state bitwise identical, so the failure is not explained by empty-segment indexing.
- The inverse/WY representation, weighted RHS, state projection and decayed innovation are rounded before a state returned as FP32. Improving only the weighted RHS passes shorter cases but still fails the multi-chunk weak-decay regressions.

This evidence identifies an intermediate-precision limitation under the stated tolerance, rather than establishing a recurrence-formula or V-major indexing defect. It does not establish a model-level accuracy cause or a performance result.

## Proposed correction

For MetaX BF16 Q/K/V, retain FP32 inverse, WY tensors, innovation and carried state, and use IEEE FP32 dot products for the state path. Keep the external output BF16 and final state FP32, without changing the state ABI. Preserve other backends and the existing non-BF16 route.

The corrected state error for the captured element is approximately `5.4e-8`. The original tolerance remains unchanged. FP32 intermediates cost additional memory/compute; performance acceptance is a separate follow-up, not a claimed benefit of this fix.

## Related fix

Draft PR #925: https://github.com/flagos-ai/FlagGems-vllm/pull/925. It includes the synthetic regression test and closes this issue on merge via `Fixes #923`.
