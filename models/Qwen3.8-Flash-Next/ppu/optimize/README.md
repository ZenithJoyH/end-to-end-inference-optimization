# Optimize

## 优化点文档索引

2026-09-21 规则审查：下文保留各轮历史结果与当时决定。继承的 GPQA 85.86% < 88% 阻塞尚不能由最小回归解除；
后续新增性能改动前先进入精度定位，或核验并记录用户对诊断性探索的明确授权、范围与有效期。
本次整理没有停止远程服务，也没有重新签发精度/性能验收。

稳定链接对应 state.yml 的 document 字段；历史短文件名显式映射，不复制同一优化点的文档。索引不另存性能数值，详细效果见单点文档及下方总览。

专项诊断：[QSA/TopK 同步](diag-001-qsa-topk-sync-attribution.md)、[post-op010 同步](diag-002-post-op010-stream-sync-attribution.md)、
[P4K profiling](prof-005-p4k-post-op010.md)、[主机交接空隙](prof-006a-device-idle-host-handoff.md)。

| 实验 | 分类 | 原记录状态 | 决定 |
|---|---|---|---|
| [fw-001-max-num-seqs-64-screen](fw-001-max-num-seqs-64-screen.md) | framework | complete | retain_as_pareto_screening_candidate_not_formal |
| [fw-002-max-num-seqs-48-screen](fw-002-max-num-seqs-48-screen.md) | framework | complete | retain_as_diagnostic_pareto_reference_not_formal |
| [fw-003-maxseq64-max-batched-tokens2048](fw-003-maxseq64-max-batched-tokens2048.md) | framework | complete | reverted_failed_prefrozen_guard_recovery_threshold |
| [op-001-qsa-static-score-columns](op-001-qsa-static-score-columns.md) | operator/improve | complete | defer_service_integration_until_safe_long_sequence_graph_bucketing |
| [op-002-fused-moe-block-m](op-002-fused-moe-block-m.md) | operator/improve | complete | retain_decode_only_candidate_reject_prefill_variant |
| [op-003-fused-moe-block-m-service](op-003-fused-moe-block-m-service.md) | operator/improve | complete | retain_p1k_candidate_pending_minimal_accuracy_regression_and_long_scenarios |
| [fw-004-p4k-max-batched-tokens8192](fw-004-p4k-max-batched-tokens8192.md) | framework | complete | reverted_failed_tail_latency_and_warmup_stability_guards |
| [fw-005-p4k-max-batched-tokens6144](fw-005-p4k-max-batched-tokens6144.md) | framework | complete | reverted_failed_throughput_tail_latency_and_warmup_stability_guards |
| [op-004-qsa-existing-dot-replacement](op-004-qsa-existing-dot-replacement.md) | operator/replace | complete | rejected_slower_than_current_scalar_path |
| [fw-006-p4k-long-prefill-threshold2048](fw-006-p4k-long-prefill-threshold2048.md) | framework | complete | rejected_reverted_failed_primary_guard_and_warmup_stability |
| [op-005-qsa-row-range-topk](op-005-qsa-row-range-topk.md) | operator/improve | complete | rejected_reverted_below_service_gain_threshold |
| [op-006-qsa-static-bound8448](op-006-qsa-static-bound8448.md) | framework_plus_operator/improve | rejected_rolled_back_after_formal_accuracy | removed_from_current_candidate |
| [op-007-qsa-p16k-specific-bound-headroom](op-007-qsa-p16k-specific-bound-headroom.md) | operator/improve | complete | retain_diagnostic_reject_global_deployment |
| [op-008-qsa-runtime-score-bound](op-008-qsa-runtime-score-bound.md) | framework_plus_operator/improve | inactive_after_parent_bound_rollback | guarded_source_retained_but_runtime_unbounded |
| [op-009-fused-moe-drain-block-m](op-009-fused-moe-drain-block-m.md) | operator/improve | complete | rejected_and_reverted_insufficient_end_to_end_gain |
| [op-010-native-mm-provider](op-010-native-mm-provider.md) | operator/replace | complete | retain_p4k_d1024_performance_only |
| [op-011-m64-gemm2-bn128](op-011-m64-gemm2-bn128.md) | operator/improve | complete | rejected_before_service_integration |
| [op-012-m64-gemm1-silu-fusion](op-012-m64-gemm1-silu-fusion.md) | operator/improve | complete | rejected_before_service_integration |
| [op-013-shape-selective-mm-provider](op-013-shape-selective-mm-provider.md) | operator/replace | stopped_before_implementation | no_go_insufficient_production_shape_evidence_and_weighted_gain |
| [op-014-repeat-interleave-output-size](op-014-repeat-interleave-output-size.md) | framework | rejected_and_reverted | no_go_same_device_abr_primary_gain_below_one_percent |
| [fw-007-request-group-index-put-side-probe](fw-007-index-put-index-fill-sync.md) | framework | stopped_before_service_implementation | no_go_side_path_not_prof005_target |
| [fw-009-gdn-prefill-bool-index-sync](fw-009-gdn-initial-state-bool-index.md) | framework | stopped_before_service_implementation | no_go_predicted_p4k_gain_below_one_percent |
| [fw-008-common-slot-graph-host-sync](fw-008-common-slot-graph-host-sync.md) | framework | rejected_and_reverted | no_go_p4k_d128_primary_gain_below_one_percent |
| [op-015-qsa-sparse-gqa-group3-literal4](op-015-qsa-sparse-gqa-group3.md) | operator/improve | stopped_before_service_implementation | no_go_production_rows4096_regression |
| [fw-010-ring-allreduce-causal-control](fw-010-ring-allreduce-causal-control.md) | framework | stopped_before_service_implementation | no_go_simple_protocol_regression |
| [op-016-moe-splitk-reduction-frontier](op-016-moe-splitk-reduction-frontier.md) | operator/improve | stopped_before_microbenchmark | no_go_complete_transaction_upper_bound_below_eight_percent |
| [fw-011-p4k-scheduler-framework-frontier](fw-011-p4k-scheduler-framework-frontier.md) | framework | stopped_before_experiment | no_go_no_new_equivalent_single_variable_candidate |
| [op-017-qsa-block-centric-traversal-frontier](op-017-qsa-algorithmic-frontier.md) | operator/improve | stopped_before_microbenchmark | no_go_no_credible_eight_percent_rows4096_bound |
| [op-018-qsa-selected-set-overlap](op-018-qsa-selected-set-overlap.md) | operator/improve | complete | passed_overlap_gate_proceed_to_complete_transaction_microbenchmark |
| [op-019-qsa-r4-union-mask](op-019-qsa-r4-union-mask.md) | operator/improve | stopped_before_performance_timing | no_service_integration_eager_dynamic_precondition_invalid_graph_gate_not_reached |
| [op-020-qsa-producer-integrated-r4-rows64](op-020-qsa-producer-integrated-r4.md) | operator/improve | rows64_single_graph_correctness_passed | proceed_only_to_real_p4k_producer_fixture_and_rows4096_correctness_no_timing_yet |
| [op-021-real-p4k-qsa-producer-fixture](op-021-real-p4k-qsa-producer-fixture.md) | operator/diagnostic-prerequisite | complete | passed_real_prefill_and_mixed_producer_replay_proceed_to_op020_rows4096_correctness_no_timing_yet |
| [op-020-real-p4k-rows4096-correctness](op-020-qsa-producer-integrated-r4.md) | operator/improve | passed_correctness_only | proceed_to_separate_op022_complete_consumer_transaction_timing_no_service_integration |
| [op-022-qsa-r4-complete-consumer-transaction](op-022-qsa-r4-complete-consumer-transaction.md) | operator/improve | no_go | stopped_after_prefill_eager_and_graph_regressed_over_32_percent_mixed_not_run |
| [op-023-p16k-native-mmout-provider](op-023-p16k-native-mmout-provider.md) | operator/replace | complete_passed_d128 | retain_native_mmout_for_p16k_current_combination_do_not_expand_d1024_from_this_milestone |
| [op-027-current-service-native-mmout](op-027-current-service-native-mmout.md) | operator/replace | complete_passed_milestone_accuracy_pending | Current acc-011 P16K/D128 A/B/R passed: native `mm_out` +2.7365% output/total throughput vs A, A/R drift 0.0878%; original 8010 restored, candidate not deployed pending precision and full-scenario checks |
| [perf-016-current-acc011-p16k-three-phase-entry](perf-016-current-acc011-p16k-three-phase-entry.md) | framework/diagnostic-baseline | complete_three_phase_scenario_entry_performance_only | Current-config Prefill 5713.816 total tok/s, Decode 181.107 output tok/s, Mixed 182.540 output tok/s medians; 3+3 each, zero failures, original 8010 restored |
| [fw-016-p16k-maxseq32-to64-current-acc011](fw-016-p16k-maxseq32-to64-current-acc011.md) | framework | incomplete_rejected_no_gain_restored | A/B 3+3 complete: +0.354% output throughput, below frozen +1%; R interrupted after graph replay, no full comparator; 8010 restored, do not deploy maxseq64 |
| [perf-015-p16k-post-rb001-unbounded-entry](perf-015-p16k-post-rb001-unbounded-entry.md) | framework/diagnostic-baseline | complete_three_phase_historical_identity | Historical maxseq64/tuned-MoE/native-mmout Prefill/Decode/Mixed all complete; 5813.266 input+output, 184.497 output, 239.972 output tok/s respectively; not current acc011 baseline |
| [fw-015-length-aware-dual-qsa-routing](fw-015-length-aware-dual-qsa-routing.md) | framework | planned_protocol_only | fail_closed_short_request_bound_plus_unbounded_long_request_replica |
| [op-024-p16k-qsa-graph-score-bound-4352](op-024-p16k-qsa-graph-score-bound-4352.md) | operator/improve | complete_valid_failed_superseded_control | reject_4352; later rb-001 removes 8448 too |
| [prof-007-p16k-post-op010-reprofile](prof-007-p16k-post-op010-reprofile.md) | profiling/diagnostic | complete | valid_current_phase_attribution_proceed_parallel_qsa_moe_audits_and_op023_d128_repair |
| [op-025-p16k-qsa-post-prof007-frontier](op-025-p16k-qsa-post-prof007-frontier.md) | operator/improve | stopped_before_microbenchmark | no_go_no_new_complete_qsa_transaction_headroom_above_eight_percent |
| [op-026-p16k-fused-moe-post-prof007-frontier](op-026-p16k-fused-moe-post-prof007-frontier.md) | operator/improve | stopped_before_microbenchmark | no_go_no_distinct_complete_fused_transaction_candidate_above_eight_percent |
| [fw-013-p16k-no-async-scheduling-arrival-control](fw-013-p16k-no-async-scheduling-arrival-control.md) | framework | incomplete_identity_contract | stop_before_candidate_benchmark_do_not_repair_contract_post_measurement |
| [fw-014-p16k-no-async-scheduling-repaired-contract](fw-014-p16k-no-async-scheduling-repaired-contract.md) | framework | complete_valid_failed | reject_no_async_scheduling_keep_current_async |
| [diag-003-p16k-qsa-shape-topk-census](diag-003-p16k-qsa-shape-topk-census.md) | operator/diagnostic | complete_no_go | no_go_no_credible_ge_8pct_complete_qsa_transaction_candidate |
| [diag-004-p16k-qsa-selected-union-telemetry](diag-004-p16k-qsa-selected-union-telemetry.md) | operator/diagnostic | incomplete_output_consistency | stop_no_union_oracle_no_promotion |
| [acc-008-full-gpqa-dual-service-current-candidate](acc-008-full-gpqa-dual-service-current-candidate.md) | accuracy/formal-gate | failed_gate_diagnosis_continues | 167/198; QSA8448 confirmed as truncation contributor but 5-case A/B recovered 0 correct |
| [acc-009-full-gpqa-dual-qsa-unbounded](acc-009-full-gpqa-dual-qsa-unbounded.md) | accuracy/formal-gate | failed_gate_rollback_retained | 174/198, 8 caps; unbounded state retained but still one answer below gate |
| [acc-010-full-gpqa-dual-user-services](acc-010-full-gpqa-dual-user-services.md) | accuracy/formal-gate | failed_gate_root_cause_partially_confirmed | 174/198, 7 caps and 17 completed wrong answers; historical 181/198 PPU run has matching 198 prompts/targets but multiple implementation/config differences; current identical dual services diverge on 4/6 greedy short probes across device groups; doc171 evaluator choice erasure confirmed; gate still failed |
| [accdiag-003-cache-abi-graph-output-20260923](accdiag-003-cache-abi-graph-output-20260923.md) | accuracy/diagnosis | completed_diagnostic_no_accuracy_fix | Same-device A/B/revert: cache mutation ABI changes 5/6 short trajectories but lowers KV capacity 26.8% and does not improve cross-port agreement; graph output view changes none. Both reverted. Later audit found restart omitted original 8000 library path, limiting the zero-code control; accdiag004 corrected the live path against 8010. |
| [accdiag-004-first-divergent-token-20260923](accdiag-004-first-divergent-token-20260923.md) | accuracy/diagnosis | completed_boundary_localized | Corrected 8000 library-path drift introduced by prior restart; original old value unknown. Three matched-service cross-port first splits at tokens 4/56/12 were top-two near-ties (margin ≤0.25), not a proven final-answer regression. |
| [accdiag-005-graph-eager-numerics-20260923](accdiag-005-graph-eager-numerics-20260923.md) | accuracy/diagnosis | completed_execution_mode_boundary_confirmed_short_only | Same-card graph/eager A/B/revert changes all three short trajectories; docs140/168 eager match 8010 graph for 64 tokens, then graph revert restores all three original hashes. No score-level attribution. |
| [accdiag-006-full-decode-vs-piecewise-20260923](accdiag-006-full-decode-vs-piecewise-20260923.md) | accuracy/diagnosis | incomplete_piecewise_startup_failed_full_graph_restored | PIECEWISE-only worker died during memory profiling, so submode comparison has no accuracy data. FULL_AND_PIECEWISE 8000 recovered; fixed probes and C1/C8 passed; 8010 unchanged. |
| [accdiag-007-nv-paired-20260924](accdiag-007-nv-paired-20260924.md) | accuracy/diagnosis | completed_observational_only | Identical 198 prompts/targets; NV 184/198 versus PPU 174/198, but NV uses different adaptation code and 90K versus 60K generation budget. Response outcomes only, not a causal implementation A/B. |
| [accdiag-008-current-output-replay-20260924](accdiag-008-current-output-replay-20260924.md) | accuracy/diagnosis | completed_batch_sensitive_boundary_no_score_cause | Formal HTTP log recovered/paired all 198 reasoning traces. Current-service short probes show a batch-sensitive near-tied token-11 split; 8010 C8-started long reply matched formal doc168 reasoning for 90 tokens yet answered C. Subsequent route recovery showed formal doc168 was on original 8000, so this was cross-endpoint, not a same-instance counterfactual. |
| [accdiag-009-sustained-peer-overlap-20260924](accdiag-009-sustained-peer-overlap-20260924.md) | accuracy/diagnosis | completed_no_wrong_reproduction | Same current 8010 C8 long doc168 replay with only seven peers' budget extended 64→128 tokens answered correct C at 17,329. First split from formal moved token 91→92, but formal actually ran on original 8000. Stop short-peer sweep; gate unchanged. |
| [accdiag-010-formal-route-recovery-20260924](accdiag-010-formal-route-recovery-20260924.md) | accuracy/diagnosis | completed_full198_route_recovered | One-to-one evaluator/proxy log correlation recovers all 198 formal routes. Backend0/8000 scored 87/100 with four caps; backend1/8010 scored 87/98 with three caps. Formal doc168 uniquely routed to 8000; no one-sided service collapse or score change. |
| [accdiag-011-port8000-sustained-cohort-20260924](accdiag-011-port8000-sustained-cohort-20260924.md) | accuracy/diagnosis | incomplete_pre_target_service_failure | Current-8000 cohort replay failed at nine peers from a FlagGems SQLite cache lock; doc168 was never dispatched and has no diagnostic answer. 8000 remains down; formal gate unchanged. |
| [accdiag-012-flaggems-sqlite-cache-lock-20260924](accdiag-012-flaggems-sqlite-cache-lock-20260924.md) | accuracy/diagnosis-output-health | confirmed_service_failure_chain_lock_holder_unconfirmed | Shared SQLite index-autotune cache raised database-is-locked during new-shape benchmark table creation/config lookup; the worker error led to RPC timeout and 8000 shutdown. Exact lock holder and score relevance unproven; no fix or restart. |
| [accfix-001-flaggems-sqlite-cache-safety-20260924](accfix-001-flaggems-sqlite-cache-safety-20260924.md) | accuracy/output-health repair | cache_repair_formal_gate_passed | Private FlagGems patch plus separate WAL DBs; eight-process stress and both ports' C1+2×C9 passed. Full GPQA had no observed SQLite lock; exact original failing cohort not replayed. |
| [acc-011-full-gpqa-dual-cachefix-20260924](acc-011-full-gpqa-dual-cachefix-20260924.md) | accuracy/formal-gate | formal_gate_passed | Run-003: 175/198 = 88.3838% strict-match, 9 caps/8 overlapping timeouts, schema-3 gate passed and checked against both-service manifest. One-answer gain over acc-010 is not causally attributed to the cache repair. |
| [rb-001-qsa-score-bound-rollback](rb-001-qsa-score-bound-rollback.md) | rollback | applied_runtime_and_candidate_decision | QSA score bound removed from current candidate and future launch contract |

