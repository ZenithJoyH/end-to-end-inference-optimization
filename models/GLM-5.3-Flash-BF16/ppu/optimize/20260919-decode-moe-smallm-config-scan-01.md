# 20260919-decode-moe-smallm-config-scan-01 small-M Decode MoE GEMM2

- 状态：`retained`
- 分类：`operator/improve`
- 目标场景：P1024/D1024/C64/N128，`max_num_seqs=32`
- 目标阶段：Decode
- 依赖：FlagGems-vllm fused-MoE aligned BF16 path

## 优化方向与瓶颈依据

16-rank profile 显示 P1K Decode 中 fused-MoE 占 rank0 设备活动 43.59%，而原
large-M 配置要求 `M>=4096`，不覆盖稳定 cached32 路径。

## 优化内容与适用边界

对 PPU BF16、E288/H4096/I128/topk8、非量化 GEMM2、`1<=M<=32` 且 incoming
`BLOCK_SIZE_M=16` 使用
`BM16/BN128/BK32/GM8/SPLIT_K1/warps4/stages4/int32-offset`。其他 shape、dtype、
量化和 layout 全部 fallback。

## 正确性与路径命中

M=1/8/16/31/32、每个 3 seed 全部通过 eager、数值、graph capture 和两次 replay；
整体最低观测加速 1.3663×。源码聚焦测试 18/18 通过，服务 graph 路径命中。
沿用已通过的正式精度 `172/198 >= 0.86`，本点未重新跑完整精度。

## 性能效果

算子 GEMM2 从 0.34180 ms 降至 0.15886 ms，约 2.1516×；多 shape/seed 中位
2.1424×。

| 角色 | 输出吞吐 | P99 TTFT | P99 TPOT |
|---|---:|---:|---:|
| baseline | 840.963 tok/s | 43.028 s | 37.793 ms |
| candidate | 1004.382 tok/s | 36.759 s | 31.647 ms |
| revert | 847.618 tok/s | 42.251 s | 37.619 ms |

候选吞吐 +19.432%，TTFT/TPOT 分别改善 14.569%/16.262%，回退漂移 0.791%。
正式比较器因旧契约缺失 SLO 阈值标为 `incomplete`，但冻结数值门槛通过。

## 决定、风险与回退

候选保留在 FlagGems-vllm 工作树，尚未提交或推送。回退脚本恢复原 GEMM2 config；
不能把 M<=32 参数外推到 M64。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/moe-smallm-analysis`
- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p1024-d1024-c64-n128`

