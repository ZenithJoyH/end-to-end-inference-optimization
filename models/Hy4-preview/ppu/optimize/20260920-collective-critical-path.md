# 20260920-collective-critical-path：AllReduce 暴露时间归因

- experiment-id：`20260920-collective-critical-path`
- 分类：`framework/diagnostic`
- 状态：`completed`

## 方向与结果

对 rank0 device 区间做并集分析。AllReduce 时间在 Prefill/Mixed/Decode 中
分别有 `96.75%/96.14%/96.15%` 未与其他 device kernel 重叠；暴露通信约占
GPU phase marker 的 `19.82%/10.14%/8.19%`。

## 决策与边界

排除“通信已基本隐藏”的解释，将按消息大小协议或 all-reduce+residual/norm
融合列为后续方向。该并集是关键路径上限代理，不是完整依赖 DAG，也不是收益。

