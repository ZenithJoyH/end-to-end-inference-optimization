# 20260914-gemm-m-key-bucketing GEMM M-key 分桶

- 状态：`reverted`
- 分类：`framework`
- 目标场景：P1024/D1024/C64/N128
- 目标阶段：Mixed / Decode
- 依赖：MM/Linear 调优 key 生成

## 优化方向与瓶颈依据

尝试用对数分桶减少动态 M 导致的调优 key 数量和运行时波动。

## 优化内容与适用边界

把 MM/Linear 的 M-key 从原对齐策略改为 `log` 分桶；同一冻结 DB 和 workload 下做
候选与回退对照。

## 正确性与路径命中

候选和回退均完成 3 预热 + 3 measured，服务正常；DB 对照表明稳定性主要来自离线
预热库，而非新分桶。

## 性能效果

| 角色 | 输出吞吐 | P99 TTFT | P99 TPOT |
|---|---:|---:|---:|
| baseline | 770.006 tok/s | 45.254 s | 41.335 ms |
| candidate | 768.293 tok/s | 45.177 s | 41.474 ms |

输出吞吐变化 -0.222%，P99 TTFT 改善 0.169%，P99 TPOT 回退 0.336%。

## 决定、风险与回退

吞吐主指标失败，决定回退并恢复 `align32`。回退结果也作为当前 P1K scenario-entry
baseline 使用。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p1024-d1024-c64-n128`
- candidate run：`candidates/gemm-m-key-bucketing-01/results/candidate-gemm-m-key-bucketing-02/run-record.json`
- revert run：`reverts/gemm-m-key-bucketing-01-results/revert-gemm-m-key-bucketing-01/run-record.json`

