# 性能优化案例索引

本目录保存已经实际执行的端到端推理优化案例。案例可以成功、失败、回退或被阻塞，但必须有真实目标、环境和证据。

## 索引

| 案例 ID | 模型 | 平台/硬件 | 引擎 | Workload | 瓶颈 | 主要改动 | 结果 | 证据等级 |
|---|---|---|---|---|---|---|---|---|
| [20261022-qwen3vl-metax-pr977](20261022-qwen3vl-metax-pr977/README.md) | Qwen3-VL-30B-A3B BF16 MoE | TP2 MetaX C550 / mx-59 / GPU0,1 | 上游 bad340d，含PR977；原gems-opt/Plugin/采样保留 | E128/H2048/I384/topk8，BF16/FP16 M0..8192 | E128通用GEMM1选参未按64KiB约束 | 独立容器试用最新上游，移除本地943 MoE改动 | B/C/R通过18/14/18项；候选大M要求98304B超65536B；未跑E2E、未回写原服务 | resource failure reproduced；性能未知 |
| [20261021-hy4-preview-ppu03-e2e](20261021-hy4-preview-ppu03-e2e/README.md) | HY4-preview W8A8 | TP16 PPU-ZW810E / PPU-03 | env031 Plugin/FGV45e/FG3ba | P1K目标；三阶段C8/N8里程碑 | profiling主机OOM；短上下文索引CPU逐行开销 | 单文件15行批量range，无库升级；当前已回退 | 81轮B/C/R：Prefill12.88x、Mixed4.84x通过；Decode异步分批/Prefill干扰已定位，原incomplete保留；无新正式gate | Prefill/Mixed reproduced；最终验收incomplete |
| [20261020-deepseekv4-flash-metax59-container](20261020-deepseekv4-flash-metax59-container/README.md) | DeepSeek-V4-Flash W8A8 | TP8 MetaX C550 / mx-59 | vLLM0.24 empty + Plugin main + 源码 FlagTree | 全量 GPQA198，非性能任务 | strict加粗提取失败；真实MoE限幅遗漏已修复，剩余低分未完全归因 | 生产文件仍23；单文件补传limit，复用原生activation；graph/C1/C8通过 | 新正式100/198=50.51%，去加粗辅助140/198=70.71%；无gate | accuracy-failed/partially-localized |
| [HY4-preview PPU-03 初步性能](20261020-hy4-preview-ppu03-initial-perf/README.md) | HY4-preview W8A8 | TP16 PPU-ZW810E / PPU-03 | vLLM 0.24.0 + Plugin + FlagGems | P1K/D128/C8/N8 缩减 Mixed；正式四场景未测 | Decode 基线波动，TPOT 守护失败 | batched-token 2048→512 候选已回退 | Mixed 输出 10.18→9.85 token/s，原 8010 已恢复；无新精度 gate | observation；正式比较 incomplete |
| [HY4-preview PPU-03 Plugin迁移](20261018-hy4-preview-ppu03-migration/README.md) | HY4-preview W8A8 | TP16 PPU-ZW810E / PPU-03 | vLLM 0.24.0 + Plugin + FlagGems-vllm/FlagGems | GPQA Diamond 198 题/C64；非性能优化 | 新旧 Plugin、INT8 与 sparse MLA 接口兼容 | HY4 Plugin 接入及 BF16 算子适配，2048 配置保留 | strict 183/198=92.42%，超过 87% 门槛；完整性能未验收 | 精度 gate 已绑定；性能未测 |
| [20261018-hy4-preview-ppu03-repo-update](20261018-hy4-preview-ppu03-repo-update/README.md) | hy4-preview 容器 | PPU-03 | vLLM0.24.0；Plugin024plugin-opt、两Gems gems-opt | 指定分支更新；无推理测试 | 非性能任务；新Plugin分支缺原HY4模块 | 私有源码及安装完整备份，固定SHA替换与editable重装 | 三包实际导入/入口/干净工作区通过；HY4运行未验证 | version update verified / model not run |
| [20261017-minimax-m3-ppu13-plugin-support](20261017-minimax-m3-ppu13-plugin-support/README.md) | MiniMax-M3 BF16 | TP16 PPU-ZW810E / PPU-13 | 新发布镜像 + 用户指定 Plugin620892ab | 分支替换及文本推理回归 | 非性能任务 | topk/FP32 router/OAI统一各1份源码并安装，旧副本归档可恢复 | [当前状态](../../models/MiniMax-M3/ppu/20261017-minimax-m3-ppu13-plugin-support/optimize/README.md)；canonical安装后CPU600通过，PPU模型未测；历史GPQA179/198=90.40% | single final checkout installed / hardware and performance not run |
| [20261015-qwen36-27b-metax-fg20-e2e](20261015-qwen36-27b-metax-fg20-e2e/README.md) | Qwen3.6-27B BF16/GDN | TP2 MetaX C550 / mx-59 / 2,3 | vLLM0.20.2 + Plugin b8f2734 + FG-vLLM de2298b/FP32补丁 | P1K阶段milestone；四正式场景未测 | full在线调优及GDN冗余JIT造成阶段长停顿 | full20/原容差/10%不变，私有修复验证与metadata BCR | 87轮/27测完成；PF+0.58%通过，D因TTFT13.45%不完整，Mixed+0.26%<2%；原代码/18002恢复 | full reproduced / GDN-JIT observation |
| [20261022-qwen3vl-metax-opt10-results](20261022-qwen3vl-metax-opt10-results/README.md) | Qwen3-VL-30B-A3B BF16 MoE | TP2 MetaX C550 / mx-59 / GPU6,7 | gems-opt + inline MoE + common sampling + localhist | P1K/P4K/P16K/P32K/P64K，D1K/C64/N128 | P1K旧shape-JIT关联；新复测稳态1.45%；P4K旧波动 | 仅归档，源码/服务不变；与GPU0/1受控数据隔离 | 最新SUMMARY总TPS3022/5411/6369/5799/4969；P1K四轮用户确认稳态 | GPQA65.66/ERQA40.50均通过；人工性能完整、P1K稳态确认；最终性能验收未完成 |
| [20261021-qwen3vl-metax-p1k-opt9](20261021-qwen3vl-metax-p1k-opt9/README.md) | Qwen3-VL-30B-A3B BF16 MoE | TP2 MetaX C550 / mx-59 | opt9 private stack; gems-opt | P1K/D1K/C64/N128 steady E2E | Both-rank phase traces: MoE then sampling radix/hist | Local histogram retained; other configs unchanged | B1455/C1510/R1485tok/s; +3.76%vsB,+1.67%vsR; bitwise/graph passed | performance_only; GPQA deferred; source patch active in useropt10; latest results in20261022case |
| [20261015-qwen3vl-metax-p64k-opt3](20261015-qwen3vl-metax-p64k-opt3/README.md) | Qwen3-VL-30B-A3B BF16 MoE | TP2 MetaX C550 / mx-59 / 0,1 | vLLM ee0da84 + Plugin024plugin-opt + FlagGems-vllm | P64K/D1K/C64/N128; user manages tests | MoE parameters retained; PR selector scope simplified | Inline stage defaults + direct sampling; no external JSON loader | Prior op019 P64 +6.81%; pr02955GPU/TP2graph/MetaXCI passed; no new E2E | PR943 Ready090ef1d; source8111 restored unchanged; formal accuracy deferred |
| [20261015-qwen38-flash-next-ppu07-container](20261015-qwen38-flash-next-ppu07-container/README.md) | Qwen3.8-Flash-Next | PPU-ZW810E / PPU-01→PPU-07 | 私有Plugin FP32；Gems i64/randn；QSA M16/PLE CTA | 精度诊断与Plugin PR收敛 | BF16归约次序、索引溢出、PLE原地状态同步 | 私有修复/完整rank取证；新PR候选三文件独立整理 | acc017严格177/198=89.39%有效gate；仍7条60K。eng053 CPU53通过，新树模型/graph待测 | 原组合正式精度通过；不宣称60K因果解决或性能通过；PR候选needs_revision |
| [20261013-qwen36-35b-metax-e2e-current](20261013-qwen36-35b-metax-e2e-current/README.md) | Qwen3.6-35B-A3B BF16 MoE/GDN | TP2 MetaX C550 / mx-59 / 6,7 | 当前公共MoE代码926a5544；vLLM0.20.2 + Plugin + FlagGems-vllm | P1K→P4K→P16K→P32K，D1K/C64/N128 | 稳态吞吐与Mixed慢轮；阶段归因待测 | 用户明确要求当前容器优化；快照与C8护栏已建立 | 65536全量GPQA164/198=82.83% gate通过；P1K基线不稳，私有graph队列问题待隔离，正式性能未完成 | observation |
| [20261013-qwen36-35b-metax-performance-gap](20261013-qwen36-35b-metax-performance-gap/README.md) | Qwen3.6-35B-A3B BF16 MoE/GDN | TP2 MetaX C550 / mx-59 | vLLM0.20.2，不同Plugin/FlagGems/FlagTree与补丁 | 历史P4K/D1K/C64/N128 | 生成阶段gap；采样、GDN/MoE/Attention及调度多变量 | 只读诊断，未修改服务 | begin输出吞吐−29.81%、TPOT+40.87%；具体贡献未测，历史身份不完整 | observation |
| [20261013-qwen3vl-metax-flaggems-e2e-opt1](20261013-qwen3vl-metax-flaggems-e2e-opt1/README.md) | Qwen3-VL-30B-A3B BF16 MoE | TP2 MetaX C550 / mx-59 / 0,1 | 用户opt2 MoE JSON；FlagGems sort int32 | P1K→P4K→P16K→P32K，D1K/C64/N128；额外P64K | 随机采样sort热点；单行计数类型改进 | 保持FlagGems选择与blacklist，用户服务未变 | sampled P1K B/C/R +19.73%，TPOT-16.53%；私有保留；精度暂缓/其余场景未测 | final acceptance incomplete |
| [20261012-qwen3vl-metax-sampling-migration](20261012-qwen3vl-metax-sampling-migration/README.md) | Qwen3-VL-30B-A3B-Instruct | MetaX C550 / mx-59 | vLLM ee0da84ab + Plugin + FlagGems-vllm + FlagTree0.7.0.post2 | 算子M64/V151936与TP2 graph/C8；非正式性能场景 | 采样归属/tail mask、完整MoE接入、旧编译器API与遗留vendor特化 | 迁入算子库、MetaX完整MoE、新FlagTree正常warmup及旧MCTLLASS清理及用户要求的NV调用对齐 | 采样历史49+8；最新18NV路由对照/3dtype graph/TP2真实配置及18请求通过，已回写；正式精度/性能未测 | 范围正确性reproduced；历史算子性能observation |
| [20261012-qwen36-27b-metax-flash-attention](20261012-qwen36-27b-metax-flash-attention/README.md) | Qwen3.6-27B BF16 GQA/linear hybrid | TP2 MetaX C550 / mx-59 | vLLM0.20.2 + Plugin + FlagGems-vllm | P1K→P4K→P16K→P32K，D1K/C64/N128；Decode算子诊断 | packed GQA6 Decode落入legacy | MetaX受保护SplitKV调度及partial独立strides | [当前状态](../../models/Qwen3.6-27B/metax/optimize/README.md)；未部署、未验收 | 算子A/B/revert reproduced；修正版30000 FlagGems80.30%／原生80.81%通过；原生50000为79.80%失败、截断14→5，轨迹分叉待定位；端到端收益未知；FG组合诊断Decode+1.71%、Mixed未准入且比较配置缺口，已回退 |
| [20261010-minimax-m31-w8a8-ppu-tp8-e2e](20261010-minimax-m31-w8a8-ppu-tp8-e2e/README.md) | MiniMax-M3.1 W8A8 | TP8 PPU-ZW810E / PPU-07 | vLLM 0.24.0 + Plugin + FlagGems | P1K→P4K→P16K→P32K，D1K/C64/N128 | PPU BF16 M8 A矩阵加载K地址缺位已确认 | 私有Plugin head tile16修复；用户TP8配置与原11exports不变 | [当前状态](../../models/MiniMax-M3.1-W8A8/ppu/optimize/README.md) | 完整198通过85.86%；P1K基线1968.23TPS；完整机制A/B/A验证；FW004已回退，性能未验收 |
| [20261008-minimax-m31-w8a8-ppu-e2e](20261008-minimax-m31-w8a8-ppu-e2e/README.md) | MiniMax-M3.1 W8A8 | TP16 PPU-ZW810E / PPU-07 | vLLM 0.24.0 + Plugin + FlagGems | P1K→P4K→P16K→P32K，D1K/C64/N128 | C64超capture32回退NONE；动态shape编译关联慢预热 | capture64历史GPQA84.85%；Mixed图16rank/105+2及新GPQA85.86%通过 | [当前状态](../../models/MiniMax-M3.1-W8A8/ppu/optimize/README.md) | 旧P1K单实例10.510×，缺独立重复/回退；新组合收益未知，四场景未验收 |
| [20260921-minimax-m3-ppu-e2e](20260921-minimax-m3-ppu-e2e/README.md) | MiniMax-M3 BF16 MoE | TP16 PPU-ZW810E / PPU-07 | vLLM 0.24.0 + Plugin + FlagGems | P1K→P4K→P16K→P32K，D1K/C64/N128 | 待 Prefill/Decode/Mixed 定位 | 独立优化容器→框架工作点→算子 A/B | 环境门禁已过；待授权释放源服务的 16 张 PPU | `observation` |
| [20260919-qwen38-flash-next-ppu-e2e](20260919-qwen38-flash-next-ppu-e2e/README.md) | Qwen3.8-Flash-Next | PPU-ZW810E / PPU-01 | 版本见模型运行记录 | P1K→P4K→P16K→P32K，D1K/C64/N128 | QSA、MoE、GEMM、阶段干扰 | 调度、score 上界、算子 provider | 活跃；[当前状态与单点结果](../../models/Qwen3.8-Flash-Next/ppu/optimize/README.md)，历史 acc-011 精度通过但服务重启后待复测，op027 性能里程碑通过未部署 | 见各实验 |
| [20260914-hy4-preview-ppu-e2e](20260914-hy4-preview-ppu-e2e/README.md) | Hy4-preview W8A8 linear/MoE | TP16 PPU-ZW810E / PPU-07 | vLLM 0.24.0 + Plugin + FlagGems | P4096/D1024/C64/N128；缩减 profiling | sparse MLA、fused MoE、scaled MM、Indexer 同步与冷启动 | Plugin/FlagGems 算子与数据流特化，native router MM | 最新稳态 278.14 output tok/s；较前 checkpoint +22.10%；正式 A/B/revert 待补 | `reproduced` |
| [20260911-glm53-flash-ppu-e2e](20260911-glm53-flash-ppu-e2e/README.md) | GLM-5.3-Flash-BF16 | TP16 PPU-ZW810E / PPU-13 | vLLM 0.24.0 + Plugin + FlagGems | 正式矩阵与缩减探针见模型记录 | MoE、MLA、mHC、调度 | 框架与算子多轮优化 | 点52去全部临时hook后原脚本默认flagos C64 64/64及完整模型最小/FULL回归通过；同实例新198题/C64 GPQA实际运行中，分数待定；[当前状态](../../models/GLM-5.3-Flash-BF16/ppu/optimize/README.md) | 新gate/稳态性能待验，PR未就绪 |
| [20260904-xingchen4-ppu-isolated-e2e](20260904-xingchen4-ppu-isolated-e2e/README.md) | XingChen4-29B-A4B BF16 | TP4 PPU-ZW810E / PPU-01 | vLLM 0.24.0 + Plugin + FlagGems | P1K/D1K/C64；P4K/D256/C64；P16K/D256/C32，各三轮 | MLA decode约60.6% GPU kernel时间 | operator/improve：H8的head tile64→16，限shape、可回退 | 保留：输出/总吞吐约+95.5%/+73.2%/+31.9%；GPQA按用户指示暂缓 | `reproduced` |
| [20260903-imported-deepseek-v4-flash-w8a8](20260903-imported-deepseek-v4-flash-w8a8/README.md) | DeepSeek-V4-Flash W8A8 | 8× MetaX C550 | vLLM 0.20.2 + Plugin-FL + FlagGems | P1K/P4K, D1K, C64 | Indexer、Sparse MLA、cache copy、调度 | graph-safe/fusion/shape specialization | 原文最终组合显著提升；本项目未复测 | `observation` |
| [20260903-imported-glm-5-2-w8a8](20260903-imported-glm-5-2-w8a8/README.md) | GLM-5.2 W8A8 | TP16 MetaX | vLLM + Plugin-FL + FlagGems/MCTlass | P1K/P4K | Indexer、MoE、Sparse MLA、采样、KV 抢占 | 分阶段 backend、精确算法、head packing、调度 | 原文持续演进；本项目未复测 | `observation` |
| [20260903-imported-qwen3-6-moe](20260903-imported-qwen3-6-moe/README.md) | Qwen3.6-35B-A3B MoE BF16 | Hygon BW gfx936 | vLLM + Plugin-FL + FlagGems/ROCm | P1K/D256/C64 | MoE、DeltaRule、通信 | MoE 分阶段配置与 grouped-GEMM 原型 | 无最终 E2E 验收 | `observation` |

