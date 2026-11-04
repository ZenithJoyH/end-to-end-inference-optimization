# 20260916-sparse-mla-bk32-range：BK32 覆盖 128<=SQ<=2048

- experiment-id：`20260916-sparse-mla-bk32-range`
- 分类：`operator/improve`
- 状态：`retained`

## 方向与改动

将 SQ2048 的 BK32/BH4 特化扩展到 `128<=SQ<=2048`；SQ<=64 保持 Split-K，
65–127 与非目标 shape fallback。

## 效果与正确性

SQ128/256/512/1024/1536/2048 在 ramp 与全长分布上相对 BK64 为
`1.030x–1.185x`，最大绝对误差 `1.22e-4`。数值、graph capture、三次 replay
及 small-head 测试 `8/8` 通过。

## 决策与边界

保留；当时尚无单变量父场景 profiler-off 结果，收益包含于后续组合测试。

