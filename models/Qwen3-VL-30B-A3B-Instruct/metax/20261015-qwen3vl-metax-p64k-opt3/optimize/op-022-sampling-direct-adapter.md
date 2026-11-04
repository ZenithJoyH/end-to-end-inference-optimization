# op022: Direct FlagGems sampling adapter

Saved in mx-59 / `qwen3vl-p64k-opt-20261015`; **user restart pending**. This round performed no service start/restart/signal, no model request, no GPU kernel and no benchmark. Running8111 API identity was unchanged.

## Final implementation

The user explicitly requested removing op021 sampling dispatch and calling FlagGems-vllm through Plugin's generic FlagGems adapter. The final chain is `common ops/sampler.py -> FlagGems impl/sampler.py -> flaggems_vllm.apply_top_k_top_p`. The existing package-root API performs provider/vendor selection. The adapter resides under the existing FlagGems backend directory, but this filter is no longer registered or selected through OpManager.

Restored the four FlagGems/reference backend method and registration files exactly to their frozen op021 pre-change bytes. Removed the sampling CachedOp and dispatcher marker; retained the generic general-plugin hook and idempotent direct-adapter marker. MetaX compatibility file remains at original Plugin HEAD with no direct library integration.

The existing VLLM_FL_USE_FLAGGEMS_VLLM switch and use_flaggems_op whitelist/blacklist guard both installation and filter invocation. No-filter calls return the same logits object. Disabled integration calls the captured native/platform filter. The adapter imports the existing root API lazily and catches only pre-mutation metadata NotImplementedError for native fallback. Execution/compilation/dependency errors propagate. There is no new sampler per-op dispatch preference or manager failure cache. k/p objects and in-place return semantics are preserved. No platform/model/shape conditions are duplicated in the Plugin.

Six Plugin files changed this round. MoE JSON, GEMM2, gems-opt, all operator-library sources, vLLM, Worker, general-plugin hook, MetaX compatibility and start-model.sh remain unchanged from the fresh inspection. Four complete repository source inventories and revisions were verified; the same isolated image and normalized mounts were retained.

## Verification and boundaries

18 CPU route checks passed in1.49s: k/p/k+p with enable/disable/blacklist choices; switches changed after installation; unsupported metadata followed by supported input; runtime/import/module errors; no-filter identity; repeated install/module reload and native-callable preservation; absence of sampling CachedOp/backend methods/registrations and platform special cases. Tests use actual common shim/adapter source, mock external platform/library imports, hide all GPUs and assert CUDA is not initialized. All six files passed syntax and whitespace checks. Ruff was unavailable; no tool was installed.

These tests prove routing contracts only. Full minimal-regression remains **incomplete**: new graph capture/two replays and actual HTTP library hit are deferred because the user explicitly requested no restart. Historical op020 hardware results are not relabelled. GPQA remains deferred by user. No new E2E measurement, throughput claim or other-platform hardware claim; pr_readiness=experimental.

## Evidence and handoff

Remote controls `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/commands/op022-sampling-direct-20261019`: inspection.json, candidate.json/candidate.patch, test_direct.py and apply_check.py. Native log `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/logs/op022-direct-cpu.log`; receipt `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/op022-direct-adapter.json`. Full paths and SHA values are in state.yml. The candidate JSON contains exact before/after bytes for a scoped rollback; do not reset any repository or revert MoE/library changes.

Current workers keep already imported code. User restarts when appropriate to load this direct adapter, then verifies the new service's graph/HTTP path and completes the same steady-state warmup before a performance comparison. No startup or warmup code was changed in this round. op021 dispatch ownership is superseded; generic FlagGems integration remains. This refactor does not justify a SOP revision.