20260904 XingChen4案例为本项目实际执行；其他标记imported的条目为用户历史案例资料导入，不等同于当前项目重新执行。原始性能数字与结论需回到各案例的环境和版本解释。

## 命名

案例目录使用：

```text
YYYYMMDD-<model>-<platform>-<short-objective>
```

目录中的 `README.md` 从 [TEMPLATE.md](TEMPLATE.md) 初始化。模型/平台 `optimize/` 只保存
`state.yml`、多轮 README 和单点 Markdown；案例目录只保留少量可复用结论与链接。
执行配置、命令、补丁和逐轮原始结果保存在外部 case 目录，记录绝对路径与 SHA。
活跃案例的过程文件必须先核验外部副本及引用再移除，不能因精简而丢失唯一证据。
索引不复制活跃案例的瞬时进度，以模型 `state.yml` 和 README 为当前事实入口。

## 检索标签

案例至少填写以下标签，便于后续复用：

- 模型结构：dense、MoE、MLA、GQA/MQA、mHC、multimodal 等。
- 阶段：cold-start、prefill、decode、mixed。
- 层级：request、scheduler、framework、memory、communication、operator。
- 平台、设备型号、设备数量和是否跨机。
- 引擎、Plugin、backend、dtype、量化和 graph/eager。
- 目标：TTFT、TPOT、ITL、throughput、memory、stability、cost。

## 纳入标准

- 必须来自实际执行或可复现失败。
- 必须记录 baseline、变量、验证和结论。
- 推测可以记录，但不能伪装为验证事实。
- 失败案例不删除；说明失败机制和后续是否值得重试。
- 同一案例的多个实验保留独立编号，不能只留下最优结果。

- [HY4-preview PPU-03 新FGV下8192预算对比](20261020-hy4-preview-ppu03-batched8192/README.md)：新anchor独立初测完成；8192无净吞吐收益且TTFT守护失败，已恢复2048；Decode参考未稳，无GPQA。
