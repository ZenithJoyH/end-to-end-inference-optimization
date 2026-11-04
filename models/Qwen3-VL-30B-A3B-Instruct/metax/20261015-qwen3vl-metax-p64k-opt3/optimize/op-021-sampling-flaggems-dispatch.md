# op021: Sampling integration belongs to FlagGems dispatch

Saved in `qwen3vl-p64k-opt-20261015` on mx-59. **User restart pending**; no service was started, restarted or signalled, and no inference/GPU test was run. The active opt8 benchmark was preserved.

## Request and final ownership

The user requested on 2026-10-19 that the existing FlagGems-vllm top-k/top-p integration live in Plugin FlagGems rather than vendor/metax. This continues the already isolated case; image `sha256:7f911fa80c3968dac43376cf59cd5b5d9b53db28364f8ecec78a6dd2a468d59c` and mounts match the verified op020 environment. `/workspace` repositories are private to the target container. Source container is untouched.

The chain is now `register_model -> common ops/sampler shim -> CachedOp(apply_top_k_top_p) -> default.flagos -> FlagGemsBackend -> flaggems_vllm.apply_top_k_top_p`. Existing library runtime selection still chooses the MetaX implementation. No hardware/model-name tests are added to the common caller. MetaX vendor sampling file is restored exactly to Plugin HEAD and contains only its original PyTorch/no-Triton compatibility behavior.

The common shim captures the previous native/platform filter and passes it as `native_filter` to both backend implementations. This keeps reference/disabled/unsupported paths from recursing through the patched vLLM global and preserves non-target native samplers. The FlagGems adapter catches only the library's pre-mutation metadata NotImplementedError locally, so an unsupported shape does not permanently mark default.flagos failed. Other failures follow existing dispatch strict/fallback semantics. Registration uses the existing library switch, FlagGems whitelist/blacklist and default.flagos policies; no new environment variable is introduced. Repeat installation is idempotent; no-filter calls preserve identity without dispatch.

Modified scope: common entry and general-plugin install, FlagGems backend/adapter/registration, reference backend/registration, restoration of the original vendor patch. No Worker, vLLM, operator library, MoE config, GEMM2, gems-opt, startup script or root library __all__ changes. Four source inventories were compared against the frozen inspection and only these eight Plugin files differ.

## Validation and limits

20 CPU contract cases passed using actual Plugin CachedOp, manager, policy, registrations and sampler adapter, with external platform/library imports mocked and all GPU visibility disabled. Each test asserts torch.cuda is not initialized. Coverage includes k/p/k+p object identity; default.flagos/reference/per-op reference; disabled/blacklisted registration; metadata fallback followed by a supported call; policy cache invalidation; strict runtime/import errors; existing non-strict failed-implementation fallback; no-filter identity; repeated install/module reload; original MetaX compatibility and general-plugin hook placement. This is routing evidence, not hardware numerical evidence.

All eight files passed syntax and whitespace checks. Lint: `not_run`; ruff unavailable; syntax/whitespace checks passed; Plugin config excludes vllm_fl/**.

Initial CPU harness attempts are retained: system Python lacked pytest; an early retry compared against pre-change fingerprints; mock setup omitted VENDOR_DEVICE_MAP/eager impl package isolation; and the disabled-op import guard incorrectly included pre-existing global library registration for other ops. These are measurement/harness failures, with 12passed/8failed in r4 before the isolation fix. The same product patch was used throughout and all20 final cases pass. No numerical mismatch or kernel failure was observed by these tests.

Full minimal-regression remains **incomplete**: new graph capture/replays, smoke/C8 and actual HTTP library dispatch after user restart were not run, to respect user ownership and the active benchmark. Historical op020 numerical/graph results belong to the earlier integration and are not relabelled as new validation. Formal GPQA remains deferred by user. No E2E timing or performance gain is claimed. Other-platform hardware and complete optional-dependency imports remain untested; pr_readiness=experimental.

## Handoff and rollback

Current service identity was unchanged by this operation. Already running workers keep their old imported code; user restart is required to load the common dispatch path. No new startup action or warmup code was added. After restart, kernel/JIT warmup and production graph/HTTP proof are still required for comparable steady-state timing.

Remote controls: `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/commands/op021-sampling-dispatch-20261019`. `candidate.json` contains before/after bytes, `candidate.patch` is the scoped diff, `inspection.json` freezes original four-repository inventories. Test scripts and all failed logs/receipts remain external. Final CPU receipt: `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/op021-dispatch-cpu-r5.json`; final source/identity receipt: `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/op021-refactor.json`. Exact SHA values are in state.yml.

Rollback restores only each changed file's frozen before bytes (removing only newly created files after identity checks), then a user-managed restart reloads the old integration. Do not reset any repository or revert MoE/library/gems-opt changes. The old op020 ownership record is superseded only for Plugin routing; its native evidence remains historical. No SOP change is justified by this scoped ownership refactor.
