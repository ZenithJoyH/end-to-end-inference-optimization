# 20260916-indexer-exact-pointwise：BF16 pointwise 精确融合

- experiment-id：`20260916-indexer-exact-pointwise`
- 分类：`operator/improve`
- 状态：`retained`

## 方向与改动

只融合 BF16 ReLU 与权重乘法，保留原生 `torch.sum` 归约顺序，避免更激进融合
导致 Top-K 集合变化。

## 效果与正确性

中间乘积和 FP32 logits exact fraction 均为 1.0；归约链 `1.293x`，完整
scoring block `1.092x`。trace 中 ReLU+mul `353.904 -> 173.354 ms`，Indexer
wall 再降 `3.79%`。完全融合方案改变约 `0.077%` Top-K 集合，已拒绝。

## 决策与边界

保留精确方案，拒绝改变选择集合的完全融合。全 trace device activity 仅
下降 `0.44%`，体现 Amdahl 上限。

