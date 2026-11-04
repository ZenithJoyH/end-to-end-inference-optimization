# fw-005-p4k-max-batched-tokens6144

- 实验 ID：`fw-005-p4k-max-batched-tokens6144`；分类：`framework`；原记录状态：`complete`。
- 来源：[state.yml](state.yml) 同 ID 条目；本次为历史记录整理，没有重跑评测。

## 优化方向与瓶颈依据

优化方向由实验名标识：p4k max batched tokens6144。历史条目没有单列的场景、阶段和瓶颈数值保持待核验，不补造。

## 优化内容与适用边界

Rejected and reverted. The 6144 and 8192 screens show monotonic P99 ITL degradation as admission budget increases, so no further blind scheduler-budget scan is planned. Service-15 restored 4096 plus the exact M64 BM16 config and passed graph/startup/content checks.

## 正确性与路径命中

已记录验证结论见下方原始结果及外部证据。未单列的最小回归、完整精度或 graph 检查保持待核验，不由性能通过推定精度通过。

## 性能效果

Output-throughput median improved only 1.35% from 452.18 to 458.30 tok/s, below the frozen 3% threshold. P99 ITL regressed 36.54% from 756.22 to 1032.50ms and warmup stability failed, while P99 TTFT/TPOT/E2E remained within guard. All measured rounds completed 128/128 with zero failures.

保留原记录的单位与结论边界；缺失的同 workload baseline/candidate/revert、波动及守护项不补算。

## 决定、风险与回退

- 原决定：`reverted_failed_throughput_tail_latency_and_warmup_stability_guards`。
- 回退与风险以外部原始契约为准；本次未部署或执行回退。
- 继承的正式精度阻塞不会因补文档而解除。

## 外部证据

- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/transitions/p4k-maxbt4096-to6144-service-14/p4k-maxbt4096-to6144-service-14-raw.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/smoke/p4k-maxbt6144-graph-01/canonical.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/p4k-maxbt6144-mixed-candidate-01/run-record.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/p4k-maxbt6144-mixed-candidate-summary-01.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/transitions/p4k-maxbt6144-failed-restored4096-service-15/p4k-maxbt6144-failed-restored4096-service-15-raw.json`
