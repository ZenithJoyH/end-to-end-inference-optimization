# 性能优化案例索引

本目录保存已经实际执行的端到端推理优化案例。案例可以成功、失败、回退或被阻塞，但必须有真实目标、环境和证据。

## 索引

| 案例 ID | 模型 | 平台/硬件 | 引擎 | Workload | 瓶颈 | 主要改动 | 结果 | 证据等级 |
|---|---|---|---|---|---|---|---|---|
| [20261021-hy4-preview-ppu03-e2e](20261021-hy4-preview-ppu03-e2e/README.md) | HY4-preview W8A8 | TP16 PPU-ZW810E / PPU-03 | env031 Plugin/FGV45e/FG3ba | P1K目标；三阶段C8/N8里程碑 | profiling主机OOM；短上下文索引CPU逐行开销 | 单文件15行批量range，无库升级；当前已回退 | 81轮B/C/R：Prefill12.88x、Mixed4.84x通过；Decode异步分批/Prefill干扰已定位，原incomplete保留；无新正式gate | Prefill/Mixed reproduced；最终验收incomplete |
| [20261024-qwen3vl-metax-fixed-splits](../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261024-qwen3vl-metax-fixed-splits/README.md) | Qwen3-VL-30B-A3B | TP2 MetaX C550 / mx-104 / GPU4,5 | 同源私有 clone，sampling/gems-opt/MoE 不变 | GPQA198 两组1/16；有限doc20窗口；CPU参考 | 分片数改变logits后跨越top-p边界 | 参数诊断与中性/有限窗口取证；无生产数学修改 | 1两轮66.16≥64，16两轮60.61失败；实际noise相同，CPU32probs逐位一致，support2→1解释目标首差；恢复1/graph16+C8；监控停用 | 目标窗口机制已验证，16全cohort仅15/32复现，不外推全部formal错题；无新E2E收益 |
| [20261023-qwen3vl-metax-mx104-migration](20261023-qwen3vl-metax-mx104-migration/README.md) | Qwen3-VL-30B-A3B | TP2 MetaX C550 / mx-104 / GPU4,5 | Exact mx59 private runtime snapshot | P1K full + reduced P64K;180 rounds | User-directed migration and split comparison | Preserve sampling/gems-opt/MoE/prefix ON;scalar split0/1 | Migration/ERQA400 passed45.73(native),45.50(all400);6-process native/source audits passed | Targeted failed: split1 output/total -11.37%/-38.30%,TPOT+13.33%/+85.27%;reversion drift<0.1%;exact split1/helper restored graph16/C8 passed;monitor stopped;fullP64K not_run,no new-host GPQA/formal gate |
| [20261022-qwen36-35b-mx104-stack-regression](20261022-qwen36-35b-mx104-stack-regression/README.md) | Qwen3.6-35B-A3B BF16 | TP2 MetaX C550 / mx-104 / GPU0,1 | 原优化d1653d9 vs release/0.2+editable候选 | GPQA198与四场景P1K–P32K/D1K/C64/N128 | 整理/安装/迁移退化回归 | 独立同源A/B容器、原安装恢复、5%守护及回退 | GPQA160/198→147/198失败；两轮64取证/原配置恢复完成，shortlist命中，分组24/8→23/9且strict24/26；有序64独立核验/原配置恢复通过、32题全文一致strict25/25；完整147<160仍阻塞；性能incomplete | incomplete |
| [20261022-old-container-c64-accuracy](20261022-minimax-m31-old-container-c64-accuracy/README.md) | MiniMax-M3.1-Flash W8A8 | TP8 PPU-ZW810E / PPU-07 /0–7 | 原容器Plugin08da/FV4638/FG3b76；FlagTree0.6.2a1 | 用户原脚本；GPQA198/Math500500/ERQA400，全部C64 | 与new2既有原生产物逐题比较；非单变量A/B | 不改源码；原容器新实例、独立精度run | GPQA167/198、Math469/500、ERQA252/400；无性能 | 全部原生终态复核；监控已删除，模型服务保留 |
| [20261022-qwen36-35b-mx104-sampler-fix](20261022-qwen36-35b-mx104-sampler-fix/README.md) | Qwen3.6-35B-A3B BF16 MoE/GDN | TP2 MetaX C550 / mx-104 / GPU4,5 | vLLM0.20.2 + Plugin release/0.2@7cb559947 | 导入生命周期修复；C1+两轮C8，非性能任务 | sampler/GDN eager import循环与消费者旧alias | Plugin三文件延迟幂等安装+精确alias刷新；采样数值不变 | 6导入/25数值通过；17请求、504shortlist、至少512graph replay；临时服务已关闭 | target-service verified；正式精度/性能未测 |
| [20261022-qwen36-27b-mx104-code-audit](20261022-qwen36-27b-mx104-code-audit/README.md) | Qwen3.6-27B BF16 dense/GDN | mx-104 / verify容器；无模型服务 | vLLM0.20.2 + Plugin release/0.2@7cb55994 + 两套Gems | 代码审计及用户指定Plugin基线迁移 | 旧开关/调用链漂移、安装态MoE、GDN特化形状不匹配 | 原实现保全；两文件优化迁移、离线bundle/补丁/回退材料 | 10项CPU单测、CLI/MetaX路由及源码保护通过；模型graph/精度性能not_run | 不继承旧性能，不归因运行收益 |
| [20261022-qwen36-35b-mx104-code-audit](20261022-qwen36-35b-mx104-code-audit/README.md) | Qwen3.6-35B-A3B BF16 MoE/GDN | mx-104 / verify容器，运行拓扑未绑定 | vLLM0.20.2 + Plugin release/0.2@7cb559947 + 两套Gems | 代码整理与基线迁移，无新模型测试 | 安装专属MoE、源码分叉及Plugin基线迁移 | MoE回收FGV并改editable；Plugin原8修改迁移至release/0.2 | 101 CPU/mock通过；Plugin89模块/50函数/5impl一致；FGV276文件不变；vLLM无diff；精度/性能not_run | editable/source/import verified；模型执行未测 |
| [20261022-thinking-gpqa-metax103](20261022-thinking-gpqa-metax103/README.md) | DeepSeek-V4-Flash W8A8 | TP8 MetaX C550 / mx-103 | vLLM0.24empty + 私有Plugin/FG/FGV | P1K/P4K/P16/P32,D1024/C64/N128,prefixOFF | headpack跨通信stream临时缓冲滞留约2.75GiB | fw005仅改现有Plugin prefill.py，原生TP P2P compute-stream复用，保留0.85/KV567220及用户脚本 | 新GPQA172/198=86.87%；14轮1792/1792；P16三轮357.43/356.90/357.77、P32 207.97/208.25/208.17tok/s；0OOM/非法访存/新增抢占 | 八卡精确/43层内存机制及同预算运行稳定性通过；当前独立B/C/R和四场景最终正式验收未完成；无相对原镜像加速比 |
| [20261022-qwen3vl-metax-pr977](20261022-qwen3vl-metax-pr977/README.md) | Qwen3-VL-30B-A3B BF16 MoE | TP2 MetaX C550 / mx-59 / GPU0,1 | 上游 bad340d，含PR977；原gems-opt/Plugin/采样保留 | E128/H2048/I384/topk8，BF16/FP16 M0..8192 | E128通用GEMM1选参未按64KiB约束 | 独立容器试用最新上游，移除本地943 MoE改动 | 纯上游大M仍超限；PR943刷新316f，63GPU/TP2graph与CI通过；新独立环境GPQA62.12失败、ERQA41通过；受控旧125/124、新128/125未复现版本退化；a157已同步；op006 Plugin固定kvcache split1，数值/graph/C8通过，完整GPQA 131/198=66.16分，达到64分阈值；ERQA/E2E未重测，未回写生产 | resource failure reproduced；性能未知 |
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
| [20261010-minimax-m31-w8a8-ppu-tp8-e2e](20261010-minimax-m31-w8a8-ppu-tp8-e2e/README.md) | MiniMax-M3.1 W8A8 | TP8 PPU-ZW810E / PPU-07 | vLLM 0.24.0 + Plugin + FlagGems | P1K→P4K→P16K→P32K，D1K/C64/N128 | 历史M8加载K地址缺位；ERQA D80 SDPA splitKV combine输出stride错误 | 保留headtile16等历史改动；FG3b76f81升级及Plugin/FV INT8接口兼容 | [当前状态](../../models/MiniMax-M3.1-W8A8/ppu/optimize/README.md) | 2026-10-19：新版安装生效，20单测/八卡56项逐位相等及graph2/正常服务105+2通过，ERQA六次短复现从6/6 NUL变0/6；原GPQA160/198低于81%，新完整精度未跑、无新gate/E2E；运行preview与用户脚本Flash权重分开记录 |
| [20261008-minimax-m31-w8a8-ppu-e2e](20261008-minimax-m31-w8a8-ppu-e2e/README.md) | MiniMax-M3.1 W8A8 | TP16 PPU-ZW810E / PPU-07 | vLLM 0.24.0 + Plugin + FlagGems | P1K→P4K→P16K→P32K，D1K/C64/N128 | C64超capture32回退NONE；动态shape编译关联慢预热 | capture64历史GPQA84.85%；Mixed图16rank/105+2及新GPQA85.86%通过 | [当前状态](../../models/MiniMax-M3.1-W8A8/ppu/optimize/README.md) | 旧P1K单实例10.510×，缺独立重复/回退；新组合收益未知，四场景未验收 |
| [20260921-minimax-m3-ppu-e2e](20260921-minimax-m3-ppu-e2e/README.md) | MiniMax-M3 BF16 MoE | TP16 PPU-ZW810E / PPU-07 | vLLM 0.24.0 + Plugin + FlagGems | P1K→P4K→P16K→P32K，D1K/C64/N128 | 待 Prefill/Decode/Mixed 定位 | 独立优化容器→框架工作点→算子 A/B | 环境门禁已过；待授权释放源服务的 16 张 PPU | `observation` |
| [20260919-qwen38-flash-next-ppu-e2e](20260919-qwen38-flash-next-ppu-e2e/README.md) | Qwen3.8-Flash-Next | PPU-ZW810E / PPU-01 | 版本见模型运行记录 | P1K→P4K→P16K→P32K，D1K/C64/N128 | QSA、MoE、GEMM、阶段干扰 | 调度、score 上界、算子 provider | 活跃；[当前状态与单点结果](../../models/Qwen3.8-Flash-Next/ppu/optimize/README.md)，历史 acc-011 精度通过但服务重启后待复测，op027 性能里程碑通过未部署 | 见各实验 |
| [20260914-hy4-preview-ppu-e2e](20260914-hy4-preview-ppu-e2e/README.md) | Hy4-preview W8A8 linear/MoE | TP16 PPU-ZW810E / PPU-07 | vLLM 0.24.0 + Plugin + FlagGems | P4096/D1024/C64/N128；缩减 profiling | sparse MLA、fused MoE、scaled MM、Indexer 同步与冷启动 | Plugin/FlagGems 算子与数据流特化，native router MM | 最新稳态 278.14 output tok/s；较前 checkpoint +22.10%；正式 A/B/revert 待补 | `reproduced` |
| [20260911-glm53-flash-ppu-e2e](20260911-glm53-flash-ppu-e2e/README.md) | GLM-5.3-Flash-BF16 | TP16 PPU-ZW810E / PPU-13 | vLLM0.24 + 官方三库/必要兼容 | 点62 FGV Draft PR1044已提交 | 公共Sparse MLA H4/graph能力交付 | 紧凑H4复用公共kernel，必要thead64/128边界保留 | PPU33/0skip、8capture/16replay、格式/wheel/Hosted CI通过；[点62](../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261102-flaggems-vllm-sparse-mla-pr-62.md) | 12形状2项低于0.9，Draft/G6未过；fresh main/非PPU/整模未验，生产源/实例/参数未改；非E2E/新精度gate |
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

