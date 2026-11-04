# 20260916-router-native-mm：native router FP32 MM

- experiment-id：`20260916-router-native-mm`
- 分类：`operator/replace`
- 状态：`retained_after_accuracy_gate`

## 方向与改动

在 HY4 Plugin 模型边界接入 PPU vendor FP32 GEMM，guard 同时约束 T-Head、
H6144/E256、FP32 weight/output、无 bias、最高精度、TF32 关闭和有效 MM policy。

## 效果与正确性

含 BF16→FP32 cast 的 wrapper 在 M1–2048 为 `2.78x–11.46x`，profiler 证明
命中 vendor GEMM，graph replay 与 Plugin `17/17` 通过。M2048 随机输入有
`1/2048` 行在极小 8/9 间隔处改变专家集合；根因是 GEMM 累加顺序，而非 TF32。
后续正式 GPQA gate 为 `92.93% >= 87%`。

## 决策与边界

保留。TF32 路径会改变 `10/2048` 行专家集合，明确拒绝。