镜像谱系和挂载门禁已通过。用户已授权释放全部卡；源容器仍保留。当前优化容器的私有 Plugin writable layer 仍含 op008 的可选实现，但由于不再设置静态 QSA score bound，该路径返回 `None` 并由 FlagGems 使用完整 `capacity`，不计入当前候选。历史 op010 的原生 `mm/mm_out` 性能收益不代表当前 acc-011 服务配置；当前服务是 native `mm`、FlagGems `mm_out`，op027 的 native `mm_out` 只保留为未部署的性能候选。acc-011 在实验前的双 TP8 身份取得 175/198、通过 0.88 阈值；op027 重启了 8010，虽已按原 argv/环境恢复且两端健康，该旧 gate 不再直接绑定现态。原 gate manifest 把 replica PID/start-ticks 纳入稳定 `launch_config`，不满足现有 rebind 仅变更实例字段的约束，正式性能验收前须重新完成精度评测。旧 `perf-014` 含已回退的 QSA bound，[perf-015-p16k-post-rb001-unbounded-entry.md](perf-015-p16k-post-rb001-unbounded-entry.md) 重建无边界 Prefill/Decode/Mixed 三阶段基线，其既有结果仍按原身份和配置边界解读。

| 阶段 | 状态 | 结论 |
|---|---|---|
| Host/模型/工作目录预检 | complete | 目标存在，PPU-01 连通 |
| 源容器 inspect/谱系 | complete | 无暂停快照，代码指纹匹配 |
| 优化容器/挂载 diff | passed | `/mnt` 单一 bind mount 完全一致 |
| 资源隔离 | passed | 源服务已优雅停止；两套 TP8 graph 服务独占 0–7 与 8–15 |
| graph smoke/C8 | failed_output_health | graph 已多次 replay；10 题 C8 strict-match 0.9，但1个样本在 30000 token 上限截断，不签发 gate |
| P1K Prefill baseline | complete_clean | P1024/D1/C32/N64，3+3 轮在无其他流量时通过稳定性门禁 |
| P1K Decode baseline | complete_clean | P32/D1024/C32/N64，3+3 轮无干扰重跑通过稳定性门禁 |
| P1K Mixed baseline | complete_clean | P1024/D1024/C64/N128，输出吞吐中位 330.73 tok/s，P99 TTFT 中位 104.90s |
| `max-num-seqs=64` graph smoke | passed | 三轮共 24 请求，canonical 与 32 完全一致 |
| `max-num-seqs=64` Mixed screen | complete | 吞吐 +72.51%，P99 TTFT -88.14%，P99 E2E -38.38%；P99 TPOT +14.97%、P99 ITL +561.37% |
| `max-num-seqs=48` graph smoke | passed | 三轮共 24 请求，canonical 与 32/64 完全一致 |
| `max-num-seqs=48` Mixed screen | complete | 吞吐 +26.17%；P99 TTFT +5.33%、P99 E2E +7.34%、P99 TPOT +8.48%、P99 ITL +12.98% |
| Decode MoE M64 `BLOCK_SIZE_M=16` microbench | passed | 完整 GEMM1+激活+GEMM2 比默认 32 快 18.15%，BF16 bitwise 相等，graph capture/replay 通过；Prefill 变体回退约 5%并已拒绝 |
| Decode MoE 服务 A/B/R | passed_targeted | B 相对 R：输出吞吐 +3.35%，TPOT 中位/P99 -3.53%/-3.29%，E2E 中位/P99 -3.21%/-3.11%；P99 TTFT +0.75%、P99 ITL +1.22%，均在 5% guard 内 |
| Revert 漂移核验 | passed | R 相对 A 的吞吐、P99 TTFT/TPOT/ITL/E2E 漂移均小于 1% |
| 恢复候选 graph replay | passed | 新服务实例 `9b65cc77d73c-8030-851140-252804487`；24 次回放与基线 canonical SHA-256 一致 |
| M64 文本字节比较 `acc-002` | invalid | revert 自身两轮 31/64 输出不稳定，且首轮冷 cache/autotune 时间明显偏高；不可归因为候选精度回退 |
| M64 128-token 语义回归 `acc-003` | failed_output_health | 候选 57/64、57/64，revert 61/64、62/64；所有失分均为 `finish_reason=length` 且精确命中 128-token 上限，没有完整错误答案 |
| M64 非截断语义回归 `acc-004` | passed_scoped | 恢复正常 EOS、上限 512；candidate/revert 的 warmup 和两轮测量均 64/64，两端都观测到 64 running requests |
| P4K Prefill scenario-entry | complete | P4096/D1/C32/N64；总 token 吞吐中位 5630.21 tok/s，P99 TTFT 中位 23.28s |
| P4K Decode scenario-entry | complete | P4096/D1024/C32/N64；输出吞吐 286.07 tok/s，P99 TPOT 109.58ms，P99 ITL 745.55ms |
| P4K Mixed scenario-entry | complete | P4096/D1024/C64/N128；输出吞吐 452.18 tok/s，P99 TTFT 47.55s，P99 TPOT 137.25ms，P99 ITL 756.22ms |
| P4K `max-num-batched-tokens=8192` | rejected_reverted | 吞吐 +3.14%、P99 E2E -4.83%，但 P99 ITL +74.42% 且 warmup 不稳定；已恢复 4096 |
| P4K `max-num-batched-tokens=6144` | rejected_reverted | 吞吐仅 +1.35%，P99 ITL +36.54% 且 warmup 不稳定；已恢复 4096 |
| P4K bounded profiling `prof-002` | complete_with_receipt_caveat | 8 个 TP worker trace 和 async trace 最终均通过 gzip 完整性；Prefill/Mixed graph 窗口约 1.20–1.25s，QSA 占该阶段累计 device activity 43.3% |
| 现有 Qwen4 QSA `tl.dot` 替换 | rejected | 数值、selection 集、graph+2 replay 通过，但 rows64/4096 完整 transaction 分别慢 22.4%/29.8% |
| P4K `long_prefill_token_threshold=2048` | rejected_reverted | 吞吐约 -0.69%，P99 ITL 约 +0.42%，未达到 20% recovery 且 warmup 不稳定 |
| QSA row-range TopK | rejected_reverted | microbench 正确性通过；服务吞吐仅 +1.66%，低于 3% 门槛，P99 ITL -4.80% |
| QSA 静态安全上界 `8448` microbench | passed | 覆盖四个冻结场景；P4K Prefill/Decode 完整 transaction 1.555x/1.329x，P32K Decode 1.325x；selection、BF16、graph+2 replay 一致 |
| QSA `8448` P4K 独立 A/R | retained_performance | 相对干净 revert：输出/总吞吐 +7.00%，全部 median/P99 延迟改善；revert 对 entry 漂移低于 1% |
| P16K Prefill/Decode/Mixed entry | complete | 三阶段均 3+3、零失败且 warmup 稳定；Mixed 输出吞吐 261.42 tok/s，P99 ITL 654.4ms，P99 E2E 394.6s |
| P16K QSA `4352` headroom microbench | diagnostic_passed | 相对通用 `8448`，完整 QSA transaction 的 Prefill/Decode 再快 24.9%/13.6%；因不兼容 P32K，未部署 |
| P16K post-op006 profiling `prof-003` | complete_retry | no-stack retry 的 async+8 TP traces 全部完整；QSA 仍是大热点，MoE/GEMM 已与其同量级 |
| QSA runtime score bound `op-008` | passed_checkpoint_performance_only | 非 capture P16K 安全收紧到 `4352`，full-graph Decode/P32K 保持 `8448`；Prefill/Decode/Mixed 吞吐 +9.46%/+3.59%/+4.90%，全部延迟护栏改善 |
| P16K 当前组合重入 `perf-014` | complete | Prefill 总吞吐 7699.05 tok/s；干净 Decode 输出吞吐 210.085 tok/s、duration 311.95s、P99 TPOT/ITL 144.92/583.55ms；Mixed 输出吞吐 281.458 tok/s、duration 465.69s、P99 TTFT/TPOT/ITL 144.85s/213.71ms/596.88ms。三视图均 3+3、零失败 |
| P16K 原生 `mm_out` `op-023` | complete_passed_d128 | repaired fresh A/B/R 中 B 相对 A/R 中点输出/总吞吐 +3.3513%，duration -3.2427%，全部延迟改善约 3.01%–3.27%，A/R 漂移 0.1648%；comparator=`passed`, `issues=[]`。保留 native mm_out，但 D128 不自动扩展为 D1024 |
| P16K graph-QSA `4352` `op-024` | complete_valid_failed | A/B/R 对照有效，A/R 漂移 0.509%；B 相对 A/R 中点输出/总吞吐均 -0.252%，duration 反而 +0.252%。comparator=`failed`且唯一 issue 是主指标未达门槛；不扩 D1024，保留 8448 |
| P16K post-op010 re-profile `prof-007` | complete | async+TP0–7 九份 trace 完整；Decode device activity 中 QSA/MoE/native GEMM/AllReduce 约 29.1%/23.4%/17.4%/10.4%，general GEMM=0。profiler observer effect 为 -14.1%，只用于归因 |
| P16K QSA frontier `op-025` | stopped_before_microbenchmark | compiler 已自动 hoist K load；cap/lane/metadata/大 workspace R4 均有负证据。仅保留 shape+TopK 分项和无大 workspace 跨行复用诊断 |
| P16K MoE frontier `op-026` | stopped_before_microbenchmark | Decode 归类 MoE 的 93.81% 实为 M4096 异步溢入，非 M64；无新的完整事务 ≥8% 候选 |
| P16K no-async control `fw-013` | incomplete_identity_contract | A 3+3 完成；B 在请求前因 raw argv 顺序与冻结 prototype 不同而停止。未改 contract，无 B/R 性能结论 |
| P16K no-async repaired `fw-014` | complete_valid_failed | B 相对 A/R 中点输出/总吞吐 -4.455%，duration 变慢 4.662%；A/R 漂移 0.395%，comparison 有效。拒绝 no-async，保留当前 async 路径 |
| P16K QSA shape/TopK `diag-003` | complete_no_go | 8 rank 各 22,668 条、零丢失；score+TopK+expand 假设全部消除的松上界仅 Prefill 1.99%/Decode 5.80%/Mixed 6.49%，均低于 8%。实际宽度已 4096/4128、单 chunk，4352 cap 无缩减 |
| P16K QSA union `diag-004` | incomplete_output_consistency | 64/64 捕获成功，但同一冻结请求的采集前后输出由 8 token/length 变为 4 token/stop；硬门禁失败，未运行 A-B-B-A 或离线 union oracle，PPU8–15 已释放 |
| `op-008` 16K 原始 token 回归 `acc-005` | invalid | 缺少模型 chat-generation 协议，周期 filler 还泄露答案；空输出、复制与截断现象不能衡量候选语义 |
| `op-008` 16K chat 回归 `acc-006` | invalid_contract | 两端所有 wave 都 8/8 正确，但错误要求引擎同时 `running=8`；4096 batched-token budget 下分阶段 admission 只观测到 3 |
| `op-008` 16K chat 回归 `acc-007` | passed_scoped | 修复为非周期、无答案泄露的 chat-template prompt，并用客户端 barrier 证明并发；candidate/revert warmup 和两轮均 8/8、文本哈希集合一致 |
| P32K Prefill scenario-entry | deferred-too-slow/incomplete | 首个 P32768/D1/C32/N64 warmup 在 4分50秒到达 63/64；按用户要求中止客户端并切回 P4K，未接受任何性能指标，服务保持健康 |
| `op-008` P4K Prefill/Mixed checkpoint | retained_performance_only | Mixed 相对 op006 输出吞吐 +3.774%、duration -3.636%，全部 TTFT/TPOT/ITL/E2E median/P99 改善；Prefill 相对 pre-op006 entry 累计 +34.991%，不把全部收益单独归因于 op008 |
| P4K post-op008 profiling `prof-004` | complete | async+8 TP traces 有效；Decode graph 的 fused MoE/general GEMM/QSA sparse 分别约 2.278s/1.103s/0.437s，MoE 成为下一主热点 |
| MoE drain M40/48/56/63 microbench | passed | 只改 `BLOCK_SIZE_M 32→16`，完整 MoE pair 分别 +18.98%/+18.65%/+17.97%/+18.41%；BF16 bitwise 相等，graph+2 replay 通过 |
| MoE drain P4K/D128 milestone | rejected_reverted | 输出吞吐仅 +0.344%，低于预冻结 +1% 门槛；全部延迟 guard 通过但候选仍拒绝，service-39 已恢复 op008 + M64-only 配置并通过 graph smoke |
| 原生 `mm/mm_out` P4K/D128 A/B/R | retained_performance_only | 维护版比较器 `passed`；输出/总吞吐 +3.188%，P99 TTFT/TPOT/ITL/E2E 分别改善 2.961%/3.097%/3.047%/3.082%，唯一变量为 FlagGems blacklist |
| 原生 `mm/mm_out` P4K/D1024 A/B/R | retained_performance_only | 维护版 comparator `passed`、`issues=[]`；输出/总吞吐 +3.4168%，P99 TTFT/TPOT/ITL/E2E 改善 3.2163%/3.4655%/2.9641%/3.3005%，唯一变量为 provider blacklist |
| QSA native TopK stream-sync 归因 | refuted | rows 64/4096 × columns 1024/1280/8448 的 eager/graph 均命中 native sbtopk/mbtopk，但扣除 control 后 12 组均为 0 次 `cudaStreamSynchronize/TopK`；停止 TopK 替换方向 |
| M64 MoE GEMM2 `BN64→128` | rejected | BF16 bitwise 和 graph+2 replay 通过，但完整 MoE 事务 0.579ms→0.625ms，退化 7.925%；未接入服务 |
| M64 MoE GEMM1+SiLU 融合 | rejected | 数值契约和 graph+2 replay 通过，但完整 MoE 事务 0.579ms→0.620ms，退化 7.185%；未接入服务，停止同类扫点 |
| P4K post-op010 profiling `prof-005` | complete | async+8 TP traces 有效；每 rank 有 1 Prefill/63 Mixed/129 Decode 窗口，`mm_kernel_general` 退出 top20；Mixed 中 QSA/MoE/AllReduce 为主热点，同步长尾主要来自 collective 等待和 metadata 标量取值 |
| shape-selective `mm` provider `op-013` | no_go | 真实生产 M 为 Mixed 4096/Decode 2017，不是既有 M64 微基准；乐观加权完整 GEMM 收益约 6.3%，低于 8% 门槛，未实现 |
| `repeat_interleave(output_size)` 探针 `op-014` | passed_diagnostic | 三组 P4K shape 的 `item/_local_scalar_dense/cudaStreamSynchronize` 每调用 2→0，输出 bit-exact，候选 graph capture 通过，主机耗时约 -47%至-52% |
| `op-014` 服务 graph/canonical | passed | service51 完成 PIECEWISE 19/19 + FULL Decode 11/11 capture；24/24 replay 一致且 canonical SHA 与 service50 相同 |
| `op-014` 跨卡组 P4K/D1024 筛选 | invalid_control | service50 在 PPU8–15、service51 在 PPU0–7；候选首轮冷启动显著偏慢，已安全停止 benchmark 客户端，不用于归因 |
| `op-014` P4K/D128 同卡组 A/B/R | rejected_reverted | 维护版 comparator `failed`；输出吞吐 176.739→176.970 tok/s，仅 +0.1309%，低于预冻结 +1% 门槛；changed path 仅 `/plugin_sha256`，候选已回退 |
| request-group `index_put_→index_fill_` `fw-007` | no_go_side_path | 四类 shape bit-exact、graph+2 replay 通过，每调用 2 次 stream sync→0；后续证明它不是 prof-005 的目标 stack，不再错误放大其调用次数 |
| GDN initial-state 布尔索引 `fw-009` | no_go | 精确 FlagGems 路径每调用 2 次 sync→0，bit-exact；按 2340 次调用的乐观 P4K/D128 上界约 0.51%，低于 1% 门槛 |
| common-slot graph host sync `fw-008` | rejected_reverted | 真实算子四臂探针均零 mismatch，服务 graph/canonical 通过；P4K/D128 输出吞吐仅 +0.4994%，低于 1% 门槛，补丁和服务均已回退 |
| QSA group-3 literal-four `op-015` | no_go | 数值、无效/非连续页和 graph+2 replay 通过；rows64 graph +21.659%，但生产 rows4096 graph -4.563%，未修改服务源码 |
| TP8 PCCL `NCCL_PROTO=Simple` `fw-010` | no_go | 96-call rows64/4096 整链相对 default 退化 66.177%/25.156%；两臂 bit-exact、graph 稳定且 max-rank/median <1.002，保留 PCCL 默认选择 |
| MoE split-K/direct-sum 上界 `op-016` | no_go | 把 `moe_sum` 完全免费删除且忽略 atomic/zeroing 后，M4096 Prefill/Mixed/M64 Decode 完整事务上界仅 5.143%/4.808%/0.562%，低于 8% 门槛，未写微基准 |
| P4K scheduler 新前沿 `fw-011` | no_go | async 已启用且 V1 scheduler 已 running-first；partial-prefill 参数 unsupported/未消费，其余现有开关或 inert、或改变 ITL 语义/容量，无新的等价单变量候选 |
| QSA block-centric traversal `op-017` | no_go | 理想删除 expanded-index 读写及可合并 page translation 也只减少 rows4096 显式 traffic 1.0598%；8.6025GB K/V 和 129 个 softmax tile 不变，未写微基准 |
| 真实 P4K producer → R4 `op-020` | passed_correctness_only | Prefill/Mixed rows4096 完整结构、FP32 抽样、generic/candidate 数值与单 graph A/B/A 通过；Mixed `[1,4095]` 请求边界双写 race 已修复，仍未计时、未接入服务 |
| R4 完整 consumer 事务 `op-022` | no_go | Prefill 正确性与稳定性全通过，但 eager/graph 从约 9.95ms 增至 14.75/14.67ms，退化 32.52%/32.22%；按冻结停止规则不跑 Mixed、不接入服务 |
| host/device handoff `prof-006a` | no_go_or_inconclusive | event-only 公共 device gap 约 7.63%，但 189 个 Mixed step 的严格 Plugin preprocessing 因果下界为 0；event/control 与 host/event 绝对扰动 1.03%/1.22%也超过 0.5%，不实施 `fw-012` |

