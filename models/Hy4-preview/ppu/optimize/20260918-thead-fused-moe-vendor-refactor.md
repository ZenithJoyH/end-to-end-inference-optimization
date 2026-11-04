# 20260918-thead-fused-moe-vendor-refactor：平台特化迁移

- experiment-id：`20260918-thead-fused-moe-vendor-refactor`
- 分类：`operator/improve`
- 状态：`retained_and_pushed`

## 方向与改动

把误放在 FlagGems 公共 `fused_moe.py/moe_sum.py` 的 PPU-ZW810E 规则迁到
`runtime/backend/_thead/fused/`。公共实现相对优化前基线 diff 为零，非 T-Head
平台保持原行为。

## 效果与正确性

M2048 W8A8 完整算子 `2.47939 -> 2.20469 ms`（`1.1246x`），输出逐位一致，
graph replay 通过；回归 `141 passed`。提交 `7bca7a3a/0e027557` 已推送
FlagGems `support-hy4-preview`。

## 决策与边界

保留。该实验解决平台边界和可维护性，不重复计算先前算子收益。

