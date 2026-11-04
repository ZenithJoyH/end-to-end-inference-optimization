# 20260919-full-prefix-sparse-mla-grouping：full-prefix HQ4 分组复用

- experiment-id：`20260919-full-prefix-sparse-mla-grouping`
- 分类：`operator/improve`
- 状态：`retained`

## 方向与改动

GPU 验证同组四行长度连续且有效索引前缀一致后，让一个 KV tile 在四个 query、
16 个 head 间复用；失败时回退原 HQ4 路径。最终门槛为 `SQ>=384`。

## 效果与正确性

SQ512/SQ2048 full-prefix 为 `1.76x/2.88x`，随机 Top-K fallback 为
`0.985x/1.002x`；SQ384/416/448/480 为 `1.34x/1.53x/1.69x/1.77x`。
输出逐元素一致，T-Head Hy4 `26/26`、graph replay 通过。真实 P4K trace 中
Prefill/Mixed grouped 分别累计 `233.05/2072.78 ms`，证明运行时命中。

## 拒绝项与边界

TLE 路径因后端不支持 `warp_specialize` 被拒；索引排序计入开销后退化；SQ96–256
不满足门槛。保留分组路径，正式精度 gate 需绑定新源码。

