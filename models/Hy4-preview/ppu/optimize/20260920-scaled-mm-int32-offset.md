# 20260920-scaled-mm-int32-offset：scaled MM int32 logical offset

- experiment-id：`20260920-scaled-mm-int32-offset`
- 分类：`operator/improve`
- 状态：`rejected`

## 方向与结果

六个 trace 主形态中，N576 的 M2048/2029 为 `1.087x/1.092x`；两个主 GEMM
仅约 `1.019x–1.026x`，且 M2029/K6144/N2048 退化到 `0.931x`，六形态几何
均值 `1.028x`。

## 决策

N576 单点按热点上限不足约 `0.1%` E2E，不改源码、不保留。

