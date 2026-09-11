# 20260911-glm53-flash-ppu-e2e：GLM-5.3-Flash-BF16 / PPU 端到端优化

## 摘要

- 执行规则：`0.18` / `2026-09-10`
- 验收范围：`diagnostic`
- 精度/性能状态：`failed` / `incomplete`
- 状态：`running`
- 目标：在 `PPU-13` 上建立可信基线，分层定位并优化 TTFT、TPOT 与吞吐，同时保持正确性、稳定性和资源边界。
- 模型/平台产物：[models/GLM-5.3-Flash-BF16/ppu](../../../models/GLM-5.3-Flash-BF16/ppu/)

## 已核验目标事实

- 模型：`/mnt/cpfs/models/GLM-5.3-Flash-BF16`，served name `glm5.3-flash`。
- 平台/Host：T-Head PPU，`PPU-13`，16×PPU-ZW810E。
- 源适配容器：`glm5.3-flash`，镜像
  `hy4-ppu07-snapshot:20260903@sha256:29a6712e24ca8e758ac8b33d3412892f0541bff108e2c057445fa671578237f6`。
- 运行配置：vLLM 0.24.0、BF16、TP16、max model len 65536、max seqs 32、prefill eager、decode `FULL_DECODE_ONLY` graph。
- revision：vLLM `ee0da84a`、Plugin `db09b64a`、FlagGems `4a3cba02`、FlagGems-vllm `255ab560`；四个工作树均 clean。
- 当前服务 health/models 正常，队列和 KV 使用率为 0；16 个 TP worker 仍占用全部 PPU 约 89.9 GiB/卡。

## 门禁与阻塞

- 独立优化容器：`glm5.3-flash-opt-20260911`；同镜像 ID、挂载一致性 passed，私有源码 revision 与实际 import 已验证。
- 用户已明确授权暂停源 vLLM 服务；源容器仍 running。服务退出后 16 张 PPU 均为 1 MiB、无运行进程。
- 适配项目未冻结正式性能 workload；当前先采用可复现的诊断矩阵，结果不能代表业务 SLO。
- 最近正式 GPQA 为 172/198（86.87%），10 个响应达到 60K length cap，未过 88% 和零无效响应门槛；最终验收仍需解决或明确该既有缺口。

## 初始候选原则

先核验框架中的明显浪费和工作点，再以 profiler 的真实生产 shape 决定算子替换或当前实现优化。
GLM-5.2 的 Indexer、Sparse MLA、MoE、采样与调度经验只作为候选机制，不继承其 TP16 MetaX 参数或性能数字。
