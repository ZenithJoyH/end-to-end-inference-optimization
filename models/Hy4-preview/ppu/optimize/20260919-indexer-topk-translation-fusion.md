# 20260919-indexer-topk-translation-fusion：Top-K 翻译链融合

- experiment-id：`20260919-indexer-topk-translation-fusion`
- 分类：`operator/improve`
- 状态：`retained`

## 方向与改动

把 block Top-K 的有效性判断、request offset 和 `-1` 恢复融合为一个原地
Triton kernel，替代 `ge -> bitwise_not -> add_ -> masked_fill_` 四段链。

## 效果与正确性

变换本体 `[128,2048]` 为 `22.32 -> 14.60 us`（`1.53x`）；完整
`_select_topk_block` 在 rows26/128、keys4096 为 `1.123x/1.024x`。后续 trace
中四段旧签名消失，graph 与 Plugin 聚焦测试通过。

## 决策与边界

保留；后续与另外两项 Indexer 数据流改动共同重采，不能拆算组合 E2E 贡献。

