# op-001-qsa-static-score-columns

- 实验 ID：`op-001-qsa-static-score-columns`；分类：`operator/improve`；原记录状态：`complete`。
- 来源：[state.yml](state.yml) 同 ID 条目；本次为历史记录整理，没有重跑评测。

## 优化方向与瓶颈依据

优化方向由实验名标识：qsa static score columns。历史条目没有单列的场景、阶段和瓶颈数值保持待核验，不补造。

## 优化内容与适用边界

A global 512 bound is unsafe beyond P1K/D1K. Do not integrate until scheduler/graph buckets prove a conservative bound for P4K/P16K/P32K and arbitrary requests.

## 正确性与路径命中

已记录验证结论见下方原始结果及外部证据。未单列的最小回归、完整精度或 graph 检查保持待核验，不由性能通过推定精度通过。

## 性能效果

Full-capacity 20000 to static 512 columns preserved effective selected-token sets, downstream BF16 sparse output, graph capture, and two replays. Rows64 selection/transaction speedups were 4.06x/1.99x; rows4096 were 22.16x/2.64x.

保留原记录的单位与结论边界；缺失的同 workload baseline/candidate/revert、波动及守护项不补算。

## 决定、风险与回退

- 原决定：`defer_service_integration_until_safe_long_sequence_graph_bucketing`。
- 回退与风险以外部原始契约为准；本次未部署或执行回退。
- 继承的正式精度阻塞不会因补文档而解除。

## 外部证据

- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/qsa-column-bound-001/result.json`
