# fw-004-p4k-max-batched-tokens8192

- 实验 ID：`fw-004-p4k-max-batched-tokens8192`；分类：`framework`；原记录状态：`complete`。
- 来源：[state.yml](state.yml) 同 ID 条目；本次为历史记录整理，没有重跑评测。

## 优化方向与瓶颈依据

优化方向由实验名标识：p4k max batched tokens8192。历史条目没有单列的场景、阶段和瓶颈数值保持待核验，不补造。

## 优化内容与适用边界

The candidate failed two pre-frozen guards and was reverted. Service-13 restored max_num_batched_tokens=4096 in the same container/card group while preserving the exact M64 BM16 tuned config; graph capture, readiness, config-hit logging, and repository hashes passed.

## 正确性与路径命中

已记录验证结论见下方原始结果及外部证据。未单列的最小回归、完整精度或 graph 检查保持待核验，不由性能通过推定精度通过。

## 性能效果

Output-throughput median improved 3.14% from 452.18 to 466.39 tok/s, P99 TTFT improved 11.20%, P99 TPOT improved 1.93%, and P99 E2E improved 4.83%. However P99 ITL regressed 74.42% from 756.22 to 1319.02ms and the three-round warmup stability check failed. All measured rounds completed 128/128 requests with zero failures.

保留原记录的单位与结论边界；缺失的同 workload baseline/candidate/revert、波动及守护项不补算。

## 决定、风险与回退

- 原决定：`reverted_failed_tail_latency_and_warmup_stability_guards`。
- 回退与风险以外部原始契约为准；本次未部署或执行回退。
- 继承的正式精度阻塞不会因补文档而解除。

## 外部证据

- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/manifests/candidate-maxseq64-bt8192-moe-bm16-service-screen-12.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/smoke/p4k-maxbt8192-graph-01/canonical.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/p4k-maxbt8192-mixed-candidate-01/run-record.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/p4k-maxbt8192-mixed-candidate-summary-01.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/transitions/p4k-maxbt8192-failed-restored4096-service-13/p4k-maxbt8192-failed-restored4096-service-13-raw.json`
