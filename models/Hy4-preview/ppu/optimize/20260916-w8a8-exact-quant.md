# 20260916-w8a8-exact-quant：精确 per-token INT8 量化融合

- experiment-id：`20260916-w8a8-exact-quant`
- 分类：`operator/improve`
- 状态：`retained_and_migrated_to_flaggems_vllm`

## 方向与改动

将 W8A8 MoE 的 per-token INT8 量化链融合为使用
`libdevice.div_rn + rint` 的精确 Triton kernel，并与 4-warp 规则组合。

## 效果与正确性

M2048 完整算子 `2.49665 -> 2.22164 ms`（`1.1238x`），输出逐位一致；相关
FlagGems 回归通过。后续按 vLLM 专用算子边界迁入 FlagGems-vllm。

## 决策与边界

保留。算子收益不能与其他 MoE 特化直接相加。

