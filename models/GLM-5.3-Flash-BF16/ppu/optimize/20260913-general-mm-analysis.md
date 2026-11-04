# 20260913-general-mm-analysis General MM backend 对照

- 状态：`failed`
- 分类：`operator/replace`
- 目标场景：P1K Decode 的七个 BF16 shape
- 目标阶段：Decode
- 依赖：native MM 与 FlagGems MM

## 优化方向与瓶颈依据

profile 中 general MM 占有可见设备时间，因此比较 FlagGems 与当前 native 路径，
判断是否应从默认 `mm` 黑名单释放。

## 优化内容与适用边界

从 trace 提取七个精确 BF16 shape，在相同输入、正确性和 graph 条件下直接比较两个
backend；没有修改服务配置。

## 正确性与路径命中

七个 shape 的数值与 graph 均有效，比较的是实际实现而非 fallback。

## 性能效果

FlagGems 在六个主要 shape 上仅达到 native 的 0.202×～0.382×，另一个 shape
近似持平；没有任何可晋级的替换收益。

## 决定、风险与回退

决定拒绝 FlagGems MM，继续保留 `mm` 黑名单和 native 路径。没有源码改动。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/general-mm-analysis`
- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/general-mm-analysis/decode-trace-shapes-01`

