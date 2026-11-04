# 20260916-sparse-mla-sq2048-followup：SQ2048 tile 与 Split-K 深挖

- experiment-id：`20260916-sparse-mla-sq2048-followup`
- 分类：`operator/improve`
- 状态：`rejected`

## 方向与结果

补扫 `BK16`、`BH1/BH2`、4/8 warps、1/2 stages，均慢于既有
`BK32/BH4/4-warps/1-stage`。SQ2048 的 2/4-way Split-K 完整调用最好仅
`0.901x`，ramp 长度最好 `0.596x`，并增加 `32.125–64.25 MiB` workspace。

## 决策

拒绝并回退全部新增尝试，保留原 BK32 候选。停止无新 shape 证据的同类扫描。

