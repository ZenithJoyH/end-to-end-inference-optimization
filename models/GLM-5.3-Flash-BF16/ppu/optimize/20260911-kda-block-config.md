# 20260911-kda-block-config KDA block 参数扫描

- 状态：`failed`
- 分类：`operator/improve`
- 目标场景：多 shape KDA
- 目标阶段：Prefill / Decode
- 依赖：当前 KDA kernel 的 BLOCK_V、warp 参数

## 优化方向与瓶颈依据

尝试通过 tile 与 warp 数调整降低 KDA kernel 延迟，同时要求不同 shape 均不回退。

## 优化内容与适用边界

对 `BLOCK_V` 和 warp 组合做有界单变量扫描；未改变算法、dtype 或服务调度。

## 正确性与路径命中

候选只作为算子级筛选，没有任何配置同时满足跨 shape 性能晋级条件，因此未进入
源码和服务级 A/B。

## 性能效果

没有候选通过冻结的跨 shape performance gate；未形成可保留的端到端收益。

## 决定、风险与回退

决定停止并保留原配置。不存在源码改动，因而无需额外回退。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/kda-block-config`

