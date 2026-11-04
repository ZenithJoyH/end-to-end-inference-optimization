# 20260916-fused-moe-4warp：W8A8 fused MoE 4-warp

- experiment-id：`20260916-fused-moe-4warp`
- 分类：`operator/improve`
- 状态：`retained_then_superseded_by_padding_tiles`
- 目标：PPU-ZW810E，`int8_w8a8`，`M>=256`

## 方向与改动

运行时确认路径为 `FlagGemsW8A8Experts -> flag_gems.fused_experts_impl`。有限
sweep 选择四 warps；GEMM2 `BLOCK_N=256` 退化 `0.38%`，未保留。

## 效果与正确性

M256/512/1024/2048 为 `1.060x/1.154x/1.167x/1.044x`；M2048 交错样本
`2.4790 -> 2.3372 ms`（`1.061x`）。输出逐位一致，graph replay 和配置测试
`26/26` 通过。

## 决策与边界

当时保留，后续被 expert-padding 与分阶段 K tile 方案覆盖。

