# 20260916-indexer-row-range-topk：row-range Top-K

- experiment-id：`20260916-indexer-row-range-topk`
- 分类：`operator/improve`
- 状态：`retained`

## 方向与改动

blocked-prefill 原路径构造 `[rows,key_width]` dense causal mask 后调用通用
`torch.topk`。候选复用 `top_k_per_row_prefill` 的逐行 start/end ABI，删除
dense mask 和通用 Top-K，仍输出 request-relative index。

## 效果与正确性

`32/2048、64/2048、128/2048、128/4096` 分别为
`1.093x/1.129x/1.543x/1.184x`。2K 选择集合完全一致；4K 仅在完全同分 token
间选择不同 index，selected-score 多重集一致、最大 score 误差 0。聚焦测试
`6/6` 通过。

## 决策与边界

保留。服务级贡献由后续组合 checkpoint 观察，不能由微基准单独外推。

