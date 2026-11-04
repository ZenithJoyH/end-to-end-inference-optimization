# 20260919-indexer-layout-probes：QK layout 与 row-range 融合

- experiment-id：`20260919-indexer-layout-probes`
- 分类：`operator/improve`
- 状态：`rejected`

## 方向与结果

QK layout 改写在完整链上最多 `1.015x`，转置和 `einsum` 均退化；将两次
row-range 减法融合成一个 kernel，在主导 rows128/keys2048 上仅 `0.998x`。

## 决策

收益不足或退化，全部拒绝且未保留源码。

