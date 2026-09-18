# 20260911-glm53-flash-ppu-e2e：GLM-5.3-Flash-BF16 / PPU 端到端优化

## 摘要

- 执行规则：`0.18` / `2026-09-10`
- 验收范围：`diagnostic`
- 精度/性能状态：`passed` / `incomplete`
- 状态：`paused`；已保留改动已分笔 commit 并推送，最终性能验收未完成。
- 目标：在 `PPU-13` 上建立可信基线，分层定位并优化 TTFT、TPOT 与吞吐，同时保持正确性、稳定性和资源边界。
- 模型/平台产物：[models/GLM-5.3-Flash-BF16/ppu](../../../models/GLM-5.3-Flash-BF16/ppu/)

## 已核验目标事实

- 模型：`/mnt/cpfs/models/GLM-5.3-Flash-BF16`，served name `glm5.3-flash`。
- 平台/Host：T-Head PPU，`PPU-13`，16×PPU-ZW810E。
- 源适配容器：`glm5.3-flash`，镜像
  `hy4-ppu07-snapshot:20260903@sha256:29a6712e24ca8e758ac8b33d3412892f0541bff108e2c057445fa671578237f6`。
- 运行配置：vLLM 0.24.0、BF16、TP16、max model len 65536、max seqs 32、prefill eager、decode `FULL_DECODE_ONLY` graph。
- 初始 revision：vLLM `ee0da84a`、Plugin `db09b64a`、FlagGems `4a3cba02`、
  FlagGems-vllm `255ab560`。当前 Plugin HEAD 为 `96eb1bf`，FlagGems HEAD 为
  `fec9807`，FlagGems-vllm 仍为 `255ab560`；三个工作树均 clean。
- 最后服务实例曾通过 health 与空队列检查，后于 2026-09-14 18:07:48
  因 EngineCore 异常退出；容器仍运行，8011 当前未监听。该退出早于
  2026-09-15 的 Git 提交，提交过程未重启服务。

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

完整结构化证据：[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

## 最新阶段状态

当前保留组合为 index 黑名单、MQA 固定配置、native sparse MLA、
shape-gated native causal-conv、shape-gated vendor KDA 和
`max_num_batched_tokens=16384`，以及 shape-gated FlagGems MoE 分阶段配置。
`32768` 在长输出哨兵场景吞吐回退
1.523%，已拒绝并恢复 16384。最新证据排序和下一实验已合并到
[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

## 源码提交交付

- `vllm-plugin-FL` `support-glm5.3-flash`：`85302a7` index 黑名单、
  `dbb0e67` sparse MLA、`062c06f` causal-conv、`ef19fd9` Chunk KDA、
  `96eb1bf` large-M MoE stage config。
- `FlagGems` `support-glm5.3-flash`：`fec9807` thead sparse-indexer MQA 固定配置。
- 2026-09-15 已分别推送到 `ZenithJoyH/vllm-plugin-FL` 和
  `ZenithJoyH/FlagGems`；`git ls-remote` 核验远端 HEAD 为 `96eb1bf` 和
  `fec9807`。Plugin 聚焦单测 7/7 通过，两个仓库 YAML 解析通过。
- 远端容器缺少 GitHub HTTPS 凭据，首次尝试未更新任何 ref；最终使用经过
  SHA-256 校验的 Git bundle 与本机 GitHub SSH 身份完成。命令证据位于远端
  `commands/push-source-branches-20260915/`。

MoE 候选先将 trace 分解为时间几乎各半的 GEMM1/GEMM2，再对
M=4096/12401/16384 分阶段调参。保留配置在两场景正式 A/B/R 中
使输出吞吐分别改善 2.609%/0.344%，P99 TTFT 分别降低
3.714%/4.163%，比较器判定 `passed`。结构化数值与远端证据路径见
[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

保留 MoE 后的 16-rank trace 显示稳定热点迁移到 sparse MLA，fused MoE
累计设备时间约下降 14.8%。native sparse MLA 来自不暴露 tile 参数的预编译
扩展；其外围索引转换使用 BN1024 后，三个主 shape 微基准虽提升
3.55x–4.54x，但两场景端到端吞吐分别为 -0.041%/-0.005%，正式比较器
判 `failed`。该实验补丁已回退，当前服务继续使用上述 MoE 保留组合、16384
和关闭的前缀缓存。证据、反例与下一阶段排序均已并入
[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

随后按 trace 前七个 shape 比较 general mm：thead 默认配置已经把 `mm`
列入 FlagGems 黑名单，当前服务使用 native 路径。direct FlagGems 在六个
shape 上慢 17.6%–45.1%，仅 N=24 shape 持平，未达到 5% 门槛，因此未进入
服务 A/B，也没有新增代码改动。详细决策见
[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。