规划复盘 `plan-001-20260919-p1k-maxseq` 已完成。`64` 证明 admission waves 是 P1K Mixed 的主要瓶颈，但形成强吞吐/排队收益与严重 ITL 回退；`48` 不是无损折中，它增加吞吐但相对 `32` 的全部测量延迟都回退。三者只保留为 Pareto 参考，尚未通过独立实例 A/B/R。

下一实验为 `max-num-seqs=64 + max-num-batched-tokens=2048`，直接尝试缓解 Mixed 中 Prefill/Decode 竞争：要求 P99 ITL 相对 64 至少改善 30%，输出吞吐保留至少 90%，且 P99 E2E 仍优于 32。若失败，进入 32/64 配对 profiling；源码层的重复 slot-mapping 与 QSA 融合草案继续保持未应用。

`64/2048` 已完成并回退：相对 `64/4096`，吞吐 `-3.48%`、P99 TTFT `+31.49%`、P99 E2E `+6.50%`、P99 TPOT `+2.98%`，P99 ITL 仅改善 `19.25%`，未达到预冻结的 30% 门槛。规划复盘 `plan-002-20260919-p1k-profile` 将下一步切到 bounded torch-profiler capture/analyze；只有 trace 证明具体路径贡献后，才应用重复 slot-mapping 或算子草案。

