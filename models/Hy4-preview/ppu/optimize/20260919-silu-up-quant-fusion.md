# 20260919-silu-up-quant-fusion：SiLU×Up 与 INT8 quant 融合

- experiment-id：`20260919-silu-up-quant-fusion`
- 分类：`operator/improve`
- 状态：`rejected_and_reverted`

## 方向与结果

融合子链从 `119.96 us` 降至 `38.47 us`（`3.12x`）且逐位一致，但完整 MoE
仅 `1.0015x`。

## 决策

低于完整算子保留门槛，源码回退。该例说明子链加速不能替代完整算子判定。

