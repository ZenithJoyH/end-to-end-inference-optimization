# fw-003-maxseq64-max-batched-tokens2048

- 实验 ID：`fw-003-maxseq64-max-batched-tokens2048`；分类：`framework`；原记录状态：`complete`。
- 来源：[state.yml](state.yml) 同 ID 条目；本次为历史记录整理，没有重跑评测。

## 优化方向与瓶颈依据

优化方向由实验名标识：maxseq64 max batched tokens2048。历史条目没有单列的场景、阶段和瓶颈数值保持待核验，不补造。

## 优化内容与适用边界

Throughput and E2E guards passed, but the primary ITL recovery threshold failed and TPOT regressed. Do not retain or proceed to A/B/R.

## 正确性与路径命中

已记录验证结论见下方原始结果及外部证据。未单列的最小回归、完整精度或 graph 检查保持待核验，不由性能通过推定精度通过。

## 性能效果

Versus maxseq64/batched4096, output-throughput median fell 3.48% to 550.67 tok/s, P99 TTFT rose 31.49% to 16358.00 ms, P99 E2E rose 6.50% to 132621.29 ms, and P99 TPOT rose 2.98% to 114.21 ms. P99 ITL improved 19.25% to 507.11 ms, below the pre-frozen 30% recovery threshold. Three measured rounds completed 128/128 requests; warmup output-throughput spread 0.357%. Graph replay canonical matched.

保留原记录的单位与结论边界；缺失的同 workload baseline/candidate/revert、波动及守护项不补算。

## 决定、风险与回退

- 原决定：`reverted_failed_prefrozen_guard_recovery_threshold`。
- 回退与风险以外部原始契约为准；本次未部署或执行回退。
- 继承的正式精度阻塞不会因补文档而解除。

## 外部证据

- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/transitions/maxseq64-bt2048-screen-01/candidate-maxseq64-bt2048-raw.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/smoke/maxseq64-bt2048-screen-01/canonical.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/maxseq64-bt2048-mixed-candidate-01/run-record.json`
