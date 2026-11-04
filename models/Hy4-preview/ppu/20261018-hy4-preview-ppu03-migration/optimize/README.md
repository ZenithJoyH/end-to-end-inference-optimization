# 20261018-hy4-preview-ppu03-migration / optimize

完整198题GPQA C64已完成，strict-match **183/198=92.4242%**，高于预冻结87%阈值。原参数、官方原runner、独立UUID和数据指纹未改变；396样本行对应198题×2filters，每题strict/ flexible各一次。前后服务、完整四包/仓源码、131权重文件身份清单、tokenizer和启动配置一致，acceptance issue/check通过，42文件/28141872字节原生证据已SHA备份。heartbeat hy4-ppu-03已PAUSED。

当前结论见[acc006](acc-006.md)。以下包含历史记录，当前状态以本节和原生gate为准。

用户启动脚本已对齐 acc-006 的 FULL_AND_PIECEWISE/TP16/100K/2048/0.85 和运行环境，已备份、静态校验，未执行或启动服务；见[env-032](env-032.md)。

<!-- e2e:summary:start -->

- 案例：20261018-hy4-preview-ppu03-migration
- 当前状态：env031_acc006_full198_accuracy_passed
- 当前候选：env031-FGV45e14232-original2048
- 下一步：User-requested accuracy complete; retain2048, no new performance/code changes; gate invalidated by identity/config change

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| env-032 | user_launcher_aligned_to_acc006_no_service_start | — | [env-032.md](env-032.md) |
| env-001 | retained_source_but_formal_not_accepted | hy4-startup-smoke-c8 | [env-001.md](env-001.md) |
| acc-001 | not_accepted | — | [acc-001.md](acc-001.md) |
| env-002 | retained_pending_formal_accuracy | — | [env-002.md](env-002.md) |
| acc-002 | stopped_on_user_request | — | [acc-002.md](acc-002.md) |
| env-003 | retained_upstream_as_requested_runtime_unsupported_on_ppu | — | [env-003.md](env-003.md) |
| env-004 | superseded_architecture_rejected | — | [env-004.md](env-004.md) |
| acc-003 | stopped_for_architecture_refactor | — | [acc-003.md](acc-003.md) |
| env-005 | source_superseded_service06_stopped_in_env011 | — | [env-005.md](env-005.md) |
| acc-004 | not_started_user_review_hold | — | [acc-004.md](acc-004.md) |
| env-006 | deployed_in_env008 | — | [env-006.md](env-006.md) |
| env-007 | deployed_in_env008 | — | [env-007.md](env-007.md) |
| env-008 | deployed_as_requested_service_not_reloaded | — | [env-008.md](env-008.md) |
| env-009 | broad_platform_selection_withdrawn_in_env011 | — | [env-009.md](env-009.md) |
| env-010 | superseded_by_scoped_env011 | — | [env-010.md](env-010.md) |
| env-011 | retained_minimal_pass_formal_accuracy_not_established | hy4-startup-smoke-c8-paged | [env-011.md](env-011.md) |
| env-012 | tests_removed_production_unchanged_review_exported | — | [env-012.md](env-012.md) |
| env-013 | source_deployed_for_review_pending_model_validation | hy4-startup-smoke-c8-paged | [env-013.md](env-013.md) |
| env-014 | source_deployed_for_review_pending_model_validation | — | [env-014.md](env-014.md) |
| env-015 | source_deployed_for_review_pending_model_validation | — | [env-015.md](env-015.md) |
| env-016 | retained_narrow_quant_boundary_operator_passed_model_pending | — | [env-016.md](env-016.md) |
| env-017 | source_deployed_operator_passed_model_pending | — | [env-017.md](env-017.md) |
| env-018 | shared_ABI_fixed_redundant_TopK_file_removed_model_pending | — | [env-018.md](env-018.md) |
| env-019 | review_complete_findings_reported_no_source_change | — | [env-019.md](env-019.md) |
| env-020 | one_line_layout_fix_deployed_operator_scope_passed_model_pending | — | [env-020.md](env-020.md) |
| env-021 | padding_graph_fix_deployed_operator_scope_passed_model_pending | — | [env-021.md](env-021.md) |
| env-022 | current_combined_candidate_service_minimal_regression_passed_formal_held | — | [env-022.md](env-022.md) |
| env-023 | offline_candidate_ready_for_user_review_not_deployed | — | [env-023.md](env-023.md) |
| env-024 | offline_candidate_ready_for_user_review_not_deployed | — | [env-024.md](env-024.md) |
| env-025 | reviewed_changes_installed_source_verified_runtime_not_reloaded | — | [env-025.md](env-025.md) |
| env-026 | review_complete_three_local_cleanup_candidates_no_source_change | — | [env-026.md](env-026.md) |
| env-027 | three_local_cleanups_installed_CPU_contract_passed_model_pending | — | [env-027.md](env-027.md) |
| env-028 | current_env027_service_minimal_regression_passed_formal_held | — | [env-028.md](env-028.md) |
| acc-005 | stopped_on_user_request_for_performance_and_graph_mode_review | — | [acc-005.md](acc-005.md) |
| env-029 | not_accepted_preserve_failing_instance_for_diagnosis | — | [env-029.md](env-029.md) |
| env-030 | retained_one_file_boundary_fix_minimal_regression_passed_formal_held | — | [env-030.md](env-030.md) |
| env-031 | installed_and_runtime_reloaded_minimal_passed_fullGPQA_pending | — | [env-031.md](env-031.md) |
| acc-006 | passed_frozen87pct_threshold_current_env031 | — | [acc-006.md](acc-006.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|

<!-- e2e:summary:end -->

env030已用一文件最小修复解决当前PPU上FULL_AND_PIECEWISE短输入答非所问：BF16 indexer缺失splitting_ops边界，捕获dummy metadata=None后replay跳过真实索引/cache写入。只在该indexer构造处幂等补边界，计算/dispatch不变。两个gems-opt、vLLM、权重和tokenizer均未改；未开始评测，旧acc005保持取消、heartbeat暂停。

见[env030验证](env-030.md)。
