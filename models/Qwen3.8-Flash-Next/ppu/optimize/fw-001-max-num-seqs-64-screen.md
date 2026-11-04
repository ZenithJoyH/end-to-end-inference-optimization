# fw-001-max-num-seqs-64-screen

- 实验 ID：`fw-001-max-num-seqs-64-screen`；分类：`framework`；原记录状态：`complete`。
- 来源：[state.yml](state.yml) 同 ID 条目；本次为历史记录整理，没有重跑评测。

## 优化方向与瓶颈依据

优化方向由实验名标识：max num seqs 64 screen。历史条目没有单列的场景、阶段和瓶颈数值保持待核验，不补造。

## 优化内容与适用边界

Single service-instance screen only. Independent-instance A/B/R is required before formal retention. No user SLO is frozen, so maxseq64 is not selected as a final configuration.

## 正确性与路径命中

已记录验证结论见下方原始结果及外部证据。未单列的最小回归、完整精度或 graph 检查保持待核验，不由性能通过推定精度通过。

## 性能效果

Measured output-throughput median 570.53 tok/s (+72.51%), P99 TTFT median 12440.27 ms (-88.14%), and P99 E2E median 124524.00 ms (-38.38%). P99 TPOT regressed 14.97% to 110.91 ms and P99 ITL regressed 561.37% to 628.03 ms. Three measured rounds completed 128/128 requests; warmup output-throughput spread 0.137%. Graph replay canonical matched maxseq32.

保留原记录的单位与结论边界；缺失的同 workload baseline/candidate/revert、波动及守护项不补算。

## 决定、风险与回退

- 原决定：`retain_as_pareto_screening_candidate_not_formal`。
- 回退与风险以外部原始契约为准；本次未部署或执行回退。
- 继承的正式精度阻塞不会因补文档而解除。

## 外部证据

- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/transitions/maxseq64-screen-02/candidate-maxseq64-raw.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/smoke/maxseq64-screen-02/canonical.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/maxseq64-mixed-candidate-01/run-record.json`
