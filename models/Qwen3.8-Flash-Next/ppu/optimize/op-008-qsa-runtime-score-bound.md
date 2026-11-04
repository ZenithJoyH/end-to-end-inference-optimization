# op-008-qsa-runtime-score-bound

- 实验 ID：`op-008-qsa-runtime-score-bound`；分类：`framework_plus_operator/improve`；当前状态：`inactive_after_parent_bound_rollback`。
- 来源：[state.yml](state.yml) 同 ID 条目；本次为历史记录整理，没有重跑评测。

## 优化方向与瓶颈依据

优化方向由实验名标识：qsa runtime score bound。历史条目没有单列的场景、阶段和瓶颈数值保持待核验，不补造。

## 优化内容与适用边界

The first patch attempt failed on malformed hunk metadata and made no source change. The repaired patch is active in service-35; full Plugin diff SHA-256 is 19741357cd4283852ad1540c68353089cb9ea10e5c9cc997852bc28e5c45c461. Full checkpoint summary SHA-256 is df5dbd22eaa7fbc985aa7a78469a93fdf7e41a3554aa111be0c3ec4c80f54f93. This is a performance-only P16K checkpoint with a scoped minimal regression, not formal acceptance; inherited GPQA remains below threshold and independent-process formal validation is not closed.

## 正确性与路径命中

已记录验证结论见下方原始结果及外部证据。未单列的最小回归、完整精度或 graph 检查保持待核验，不由性能通过推定精度通过。

## 性能效果

Six boundary tests and 24 graph replays passed. Non-capture P16K uses aligned score width 4352 while full-graph Decode capture retains static 8448 and P32K remains capped at 8448. Relative to the op006 scenario-entry baseline, exact Prefill total-token throughput improved 9.463%, full Decode output throughput improved 3.589%, and exact Mixed output throughput improved 4.900%; every measured median/P99 latency guard improved, all requests succeeded, and warmups were stable. The repaired 16K paired semantic regression passed every warmup and both measured waves at 8/8 on candidate and revert with identical text-hash sets.

保留原记录的单位与结论边界；缺失的同 workload baseline/candidate/revert、波动及守护项不补算。

## 决定、风险与回退

- 原决定 `retain_performance_checkpoint_pending_formal_accuracy` 已被 [rb-001](rb-001-qsa-score-bound-rollback.md) 取代。
- 当前候选不设置静态 score bound；`_qsa_runtime_score_columns(None, ...)` 返回 `None`，FlagGems 使用完整 `capacity`。因此本实现保留在源码中但不再激活，也不计入当前组合收益。
- 若后续为 PR 物理移除该可选实现，应在独立清理改动中完成；本次功能回退不修改共享导入源码。

## 外部证据

- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/commands/op008-qsa-runtime-score-bound-v2.patch`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/patches/op008-qsa-runtime-score-bound-apply02/plugin-diff-after.patch`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/smoke/op008-qsa-runtime-bound-graph-01/canonical.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/p16k-op008-prefill-vs-op006-summary-01.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/p16k-d128-mixed-op008-abr-summary-01.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/p16k-op008-full-checkpoint-summary-01.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/op008-long-context-chat-minreg-03/result.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/manifests/candidate-maxseq64-bt4096-qsa-runtime-bound8448-moe-bm16-service-35.json`
