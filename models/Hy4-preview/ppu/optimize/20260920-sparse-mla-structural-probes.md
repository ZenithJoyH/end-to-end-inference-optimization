# 20260920-sparse-mla-structural-probes：Decode MLA 结构候选

- experiment-id：`20260920-sparse-mla-structural-probes`
- 分类：`operator/improve`
- 状态：`rejected`

## 方向与结果

针对 Decode generic sparse MLA 测试 sink 代数简化与 exp2/log2
online-softmax。SQ2029/2048 分别约 `0.93x` 与 `0.96x`，均退化。

PPU native `flash_mla` 在 score-selected 形态为 `1.056x–1.089x`，但
full-prefix 最低仅 `0.356x`；交替 prefix/score 的混合探针约 `1.215x`，证明
必须按输入语义分流，不能 whole-batch 替换。

## 决策

拒绝 sink 和 exp2/log2 改写；whole-batch native 替换不保留。结果成为后续
cached-prefill hybrid 的前置证据。

