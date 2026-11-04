# 20260919-maxseq64-m64-gemm1-config-01 exact-M64 MoE GEMM1 配置

- 状态：`failed`
- 分类：`operator/improve`
- 目标场景：P1024/D1024/C64/N128，`max_num_seqs=64`
- 目标阶段：Decode
- 依赖：exact-M64 fused-MoE GEMM1

## 优化方向与瓶颈依据

GEMM2 特化后 fused-MoE 仍占 Decode 44.12%，继续检查同一 M64 路径的 GEMM1
是否存在低风险 config 收益。

## 优化内容与适用边界

在保持 incoming BM32 对齐边界的前提下扫描 BN/BK/stage 等配置；3 seed 独立验证。

## 正确性与路径命中

全部候选通过 eager、数值、graph capture 和 replay；数据库未变化。没有候选达到
落源门槛，因此未进行服务 A/B。

## 性能效果

基线中位 0.302960 ms；最佳 alignment-safe 配置
`BM32/BN128/BK128/GM1/stages3/int32-offset` 为 0.288940 ms，中位 1.048522×、
最低 1.036492×，未达到 1.05× 算子门槛。

## 决定、风险与回退

决定停止，不改源码、不提交。继续扫描的预期端到端收益低于测量与维护成本。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/moe-smallm-analysis/m64-gemm1-scan-01`
- decision summary SHA-256：`486362c9f6754c67a288386ac0d31f01a821a885f28e26eeeb64cdc661c2bbc1`

