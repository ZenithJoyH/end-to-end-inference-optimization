# 20260911-index-op-blacklist index 算子黑名单

- 状态：`retained`
- 分类：`operator/replace`
- 目标场景：GLM-5.3-Flash PPU 服务通用路径
- 目标阶段：Prefill / Mixed
- 依赖：Plugin thead FlagOS 配置

## 优化方向与瓶颈依据

运行日志与调优行为表明 FlagGems `index` 路径存在额外调优和稳定性风险。目标是让
该算子继续使用已验证的 reference/native 路径，避免服务期间进入收益不确定的实现。

## 优化内容与适用边界

将 `index` 加入 thead FlagOS 黑名单；默认已有的 `mm` 黑名单保持不变。配置最终
收敛到 thead YAML，未命中的平台与算子不受影响。

## 正确性与路径命中

后续服务、精度和性能实验均使用该黑名单组合；正式精度维持
`172/198=86.87% >= 86%`。没有把“服务可运行”解释成该单点的独立性能收益。

## 性能效果

本优化点没有隔离的同 workload A/B 数值，因此不声明独立吞吐提升。效果边界是
避免进入不稳定/调优成本较高的 `index` 实现，并作为后续稳定基线的一部分保留。

## 决定、风险与回退

决定为保留。若未来 FlagGems `index` 在 live shape 上完成正确性、graph 和服务级
A/B，可从黑名单移除；回退即删除 thead YAML 中的 `index` 条目。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/index-op-blacklist`
- Plugin 提交：`85302a7`（已推送）