- [20261019 MiniMax-M3.1 Flash1019 / PPU-07 三项精度](20261019-minimax-m31-flash-ppu-tp8-accuracy/README.md)：新Flash权重独立全量精度完成：GPQA171/198=86.36%、Math500461/500=92.20%、ERQA255/400=63.75%；与preview历史分开，monitor已暂停。 reqdiag-001另确认原8035非对象请求体触发vLLM校验str.get/500，CPU双重JSON复现；外部真实编码来源未确认，服务未改。

- [20261020 MiniMax-M3.1 Flash / PPU-07 最新栈迁移](20261020-minimax-m31-latest-stack-migration/README.md)：review-001完成main全差异收敛：量化类全局包装改为目标实例，native桥接限模型加载，撤销无关MetaX扩展/重复转发并保留路由dtype；190纯CPU通过、9设备用例仅收集。设备/graph/模型仍待空闲卡，FlagTree0.7保留既有Thead兼容，原8035保留，无新正式精度/性能。

- [20261020 MiniMax-M3.1 Flash 最新栈前8卡全量精度](20261020-minimax-m31-latest-stack-tp8-0-7-accuracy/README.md)：PPU-07最新容器review-001，物理0–7/8045；设备graph和模型回归后单次串行三项全量，结果待生成，无性能。

