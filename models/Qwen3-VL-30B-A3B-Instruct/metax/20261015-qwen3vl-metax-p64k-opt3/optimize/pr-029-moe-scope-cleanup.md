# pr029: Narrow and simplify PR943 MoE configuration selection

User authorizes resolving review028 findings and marking PR943 ready after validation. Existing authorization allows stopping8111 on GPU0/1 and restoring the exact original configuration afterward. Other services, sampling, gems-opt, blacklists and retained tuning parameters remain unchanged. Runtime source is not backwritten in this publication-only cleanup.

## Pre-implementation project truth

| Field | Frozen scope |
| --- | --- |
| Operator | FlagGems-vllm MetaX fused_experts_impl, existing public signature |
| Editable | Dedicated/private PR checkout MetaX fused_moe.py; existing test retains only one CI compatibility marker |
| Read-only | Original runtime repositories, vLLM, historical JSON oracle and all model/launch settings |
| Build | Editable Python operator; py_compile, pinned Black/isort/flake8 and CI marker checker |
| Validation | e2e/accuracy minimal-regression; exhaustive host oracle, dtype/shape/device negative gates, GPU math and changed-input graphs, TP2 graph service smoke/C8 |
| Performance | No new E2E or kernel speedup claim; retain exact six measured launch values; no performance acceptance issued |
| Active set | BF16/FP16 E128,H2048,I384,topk8, representative M0..8193; nonmatch BF16/FP16/FP32; E64,H2048,I512,M8192 regular GEMM1 after pair-disable |
| Timeouts | Standalone GPU1800s, model readiness1200s, each HTTP240s |
| Profiler | Not needed for review remediation; actual dispatch/config and compiled resource proof substitute; no profiler-derived timing claim |
| Autotune | Explicit exemption: user requests retained inline measured MetaX tuning. No NVIDIA/kernel changes, no new autotune search |
| Fallback | Existing embedded/default selectors; no new Torch compute or vLLM dependency |

## Numerical contract

| Field | Frozen scope |
| --- | --- |
| API semantics | Existing contiguous forward MoE, SiLU gated projection, routed weighted sum; outputs same shape/dtype and in-place behavior |
| Device | MetaX C550, TP2 GPU0/1, actual metadata reverified |
| Tuned eligibility | E128,H2048,I384,topk8; config dtype fp16/bf16, no block quantization, C550; unknown/quantized dtype excludes inline profile |
| Accumulation/reference | Existing kernels unchanged; independent grouped FP32 reference with activated intermediate cast to input dtype |
| Tolerances | BF16 atol.004/rtol.016; FP16 atol.0005/rtol.003; FP32 atol.0001/rtol.001; no relaxation |
| Layout/boundary | Empty, singleton, nonaligned M, transition boundaries, inplace; existing noncontiguous rejection retained |
| Unsupported scope | No new quantization, training/backward, NaN/Inf or layout support claimed |
| Torch use | Metadata reads only in new production code; Torch math exists solely in external validation reference |

## Path design

| Path | Trigger / implementation | Validation / risk |
| --- | --- | --- |
| Early | Existing zero-token / rejection logic unchanged | Empty and noncontiguous tests |
| Measured | Narrow shape/dtype/device in existing get_default_config stage boundary | Exhaustive historical oracle; GEMM1/2 BLOCK_SIZE_M equal; actual dispatch, math and graph |
| Default | All nonmatches retain original selector priority; shared-memory cap uses final pair choice | Negative gates, real E64 default compilation/reference/graph |
| Unsupported | Existing assertions/errors unchanged | No added compute fallback |

Planned changes: remove the added second embedded-table protocol and stage argument from get_moe_configs; keep original embedded precedence/copy behavior; express the retained nearest-M result as equivalent bounded ranges in get_default_config. Disable measured profile for batch-invariant mode without changing unrelated embedded selection. Choose pair/regular path before estimating stage memory, accounting for FP32 bytes. Preserve five Triton kernels and every existing public signature.

Promotion requires exact-candidate GPU and service graph pass, original8111 recovery identity/smoke pass, scoped diff and CI success. Full GPQA and fresh performance are explicitly not run in this maintenance task.

## Final scope refinement before publication

