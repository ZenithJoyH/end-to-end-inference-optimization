# 20260916-gemm2-direct-sum：GEMM2 atomic direct-sum

- experiment-id：`20260916-gemm2-direct-sum`
- 分类：`operator/improve`
- 状态：`rejected_and_reverted`

## 方向与结果

尝试用 atomic direct-sum 减少 GEMM2 后处理。M256/M2048 仅
`0.813x/0.340x`，重复输出不稳定，最大差 `0.125`。

## 决策

因性能与确定性同时失败而拒绝，源码完整回退。

