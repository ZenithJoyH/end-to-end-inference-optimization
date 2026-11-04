# 20260919-indexer-redundant-fill：删除重复 output.fill_

- experiment-id：`20260919-indexer-redundant-fill`
- 分类：`operator/improve`
- 状态：`retained`

## 方向与改动

外层已初始化整个 Top-K buffer，row-wise provider 会覆盖有效和无效项，因此删除
score-selected block 内重复的 `output.fill_(-1)`。

## 效果与正确性

rows26/keys4096、rows128/keys2048、rows128/keys4096 为
`1.091x/1.086x/1.009x`。非法哨兵残留为 0，valid count 与 selected-score
多重集一致，graph replay 和 Plugin `16/16` 通过。

## 决策与边界

低风险保留，独立收益较小。

