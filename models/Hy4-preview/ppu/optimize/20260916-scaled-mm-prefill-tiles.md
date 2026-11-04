# 20260916-scaled-mm-prefill-tiles：scaled MM Prefill tile

- experiment-id：`20260916-scaled-mm-prefill-tiles`
- 分类：`operator/improve`
- 状态：`retained_in_combination`

## 方向与改动

根据 rank0 `scaled_mm_kernel=4485.144 ms/44928` 次的 trace，在 T-Head 调优
配置中为三个 Prefill shape 增加 tile 选择。

## 效果与正确性

六个 M2048 主力 shape 的 fresh-process wrapper 为 `1.001x–1.551x`；按调用
次数加权预计减少 `510.391 ms`，约为全部 scaled MM 的 `11.38%`、整段 device
activity 的 `1.28%` 上限。代表 shape 数值逐元素一致并通过 graph replay。

## 决策与边界

保留在组合中；没有独立父场景 A/B，不将投影加到端到端收益。