- [HY4-preview PPU-03 新FGV下8192预算对比](20261020-hy4-preview-ppu03-batched8192/README.md)：新anchor独立初测完成；8192无净吞吐收益且TTFT守护失败，已恢复2048；Decode参考未稳，无GPQA。

- [20261021 MiniMax Flash 移除top-k patch精度](20261021-minimax-m31-no-topk-patch-tp8-accuracy/README.md)：PPU-07最新容器，物理0–7；设备/模型回归后单次串行GPQA198、Math500500、ERQA400，独立run，监控ACTIVE，无性能。

- [20261021 MiniMax Flash 编译器dot-K16精度](20261021-minimax-m31-dot-k16-tp8-accuracy/README.md)：用户修改adjust_kernel_param.py后独立重启复测，物理0–7，fresh Triton cache；先graph/模型回归后单次GPQA/Math500/ERQA，无性能，监控ACTIVE。

- [20261021 MiniMax Flash topk_sigmoid 独立接入](20261021-minimax-m31-topk-sigmoid-integration/README.md)：历史集成记录；较早完整入口扩展/量化实验已在review-004撤回，保留Plugin split桥接与topk-sigmoid，最终源码/PR范围见当前精度案例。

- [20261021 MiniMax新topk-sigmoid容器精度与最终PR整理](20261021-minimax-m31-topk-sigmoid-tp8-accuracy/README.md)：原组合GPQA167/198、Math500467/500、ERQA267/400完成，monitor PAUSED；review-004撤除完整入口实验；review-005进一步收敛W8A8参数/激活融合回退与测试，119 CPU+4物理0回归及补丁检查通过；收敛阶段未重启；用户随后重启new2/8035，acc-007的105+2最小通过、GPQA运行中，Math500/ERQA排队，当前无本轮新正式分数或E2E收益。

- [20261022-qwen36-27b-mx104-plugin-regression](20261022-qwen36-27b-mx104-plugin-regression/README.md)：当前用户8010服务C64/模型默认采样全量完成：GPQA162/198（81.82%）达155阈值、ERQA244/400（61.00%）全400计分零剔除；独立后验通过，半小时监控删除、服务保留，性能暂停；旧结果单列，不宣称整体性能无回退。

- [20261026-qwen3vl-metax-release-splits](20261026-qwen3vl-metax-release-splits/README.md)：mx-104原始发布镜像auto0跨batch差异及完整精度；GPQA63.6364%<64、ERQA40.75%>=40，原split1服务恢复，无新精度gate或性能结论。

- 2026-10-27 Qwen3.6-35B / mx-104：[同一回归案例](20261022-qwen36-35b-mx104-stack-regression/README.md) 的 opt1/opt2 gap诊断完成：白/黑名单受控短程仅约1.9%差别，主要采样filter从shortlist64迁成完整radix，两个rank每步sweep约7.84ms，同shape完整API新增8.28ms。原服务恢复/源码未改；诊断结论，不是修复后的完整性能验收。
