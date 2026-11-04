# fw-006-p4k-long-prefill-threshold2048

- 实验 ID：`fw-006-p4k-long-prefill-threshold2048`；分类：`framework`；原记录状态：`complete`。
- 来源：[state.yml](state.yml) 同 ID 条目；本次为历史记录整理，没有重跑评测。

## 优化方向与瓶颈依据

优化方向由实验名标识：p4k long prefill threshold2048。历史条目没有单列的场景、阶段和瓶颈数值保持待核验，不补造。

## 优化内容与适用边界

Rejected at the pre-frozen primary guard and reverted before a formal A/B/R. Splitting scheduler long-Prefill chunks at 2048 did not shorten the device-side QSA-dominated graph windows enough to recover Mixed tail latency.

## 正确性与路径命中

已记录验证结论见下方原始结果及外部证据。未单列的最小回归、完整精度或 graph 检查保持待核验，不由性能通过推定精度通过。

## 性能效果

Steady candidate output-throughput median was about 449.08 tok/s, 0.69% below the 452.18 tok/s scenario-entry baseline. P99 ITL was about 759.38ms, 0.42% worse than baseline instead of the frozen 20% recovery, and the warmup series was unstable.

保留原记录的单位与结论边界；缺失的同 workload baseline/candidate/revert、波动及守护项不补算。

## 决定、风险与回退

- 原决定：`rejected_reverted_failed_primary_guard_and_warmup_stability`。
- 回退与风险以外部原始契约为准；本次未部署或执行回退。
- 继承的正式精度阻塞不会因补文档而解除。

## 外部证据

- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/p4k-longprefill2048-mixed-candidate-summary-early-stop-01.json`
