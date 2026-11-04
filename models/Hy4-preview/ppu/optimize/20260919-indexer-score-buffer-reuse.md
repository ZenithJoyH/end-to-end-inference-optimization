# 20260919-indexer-score-buffer-reuse：复用 QK score buffer

- experiment-id：`20260919-indexer-score-buffer-reuse`
- 分类：`operator/improve`
- 状态：`retained`

## 方向与改动

T-Head 路径复用刚生成的 QK scores 作为 exact pointwise 输出，删除同尺寸
`empty_like`，仍保持原 BF16 `sum` 顺序。

## 效果与正确性

rows26/128、keys4096 完整 block 为 `1.059x/1.051x`，乘积与 FP32 logits
逐位一致；组合 graph replay、Plugin `16/16` 通过。

## 决策与边界

保留。只记录 buffer/访存机制收益，不与同轮其他 Indexer 局部收益相加。

