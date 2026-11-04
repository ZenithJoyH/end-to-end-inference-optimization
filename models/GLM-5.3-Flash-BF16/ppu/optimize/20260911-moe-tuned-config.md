# 20260911-moe-tuned-config MoE 通用调优配置

- 状态：`failed`
- 分类：`operator/improve`
- 目标场景：large-M MoE
- 目标阶段：Prefill / Mixed
- 依赖：fused-MoE 通用 config 选择

## 优化方向与瓶颈依据

MoE 是设备侧热点，首先尝试用通用调优配置降低 large-M GEMM 延迟。

## 优化内容与适用边界

对 large-M 当前实现做有界 config 扫描，不改变 dispatch 或算法语义。

## 正确性与路径命中

候选完成算子筛选，但收益不足以进入服务级保留；原实现继续生效。

## 性能效果

最佳候选在两个主要 shape 上分别只改善约 1.01% 和 0.44%，低于预冻结 3%
晋级门槛。

## 决定、风险与回退

决定拒绝，没有落源。后续改为按 GEMM stage 和 live M 做更严格的 shape-gated
特化，而不是继续扩大通用配置搜索。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/moe-tuned-config`
