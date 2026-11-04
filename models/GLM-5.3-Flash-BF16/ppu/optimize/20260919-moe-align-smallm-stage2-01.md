# 20260919-moe-align-smallm-stage2-01 MoE align stage2

- 状态：`reverted`
- 分类：`operator/improve`
- 目标场景：P1024/D1024/C64/N128
- 目标阶段：Decode
- 依赖：small-M MoE routing/alignment

## 优化方向与瓶颈依据

small-M GEMM2 后的 reprofile 将 `moe_align_block_size_stage2` 列为后续 Decode
热点，旧 trace 占比约 7.68%。

## 优化内容与适用边界

为非 2 次幂专家数优化 stage2 padded vector cumsum；仅针对 PPU/E288 small-M
source path，其他路径 fallback。

## 正确性与路径命中

M=10/16/24/31/32、3 seed 共 15 组全部通过 eager、graph capture 和两次 replay；
落源后测试 34/34 通过。原记录仅证明顶层 provider 命中；2026-09-22 补充的
候选 trace 证明特化 kernel 命中数为 0，老 stage2 仍执行 2772 次。

## 性能效果

独立算子整体中位 3.883×，source-path 五个 shape 中位 3.635×。端到端结果：

| 角色 | 输出吞吐 | P99 TTFT | P99 TPOT |
|---|---:|---:|---:|
| baseline | 1011.168 tok/s | 35.249 s | 31.397 ms |
| candidate | 997.942 tok/s | 36.338 s | 31.867 ms |
| revert | 1002.872 tok/s | 36.167 s | 31.838 ms |

吞吐 -1.308%，TTFT/TPOT 分别回退 3.089%/1.495%。

## 决定、风险与回退

更正结论：候选因生产 `expert_map != None` 未命中，因此该 A/B/R 对特化的
端到端效果是 `inconclusive`，`-1.308%` 只能视为同有效路径漂移，不是局部收益
被关键路径抵消的证据。源码补丁已移除，未提交、未推送。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p1024-d1024-c64-n128/candidates/moe-align-smallm-stage2-01`