Profiling 将 Decode 热点收敛到 fused MoE。最终保留方案不修改 Plugin/FlagGems 源码，而是使用 vLLM 已支持的 `VLLM_TUNED_CONFIG_FOLDER`：对 `E=512,N=80` 冻结 `M=1..4096` 的精确配置，仅把 Decode `M=64` 的 `BLOCK_SIZE_M` 从 32 改为 16，其余 shape 精确保留默认值。实验性源码 hook 已全部回退。

`plan-004-20260919-p1k-abr` 已完成。A/B/R 证据足以保留该 P1K targeted 候选，但不代表正式验收。上游适配项目的最新 full198 本身为 170/198（85.86%），低于冻结的 88% 阈值；本项目不会降低阈值或伪造 passing gate。下一步先对完全相同的 candidate/revert TP8 服务运行并发 64、短生成、确定性的最小回归，确认精确 M64 路径输出一致；通过后建立 P4K 的 Prefill/Decode/Mixed scenario-entry baseline。

M64 最小回归经历两次证据修复：`acc-002` 证明整段生成文本不是稳定的跨 graph 实例量尺；`acc-003` 证明强制 128-token 上限只是截断了部分推理。保留全部失败证据后，`acc-004` 仅恢复正常 EOS 并把上限改为 512，题目、seed、并发 64、`FINAL=<integer>` 解析器与 100% 阈值都不变，candidate/revert 在 warmup 和两轮测量中均为 64/64。该 scoped minimal regression 允许继续性能优化，但不解决上游 full198 的 88% 正式精度阻塞。当前目标已切换为 P4K scenario-entry baseline。

