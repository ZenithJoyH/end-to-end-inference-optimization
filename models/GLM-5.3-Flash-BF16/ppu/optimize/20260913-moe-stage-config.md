# 20260913-moe-stage-config large-M MoE 分阶段配置

- 状态：`retained`
- 分类：`operator/improve`
- 目标场景：large-M BF16 MoE
- 目标阶段：Prefill / Mixed
- 依赖：FlagGems-vllm fused-MoE launcher

## 优化方向与瓶颈依据

早期通用 MoE 调参未过门槛，因此按 GEMM stage、E288 和 live M 建立更严格的配置
选择，减少 large-M 路径的无效搜索与次优 tile。

## 优化内容与适用边界

为 BF16、E=288、`M>=4096` 的支持 shape 配置 GEMM1/GEMM2 分阶段参数；不覆盖
cached32/cached64 Decode。其他 dtype、专家数和 M 回退原选择。

## 正确性与路径命中

目标 shape 和 graph 服务通过；Plugin 提交 `96eb1bf` 已推送，launcher 后迁入
FlagGems-vllm。

## 性能效果

P4096/D128/C32 从 234.512 提升至 240.631 tok/s（+2.609%）；
P1024/D512/C32 从 727.073 提升至 729.570 tok/s（+0.344%）。该结果只属于
large-M 路径，不代表 Decode small-M 收益。

## 决定、风险与回退

决定保留严格 guard。风险是 live M 变化后不命中；回退为删除 stage config 并使用
原 launcher 配置。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/moe-stage-analysis`
- comparison SHA-256：`9d87b9fd09b8b7c8b193a2321d53a667f30d027a080b51f14fb56ed4903d248b`