Initial candidate1c2218 passed55GPU cases/37references/23captures/46replays. Additional inspection found existing use_int8_w8a8 retains the activation-half configuration dtype. Add a private selector boolean, supplied as not use_int8_w8a8 from the existing call, so this quantized path retains original embedded/default selection. Other quantization keys already fail the fp16/bf16 gate. Two internal selector signatures gain the defaulted boolean; all public operator signatures and five Triton kernels remain unchanged. Final candidate38a953 requires its own GPU/service validation. No source runtime change occurred.

## Final standalone results

Final operator SHA25638a953da89ddd8889c1be604e4b0b28188a86a8cbb181a7625d0f17328e2fe61 passed55GPU cases/37mathematical references/23captures/46changed-input/routing replays. Actual C55064KiB E64/H2048/I512/M8192 BF16/FP16 regular GEMM1 stage2 compiled and passed math/graph. No tolerance changed. Existing noncontiguous rejection and inplace behavior pass. Host checks:262160historical oracle comparisons,17negative gates,896memory checks,5unchanged kernels. Final normal commit090ef1ddfac767eba515d90cd001ee40599fac1b contains only MetaX operator+one existing test marker line (66additions/5deletions total). Source runtime source files remain unchanged. TP2 service verification and restoration pending.

## Final delivery

[PR943](https://github.com/flagos-ai/FlagGems-vllm/pull/943) is open and **Ready for review**, head090ef1ddfac767eba515d90cd001ee40599fac1b, promoted at2026-10-19T07:32:34Z. The normal expected-head update touched only the MetaX operator (65additions/5deletions) and one compatibility marker in an existing test. No added library test/perf/JSON files, Plugin changes, vLLM dependency, public operator API changes or kernel arithmetic changes.

All final-head applicable CI passed: rule-check, code style, target selection, MetaX MACA3.7.2.0 and3.8.1.0 tests/benchmarks, multi-backend summary. NVIDIA correctly skipped. Native CI receipt `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/commands/pr029-moe-scope-cleanup-20261019/ci-final.json`, SHA256edb8fcb59845ccc04508dc75ea095bb62b775f43fa096104639bbd7a82779faf.

Final standalone:55cases/37references/23captures/46replays. Maximum observed mathematical absolute error .0016574263572692871, within the unchanged dtype contracts. Result `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/pr029-final-gpu-numerics.json`, SHA25625d6867cc3148f91ccea5cb1f341ddcb381be24e6e0821edc04c46debaf34c97. The actual regular stage2 binary metadata reaches65536bytes, within the device limit; no stage2 speedup claim.

TP2 integration FULL_AND_PIECEWISE/max capture64: both workers confirmed final operator hash38a953... and actual M64 stages3/1; each captured and replayed>=16times.11HTTP requests including C8 passed. Result `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/pr029-final-service-graph.json`, SHA25686fa8fb2ec9cc9ef025fce7f2db5b62ce8a56a83b9a9b15d3c35c1db95c4e3c4. Test probes exist only in the dedicated container under an opt-in environment flag; its service has been stopped.

Source8111/opt9 restored: exact argv, selected runtime environment, four repository states, critical source hashes, cwd and log path match the fresh pre-stop snapshot; smoke returned42. Native result `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/pr029-source-restored.json`, SHA2560be548e4941b29d3493ee268e7c3cd275828ec2fa781d6cbc06f1aac72d2fc11. This publication cleanup was **not backwritten to production source**; sampling, gems-opt, blacklists and retained MoE parameter values stay unchanged. Other six GPUs/services were not stopped or modified.

Combined native validation/resource/identity handoff `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/pr029-validation-handoff.json`, SHA256e235faa35a776d24047d99fd844f18c1c31dfc2f43abcc3f5dbdf845c6ae92c7. Source restoration is a maintenance identity/smoke check, not a formal accuracy rebind. Full GPQA remains deferred by user; no formal gate or fresh E2E result is claimed. Other MetaX devices, quantized GPU paths and training were not hardware validated. PR readiness is scoped to this tested inference change.

Final Ready/CI/source-ready receipt: `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/pr029-ready-handoff.json`, SHA256 `0abf0039f2398527537a118f727329fe201f578cdcea45bb94dd64f16525aa9d`. Fresh GitHub read confirms Draft=false/head090ef1d/two changed files.