P4K Prefill、Decode、Mixed 三个入口基线均完成 3+3 轮、零失败且通过预热稳定性。Mixed admission 期间观测到 `13 running / 51 capacity-waiting`，随后转为 `62 running / 0 waiting`，表明 `max-num-batched-tokens=4096` 下长 Prefill 需分批进入，再与大 Decode batch 共存。`plan-005-20260919-p4k-entry` 因此选择同一容器、同一 8 卡上的单变量 `max-num-batched-tokens: 4096 → 8192`：先做 graph replay 和同契约 P4K Mixed screen，要求吞吐至少 +3%，同时 P99 TTFT/TPOT/ITL/E2E 回退不超过 5%；不通过就回退。

`8192` 已按契约拒绝并回退：吞吐从 452.18 升到 466.39 tok/s（+3.14%），P99 TTFT/TPOT/E2E 均改善，但 P99 ITL 从 756.22 升到 1319.02ms（+74.42%），且 warmup 稳定性失败。service-13 已在同一容器和卡组上恢复 `4096 + M64 BM16`，通过 graph capture、readiness、配置命中与仓库哈希检查。`plan-006-20260919-p4k-tail-latency` 将下一个低成本单变量设为中间值 `6144`，仍使用原封冻的 3% 吞吐和 5% 四项 P99 guard；若再失败，转入 P4K tail-burst profiling，不再盲扫配置。

`6144` 也已拒绝并回退：吞吐仅 +1.35%，未达 3% 门槛；P99 ITL +36.54%，warmup 稳定性仍失败。`6144/8192` 表明 admission budget 增大时，吞吐和 ITL 长尾呈单调交换，不再继续扫 5120/7168。service-15 已恢复 `4096 + M64 BM16`，下一步是 bounded P4K Mixed tail-burst profiling，目标是区分 Prefill/Decode 干扰、graph shape 和具体 kernel/collective 延迟。

`prof-002` 已把机制收敛：P4K 中 64 个 Prefill/Mixed graph 窗口共 78.15s，单窗口约 1.20–1.25s；Decode 窗口通常只有 0.18–0.21s。QSA MQA+sparse GQA 在 Prefill/Mixed 的累计 device activity 中占 43.3%，说明长 Prefill 窗口阻塞 Decode 是 `6144/8192` ITL 单调恶化的直接原因。capture 回执因 rank0 gzip 导出超过 client timeout 而不完整，但导出结束后 8 个 worker trace 和 async trace 均通过 gzip 完整性检查；profiler-on 延迟不用作正式性能结论。

按 `plan-007-20260919-p4k-post-profile` 完成方向重排：现有 Qwen4 `tl.dot` scorer 在保持 20000 列、TopK 和 sparse attention 不变时，rows64/4096 完整 transaction 反而慢 22.4%/29.8%，已拒绝且未接入服务。静态 512 列仅对 P1K 已证安全，不会冒险扩到长上下文。下一个最小证伪实验保持 `max_num_batched_tokens=4096`，只设 `long_prefill_token_threshold=2048`，目标将 P99 ITL 至少改善 20%，同时保留至少 95% 吞吐、其他 P99 护栏不回退超过 5%。

后续两个最小实验均已拒绝并回退：`long_prefill_token_threshold=2048` 没有恢复 ITL，QSA row-range-only 服务收益也只有 1.66%。`op-006` 改为显式、能力约束的 QSA score-capacity 上界：`8448` 覆盖四个冻结 workload 的最大 compressed-visible width，同时保留默认 full-capacity 行为。微基准、focused GPU test、graph replay 和路径命中均通过；独立 candidate/revert 的精确 P4K Mixed 测量中，输出吞吐提升 7.00%，TTFT/TPOT/ITL/E2E 的 median 与 P99 全部改善，且 revert 对 scenario-entry 漂移低于 1%。因此 `plan-008-20260920-p4k-qsa-bound-retain` 保留该组合，但只作为四个冻结场景的显式 opt-in，不推广到任意更长请求。

当前目标切换到 P16K。下一步在保留服务上分别建立 Prefill、Decode、Mixed 三个视图；如果完整 P16384/D1024/C64/N128 超出诊断时间预算，就保存部分证据并进入 baseline-recovery，不缩短后冒充正式场景。正式精度仍被上游 GPQA 170/198（85.86%）低于冻结 88% 阈值阻塞，长上下文最小语义回归也必须在正式保留前补齐。

P16K 三阶段现已完整通过 3+3 轮、零失败和预热稳定性：Prefill 总 token 吞吐中位 6753.51 tok/s；Decode 输出吞吐 195.92 tok/s；Mixed 输出吞吐 261.42 tok/s、P99 TTFT 159.14s、P99 TPOT 230.22ms、P99 ITL 654.40ms、P99 E2E 394.59s。汇总 SHA-256 为 `1db6dc0fbea037758696c935e94a7264796f3c2a3fc6178da4366588aa4718f2`。

`op-007` 证明 P16K 的理论安全上界 `4352 = (16384+1024)/4` 相对通用 `8448` 仍有明显 QSA headroom：Prefill/Decode 完整 transaction 再快 24.9%/13.6%，selection、下游 BF16 和 graph+2 replay 一致。但它不能覆盖 P32K，因此没有部署；候选服务已恢复为通用 `8448` 并通过源码、readiness、graph 和配置门禁。`plan-009-20260920-p16k-entry-and-qsa-headroom` 将下一步定为 bounded P16K profiling，先确认 op-006 后热点是否仍是 QSA，再决定安全 runtime bucket、sparse GQA、MoE 或通信优化。

`prof-003` 的首次 stack capture 在 worker 导出时失败，作为无效证据保留；no-stack retry 成功生成 async 和 8 个 TP worker trace，全部通过 gzip 完整性检查。rank0 中 fused MoE、QSA sparse GQA、general GEMM、QSA MQA 分别约为 31.15s、30.40s、27.82s、17.87s，说明 QSA 仍有端到端价值，但不再是唯一热点。

`op-008` 已将 P16K-only 的静态 `4352` 转化为安全的 CPU metadata runtime bound：非 capture Prefill 按实际 `max_seq_len` 对齐收紧，full-graph Decode 在 capture 时仍使用 `8448`，P32K 也在 `8448` 封顶。6 个边界单测和 24 次 graph replay 通过；精确 P16K Prefill 总 token 吞吐提升 9.46%，P16384/D128/C64/N64 Mixed A/B/R 中输出吞吐提升 5.94%，所有 median/P99 延迟护栏均改善，重新应用候选与首次候选漂移仅 0.25%。当前 service-35 已保留该改动。

完整 P16K 检查点已通过：相对 op006 入口基线，Prefill 总吞吐 +9.463%；Decode 输出吞吐 +3.589%、duration -3.464%；Mixed 输出吞吐 +4.900%、duration -4.671%。Decode/Mixed 的全部 TTFT、TPOT、ITL、E2E median/P99 都改善，每轮请求零失败，warmup 和 measured spread 均稳定。机器可读汇总为 `p16k-op008-full-checkpoint-summary-01.json`，SHA-256 `df5dbd22eaa7fbc985aa7a78469a93fdf7e41a3554aa111be0c3ec4c80f54f93`。这仍是 `performance_only` checkpoint：没有冒充独立进程正式性能或最终验收。

长上下文最小回归也经历了两次证据修复。`acc-005` 证明直接拼 raw token IDs 会绕过模型生成协议，周期素材还会产生答案泄露和复制假象；`acc-006` 的所有语义检查其实都通过，但把“客户端同时提交 8 个请求”错误等同于“服务端同时 running=8”，与 4096 batched-token budget 下的分阶段 admission 冲突。最终 `acc-007` 使用 chat template、非周期 archive 文本、零答案字符串泄露和客户端 barrier：candidate/revert 在 warmup、measured wave1、wave2 中均为 8/8，所有请求精确 16384 prompt tokens、8 completion tokens、正常 stop、无截断、语义正确且两端文本哈希集合一致。结果 SHA-256 为 `b6b5ba1960988e16a0faebd293b8f5a33461f9469c84f6095ff736de751c9c7e`。它只清除 op008 的 scoped minimal regression，不解决正式 GPQA 阻塞。

`plan-011-20260920-p16k-checkpoint-to-p32k` 已把当前目标切换到 P32K：先在 service-35 上依次建立 Prefill、Decode、Mixed 的 3+3 入口证据；若超出预记录诊断预算，则保存运行时长、完成请求数、日志与服务健康状态并明确标记 `deferred-too-slow/incomplete`，不缩短后冒充正式场景。由于 op008 在 P32K 与 op006 同为 `8448` 上界，当前不预设任何 P32K 收益；只有新阶段证据形成后，才在 QSA、MoE、GEMM、通信和调度中选择下一项。正式精度仍被上游 GPQA 170/198（85.86%）低于冻结 88% 阈值阻塞。

