# 20260919-w8a8-moe-padding-tiles：expert padding 与分阶段 K tile

- experiment-id：`20260919-w8a8-moe-padding-tiles`
- 分类：`operator/improve`
- 状态：`retained`

## 方向与改动

目标 M2048/E256/TopK8/H6144/localI128。将 `BM64` 改为 `BM32` 降低 expert
padding；GEMM1 使用 `BK128`，GEMM2 保持 `BK64/BN128`。BN256、BK32、BM16、
2/4 stages 和 8 warps 均经 sweep 拒绝。

## 效果与正确性

随机路由 padded rows 从 23,360（`1.426x`）降至 19,872（`1.213x`）。完整
W8A8 MoE 交错中位数 `2.08731 -> 1.74568 ms`（`1.19570x`），输出逐位一致，
graph replay、T-Head Hy4 `26/26` 通过。

## 决策与边界

保留。按当时热点占比估算设备时间上限约 Prefill `3.94%`、Mixed `3.80%`，
不能直接当作端到端收益。

