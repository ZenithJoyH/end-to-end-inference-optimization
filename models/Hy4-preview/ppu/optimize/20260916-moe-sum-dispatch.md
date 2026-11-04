# 20260916-moe-sum-dispatch：T-Head moe_sum 直接分派

- experiment-id：`20260916-moe-sum-dispatch`
- 分类：`operator/replace`
- 状态：`retained_and_migrated_to_flaggems_vllm`

## 方向与改动

对 T-Head BF16/TopK8/H6144 绕过通用 autotuner 分派，直接选择平台特化
`moe_sum`；非目标 shape 与平台保持原路径。

## 效果与正确性

M256/M2048 为 `1.303x/1.072x`，逐位一致，graph 两次 replay 通过；
`moe_sum` 回归 `76/76`。后续迁入 FlagGems-vllm 专用实现。

## 决策与边界

保留，端到端贡献包含在组合结果中。

