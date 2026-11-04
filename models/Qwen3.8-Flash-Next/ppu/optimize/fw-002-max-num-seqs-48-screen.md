# fw-002-max-num-seqs-48-screen

- 实验 ID：`fw-002-max-num-seqs-48-screen`；分类：`framework`；原记录状态：`complete`。
- 来源：[state.yml](state.yml) 同 ID 条目；本次为历史记录整理，没有重跑评测。

## 优化方向与瓶颈依据

优化方向由实验名标识：max num seqs 48 screen。历史条目没有单列的场景、阶段和瓶颈数值保持待核验，不补造。

## 优化内容与适用边界

Maxseq48 is non-dominant only when weighting throughput against ITL; it does not improve any measured latency guard versus maxseq32 and is not selected for A/B/R without an explicit SLO.

## 正确性与路径命中

已记录验证结论见下方原始结果及外部证据。未单列的最小回归、完整精度或 graph 检查保持待核验，不由性能通过推定精度通过。

## 性能效果

Measured output-throughput median 417.28 tok/s (+26.17%), P99 TTFT median 110491.92 ms (+5.33%), P99 E2E median 216908.61 ms (+7.34%), P99 TPOT median 104.65 ms (+8.48%), and P99 ITL median 107.28 ms (+12.98%) versus maxseq32. Three measured rounds completed 128/128 requests; warmup output-throughput spread 0.594%. Graph replay canonical matched maxseq32.

保留原记录的单位与结论边界；缺失的同 workload baseline/candidate/revert、波动及守护项不补算。

## 决定、风险与回退

- 原决定：`retain_as_diagnostic_pareto_reference_not_formal`。
- 回退与风险以外部原始契约为准；本次未部署或执行回退。
- 继承的正式精度阻塞不会因补文档而解除。

## 外部证据

- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/transitions/maxseq48-screen-01/candidate-maxseq48-raw.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/smoke/maxseq48-screen-01/canonical.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/maxseq48-mixed-candidate-01/run-record.json`
