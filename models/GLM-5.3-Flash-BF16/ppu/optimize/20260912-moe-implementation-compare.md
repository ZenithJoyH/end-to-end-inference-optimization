# 20260912-moe-implementation-compare MoE 实现对照

- 状态：`failed`
- 分类：`operator/replace`
- 目标场景：MoE Prefill/Mixed
- 目标阶段：Prefill / Mixed
- 依赖：reference、native sum 与当前 fused-MoE

## 优化方向与瓶颈依据

比较现有 MoE 实现，判断是否可通过整体 backend 替换而不是继续调优当前 kernel。

## 优化内容与适用边界

分别对照 reference、native sum、native alignment 与当前 fused 路径；未改变模型
路由或专家语义。

## 正确性与路径命中

reference 与 native sum 的性能均不占优；native alignment 的等价性证据不足，未进入
服务候选。

## 性能效果

reference 更慢，native sum 更慢；native alignment 因等价性未证明而没有可接受的
端到端数字。

## 决定、风险与回退

决定拒绝整体实现替换，继续保留 fused-MoE，并转向严格 shape-gated 的 stage config。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/moe-implementation-compare`

