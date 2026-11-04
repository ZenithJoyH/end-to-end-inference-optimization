# 20261015-qwen3vl-metax-p64k-opt3 / optimize

op020: [sampling integration](op-020-sampling-reconnect.md) ready in isolated8111; numeric/graph/actualHTTP library route passed, current worker shapes warmed; MoE/GEMM2/gems-opt/start script unchanged. E2E pending user, GPQA deferred.

2026-10-18当前：[op019大M G1对照](op-019-moe-gemm1-prefill-profile.md)：精确P64 B/C/R 71.944/76.840/72.080TPS，C/B+6.81%，漂移+0.19%，native passed，保留candidate。小M/G2/采样/gems-opt保持，数值/graph通过，正式精度及四场景验收未完成。

2026-10-17当前：[op018 GEMM1限域对照](op-018-moe-gemm1-decode-profile.md)：P4K B/C/R 899.66/940.41/898.50TPS，C/B+4.53%，漂移-0.13%，原生passed，保留candidate。G2固定、采样参考和gems-opt不变；数值/graph通过，P64/正式精度未验收。

<!-- e2e:summary:start -->

- 案例：20261015-qwen3vl-metax-p64k-opt3
- 当前状态：pr943-ready-for-review-source8111-restored
- 当前候选：Same retained MoE G1/G2 values inline in MetaX operator + gems-opt + direct common sampling adapter
- 下一步：Await maintainer review of PR943. Original8111/opt9 restored unchanged; dedicated validation service stopped. No further runtime changes or formal accuracy/performance claims.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| diag-001-p64k-phase-kv | route-to-framework-lifecycle-test | p65536-d1024-c64-n128 | [diag-001-p64k-phase-kv.md](diag-001-p64k-phase-kv.md) |
| fw-001-p64k-admission | reverted; cap8/graph8 not retained, main gain below5% | p65536-d1024-c64-n128 | [fw-001-p64k-admission.md](fw-001-p64k-admission.md) |
| fw-002-p64k-kv-budget | retained in independent optimization container after original target B/C/R passed; source unchanged; performance_only | p65536-d1024-c64-n128 | [fw-002-p64k-kv-budget.md](fw-002-p64k-kv-budget.md) |
| op-003-moe-config-plugin | Retain new env entry in independent container and export in user start-model.sh; own8111 graph service reloaded, source not written back | p65536-d1024-c64-n128 | [op-003-moe-config-plugin.md](op-003-moe-config-plugin.md) |
| maint-004-plugin-024plugin-opt | Use requested024plugin-opt HEAD08da21cb39601752040196232b60a152382c0f8f as subsequent Plugin baseline; retain only JSON/package-data adaptation and existing integration switch in launch script | p65536-d1024-c64-n128 | [maint-004-plugin-024plugin-opt.md](maint-004-plugin-024plugin-opt.md) |
| op-005-pr595-shared-moe-config | Retain exact PR595 JSON and native reader delegation with FlagOS compute on user-confirmed gems-opt; no performance or formal accuracy claim | p65536-d1024-c64-n128 | [op-005-pr595-shared-moe-config.md](op-005-pr595-shared-moe-config.md) |
| op-006-independent-moe-json-loader | Keep library-owned external JSON loader and shared PR595 file, remove two MoE reverse imports; standalone and numerical/graph regressions passed | p65536-d1024-c64-n128 | [op-006-independent-moe-json-loader.md](op-006-independent-moe-json-loader.md) |
| maint-007-remove-added-moe-tests | completed | — | [maint-007-remove-added-moe-tests.md](maint-007-remove-added-moe-tests.md) |
| op-008-plugin-topk-topp-integration | Keep policy-aware MetaX library sampling integration, retain existing fallback for NotImplementedError; no kernel or MoE config changes | p65536-d1024-c64-n128 | [op-008-plugin-topk-topp-integration.md](op-008-plugin-topk-topp-integration.md) |
| maint-009-remove-sampling-test-perf | Removed only two new FlagGems-vllm sampling test/perf assets with backups; preserve existing __all__ and new public API entry | — | [maint-009-remove-sampling-test-perf.md](maint-009-remove-sampling-test-perf.md) |
| maint-010-root-export-cleanup | Removed redundant new root __all__ item from active private copy; root file now exactly matches HEAD; ops/backend exports and explicit Plugin API preserved | — | [maint-010-root-export-cleanup.md](maint-010-root-export-cleanup.md) |
| maint-011-flaggems-vllm-convergence | Retain only seven necessary source changes relative HEAD; six files simplified this round. Preserve kernels, user JSON and prior test/perf removals. | — | [maint-011-flaggems-vllm-convergence.md](maint-011-flaggems-vllm-convergence.md) |
| op-012-sampling-call-rollback | Retain requested original reference callback; no performance recovery claim because reverse comparison failed drift/spread gates | p4096-d1024-c64-n128 | [op-012-sampling-call-rollback.md](op-012-sampling-call-rollback.md) |
| diag-013-sampling-variance | diagnosis-and-comparison-complete; retain initial reference route as requested | p4096-d1024-c64-n128 | [diag-013-sampling-variance.md](diag-013-sampling-variance.md) |
| diag-014-opt4-opt6-gap | Keep user opt6 environment untouched; prioritize MoE configuration semantics ablation after manual benchmark ends | — | [diag-014-opt4-opt6-gap.md](diag-014-opt4-opt6-gap.md) |
| op-015-moe-gemm2-stage1-json | Retain GEMM2 stage1 via optional Plugin gemm2 directory. Base PR595 JSON, all GEMM1 parameters, reference sampler, gems-opt, sort and other settings unchanged. | p4096-d1024-c64-n128 | [op-015-moe-gemm2-stage1-json.md](op-015-moe-gemm2-stage1-json.md) |
| diag-016-opt7-stage1-gap | No source/config/service change; stage1-only has not restored manual E2E. Prepare exact old GEMM2 decode profile and stage3 controls externally, not applied. | p4096-d1024-c64-n128 | [diag-016-opt7-stage1-gap.md](diag-016-opt7-stage1-gap.md) |
| op-017-moe-gemm2-decode-profile | Retain only complete old G2 geometry M8..64 via existing Plugin stage JSON; keep base/G1/sampling/gems-opt/other settings | p4096-d1024-c64-n128 | [op-017-moe-gemm2-decode-profile.md](op-017-moe-gemm2-decode-profile.md) |
| op-018-moe-gemm1-decode-profile | Retain only bounded GEMM1 M8..64 old geometry in Plugin root JSON | — | [op-018-moe-gemm1-decode-profile.md](op-018-moe-gemm1-decode-profile.md) |
| op-019-moe-gemm1-prefill-profile | Retain only root G1 largeM warp8/group1 JSON | — | [op-019-moe-gemm1-prefill-profile.md](op-019-moe-gemm1-prefill-profile.md) |
| op-020-sampling-reconnect | Keep only MetaX Plugin sampler change; current graph service warmed for user test | — | [op-020-sampling-reconnect.md](op-020-sampling-reconnect.md) |
| op-021-sampling-flaggems-dispatch | Retain source refactor for user restart; hardware/model validation incomplete | — | [op-021-sampling-flaggems-dispatch.md](op-021-sampling-flaggems-dispatch.md) |
| op-022-sampling-direct-adapter | Retain direct adapter on disk; user owns restart; full service regression pending | — | [op-022-sampling-direct-adapter.md](op-022-sampling-direct-adapter.md) |
| diag-023-native-moe-gemm2-feasibility | User cancelled native GEMM2 adaptation; no implementation or restart | — | [diag-023-native-moe-gemm2-feasibility.md](diag-023-native-moe-gemm2-feasibility.md) |
| op-024-moe-inline-config | Source migration complete, inline retained stage tables; full runtime validation pending user restart | — | [op-024-moe-inline-config.md](op-024-moe-inline-config.md) |
| maint-025-zombie-cleanup | bounded-reap-through-idle-PID1-no-restart | maintenance-no-performance-measurement | [maint-025-zombie-cleanup.md](maint-025-zombie-cleanup.md) |
| pr-026-moe-upstream | submit-current-MetaX-MoE-only | publication-no-new-performance-measurement | [pr-026-moe-upstream.md](pr-026-moe-upstream.md) |
| pr-027-marker-gpu-graph | ready-after-marker-and-GPU-graph-pass | pr943-correctness-graph-no-performance-comparison | [pr-027-marker-gpu-graph.md](pr-027-marker-gpu-graph.md) |
| review-028-moe-pr-scope | needs_revision before mark-ready; runtime restored | read-only-PR-review | [review-028-moe-pr-scope.md](review-028-moe-pr-scope.md) |
| pr-029-moe-scope-cleanup | publish-and-mark-ready | pr943-maintenance | [pr-029-moe-scope-cleanup.md](pr-029-moe-scope-cleanup.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p65536-d1024-c16-n16 | baseline | output_throughput | 67.55284493748718 | token/s | milestone/performance_only; failed gain threshold; reverted |
| p65536-d1024-c16-n16 | candidate | output_throughput | 67.78044546384557 | token/s | milestone/performance_only; failed gain threshold; reverted |
| p65536-d1024-c16-n16 | revert | output_throughput | 67.57673942194891 | token/s | milestone/performance_only; failed gain threshold; reverted |
| p65536-d1024-c16-n16 | baseline | p99_ttft_ms | 196477.7410311624 | ms | milestone/performance_only; failed gain threshold; reverted |
| p65536-d1024-c16-n16 | candidate | p99_ttft_ms | 195659.63234053925 | ms | milestone/performance_only; failed gain threshold; reverted |
| p65536-d1024-c16-n16 | revert | p99_ttft_ms | 196121.86023294926 | ms | milestone/performance_only; failed gain threshold; reverted |
| p65536-d1024-c16-n16 | baseline | p99_tpot_ms | 112.7138475929355 | ms | milestone/performance_only; failed gain threshold; reverted |
| p65536-d1024-c16-n16 | candidate | p99_tpot_ms | 111.88898256516497 | ms | milestone/performance_only; failed gain threshold; reverted |
| p65536-d1024-c16-n16 | revert | p99_tpot_ms | 112.30083708155205 | ms | milestone/performance_only; failed gain threshold; reverted |
| p65536-d1024-c16-n16 | baseline | p99_itl_ms | 1547.2471603844315 | ms | milestone/performance_only; failed gain threshold; reverted |
| p65536-d1024-c16-n16 | candidate | p99_itl_ms | 1549.6351448819041 | ms | milestone/performance_only; failed gain threshold; reverted |
| p65536-d1024-c16-n16 | revert | p99_itl_ms | 1550.6234006397426 | ms | milestone/performance_only; failed gain threshold; reverted |
| p65536-d1024-c8-n8 | baseline | output_throughput | 66.68025287675601 | token/s | milestone/performance_only passed; original C64/N128 pending |
| p65536-d1024-c8-n8 | candidate | output_throughput | 75.79637699154189 | token/s | milestone/performance_only passed; original C64/N128 pending |
| p65536-d1024-c8-n8 | revert | output_throughput | 67.05947538911373 | token/s | milestone/performance_only passed; original C64/N128 pending |
| p65536-d1024-c8-n8 | baseline | p99_ttft_ms | 71643.34908316843 | ms | milestone/performance_only passed; original C64/N128 pending |
| p65536-d1024-c8-n8 | candidate | p99_ttft_ms | 71426.7881740909 | ms | milestone/performance_only passed; original C64/N128 pending |
| p65536-d1024-c8-n8 | revert | p99_ttft_ms | 71234.82868913561 | ms | milestone/performance_only passed; original C64/N128 pending |
| p65536-d1024-c8-n8 | baseline | p99_tpot_ms | 95.8919092436992 | ms | milestone/performance_only passed; original C64/N128 pending |
| p65536-d1024-c8-n8 | candidate | p99_tpot_ms | 94.60663349141903 | ms | milestone/performance_only passed; original C64/N128 pending |
| p65536-d1024-c8-n8 | revert | p99_tpot_ms | 95.36793548823175 | ms | milestone/performance_only passed; original C64/N128 pending |
| p65536-d1024-c8-n8 | baseline | p99_itl_ms | 1393.055718401447 | ms | milestone/performance_only passed; original C64/N128 pending |
| p65536-d1024-c8-n8 | candidate | p99_itl_ms | 1374.6006898023188 | ms | milestone/performance_only passed; original C64/N128 pending |
| p65536-d1024-c8-n8 | revert | p99_itl_ms | 1376.2584668304771 | ms | milestone/performance_only passed; original C64/N128 pending |
| p65536-d1024-c64-n128 | baseline | output_throughput | 68.77173937571385 | token/s | historical pre-op003 source identity; original target one measured round after declared warm; targeted/performance_only |
| p65536-d1024-c64-n128 | candidate | output_throughput | 76.27851497242928 | token/s | historical pre-op003 source identity; original target one measured round after declared warm; targeted/performance_only |
| p65536-d1024-c64-n128 | revert | output_throughput | 68.65713036941878 | token/s | historical pre-op003 source identity; original target one measured round after declared warm; targeted/performance_only |
| p65536-d1024-c64-n128 | baseline | p99_ttft_ms | 917727.6924517938 | ms | historical pre-op003 source identity; original target one measured round after declared warm; targeted/performance_only |
| p65536-d1024-c64-n128 | candidate | p99_ttft_ms | 812555.9979986772 | ms | historical pre-op003 source identity; original target one measured round after declared warm; targeted/performance_only |
| p65536-d1024-c64-n128 | revert | p99_ttft_ms | 919620.0420580247 | ms | historical pre-op003 source identity; original target one measured round after declared warm; targeted/performance_only |
| p65536-d1024-c64-n128 | baseline | p99_tpot_ms | 115.60785086680738 | ms | historical pre-op003 source identity; original target one measured round after declared warm; targeted/performance_only |
| p65536-d1024-c64-n128 | candidate | p99_tpot_ms | 96.52425112699832 | ms | historical pre-op003 source identity; original target one measured round after declared warm; targeted/performance_only |
| p65536-d1024-c64-n128 | revert | p99_tpot_ms | 115.46880431113654 | ms | historical pre-op003 source identity; original target one measured round after declared warm; targeted/performance_only |
| p65536-d1024-c64-n128 | baseline | p99_itl_ms | 1548.425315637141 | ms | historical pre-op003 source identity; original target one measured round after declared warm; targeted/performance_only |
| p65536-d1024-c64-n128 | candidate | p99_itl_ms | 1559.6350834798068 | ms | historical pre-op003 source identity; original target one measured round after declared warm; targeted/performance_only |
| p65536-d1024-c64-n128 | revert | p99_itl_ms | 1554.2309419531375 | ms | historical pre-op003 source identity; original target one measured round after declared warm; targeted/performance_only |
| p4096-d1024-c64-n128 | baseline | output_throughput | 959.7011200189432 | token/s | Observed median2; comparison incomplete from R variation/drift, not accepted recovery or causal speedup |
| p4096-d1024-c64-n128 | candidate | output_throughput | 901.5429417702901 | token/s | Observed median2; comparison incomplete from R variation/drift, not accepted recovery or causal speedup |
| p4096-d1024-c64-n128 | revert | output_throughput | 735.0341150695159 | token/s | Observed median2; comparison incomplete from R variation/drift, not accepted recovery or causal speedup |
| p4096-d1024-c64-n128 | baseline | p99_ttft_ms | 18390.858238823712 | ms | Observed median2; comparison incomplete from R variation/drift, not accepted recovery or causal speedup |
| p4096-d1024-c64-n128 | candidate | p99_ttft_ms | 18562.71285568364 | ms | Observed median2; comparison incomplete from R variation/drift, not accepted recovery or causal speedup |
| p4096-d1024-c64-n128 | revert | p99_ttft_ms | 18418.084403043613 | ms | Observed median2; comparison incomplete from R variation/drift, not accepted recovery or causal speedup |
| p4096-d1024-c64-n128 | baseline | p99_tpot_ms | 65.84078578144141 | ms | Observed median2; comparison incomplete from R variation/drift, not accepted recovery or causal speedup |
| p4096-d1024-c64-n128 | candidate | p99_tpot_ms | 69.59988711900255 | ms | Observed median2; comparison incomplete from R variation/drift, not accepted recovery or causal speedup |
| p4096-d1024-c64-n128 | revert | p99_tpot_ms | 116.06355976654748 | ms | Observed median2; comparison incomplete from R variation/drift, not accepted recovery or causal speedup |
| p4096-d1024-c64-n128 | baseline | p99_itl_ms | 579.6282935934141 | ms | Observed median2; comparison incomplete from R variation/drift, not accepted recovery or causal speedup |
| p4096-d1024-c64-n128 | candidate | p99_itl_ms | 583.6572258733213 | ms | Observed median2; comparison incomplete from R variation/drift, not accepted recovery or causal speedup |
| p4096-d1024-c64-n128 | revert | p99_itl_ms | 580.4978430969641 | ms | Observed median2; comparison incomplete from R variation/drift, not accepted recovery or causal speedup |

<!-- e2e:summary:end -->
