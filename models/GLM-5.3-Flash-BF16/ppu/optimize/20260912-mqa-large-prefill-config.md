# 20260912-mqa-large-prefill-config 大 Prefill MQA 配置

- 状态：`failed`
- 分类：`operator/improve`
- 目标场景：large-Prefill MQA
- 目标阶段：Prefill
- 依赖：MQA Triton config

## 优化方向与瓶颈依据

在不切换 reference 实现的前提下，为大 Prefill shape 搜索更合适的 MQA tile 配置。

## 优化内容与适用边界

对两个代表性大 shape 做有界 config 微基准；不修改其他 MQA shape 的选择。

## 正确性与路径命中

候选完成微基准筛选，但没有达到进入源码和服务 A/B 的性能门槛。

## 性能效果

两个代表 shape 的最佳收益分别为 1.71% 和 1.91%，均低于 3% 晋级门槛。

## 决定、风险与回退

决定拒绝，没有落源。继续扩大搜索空间的预期端到端收益不足。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/mqa-large-prefill-config/microbench-01`

