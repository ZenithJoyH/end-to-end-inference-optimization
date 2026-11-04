# 20260914-nonzero-blacklist nonzero 算子黑名单

- 状态：`reverted`
- 分类：`operator/replace`
- 目标场景：P1024/D1024/C64/N128
- 目标阶段：Mixed
- 依赖：thead FlagOS blacklist

## 优化方向与瓶颈依据

Mixed trace 中 `aten::nonzero` 与 to/copy/synchronize 链有较高 inclusive 时间，并有
FlagGems 相关告警；尝试切回 reference/native 路径。

## 优化内容与适用边界

单变量将 `nonzero` 加入 thead 黑名单，其他路由和服务参数不变。

## 正确性与路径命中

告警消失，说明黑名单生效；但候选没有在冻结预热预算内形成稳定可比较的服务结果。

## 性能效果

预热稳定性和吞吐晋级门槛均未通过，没有有效 measured 提升可报告。

## 决定、风险与回退

决定回退 `nonzero` 黑名单。原因是告警消失不等于关键路径改善，且 inclusive CPU
时间存在重叠。thead YAML 恢复原配置。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p1024-d1024-c64-n128`

