# 20260915-sparse-mla-small-sq-split-k：small-SQ Split-K

- experiment-id：`20260915-sparse-mla-small-sq-split-k`
- 分类：`operator/improve`
- 状态：`retained`
- guard：`SQ<=64/HQ4/DQK576/TOPK2048/DV512`，且提供 sink 与 `topk_length`

## 方向与改动

在 T-Head vendor backend 中沿 Top-K 使用 8/16 个 CTA 生成 FP32
online-softmax partial，再由第二阶段合并；非目标平台和 shape 回退通用实现。

## 效果与正确性

增长上下文中 SQ1/8/32/64 为 `2.677x/2.664x/2.101x/1.142x`。SQ128 实验版
退化 `7.9%`，最终 guard 使其 fallback。零长度、无效 index、无限 sink、数值、
graph replay 与聚焦测试 `5/5` 均通过。

## 决策与边界

保留 small-SQ 路径，拒绝 SQ128 扩展。隔离加速不等于服务收益。

