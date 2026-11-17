# 性能优化案例索引

按平台查找案例，同一组内按案例日期倒序排列。点击案例查看结论、适用条件和实验主记录。

## 索引

[沐曦 MetaX](#沐曦-metax) · [平头哥 PPU](#平头哥-ppu) · [历史导入](#历史导入)

### 沐曦 MetaX

| 案例日期 | 模型与问题 |
|---|---|
| 2026-11-05 | [Qwen3-VL · opt16 采样路径的同机热态 1K 对照](../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261105-qwen3vl-opt16-hot1k-mx59-001/README.md) |
| 2026-11-05 | [Qwen3-VL opt17 C64 accuracy，mx-59](../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261105-qwen3vl-c64-accuracy-mx59-001/README.md) |
| 2026-11-05 | [C588 Host PCIe 单 die 与双 die 带宽归因](20261105-metax-pcie-c588-bottleneck/README.md) |
| 2026-11-05 | [C588 与 C550 · 主机 PCIe、内存带宽与 CPU 执行效率](20261105-metax-cpu-platform-gap/README.md) |
| 2026-11-05 | [MiniMax-M3 C588 通信配置实测](20261105-m3-c588-comm-e2e-092/README.md) |
| 2026-11-05 | [DeepSeek-V4-Flash · TP8 跨八张物理卡与 NUMA 绑定](20261105-c588-tp8-eight-cards/README.md) |
| 2026-11-05 | [DeepSeek-V4-Flash：用户指定启动脚本的 NUMA 绑定](20261105-c588-numa-launch/README.md) |
| 2026-11-05 | [BGE-M3 / mx-59 启动脚本整理](20261105-bge-m3-mx59-serve-cleanup/README.md) |
| 2026-11-05 | [BGE-M3 / mx-59：1K发布镜像对比](20261105-bge-m3-mx59-base-1k/README.md) |
| 2026-11-04 | [Qwen3-VL · opt16 端到端性能差距诊断](../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261104-qwen3vl-opt16-performance-gap/README.md) |
| 2026-11-04 | [Qwen3-VL / mx-59 top-k/top-p PR](../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261104-qwen3vl-mx59-topk-topp-pr/README.md) |
| 2026-11-04 | [Qwen3.6-35B-A3B / mx-59 / PR1067验证](../../models/Qwen3.6-35B-A3B/metax/20261104-qwen36-mx59-pr1067-verification-001/README.md) |
| 2026-11-04 | [Qwen3.6-35B / mx-59 主线 MoE 配置](../../models/Qwen3.6-35B-A3B/metax/20261104-qwen36-mx59-main-config-001/README.md) |
| 2026-11-04 | [Qwen3.6-35B：C588双die与C550双卡的收益差异](20261104-qwen35-metax-c588-c550-gap/README.md) |
| 2026-11-04 | [MiniMax-M3：C588-6 单机与 C550 101/102 双机的历史性能对比](20261104-minimax-m3-metax-cross-topology/README.md) |
| 2026-11-04 | [MiniMax-M3：通信显存与KV容量机制诊断](20261104-minimax-m3-metax-comm-kv-diagnosis/README.md) |
| 2026-11-04 | [多模型 · C588 与 C550 拓扑和瓶颈对照](20261104-metax-models-c588-c550-overview/README.md) |
| 2026-11-04 | [DeepSeek-V4-Flash / mx-104 Plugin规范审查](20261104-dsv4-metax104-plugin-review/README.md) |
| 2026-10-26 | [Qwen3-VL / MetaX：发布镜像splits与完整精度核验](20261026-qwen3vl-metax-release-splits/README.md) |
| 2026-10-24 | [Qwen3-VL · 固定 Attention splits 的 GPQA 对照](../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261024-qwen3vl-metax-fixed-splits/README.md) |
| 2026-10-23 | [Qwen3-VL / MetaX：mx-59 验证环境迁移至 mx-104](20261023-qwen3vl-metax-mx104-migration/README.md) |
| 2026-10-22 | [DeepSeek V4 Flash W8A8：mx-103精度与端到端优化](20261022-thinking-gpqa-metax103/README.md) |
| 2026-10-22 | [Qwen3-VL / MetaX：PR977 最新上游验证](20261022-qwen3vl-metax-pr977/README.md) |
| 2026-10-22 | [Qwen3-VL / MetaX opt10 全量端到端记录](20261022-qwen3vl-metax-opt10-results/README.md) |
| 2026-10-22 | [Qwen3.6-35B / mx-104 整理与迁移完整回归](20261022-qwen36-35b-mx104-stack-regression/README.md) |
| 2026-10-22 | [Qwen3.6-35B / mx-104 Plugin 采样导入生命周期修复](20261022-qwen36-35b-mx104-sampler-fix/README.md) |
| 2026-10-22 | [Qwen3.6-35B / mx-104 verify 容器代码整理](20261022-qwen36-35b-mx104-code-audit/README.md) |
| 2026-10-22 | [Qwen3.6-27B · Plugin release/0.2 迁移与精度回归](20261022-qwen36-27b-mx104-plugin-regression/README.md) |
| 2026-10-22 | [Qwen3.6-27B / mx-104 verify 容器代码整理](20261022-qwen36-27b-mx104-code-audit/README.md) |
| 2026-10-21 | [Qwen3-VL MetaX opt9 P1K 稳态](20261021-qwen3vl-metax-p1k-opt9/README.md) |
| 2026-10-20 | [DeepSeek-V4-Flash · mx-59 容器与依赖核验](20261020-deepseekv4-flash-metax59-container/README.md) |
| 2026-10-15 | [Qwen3-VL / MetaX / P64K opt3](20261015-qwen3vl-metax-p64k-opt3/README.md) |
| 2026-10-15 | [Qwen3.6-27B / MetaX / 当前20FG端到端优化](20261015-qwen36-27b-metax-fg20-e2e/README.md) |
| 2026-10-13 | [Qwen3-VL / MetaX / FlagGems端到端优化](20261013-qwen3vl-metax-flaggems-e2e-opt1/README.md) |
| 2026-10-13 | [Qwen3.6-35B-A3B / mx-59：base 与 begin 性能 gap 诊断](20261013-qwen36-35b-metax-performance-gap/README.md) |
| 2026-10-13 | [Qwen3.6-35B-A3B / mx-59 当前容器端到端优化](20261013-qwen36-35b-metax-e2e-current/README.md) |
| 2026-10-12 | [Qwen3-VL / MetaX 采样算子归属迁移](20261012-qwen3vl-metax-sampling-migration/README.md) |
| 2026-10-12 | [20261012 Qwen3.6-27B / MetaX Flash Attention](20261012-qwen36-27b-metax-flash-attention/README.md) · [实验记录](../../models/Qwen3.6-27B/metax/optimize/README.md) |

### 平头哥 PPU

| 案例日期 | 模型与问题 |
|---|---|
| 2026-10-22 | [MiniMax Flash 原容器64并发精度重测](20261022-minimax-m31-old-container-c64-accuracy/README.md) |
| 2026-10-21 | [MiniMax Flash 新 topk-sigmoid 容器精度](20261021-minimax-m31-topk-sigmoid-tp8-accuracy/README.md) |
| 2026-10-21 | [MiniMax-M3.1 算子接入与适配整理](20261021-minimax-m31-topk-sigmoid-integration/README.md) |
| 2026-10-21 | [MiniMax Flash1019 移除 top-k patch 精度复测](20261021-minimax-m31-no-topk-patch-tp8-accuracy/README.md) |
| 2026-10-21 | [MiniMax Flash1019 编译器dot-K16精度复测](20261021-minimax-m31-dot-k16-tp8-accuracy/README.md) |
| 2026-10-20 | [MiniMax-M3.1 Flash 最新栈 / PPU-07 前8卡全量精度](20261020-minimax-m31-latest-stack-tp8-0-7-accuracy/README.md) |
| 2026-10-20 | [MiniMax-M3.1 Flash / PPU-07 最新栈迁移](20261020-minimax-m31-latest-stack-migration/README.md) |
| 2026-10-19 | [MiniMax-M3.1 Flash1019 / PPU-07 三项精度](20261019-minimax-m31-flash-ppu-tp8-accuracy/README.md) |
| 2026-10-17 | [MiniMax-M3 / PPU-13 指定 Plugin 分支验证](20261017-minimax-m3-ppu13-plugin-support/README.md) · [实验记录](../../models/MiniMax-M3/ppu/20261017-minimax-m3-ppu13-plugin-support/optimize/README.md) |
| 2026-10-15 | [Qwen3.8-Flash-Next 优化容器复刻至 PPU-07](20261015-qwen38-flash-next-ppu07-container/README.md) |
| 2026-10-10 | [MiniMax-M3.1 Flash W8A8（09-29 preview） / PPU-07 / TP8 优化](20261010-minimax-m31-w8a8-ppu-tp8-e2e/README.md) · [实验记录](../../models/MiniMax-M3.1-Flash-W8A8/ppu/optimize/README.md) |
| 2026-10-08 | [MiniMax-M3.1 Flash W8A8 · 总吞吐优化](20261008-minimax-m31-w8a8-ppu-e2e/README.md) · [实验记录](../../models/MiniMax-M3.1-Flash-W8A8/ppu/optimize/README.md) |
| 2026-09-21 | [MiniMax-M3 · PPU 端到端优化](20260921-minimax-m3-ppu-e2e/README.md) |
| 2026-09-19 | [Qwen3.8-Flash-Next · Mixed 吞吐、调度间隙与 MoE](20260919-qwen38-flash-next-ppu-e2e/README.md) · [实验记录](../../models/Qwen3.8-Flash-Next/ppu/optimize/README.md) |
| 2026-09-11 | [GLM-5.3-Flash-BF16 · Sparse MLA、MoE 与 graph 派发](20260911-glm53-flash-ppu-e2e/README.md) · [Plugin PR](../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261102-plugin-sparse-mla-pr-63.md) |
| 2026-09-04 | [xing4 / PPU-01：隔离吞吐优化](20260904-xing4-ppu-isolated-e2e/README.md) |

### 历史导入

以下三项为用户提供的历史案例，性能数字沿用原始记录，项目内尚未复测。

| 案例日期 | 模型与问题 |
|---|---|
| 2026-09-03 | [Qwen3.6-35B-A3B · 海光 BW 上的 MoE、DeltaRule 与通信](20260903-imported-qwen3-6-moe/README.md) |
| 2026-09-03 | [GLM-5.2 W8A8 · 稀疏注意力、MoE 与 KV 抢占](20260903-imported-glm-5-2-w8a8/README.md) |
| 2026-09-03 | [DeepSeek-V4-Flash W8A8 · Indexer、Sparse MLA 与缓存复制](20260903-imported-deepseek-v4-flash-w8a8/README.md) |

### 既有案例详表

| 案例 ID | 模型 | 平台/硬件 | 引擎 | Workload | 瓶颈 | 主要改动 | 结果 | 证据等级 |
|---|---|---|---|---|---|---|---|---|
| [20261021-hy4-preview-ppu03-e2e](20261021-hy4-preview-ppu03-e2e/README.md) | HY4-preview W8A8 | TP16 PPU-ZW810E / PPU-03 | env031 Plugin/FGV45e/FG3ba | P1K目标；三阶段C8/N8里程碑 | profiling主机OOM；短上下文索引CPU逐行开销 | fw001批量range未安装；fw002一处PPU特化去重补丁，库版本不升级 | 81轮B/C/R：Prefill12.88x、Mixed4.84x通过；Decode异步分批/Prefill干扰已定位；新增28.6s为TopK冷JIT/TTGIR，fw002修复后16rank精确Mixed无编译、约4.2s；原incomplete保留；无新正式gate | fw001历史Prefill/Mixed reproduced；003正式Decode波动/211证据冻结；004四targeted B/C/R passed，Mixed4.934x/P4K+40.913%；837SHA已核验；同15行已保留并新验证通过/119SHA核验；005启动控制parser错误/0请求/41文件冻结；006 C16两组54新轮BCR passed，Prefill12.780x/Mixed6.497x，漂移≤2.374%，619项冻结复核；007 C32基线/候选各18轮passed，回退Prefill9轮准入/独立复验passed，Mixed采集中；收益待比较，正式验收incomplete；最终验收incomplete |
| [HY4-preview PPU-03 初步性能](20261020-hy4-preview-ppu03-initial-perf/README.md) | HY4-preview W8A8 | TP16 PPU-ZW810E / PPU-03 | vLLM 0.24.0 + Plugin + FlagGems | P1K/D128/C8/N8 缩减 Mixed；正式四场景未测 | Decode 基线波动，TPOT 守护失败 | batched-token 2048→512 候选已回退 | Mixed 输出 10.18→9.85 token/s，原 8010 已恢复；无新精度 gate | observation；正式比较 incomplete |
| [HY4-preview PPU-03 Plugin迁移](20261018-hy4-preview-ppu03-migration/README.md) | HY4-preview W8A8 | TP16 PPU-ZW810E / PPU-03 | vLLM 0.24.0 + Plugin + FlagGems-vllm/FlagGems | GPQA Diamond 198 题/C64；非性能优化 | 新旧 Plugin、INT8 与 sparse MLA 接口兼容 | HY4 Plugin 接入及 BF16 算子适配，2048 配置保留 | strict 183/198=92.42%，超过 87% 门槛；完整性能未验收 | 精度 gate 已绑定；性能未测 |
| [20261018-hy4-preview-ppu03-repo-update](20261018-hy4-preview-ppu03-repo-update/README.md) | hy4-preview 容器 | PPU-03 | vLLM0.24.0；Plugin024plugin-opt、两Gems gems-opt | 指定分支更新；无推理测试 | 非性能任务；新Plugin分支缺原HY4模块 | 私有源码及安装完整备份，固定SHA替换与editable重装 | 三包实际导入/入口/干净工作区通过；HY4运行未验证 | version update verified / model not run |
| [20260914-hy4-preview-ppu-e2e](20260914-hy4-preview-ppu-e2e/README.md) | Hy4-preview W8A8 linear/MoE | TP16 PPU-ZW810E / PPU-07 | vLLM 0.24.0 + Plugin + FlagGems | P4096/D1024/C64/N128；缩减 profiling | sparse MLA、fused MoE、scaled MM、Indexer 同步与冷启动 | Plugin/FlagGems 算子与数据流特化，native router MM | 最新稳态 278.14 output tok/s；较前 checkpoint +22.10%；正式 A/B/revert 待补 | `reproduced` |

- [HY4-preview PPU-03 新FGV下8192预算对比](20261020-hy4-preview-ppu03-batched8192/README.md)：新anchor独立初测完成；8192无净吞吐收益且TTFT守护失败，已恢复2048；Decode参考未稳，无GPQA。

Hy4-preview 2026-10-23 更新：007 C32 已完成并冻结：54轮全新测量、两原生比较passed，0丢轮；Prefill总吞吐12.599x，Mixed输出7.81187x，全部B/R指标最大漂移0.953954%。621项SHA及3份服务日志固定前缀独立复核passed。007完成时为before回退服务，后已按用户切换新权重指令精确停止；旧候选未自动保留。008稳态profiling已准备本地契约、三阶段dry-run、流式校验器（17项）、预热准入（24项）及进程树资源采样/判定（27项本地检查）；实际watchdog、原生回执和生命周期尚待集成，未部署/采集。acceptance仍incomplete，无精度gate或C64正式结论。 [记录](20261021-hy4-preview-ppu03-e2e/README.md)

## 维护方式

历史记录中的 heartbeat/automation 标识、`codex/*` 分支和 `~/.codex` 产物路径是当时执行器的证据，不代表当前环境；新旧执行器的进度监控、会话和权限映射见[执行说明](../agent-execution.md#执行环境适配codex-与-dsh)。案例 ID 沿用 `YYYYMMDD-<model>-<platform>-<short-objective>`。新案例用[摘要模板](TEMPLATE.md)记录目标、结论、适用边界和证据链接。每个案例只占一行，结果变化时更新原案例；逐轮实验写入模型的 `optimize/`。历史直接指向模型主记录的条目沿用原入口。