P32K 首个 Prefill warmup 在 4分50秒完成到 63/64（约 4.55 秒/请求），用户此时明确要求长场景过慢时优先基于 P4K 分析和优化。只向精确 benchmark 客户端发送 SIGINT 后，候选服务恢复为 `0 running / 0 waiting` 且 health 正常；该轮没有 native result，不计算吞吐或加速比，作为 `deferred-too-slow/incomplete` 保留，P32K 仍在最终正式矩阵中。

`plan-012-20260920-p32k-defer-p4k-surrogate` 将快速迭代目标转回 P4K milestone。首个假设不是新改代码，而是测量已保留 op008 在 P4K 的端到端贡献：P4K prof-002 中 QSA 占 Prefill/Mixed 累计 device activity 43.3%，op006 的静态 `8448` 已带来 7.00% Mixed 收益，而 op008 能从 P4K CPU metadata 得到更紧的 non-capture score width。先证明实际 width/path hit，再跑冻结的 P4096 Prefill 和 Mixed 3+3；通过后才刷新 profiling 并选择新的 QSA/MoE/GEMM/通信热点。

P4K 代理场景验证了 op008 的继续保留价值：相对 op006，精确 P4096/D1024/C64/N128 Mixed 输出吞吐提升 3.774%，duration 降低 3.636%，TTFT、TPOT、ITL、E2E 的 median/P99 全部改善。Prefill 相对更早的 pre-op006 entry 累计提升 34.991%，但缺少单独 op006 Prefill 服务结果，因此不把全部 Prefill 收益归给 op008。

`prof-004` 在 post-op008 服务上完成 async+8 TP trace，Decode graph 的 fused MoE、general GEMM、QSA sparse 累计 activity 分别约 2.278s、1.103s、0.437s。对 profiler 中可精确映射的 M40/M48/M56/M63 退坡批量，仅改 `BLOCK_SIZE_M 32→16` 的完整 MoE microbenchmark 均提升约 18%，数值与 graph 回放通过；但同配置 P4096/D128/C64/N64 服务 milestone 只提升 0.344%，低于预冻结 1% 门槛。该四键配置已拒绝并回退，不能用局部 kernel 收益冒充端到端优化。

首次 service-38 切换在新服务已启动后因进程树证据对象形成循环引用而中止证据写入；空 `after-process.json` 被原样保留，随后在不再次重启的前提下补齐 recovered process manifest、readiness、配置命中和两次 graph replay。拒绝候选后，service-39 以精确 PID/start-ticks/argv 回退到 `op008 + M64 BM16`，配置 SHA-256 恢复为 `c695793cb283b8d48782d2b0bf5aa6ff54c03c4b8d9251f776bcfdb8833c3e18`。

`plan-013-20260920-p4k-post-op008-and-moe-drain` 将下一步转向 prof-004 的第二大 Decode graph 热点 general GEMM：先把 kernel signature 映射回实际 tensor shape、dtype、转置/layout 和 dispatch/backend，再比较已有 vendor/native 实现；只有完整 transaction 至少提升 8% 且数值、graph 均通过，才进入服务集成。M40/M48/M56/M63 的继续调参已明确停止，P32K 仍保留为最终正式目标，正式精度仍被上游 GPQA 170/198 低于 88% 阈值阻塞。

`op-010` 已完成并保留：服务实际命中 `aten::mm.out`，对应 FlagGems 排除键必须使用 Python 函数名 `mm_out`。精确 `mm_out` 微基准显示 8 组 M64 投影中 5 组原生实现更快，3 组 FlagGems 更快；随后用单变量服务 blacklist 验证端到端净收益。正确绑定的 P4096/D128/C64/N64 独立 baseline/candidate/revert 比较由维护版比较器判定 `passed`，输出吞吐 +3.188%，全部 P99 守护改善，且 changed path 仅为 `VLLM_FL_FLAGOS_BLACKLIST_APPEND`。当前 service-46 保留 `mm,mm_out` 原生路径，已通过全量 graph capture 和两次回放。

精确 P4096/D1024/C64/N128 已升级为同 contract A/B/R：normal baseline、既有 native candidate 和 fresh normal revert 各有唯一 3+3 产物，维护版 comparator 返回 `passed`、`issues=[]`。candidate 相对 baseline 的输出/总 token 吞吐均提升 3.4168%，P99 TTFT/TPOT/ITL/E2E 分别改善 3.2163%/3.4655%/2.9641%/3.3005%；changed path 仅为 `VLLM_FL_FLAGOS_BLACKLIST_APPEND`。comparator SHA-256 为 `dac9c81c3537e3eb45a8a4fab33182274e01017d36b15e4f969c1d4f6979a6e4`。service48 已恢复 native provider，readiness、full graph capture 和 canonical replay 通过。

`plan-014-20260920-op010-retain-and-hotspot-rerank` 已按规划复盘把下一主实验设为 post-op010 bounded profiling。原因是 prof-004 早于 native `mm/mm_out`，而后续 GEMM2 `BN128`和 GEMM1+SiLU 融合分别让完整 MoE 事务退化 7.925%/7.185%，native TopK 也已被独立探针证伪为 stream-sync 根因。因此当前不再盲扫 kernel，先重建 Prefill/Decode/Mixed 热点和同步路径排序。

`prof-005` 已用源码证明的 `new/cached` marker 语义完成全 rank 重分段。原生
`mm/mm_out` 真实命中，但 QSA、MoE 和 collective 仍是当前主热点。生产
M4096/M2017 计数使 `op-013` 在实现前就因加权收益不足而停止。`op-014`
虽在独立探针中消除了 `repeat_interleave` 相关 stream sync，并通过 full graph 和
24 次 canonical replay，但同卡组 P4096/D128/C64/N64 A/B/R 的输出吞吐只改善
0.1309%，低于 1% 门槛。comparator SHA-256 为
`05f8dd6a800becf1e198e3e2ec0613c9103c40a04221ed2f9747a28fc6bd20f3`；补丁已回退，
当前转向 `nonzero_numpy/index_put_` 因果探针和 cached64 graph-wrapper/collective 等待分离。

`fw-007` 随后证明 request-group 的一维 `index_fill_` 可以消除同步，但 stack
回溯确认它不是 prof-005 的 `nonzero_numpy/index_put_` 来源，旧的 36 层放大
被撤销。真实路径是上游 GDN prefill 的
`initial_state[~prefill_has_initial_state, ...] = 0`；`fw-009` 精确启用 FlagGems
后证明预计算整型索引 `index_fill_` 可将每调用 2 次同步降为 0，但按
36 层×65 个相关窗口计算的乐观 P4K/D128 上界仍只有约 0.51%。因此同样在服务
实现前停止。PPU0–7 已释放供 common-slot 探针，PPU8–15 上的保留 service50
保持 healthy。

`fw-008` 进一步验证了 cached64 graph-wrapper 同步。真实 common-slot producer
与 GPU consumer 在每臂 2000×3 次下均无陈旧读，同流 no-fence 比 host sync
每 pair 少约 6.34µs；服务57也通过 full graph 和 24/24 canonical。但冻结的
P4K/D128 3+3 筛选只得到 +0.4994% 输出吞吐，全部延迟虽小幅改善，主指标仍低于
+1% 门槛。候选已停止并反向应用补丁，说明 profiler 中 1.857s/2.920s 的直接同步
主要暴露前序 backlog，不能等额转化为可消除端到端时间。

规划复盘 `plan-017-20260920-post-metadata-sync-rerank` 因此停止继续追逐小型
metadata sync。下一优先级是 prof-005 的 QSA sparse GQA：当前 TP8 live query
为 `[rows,3,256]` BF16、TOPK 2051，但 wrapper 将 `GROUP_SIZE=3` 圆到
`BLOCK_M=16`。该 kernel 在 Mixed 中 755 次累计 7.339s；若完整 sparse call
能提升 8%，乐观对应约 1.46% Mixed marker wall，足以进入服务 +1% 门槛。
首个实验只在独立 microbenchmark 中实现 exact-group3 特化，覆盖 rows
1/8/64/4096、无效索引、非连续页和 graph+2 replay；完整调用加速低于 8% 就停止，
不修改服务源码。collective 因果控制排第二；已拒绝的 MoE M40/48/56/63 BM16、
GEMM2 BN128 和 GEMM1+SiLU 不再重复。

`op-015` 已按上述门槛停止，没有进入服务集成。字面量
`tl.arange(0,4)` 候选对当前通用 kernel 数值一致，也通过无效/非连续页、
graph capture 和两次 replay；valid rows64 graph 提升 21.659%，但生产代表的
valid rows4096 graph 反而退化 4.563%（eager 退化 4.549%），未达预冻结 8% 门槛。
该结果证伪了“仅缩小头 lane”在 P4K 生产 rows 上的优化假设，FlagGems 和现服务都
未修改。下一个有界实验转为 TP8 collective 的无 profiler 生产 message-sequence 因果
控制；只比较现有支持路径，并要求 bit-exact、graph+2 replay、无 rank 异常点、
加权 transaction 至少 +8% 且可信 P4K Mixed 贡献至少 +1%。

`plan-018-20260920-post-op015-rerank` 已因 rows64 与 rows4096 结果冲突提前触发。
当前顺序是：先做 `fw-010` TP8 collective 因果控制；只有新 QSA 方案能改变
memory traffic、TOPK/block 遍历或其他完整事务机制时才重开 QSA；MoE split-K/
归约融合保留为第三候选，不重复已拒绝的 M-key/config 扫描。

