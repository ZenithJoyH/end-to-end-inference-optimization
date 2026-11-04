# 20260916-sparse-index-blockn2048：sparse index 转换 BLOCK_N=2048

- experiment-id：`20260916-sparse-index-blockn2048`
- 分类：`operator/improve`
- 状态：`retained`

## 方向与改动

Plugin 对 HY4 BF16 sparse index 转换按 shape 将 `BLOCK_N` 从 128 提升到
2048，把每行 program/valid-count 原子加从 16 次降到 1 次。

## 效果与正确性

M256/M2048 为 `1.567x/4.616x`，indices/counts 逐位一致，graph replay 通过。
该 kernel 在当时 profile 的 Prefill/Mixed/Decode 占比约
`2.88%/2.70%/1.67%`，Prefill 设备时间理论上限约 `2.25%`。

## 决策与边界

保留；微基准高倍加速受热点占比约束。

