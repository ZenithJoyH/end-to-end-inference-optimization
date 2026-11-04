# op-005-qsa-row-range-topk

- 实验 ID：`op-005-qsa-row-range-topk`；分类：`operator/improve`；原记录状态：`complete`。
- 来源：[state.yml](state.yml) 同 ID 条目；本次为历史记录整理，没有重跑评测。

## 优化方向与瓶颈依据

优化方向由实验名标识：qsa row range topk。历史条目没有单列的场景、阶段和瓶颈数值保持待核验，不补造。

## 优化内容与适用边界

Rejected and fully reverted. Post-revert FlagGems tracked source was clean; no row-range code remains in the retained candidate.

## 正确性与路径命中

已记录验证结论见下方原始结果及外部证据。未单列的最小回归、完整精度或 graph 检查保持待核验，不由性能通过推定精度通过。

## 性能效果

The isolated row-range provider microbenchmark passed correctness and graph checks, but exact P4K Mixed service output throughput improved only 1.66%; P99 ITL improved 4.80%. This missed the frozen 3% throughput threshold.

保留原记录的单位与结论边界；缺失的同 workload baseline/candidate/revert、波动及守护项不补算。

## 决定、风险与回退

- 原决定：`rejected_reverted_below_service_gain_threshold`。
- 回退与风险以外部原始契约为准；本次未部署或执行回退。
- 继承的正式精度阻塞不会因补文档而解除。

## 外部证据

- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/p4k-qsa-row-range-mixed-candidate-summary-02.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/patches/op-005-qsa-row-range-topk-revert-06`