`fw-010` 也已在服务集成前停止。service50 日志证明实际走
vLLM `pynccl.py` 和 PCCL 2.1.0；无 profiler TP8 graph 探针覆盖每 step 96 次归约。
默认/Simple 的 rows64 整链为 1.450/4.286ms，rows4096 为 18.776/25.087ms，
`NCCL_PROTO=Simple` 分别退化 66.177% 和 25.156%。两臂均 bit-exact、graph 稳定，
所有 max-rank/median 低于 1.002，因此 profiler 中的 rank spread 没有在无 profiler
事务中复现。服务保持 PCCL 默认选择；下一步转为不重复已拒绝配置扫描的
MoE split-K/归约融合完整事务上界分析。

`op-016` 的上界分析同样在实现前停止。当前 FlagGems wrapper 强制
`SPLIT_K=1`，kernel 的 grid、K-loop 和写回也没有使用 split-K；已有 `direct_sum`
虽可省去独立 `moe_sum`，但会新增 BF16 atomic 和 output zeroing，且数值顺序不同。
即使把这些实现成本全部置零，免费删除 `moe_sum` 的完整事务上界也只有
M4096 Prefill 5.143%、prof005 Mixed 4.808%、M64 Decode 0.562%，未达 8%
门槛，因此未写新 kernel、未占卡。

并行的 `fw-011` scheduler 审计也没有找到可实验的新单变量：当前 async
scheduling 已开，vLLM V1 Scheduler 已是 running-first；concurrent partial-prefill 在
当前 revision 中 unsupported/不被 scheduling loop 消费，DP1 的 prefill interval 也 inert。
其余开关要么重复已拒绝的 admission 权衡，要么改变 ITL 语义或降低 KV 容量，
不满足“Mixed 可信 +1% 且 ITL 回退 <=5%”的立项条件。

`op-017` 又排除了不重复旧方案的 block-centric QSA 路线：直接消费
512 个 compressed TopK block index、省掉 `[rows,2051]` expanded index 并合并
4-token page translation，即使把这些 metadata 成本全部置零，rows4096 明确字节
上界也只有 1.0598%；精确 attention 仍必须读取 8.6025GB K/V 并执行 129 个
online-softmax tile。`plan-019` 因此只保留一个最后的 exact-semantics 诊断：
在隔离 P4K 服务中一次性统计同 request 相邻 row 的 compressed selected-set 重叠。
只有扣除 union/mask 余量后仍能保守证明至少 12% K/V 复用，才会设计 row-group
kernel；该 telemetry 只是 profiling 诊断，不作为性能收益。

`op-018` 已完成并精确回退。P4096 Prefill 与实际包含两个 request run
的 Mixed 样本中，R2/R4/R8/R16 的保守 `rho` 分别约为
44.1%/69.5%/83.9%/91.7%，Mixed coverage 仍为 99.93%/99.87%/99.74%/99.48%，
因此四个尺寸都通过 12% 设计门槛。这些数字是精确 selected-set 的 K/V
复用上界，不是 kernel 或端到端加速。成本模型将 `op-019` 首个实现收敛到 R4：
12 个 query-head lane 仍落在 BM16，复用约 69.5%，而 R2 同样占 BM16 却只复用 44%。
在完整 selection+sparse 事务中付出 union、membership mask、独立 softmax state 和 layout
开销；只有 rows4096 完整事务至少提升 8%、数值与 graph+2 replay 通过，
才允许进入服务集成。遥测 helper 已删除，`qsa.py` 恢复为 `e18fbb22…`，
PPU0–7 已释放，service50 保持 healthy。

`op-019` 的精确 fixture 门禁已通过。Prefill/Mixed fixture 均逐项复现
`op-018` 的 R2/R4/R8/R16 计数，每行 selected index 无重复。R4 union 的
Prefill max/p99/p90/p50 为 `3460/3292/3036/2052`，Mixed 为
`3400/3292/3056/2048`，证明 8192-token direct-address workspace 容量充足；但
last-row leader coverage 只有约 82%，低于冻结的 90% shortcut 门槛，因此不会采用
近似 leader 方案。临时 capture patch 已精确回退，当前仅进入 standalone
`clear+build+grouped-attention+fallback` 完整事务 microbenchmark；在 Prefill 和
Mixed rows4096 的 eager/graph 都达到 8% 且正确性、fallback、graph replay 全通过前，
不改服务源码。

`op-019` 随后在 graph 前的 eager 动态输入预检处停止，没有产生可晋级性能数字。
R4 prototype 已在 PPU 编译；最终 smoke 的初始 rows4096 generic 对照、抽样 FP32、
fixture 结构、fallback 和 group-base 双射 assertion 未触发，但该失败运行没有生成
结构化 `result.json`，不能扩展成完整 correctness suite。其后虽有
`selected_A != selected_B`，同一 eager generic 路径的输出却完全相同，因此没有
建立可信的 rows4096 changed-input control，graph 门禁并未进入。较早的同指针 copy、
原地 Triton 变换和独立 B pointer 尝试也只是不确定证据，不能据此宣称 PPU cache
缺陷。全 `-1` 索引能正确归零；独立 rows1/TOPK1 控制只证明小形态下 token0/token2049
分别命中 V0/V2049，不能证明 rows4096 动态替换或 graph replay。根据冻结规则，不跑
full timing，也不进入 FlagGems/服务集成；若重开，必须把真实 producer 纳入一个
captured transaction（或使用等价且已验证的单 graph 动态机制），并持久化 selected、
完整 membership、generic/candidate output 的同 graph A/B/A。清理后 `qsa.py` 仍为
`e18fbb22…`，PPU0–7 空闲，service50 healthy；这只证明 op-019 没有持久源码/服务
改动，FlagGems 工作区仍包含此前保留的 QSA diff，并非全局 clean。

`plan-020` 因此把下一步收窄为 `op-020` rows64 单 graph 证伪：在同一 captured
transaction 内用 phase-driven Q staging 依次产生 A/B/A，调用真实
`qsa_select_paged_tokens`，并逐次持久化 selected、完整 membership、generic 与
candidate output；两张独立 graph、静态 selected replay 或只有 hash 变化都不满足
门禁。任一动态重建、数值、fallback 或 replay 失败即停止，不获取 rows4096 fixture，
也不进入性能计时或服务集成。并行复盘的 `prof-006a` 仍只是 host/scheduler 因果诊断：
只有低扰动测得全 TP rank 公共 device-idle 下界超过 Mixed 墙钟 1%，且能归因到
Plugin 可修改交接段，才允许设计 `fw-012`；当前没有可直接实施且可信收益不低于 1%
的新 scheduler 配置。

`op-020` 的 rows64 单 graph 证伪现已通过。首次 smoke 在 capture 语义 guard
安全停止，证明该 PPU capture 只记录、不执行 transaction；仅把初始 phase 改为 A 后，
同一 graph 在三次连续 replay 中由 graph 内 phase flip 产生 A/B/A，期间没有外部输入
写入。64/64 selected 行、130944 个 selected cell 和 16/16 个完整 R4 group membership
都在 A→B 时变化，A2 又逐项回到 A1；每次完整 139264-cell membership、group metadata、
generic/candidate output 都对齐 CPU/eager oracle。候选对 generic 最大绝对误差为
`0.0009765625`。该结果不含 timing、不改 FlagGems/Plugin/服务、也不是 speedup；
只有获取非业务 synthetic 请求的真实 P4K producer fixture，并通过 rows4096
Prefill/Mixed 形态、正确性和同一单 graph A/B/A 后，才能进入冻结的 8% 完整事务计时。

`op-021` 已将这个真实 producer 输入缺口关闭。隔离的 PPU0–7/8031 eager
服务分别捕获了 P4K Prefill 和真实两个 request run 的 Mixed fixture：两者均为
4096 行、`selected=[4096,2051]`，实际 hybrid KV 页宽为 1600；Prefill/Mixed
分别只需要 1/2 个可达 cache 页，原始文件总计 38,256,652/38,666,264 字节。
所有文件 SHA 通过，恢复捕获前保留 QSA 路径 `e18fbb22…` 后的 producer replay 与
捕获 `selected` 逐 cell
完全一致。Prefill/Mixed manifest SHA-256 分别为
`e9765fa23ae19d487c9c7773c3f0b5ea65e5870012eb6ab4cacf7be9efcaeabd` 和
`4d066545ab78ea30d340ce9a76db0325dfd4acee15b14c46fd719790779a037e`。
捕获中的同步和 D2H 使所有 timing 无效；该结果不是加速比，也没有保留新源码或服务候选。
捕获时 manifest 中的 `qsa.py` SHA 为临时插桩版 `8bbe4847…`；replay 前已精确
恢复为 `e18fbb22…`。保留 8030 服务进程/配置未重启或 reload，但共享
`qsa.py` 在隔离捕获期间曾短暂插桩，因此不宣称共享源码全程未变。

过程中修正了两个关键 ABI 误解：hybrid Mamba/attention 页统一后，QSA kernel
真正使用的 `k_cache.shape[1]` 是 1600，而不是原始预估的 16/4；FlagGems
`index_select` 会先 materialize 完整 41.82GiB cache 并 OOM，最终 helper 改为可达页逐页
D2H 后在 CPU 拼接。所有失败尝试均通过 trap 停掉精确隔离进程、恢复
`qsa.py=e18fbb22…`、确认 8030 healthy 并释放 PPU0–7。

`plan-022` 将立即实验更新为 `op-020-real-p4k-rows4096-correctness`：先 Prefill、
后 Mixed，分别要求固定 manifest SHA、完整 R4 membership/shape-similarity、eager
generic/candidate 数值一致，以及同一 captured graph 内部 phase 推进的 A/B/A。
两个 phase 全部通过前仍禁止计时和服务集成。

