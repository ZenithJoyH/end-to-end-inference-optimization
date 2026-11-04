# 20260915-sparse-mla-hq4-tile：HQ4 BK64/BH4 tile

- experiment-id：`20260915-sparse-mla-hq4-tile`
- 分类：`operator/improve`
- 状态：`superseded_by_bk32_range`
- 目标 shape：`HQ4/DQK576/TOPK2048`

## 方向与改动

针对 TP16 后每 rank 仅四个 query heads 的形状，在 FlagGems sparse MLA
autotune 中加入 `BK64/BH4/4-warps/2-stages`，替代最小 `BH16` 的浪费。

## 效果与正确性

`SQ8/SKV8192` 从 `194.33 us` 降至 `176.85 us`（`1.099x`）；
SQ1/8/64/256/2048 sweep 均为正收益。small-head 测试 `3/3`，数值、graph
capture 和三次 replay 通过。

## 决策与边界

当时保留，随后被覆盖范围更广的 BK32/BH4 方案取代。这里只记录算子证据，
不重复计算组合收益。

