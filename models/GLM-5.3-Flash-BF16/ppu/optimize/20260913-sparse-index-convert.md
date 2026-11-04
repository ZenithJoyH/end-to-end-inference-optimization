# 20260913-sparse-index-convert Sparse Index 转换优化

- 状态：`reverted`
- 分类：`operator/improve`
- 目标场景：Sparse MLA Prefill/Mixed
- 目标阶段：Prefill / Mixed
- 依赖：外围索引转换 kernel

## 优化方向与瓶颈依据

vendor sparse MLA 外围存在索引转换开销，尝试通过增大 `BLOCK_N` 降低转换 kernel
时长和 launch 数。

## 优化内容与适用边界

把辅助索引转换的 `BLOCK_N` 调整为 1024；不修改 sparse attention 主 kernel。

## 正确性与路径命中

目标 shape 微基准和服务均能运行，候选确实命中辅助 kernel；没有数值回归。

## 性能效果

三个主 shape 的辅助 kernel 微基准提升 3.55×～4.54×，但端到端
P4096/D128/C32 为 -0.041%，P1024/D512/C32 为 -0.005%，没有服务收益。

## 决定、风险与回退

因算子局部收益未进入关键路径，决定回退。补丁已移除，原转换配置恢复。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/sparse-index-convert`
- comparison SHA-256：`2f44b4c7b3a2509fd3e4a8a906d12421ccba013bef7c127a53ad562d72c6b337`