`op-020` 的真实 P4K rows4096 正确性门禁已通过。Prefill 和 Mixed
都精确重放了 op021 的 producer selected，完整 membership/metadata、抽样
FP32 attention、eager generic/candidate 及一张 graph 内部推进 A/B/A 均通过；
Prefill/Mixed `rho` 分别为 `0.695121889/0.694797948`，与冻结 shape
完全一致。首次 Mixed 回放暴露了候选原型的真实请求边界 bug：
`starts=[0,1,4096]` 时，request0 的一行 tail group 与 request1 的首 group
同时写 rows1–3，两次诊断分别出现 283/69 个 BF16 位级不一致元素。
修复通过 `request0` 同时约束 lane、score 和 source row，未放宽任何门禁；
修复后 Prefill/Mixed A1/A2 候选输出也逐位一致。当前修复仅存在于
standalone 原型（SHA `7a2dd94e…`），没有修改已安装 FlagGems 或保留服务。

`plan-023` 将下一步冻结为 `op-022-r4-complete-consumer-transaction-timing`：
对 Prefill/Mixed 分开比较当前 generic sparse attention 与包含 output clear、
workspace clear、membership build、grouped attention/fallback 的完整 R4 事务。
eager 和 graph 四项中任一中位收益低于 8%、MAD/中位数超过 3% 且
扩展采样后仍不稳定，或任何正确性/graph/隔离检查失败，都在源码和服务
集成前停止。即使全部通过，也只能进入隔离 P4K 服务 milestone，不是
端到端收益或正式验收结论。

`op-022` 在 Prefill 第一个正式计时 phase 即按冻结条件停止。完整
fixture/source SHA、8396800-cell membership、1025 group slot、writer ownership、
抽样 FP32、eager 数值、静态 graph 三次位级回放和计时后守卫全部通过。
在 7 组交错顺序、每组 5 次完整调用中，eager generic/R4 中位为
`9.950968/14.746951 ms`，graph 为 `9.941424/14.667456 ms`，按冻结公式
分别退化 `32.5219%/32.2212%`；四个臂/模式的 MAD/中位数均低于
0.8%。候选每次都包含 33,644,552-byte workspace、output/workspace clear、
membership build 和 grouped/fallback attention。该结果证明这个完整组合慢，
不把退化静默归因给某一个子算子。由于 Prefill 已远低于 +8% 门槛，
Mixed 不再运行，原型不安装、不创建服务候选。

`plan-024` 因此停止 R4 direct-membership 路线，立即实验切换为
`prof-006a-device-idle-host-handoff-proof`。先在隔离 PPU0–7 服务上证明
event-only 扰动不超过 0.5%，再要求 8 个 TP rank 完整覆盖、扣除扰动后的
Plugin 可修改 common-rank idle 严格高于 Mixed 墙钟 1%。任一门禁失败即停止，
不盲目实现新 scheduler 补丁。

`prof-006a` 已完成并按门禁否决 `fw-012`。`no-probe / event /
event+host-ring` 三臂均完成 P4096/D128/C64/N64 三次 measured，两个插桩臂
都有 engine+TP0–7、579 个实际 forward step、每轮 63 个 Mixed step 和零
overflow。event-only 公共 inter-forward device idle 中位为墙钟的
`7.6339%`，但所有 `3x63` Mixed step 在 worker entry 时前一 forward 都未在
所有 TP rank 完成，因此严格可归因 Plugin preprocessing 的下界为 `0`。
event 相对 control 为 `-1.0349%`，event+host 相对 event 为 `+1.2161%`，
两者绝对值均超过 0.5% 扰动门禁；同时三臂内 MAD/中位数都低于
0.16%，说明不是单轮异常。该结果只证明稳定 device gap，不证明它由
Plugin host handoff 造成或可被 scheduler 补丁回收。所有私有插桩已回退，
PPU0–7 已释放，8030 保留服务健康。

`plan-025` 将当前 P4K 代码实现周期收口：`op-010` 仍是最新保留的
精确 P4K/D1024 端到端改动，输出和总 token 吞吐 `+3.4168%`；不把
`op-022` 的局部退化或 `prof-006a` 的未归因 idle 叠加成收益。下一可执行
方向是在有足够长时间窗口时回到原样 P32K recovery 合同；如仍超时，
保留 `deferred-too-slow/incomplete` 而不缩短或改名后冒充正式场景。

`plan-026` 按用户新优先级把当前目标切回 P16K，P32K 仍保留在最终矩阵中但暂缓。
P4K 的后续 QSA 方向已冻结为“精确跨行 K/V 复用，且不使用已被 `op-022`
证伪的 33.6-MiB direct-address clear/build workspace”。它只在新机制能保守证明完整事务
至少 `8%` headroom 时重开。当前立即实验是 [perf-014-p16k-current-combination-entry.md](perf-014-p16k-current-combination-entry.md)：
对含 op010 的保留组合重建 P16384 Prefill/Decode/Mixed 入口证据；三阶段有效后再决定是否做
post-op010 P16K reprofile，不从 P4K 结果外推 P16K 加速比。

`plan-027/028` 完成了当前组合 P16K 入口与首个候选审计。`perf-014`
的 Prefill/Decode/Mixed 吞吐中位分别为 7699.05 total tok/s、210.085 output tok/s
和 281.458 output tok/s。`op-023` 的 native `mm_out` 原始 A/B/R 信号为 +3.081%，
但 comparator 因冻结合同漏列角色元数据而 `incomplete`，只作诊断证据。`op-024`
则得到完整有效的负结果：4352 相对 8448 的 A/R 中点输出/总吞吐均
`-0.2517%`，duration 反而更慢 `0.2517%`；因此不扩 D1024、不部署 4352。
当前立即实验切换为 [prof-007-p16k-post-op010-reprofile.md](prof-007-p16k-post-op010-reprofile.md)，
用 async+TP0–7 刷新当前 Prefill/Decode/Mixed 热点，再冻结下一个可证伪候选。

`prof-007` 已完成当前组合的全 rank P16K 归因。Decode device activity 中
QSA sparse+MQA、fused MoE、native GEMM 和 AllReduce 的跨 rank 中位分别是
29.497s、23.719s、17.618s 和 10.510s；Mixed 中分别是 9.479s、7.315s、
5.615s 和 2.961s。general GEMM 为 0，op010 路径确实命中。主要 rank 不均衡
来自 AllReduce/sync，QSA/MoE/GEMM 自身各 rank 接近。当前并行执行三件事：
仅 D128 的 op023 repaired-contract 复测、排除旧失败路线的 QSA 候选审计，
以及 fused-MoE 新机制审计。profiler-on 吞吐下降 14.0567% 只是观察开销，
不作为优化收益。

`plan-033`（2026-09-24 只读规划复盘）把当前 acc-011 服务与旧实验严格分开：
8000/8010 均健康，现态为 maxseq32、batch4096、无 QSA 静态边界、无 M64 tuned folder、
native `mm` + FlagGems `mm_out`。旧 [perf-015](perf-015-p16k-post-rb001-unbounded-entry.md)
三阶段原始回执其实已完整，但属于 maxseq64/tuned-MoE/native-mmout 的另一身份，不能
作为现态 baseline。当前 [op-027](op-027-current-service-native-mmout.md) 只证明
P16K/D128 同卡 provider 切换的 +2.7365%，候选未部署。新方向优先检验
`max-num-seqs 32→64` 是否能减少 C64 分批准入，同时严守 P99 ITL、KV 抢占和
完整 GPQA；P1K 曾出现吞吐提高但 ITL 大幅恶化，故不能直接应用。第二个候选是
[fw-015 长度感知双路由](fw-015-length-aware-dual-qsa-routing.md)：只给实际 token
预算不超过 33792 的请求使用 bounded QSA，所有长/模糊请求 fail-closed 到无边界服务；
旧 bounded/unbounded 性能差仅是跨时历史信号，不是当前净收益。首步是给现态建立
P16K Prefill/Decode/Mixed 无 profiler 三视图，再做独立单变量 A/B/R；若阶段证据
仍不能归因，才按当前源码/服务重新 profiling。旧 no-async、Simple collective、
全局 QSA 静态 cap、M64 小 shape 和盲目增大 batched-token 的路线暂缓。

`plan-034`（2026-09-28 复盘）将 [perf-016](perf-016-current-acc011-p16k-three-phase-entry.md)
的当前配置三视图固定为 Prefill 5713.816 total tok/s、Decode 181.107 output tok/s、
Mixed 182.540 output tok/s；三者均为 3+3、零失败，不能与旧不同配置结果相减。
[fw-016](fw-016-p16k-maxseq32-to64-current-acc011.md) 的 maxseq64 候选相对同卡 A
只有 +0.354% 输出吞吐，低于预冻结 +1% 门槛；R 在 graph replay 后中断，故无完整
A/B/R 比较回执或漂移结论。原 8010 已恢复，两个端口健康，64 未部署。当前 Mixed
TTFT 明显高于 C32 Decode，但输出吞吐几乎相同；maxseq64 下仍观测到排队且 KV
占用低，说明单纯调准入上限不是可靠方向。下一步优先为已通过 D128 A/B/R 的
[op-027 native `mm_out`](op-027-current-service-native-mmout.md) 补最小精度、全量 GPQA
和 D1024 同配置验证；若无法通过或阶段归因不清，再对当前 TP0–7 做有界 scheduler/
Prefill/Decode trace。旧 acc-011 175/198 回执不自动绑定新服务，不宣布累计或正式 P16K
收益。
