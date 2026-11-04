# op020: Reconnect existing MetaX top-k/top-p

Integration retained and **ready for user benchmark** in `qwen3vl-p64k-opt-20261015` /8111 /API1129815. No new end-to-end performance claim. GPQA remains deferred by user.

## Scope and implementation

User reported opt7 performance recovered and requested restoring sampling for their next benchmark. Continue the existing isolated container, GPU0,1, source8000 protected. Change only `/workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/vendor/metax/patches/topk_topp_sampler.py`; reuse VLLM_FL_USE_FLAGGEMS_VLLM and use_flaggems_op policy. The explicit package-root `apply_top_k_top_p` is vendor-bound through existing runtime.replace_customized_ops. No root init/__all__, Worker, operator implementation, library test/perf or vLLM change.

No-filter returns the same object. Supported MetaX FP32 rank2 contiguous M<=64/1<=V<=262144 calls the library; unsupported metadata falls back before mutation. Only NotImplementedError is caught; runtime/compilation/dependency errors propagate. Preserve original k/p tensor objects, dtype/device and in-place semantics. Platform scope follows the existing MetaX patch; other hardware untested.

Keep root MoE JSON4be4fddffd202553b12bbec915a8ccee4f54fd2f4bd653ec1620e3e267a0b1fe, GEMM2f392cfb568239f036bcc0ce16eadf5a6fa0b3ffbfb549310a916b248b3bfc7ca, gems-opt/c3c5f5ab, all other files in four repositories and start-model.sh. Target and source fingerprints plus image lineage/mount parity were verified again.

## Validation and resolved initial failure

Initial ops-namespace import selected the generic placeholder. Its NotImplementedError entered the old reference outside the test's FlagGems context:13 routing tests passed, numerical suite41passed/6failed. The signed-zero and BF16 top-p cases exposed that wrong path. Preserve initial patch/logs.

A single import correction to the existing root vendor-bound function fixes the original47 cases without any case deletion, tolerance change or operator modification. Direct-path probe proves actual MetaX source and exact agreement with the current FlagGems reference, both with and without an outer activation context. Root __all__ stays HEAD. Confirmed cause is the consumer import boundary.

Final minimal-regression:14 route/optional-policy/error/idempotence checks;45 value/mask cases plus2 changing-input standalone graph tests (2captures/12replays);9 boundary cases including CPU/FP16/noncontiguous/filter metadata/M65/wide/empty batch. All pass. Both actual workers confirm unchanged M64/M8192 GEMM1/GEMM2, production graph capture and16 delegated replays each,17smoke/C8 plus exact8192-token prompt. HTTP calls to the library and same-object return are separately proven after readiness; all observation hooks restored. These are scoped correctness checks, not formal GPQA.

Receipt-only checks also required two harness fixes: compare the sampler against the intended candidate SHA instead of the old unchanged-sampler guard, and restore four MoE configuration variables in the receipt retry. The same already validated running instance was reused; neither repair changed product code or restarted the service.

## Per-process preparation and user handoff

Historical diag013 showed first-seen M compilation can stall Decode tail. This round uses bounded external validation after production capture: every M1..64, k int32/int64, BF16-exact/FP32-temperature domains and reference/library paths,512calls perworker. It does not advance model sampling RNG or change product startup code.

- worker 1130302 / GPU0: 512 calls, 277.89s preparation.
- worker 1130303 / GPU1: 512 calls, 277.93s preparation.

Directly benchmark current8111 instance. A restart reloads the integration but invalidates process-local warmup; do not assume cross-process cache reuse. start-model.sh is unchanged. No benchmark client was launched by the agent this round.

User prior opt7 SUMMARY values: P4K996.45/P16K365.32/P64K76.62 output token/s. They predate this integration and remain manual evidence; raw paths/SHA are in state. Current combined throughput and steady variance await the user's new result; historical isolated sampling/MoE gains are not added.

## Evidence, dependencies and rollback

Remote root `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3`; commands/op020-sampling-reconnect-20261018 holds frozen.json, candidate_r2.json and sampler-r2.patch. Results op020-checks.json, op020-diagnosis-r2.json, op020-boundaries-r2.json, op020-service-health.json, op020-sampling-admission.json and op020-final.json; initial failed log logs/op020-numerics-graph.log retained. Native current manifest `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/manifests/op020-service-service.json`. All hashes in state.yml.

Rollback only restores the frozen sampler bytes and restarts own8111 service after idle/identity checks; do not revert MoE/GEMM2/gems-opt or touch source8000. Cross-repository dependency is the existing vendor-bound sampling API in the frozen FlagGems-vllm; source library unchanged. pr_readiness=experimental pending current E2E, GPQA and affected other-platform coverage. planning-op020-reconnect-handoff records the measurement gap; no global SOP change.
