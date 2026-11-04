# fw-011-p4k-scheduler-framework-frontier

- 实验 ID：`fw-011-p4k-scheduler-framework-frontier`；分类：`framework`；原记录状态：`stopped_before_experiment`。
- 来源：[state.yml](state.yml) 同 ID 条目；本次为历史记录整理，没有重跑评测。

## 优化方向与瓶颈依据

优化方向由实验名标识：p4k scheduler framework frontier。历史条目没有单列的场景、阶段和瓶颈数值保持待核验，不补造。

## 优化内容与适用边界

This audit excludes re-sweeping max_num_batched_tokens 6144/8192, long_prefill_token_threshold2048, and max_num_seqs48/64. No remote run or source/service change was performed. Reopen scheduler work only after low-overhead evidence proves a removable host scheduler critical-path gap above 1% Mixed wall.

## 正确性与路径命中

已记录验证结论见下方原始结果及外部证据。未单列的最小回归、完整精度或 graph 检查保持待核验，不由性能通过推定精度通过。

## 性能效果

Current async scheduling is already enabled and the V1 scheduler is already running-first. Concurrent partial-prefill controls are unsupported or not consumed, DP prefill_schedule_interval is inert at DP1, reserve_full_isl cannot reduce a P4096 prompt that equals the 4096 token budget, and the remaining existing controls either change ITL semantics, reduce capacity, or lack a credible 1% Mixed mechanism.

保留原记录的单位与结论边界；缺失的同 workload baseline/candidate/revert、波动及守护项不补算。

## 决定、风险与回退

- 原决定：`no_go_no_new_equivalent_single_variable_candidate`。
- 回退与风险以外部原始契约为准；本次未部署或执行回退。
- 继承的正式精度阻塞不会因补文档而解除。

## 外部证据

- `docs/cases/20260919-qwen38-flash-next-ppu-e2e/p4k-scheduler-framework-frontier-readonly.md`
