# 20260911-glm53-flash-ppu-e2e：GLM-5.3-Flash-BF16 / PPU 端到端优化

## 摘要

- 执行规则：`0.18` / `2026-09-10`
- 验收范围：`diagnostic`
- 精度/性能状态：`passed` / `incomplete`
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
- 当前候选正式 GPQA 已完成 198 题，strict-match 为 172/198（86.87%）。用户确认门槛修正为 86% 并指示直接用该已完成结果判定，因此精度状态为 `passed`。原 wrapper 使用误写的 0.88 contract；此处记录为门槛修正后复判，不伪装为事前冻结。12 个 60K length-cap 响应作为非阻断输出健康风险保留。重复启动的 `formal-02` 已于 2026-09-11 14:55 +08:00 停止，部分产物不参与验收。

## 初始候选原则

先核验框架中的明显浪费和工作点，再以 profiler 的真实生产 shape 决定算子替换或当前实现优化。
GLM-5.2 的 Indexer、Sparse MLA、MoE、采样与调度经验只作为候选机制，不继承其 TP16 MetaX 参数或性能数字。

## 已复现的算子慢路径

- 适配服务 FlagGems DB 的 906 张表中，892 张属于
  `_index_linearized_jit_function`；源码反查确认它对应 `aten.index.Tensor` 的
  FlagGems `index` 实现。
- 保留 thead 默认黑名单并追加 `index` 后，single 从约 131 秒降至 3.110 秒；
  C8 从两轮 8/8 在 240 秒超时恢复为 8/8 在 43.478–44.125 秒完成。
- single/C8 前后 `_index_linearized_jit_function` 表数量保持 892，运行命中记录不含
  `flag_gems.ops.index.index`，前缀缓存 query/hit 均为 0。
- 当前结论为 `reproduced`：FlagGems `index` 是该模型/平台/TP16 身份上的严重慢路径。
  正式 workload 的吞吐、TTFT、TPOT 尚未测量，不能把 sanity 改善写成最终性能收益。

完整证据：[单算子黑名单实验](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/experiments/20260911-index-op-blacklist/README.md)。
