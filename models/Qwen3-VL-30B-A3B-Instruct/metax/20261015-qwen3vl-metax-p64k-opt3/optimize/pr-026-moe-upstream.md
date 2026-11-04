# pr026: Submit retained MetaX fused MoE optimization

User explicitly authorized committing the container's fused_moe optimization to `ZenithJoyH/FlagGems-vllm:main` and opening a PR against `flagos-ai/FlagGems-vllm`. This is a publication task; do not restart services or expand into a new optimization round.

## Frozen submission contract

| Item | Scope |
|---|---|
| Source | mx-59 isolated qwen3vl-p64k-opt-20261015, /workspace/FlagGems-vllm; HEAD f6fdb9b120787e12892ac67e54979cbf829c7d64 |
| Editable/published | Only src/flaggems_vllm/runtime/backend/_metax/ops/fused_moe.py in an independent temporary submission copy |
| Read-only | Container source/index/HEAD, sampling files and exports, Plugin, gems-opt, vLLM, source container, model service |
| Build | Existing pure-Python operator; syntax/AST and configured Black/isort/flake8, no reinstall |
| Validation | Isolated actual host functions, nearest-M and stage selection, shape/dtype fallback, batch-invariant/cache/copy behavior, mocked device shared-memory capacities, unchanged Triton kernels |
| Benchmark/profiler | No new benchmark or profiler; no new speedup claim; historical E2E does not bind publication automatically |
| Timeout | CPU validation120s, lint60s; no service/GPU work planned |
| Autotune exemption | Existing MetaX-only user-requested inline measured configuration; no NVIDIA/config-search/kernel changes |
| Integration | Existing operator API/exports unchanged. User previously requested no new MoE test/perf files in the operator repo; reusable review validation stays in remote case artifacts |

The source has one95-line MoE diff (86 additions/9 removals): stage-specific inline E128/logicalN384 half configurations, GEMM2 selecting its stage even for embedded configs, batch-invariant table bypass, plus actual per-device shared-memory-aware default stage/paired-kernel selection. Existing Triton arithmetic is unchanged; new runtime calls read device metadata only. No vLLM import or external JSON loading is added.

## Semantics and paths

| Contract/path | Behavior and proof |
|---|---|
| Existing API | fused_experts_impl signatures, input/output dtype, shape, layout, alias/in-place, routing and activation arithmetic unchanged |
| Tuned | MetaX E128/logicalN384 dtype None/fp16/bf16, no active block pair; separate G1/G2 nearest-M maps |
| General | Original embedded/default selection; default stages now respect actual device capacity and account for paired weights/FP32 bytes |
| Special | VLLM_BATCH_INVARIANT bypasses measured tables; cache and copied config behavior checked |
| Unsupported/autograd | Existing error paths unchanged; forward inference only, training not validated |
| No Torch compute fallback | No new compute/copy/cast or test import; metadata-only device-property query |

Fork main is46a81d39732af0e1b0ef6c474e500591dfb2d124 and25commits behind upstream main b4d3382bb04da4e0ab444849697865b4d5fcd86e, with zero unique commits. The MoE baseline blob10c2a7879fb3a42a470a7c5c9883ec9ddf8417ab is identical in container HEAD, fork main and upstream main. Preserve existing fork history with a normal fast-forward one-file commit; do not force push or sync unrelated changes. Record an expected-head lease and inspect again before publication.

PR will state exact host/static checks and incomplete fresh hardware/graph/model acceptance; prepare as draft if these remain unmeasured. Existing numerical and graph results are historical and not silently rebound. No new end-to-end benefit is claimed.

## Submission candidate and checks

The one-file candidate is formatted using target CI versions from the repository root. This only reflows the shared-memory estimate; full AST equals the installed source. Candidate SHA256`bc655dbc521538710b054c2af8f496ed45d0d214f0d71e9ea3fdf8731aa7605b`, Git blob`6a6221a027d936ef59bee8acca6f0d6ea03ef759`. Diff is84additions/9removals in one file.393240actual host-selector comparisons against saved original JSON passed;896mocked device-capacity checks and per-device cache isolation passed. All5existing Triton kernels and27other existing functions have unchanged AST. Black24.8.0/isort5.12.0/flake8 7.1.0, syntax and whitespace checks passed. Fresh numerical hardware, graph and E2E remain not_run for this PR revision.

Exact before/after source, validator, result, PR body and publication plan were saved before any GitHub mutation under `/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/commands/pr026-moe-upstream-20261019`. All hashes are in state.yml. The plan limits publishing to one file and one normal commit parented by the inspected fork head, uses a non-force expected-head update, and creates a Draft PR. No new source/test/perf files are added elsewhere. Publication is pending.

## Published result

Fork main was normally fast-forwarded from46a81d39732af0e1b0ef6c474e500591dfb2d124 to [808cedfc36589430fbd97fcd483bfbf0f4eff74b](https://github.com/ZenithJoyH/FlagGems-vllm/commit/808cedfc36589430fbd97fcd483bfbf0f4eff74b), using force=false and an expected-head lease. Created and attached [upstream Draft PR943](https://github.com/flagos-ai/FlagGems-vllm/pull/943), head ZenithJoyH:main to upstream main b4d3382bb04da4e0ab444849697865b4d5fcd86e. Verified one commit, one file,84additions/9removals and mergeable=true. There is no merge conflict.

Code style and CI target selection passed. rule-check fails on an existing upstream mismatch: tests/test_fused_moe.py declares pytest.mark.fused_moe in module-level pytestmark, while tools/ci_checks/check_operator_markers.py only recognizes function decorators. The checker log confirms other registry/export/aten/benchmark checks passed. Neither the existing test nor checker is modified, preserving the requested MoE-only scope and no new tests/perf files. The exact CI failure and pending MetaX jobs are documented in the PR body. Hardware jobs are not claimed as passed.

Publication is complete; pr_readiness remains experimental because this exact revision has no new hardware/graph/E2E gate and the inherited CI-rule mismatch remains. All five runtime working-tree entries, container HEAD and source hash were verified unchanged before publishing. No service restart, new GPU job, upstream synchronization, force push or container index mutation was performed. Only formatting of the submission copy differs; its AST equals the installed MoE source. The source container is untouched.

Final sanitized receipt and revised PR body were archived alongside the initial controls, with hashes in state.yml. A future rollback, if requested, uses a normal revert commit on the fork and a separate PR decision; do not reset or force-push main. This publication makes no new cumulative performance or accuracy claim.
