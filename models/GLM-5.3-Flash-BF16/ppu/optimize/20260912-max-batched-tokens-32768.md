# 20260912-max-batched-tokens-32768 早期 32768 token-budget

- 状态：`failed`
- 分类：`framework`
- 目标场景：多 workload，`max_num_seqs=32`
- 目标阶段：Prefill / Mixed
- 依赖：vLLM scheduler

## 优化方向与瓶颈依据

继续提高 batch token 上限，测试能否减少 Prefill admission 轮数并提高总吞吐。

## 优化内容与适用边界

仅将 `max_num_batched_tokens` 从 16384 调整为 32768；本实验属于早期
`max_num_seqs=32` 工作点，不能外推到 max64。

## 正确性与路径命中

首轮候选进程内离散超过 15%，第二轮完成了可用对照；请求语义未变。

## 性能效果

第二轮 P4096/D128/C32 从 234.844 提升到 240.790 tok/s（+2.532%），但
P1024/D512/C32 从 720.196 降到 709.227 tok/s（-1.523%）。首轮因稳定性不足
判 `incomplete`。

## 决定、风险与回退

一个主要 workload 回退且存在稳定性问题，决定拒绝并恢复 16384。后续 max64 下的
独立 32768 探针记录在 `20260919-maxseq64-mbt32768-01.md`。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/max-batched-tokens-32768`
- comparison SHA-256：`3edf9ac243221b05939529517543ac283cb4aaf63cfc1fca7c285af0615e55d7`
- comparison SHA-256：`6ee84fe01687c8b7f7e74f3fa8c83dfc5200dfeacb55ea551995c7668b693453`

