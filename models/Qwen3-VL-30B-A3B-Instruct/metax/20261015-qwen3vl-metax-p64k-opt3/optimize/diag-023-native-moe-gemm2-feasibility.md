# diag023: Native MoE GEMM2 configuration feasibility

User subsequently declined implementation. No runtime changes were made. A read-only comparison against FlagGems-vllm HEAD f6fdb9b confirms both generic and MetaX get_moe_configs originally use embedded tables; HEAD has no VLLM_TUNED_CONFIG_FOLDER reference under src and no utils/moe_config.py. External JSON loading and optional gemm2 stage directories are additions from this optimization task.

2026-10-19 read-only analysis on mx-59 / qwen3vl-p64k-opt-20261015. User requested feasibility only, no restart. No source, environment, backend choice, JSON, service or request traffic was changed. Current op022 candidate is unchanged.

## Finding

Feasible without editing vLLM installation files: Plugin can install a bounded runtime adapter around native standard Triton Experts and its GEMM launch. This is not supported by merely replacing the JSON loader: native TritonExperts.apply selects one config once and passes the same config to both _base_w13_fn and _base_w2_fn. The functional native fused_experts_impl likewise passes one config to both dispatch_fused_moe_kernel calls. There is no explicit native GEMM2-config hook in this revision.

Verified versions: vLLM ee0da84ab9e04ac7610e28580af62c365e898389, Plugin 08da21cb39601752040196232b60a152382c0f8f, FlagGems-vllm f6fdb9b120787e12892ac67e54979cbf829c7d64. Exact current source SHA map is in state.yml.

Source locations: native experts/triton_moe.py:262 configuration selection, :336 GEMM1 launch and :454 GEMM2 launch; native fused_moe.py:999/1015 file loader, :1303 nearest-M selector, :1537 functional entry. Plugin ops/fused_moe/fused_moe_utils.py owns native/FlagOS expert selection. These are container paths under /workspace/vllm/vllm/model_executor/layers/fused_moe and /workspace/vllm-plugin-FL/vllm_fl.

## Proposed integration boundary

Keep current VLLM_TUNED_CONFIG_FOLDER and standard M-to-parameters JSON. Root table supplies the base/GEMM1 config. gemm2/ contains an optional same-named standard full table, selected with the same logical E/N/dtype/block keys and nearest original token M. Missing stage table preserves the exact original config. Explicit native overrides and VLLM_BATCH_INVARIANT keep their existing priority. Copy selected dictionaries to avoid mutating native LRU cache values.

For a proof of concept, wrap the selected native standard Triton Experts invocation and its launch callable. Bind current invocation metadata (w2 identity, original M, logical E/N, dtype/block) and substitute only that invocation's GEMM2 config; continue calling the original native kernel and orchestration. This avoids copying the long native apply implementation. An invocation-scoped/context-based mechanism is a candidate, not a graph-validated design: reset it reliably, account for nesting/concurrency, install wrappers only once before compile/capture, and verify Dynamo/custom-op boundaries before finalizing. Do not temporarily change environment variables or globally swap launch functions for every call. Do not alternate stages using call counters or guess stage only from top_k==1.

Patch the actual callable references used by each intended path: triton_moe imports its invoke function into module globals, whereas functional fused_experts_impl goes through dispatch_fused_moe_kernel. Replacing only the defining module's symbol does not cover already-bound imports. Start with current plain BF16, no-LoRA standard Triton path; explicitly cover the functional API later if it is an intended caller. Do not claim support for FlashInfer/CUTLASS/AITER, batched experts, all LoRA/quantization modes or other platform hardware from this analysis.

Plugin-native JSON adaptation can use native-compatible naming/selection and a light standard JSON reader. Sharing JSON does not require native compute to import/use FlagGems kernels, nor adding vLLM imports to FlagGems-vllm. Preserve matching filename/device/dtype and cache identities. Initial current directory contains only the shared metax alias names, which match PlatformFL's native filename.

## Constraints confirmed against current configuration

Original M is required: GEMM2 activations have routed M*top_k rows. At M64/topk8, using 512 as the table selector would choose the wrong row (the current GEMM2 nearest key is65 instead of64). Use the original MoE token count, not GEMM2 input row count.

Both GEMMs reuse token assignment prepared with base BLOCK_SIZE_M. A differing stage BM cannot be substituted without rebuilding compatible assignment. CPU enumeration over every M0..65536 (65537 choices) found zero BM mismatches for current root and gemm2 tables. This only proves that configuration invariant over that range, not numerical or hardware correctness.

Current M64: GEMM1 BM16/BN64/BK128/G1/W4/S3, GEMM2 BM16/BN64/BK128/G1/W4/S1. Current M8192: GEMM1 BM128/BN128/BK64/G1/W8/S1; GEMM2 same BM/BN/BK with G8/W4/S1. Thus stage selection must retain the full row, not override num_stages alone.

Native backend selection is an independent prerequisite. Current Plugin _get_priority_backends has CUDA/ROCm/XPU/CPU branches but no MetaX OOT branch when FlagGems is disabled, so enabling shared stage files alone does not resolve that selector gap. Validate that the actual native standard Triton class is selected; do not silently change the existing FlagOS choice as part of configuration support.

## Validation before any implementation is retained

CPU checks: names/dtype/E/N/closest-M and boundaries, missing-stage fallback, overrides/batch-invariant, copies/cache isolation, BM rejection, repeated install and both stage bindings. Then standalone native output comparison and graph capture with at least two replays, followed by actual selected native worker config proof, smoke/C8 and the same prewarmed E2E workload. Kernel shared-memory/compilation and performance must be checked independently: a JSON that loads in both libraries is not evidence of equal optimality.

No implementation or validation run against a new service was performed. pr_readiness=analysis-only. The proposed native path does not replace the current FlagOS path or alter sampling/MoE settings.
