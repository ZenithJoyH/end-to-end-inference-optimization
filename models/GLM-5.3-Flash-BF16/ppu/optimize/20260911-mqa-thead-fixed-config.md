# 20260911-mqa-thead-fixed-config MQA 固定调优配置

- 状态：`retained`
- 分类：`operator/improve`
- 目标场景：稀疏 Indexer MQA，含冷 shape
- 目标阶段：Prefill / Mixed
- 依赖：FlagGems-vllm thead runtime 与 tune config

## 优化方向与瓶颈依据

`fp8_fp4_mqa_logits` 若读取通用 FlagGems runtime，会对新 shape 枚举 144 个配置。
精度评测中 `M=2901,N=725,H=32,D=128` 的同步在线调优超过 vLLM 300 秒 RPC
超时，导致 EngineCore 和 API server 退出。

## 优化内容与适用边界

thead 使用唯一配置 `BLOCK_M=4/BLOCK_N=64/HEAD_BLOCK=16/warps=4/ctas=1/stages=2`。
迁移后进一步把算子的 runtime import 修正为 `flaggems_vllm.runtime`，保证实际读取
FlagGems-vllm 中的配置；其他平台仍按各自 runtime 选择。

## 正确性与路径命中

模块测试为 `2 passed, 20 skipped`，跳过项源于缺失的 DeepGEMM/FP8 reference。
直接算子覆盖 `M17/N73`、故障 shape、graph capture 和两次 replay，最大绝对误差
不超过 `3.815e-6`。服务级 2901-token 批次首次和复跑均为 32/32 HTTP 200，
复跑 1.18455 秒且未新增 MQA autotune 记录。

## 性能效果

该点主要消除冷 shape 的在线调优长尾和服务退出，不声明独立稳态吞吐提升。热缓存
对照从首次约 133.87 秒降到 1.617 秒，证明问题来自调优而非模型计算常态。

## 决定、风险与回退

修复保留并已提交、推送为 FlagGems-vllm `f7443e7`。风险是未覆盖的 dtype/平台
不能套用该单配置；回退为恢复包内 runtime 选择，但会重新暴露冷 shape 超时风险。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/mqa-fixed-config`
- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/diagnostics/accuracy-health-rpc-timeout-20260918-01/mqa-fix-validation-01`

