# op-007-qsa-p16k-specific-bound-headroom

- 实验 ID：`op-007-qsa-p16k-specific-bound-headroom`；分类：`operator/improve`；原记录状态：`complete`。
- 来源：[state.yml](state.yml) 同 ID 条目；本次为历史记录整理，没有重跑评测。

## 优化方向与瓶颈依据

优化方向由实验名标识：qsa p16k specific bound headroom。历史条目没有单列的场景、阶段和瓶颈数值保持待核验，不补造。

## 优化内容与适用边界

Diagnostic headroom only. A global 4352 bound is unsafe for P32K and arbitrary longer requests, so it was not deployed. Candidate service-27 restored the unchanged 8448 configuration and passed source fingerprint, readiness, graph capture, and config guards.

## 正确性与路径命中

已记录验证结论见下方原始结果及外部证据。未单列的最小回归、完整精度或 graph 检查保持待核验，不由性能通过推定精度通过。

## 性能效果

P16K-specific bound 4352 exactly covers P16384+D1024 at compress ratio 4 and preserved selected sets, downstream BF16 output, graph capture, and two replays. Relative to the retained universal 8448 bound, complete QSA transaction improved another 1.249x for Prefill and 1.136x for Decode; graph replay improved 1.248x and 1.138x. Result SHA-256 bf67a0e78ea37bcc2c19b93cde7b0d5aa442c4f0c4dbb585f4b480a27ee0660a.

保留原记录的单位与结论边界；缺失的同 workload baseline/candidate/revert、波动及守护项不补算。

## 决定、风险与回退

- 原决定：`retain_diagnostic_reject_global_deployment`。
- 回退与风险以外部原始契约为准；本次未部署或执行回退。
- 继承的正式精度阻塞不会因补文档而解除。

## 外部证据

- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/qsa-p16k-specific-bound-005/result.json`
- `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/manifests/candidate-maxseq64-bt4096-qsa-bound8448-moe-bm16-service-27.json`
