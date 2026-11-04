# 20260918-flaggems-vllm-migration：vLLM 专用算子归位

- experiment-id：`20260918-flaggems-vllm-migration`
- 分类：`operator/replace`
- 状态：`retained_and_pushed`

## 方向与改动

将 W8A8 路由、精确量化、Hy4 `moe_sum` 与 sparse MLA 专用实现迁入
FlagGems-vllm `support-hy4-preview`，Plugin 在目标符号存在时优先调用，缺包或
旧版本时回退 FlagGems。

## 效果与正确性

FlagGems-vllm 提交为 `1d532a5/2888ef1/cf156f8/d579bfe/a26a902`，Plugin
切换提交 `f7d1aaa`。运行时命中 `_thead.ops.fused_moe` 与
`_thead.fused.flashmla_sparse`；Plugin `33/33`，Hy4 `20/20`，`moe_sum`
`72/72`，有效 fused-experts 集 `46 passed/12 skipped`，graph replay 通过。

## 决策与边界

保留并推送。该实验验证代码归属与调用切换，不单独产生端到端收益结论。

