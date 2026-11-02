# MiniMax-M3.1 Flash / PPU-07 最新栈迁移

最新 review-001 已完成 Plugin main 全量差异收敛：移除 CompressedTensorsConfig 类级包装，改为当前模型配置实例；native bridge 延迟到目标模型加载；撤销无关 MetaX 扩展和重复转发，保留路由索引 dtype。190 CPU 回归通过，9 设备用例仅收集；真实设备/模型验证仍 incomplete。详见 [review-001](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261020-latest-stack-migration/optimize/review-001.md)。以下为各轮历史记录。


用户要求新容器+三库最新+迁移当前优化。新容器minimaxM3.1-opt-latest-20261020已经创建并editable安装Plugin a696859b、FV fa78ddee、FG 8200f71f，迁移保留MoE/INT32、dense split-K/B布局、OAI量化融合与MiniMax模型适配。源容器、8035服务及全局启动脚本不改；镜像谱系与相同/mnt挂载验证通过。

68项Plugin单测通过。首次设备回归因8–15卡被其他Qwen服务占用而在预检拦截；按用户指令等待，2026-10-20 03:48 UTC确认空闲后，复核容器/完整源码tree/命令SHA/挂载并只运行既有一次算子回归：INT8 56/56逐位一致且各两次graph回放通过，融合/MoE pytest34/34通过，D64/D80视觉SDPA16/16及两次graph回放通过。测试后源码未变、旧8035健康，未停止其他负载。监控已PAUSED；尚无新模型最小回归、完整精度或性能，不自动启动后续任务。新容器独立脚本准备为8045/物理8–15，当前不运行。旧分数和gate不适用于新版本组合。

记录：[env-001](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261020-latest-stack-migration/optimize/env-001.md)、[state](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261020-latest-stack-migration/optimize/state.yml)。外部案例/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration，原生产物、版本tree及命令SHA保存在其中。

标签：multimodal/MoE、PPU-ZW810E、TP8、W8A8、graph、operator、environment-migration；本轮无性能结论。

2026-10-20 后续用户要求整理 Plugin，已完成 [refactor-001](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261020-latest-stack-migration/optimize/refactor-001.md)：公共 Linear/MoE 通过既有 CachedOp 调用，平台库策略进入配置/backend，模型语义单入口，top-k/Prefill launch 兼容集中 Thead backend 并按架构/shape 限定；FV/FG 不变。最终178单测、56 INT8 graph、10模型算子、2原生fallback、FULL/PIECEWISE capture及105+2模型最小回归通过。临时8045已结束，代码和容器保留，旧8035/全局脚本保持；正式精度与性能未测，无新gate。改前备份、两份补丁和原生证据SHA均在refactor-001记录；此前env-001记录为历史迁移状态，当前以refactor-001最终记录为准。

最新完成 [cleanup-001](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261020-latest-stack-migration/optimize/cleanup-001.md)：10份历史Plugin/FV私有源码经宿主机归档及13,875条文件/链接校验后移除；容器仅保留最终安装源码，导入/注册及三库源码指纹复核通过，旧8035和全局脚本不变。

当前路径以 [rename-001](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261020-latest-stack-migration/optimize/rename-001.md) 为准：最终Plugin `/workspace/vllm-plugin-fl`，FV `/workspace/flaggems-vllm`；editable来源/注册验证通过，源码及版本未变，旧plugin/fv目录已移除。独立启动脚本仍有效，无新增精度/性能测试。

[main-001](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261020-latest-stack-migration/optimize/main-001.md)：当前Plugin已在官方main（a696859b9，跟踪origin/main）直接保留工作区修改；包版本0.0.0+ga696859b9.d20261020，源码未变，未用stash保存/恢复，没有提交推送。

当前策略以 [policy-001](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261020-latest-stack-migration/optimize/policy-001.md) 为准：撤回非必要provider/平台白名单，恢复原有fl_envs开关；199单测、56 INT8 graph、10模型算子及105+2模型最小回归通过，临时8045已退役。仅新容器独立入口显式开启已有VLLM_FL_USE_FLAGGEMS_VLLM=1；原8035/全局脚本不改，正式精度/性能未测。

当前接入以 [adapter-001](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261020-latest-stack-migration/optimize/adapter-001.md) 为准：去除两个cache/预处理dispatch及独立try融合dispatch，直接调用已有库能力；201单测通过。8–15卡被其他vLLM占用，设备/模型回归及去Thead补丁验证未执行，保留历史兼容，不冒充当前编译失败复现。原8035/全局脚本未变，无新gate或性能结果。

[compat-001](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261020-latest-stack-migration/optimize/compat-001.md) 已离线复现当前top-k兼容的必要性：六原始配置直接编译均通过，但默认AABS把调整副本K缩为1，违反topk16的K>T约束，原生autotune最终编译失败；固定K128直接JIT编译通过。两处Thead兼容保留，三库源码及服务未改，无GPU计算/新精度或性能。

最新 [env-002](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261020-latest-stack-migration/optimize/env-002.md)：FlagTree已升级至官方PPU0.7.0+ppu3.6（Triton3.6），精确安装备份及旧wheel已归档。新缓存原生AABS复现仍将K缩为1并最终编译失败，固定K128编译通过；保留top-k/GQA兼容。仅FlagTree发行包变化，三库源码/启动/旧8035未改；本轮无设备/graph/模型精度或性能验证。

上游跟踪：已在同根因[#1407的补充报告](https://github.com/flagos-ai/FlagTree/issues/1407#issuecomment-6286746272)中发布PPU0.7.0验证及已测试的独立最小复现；修复[PR1408](https://github.com/flagos-ai/FlagTree/pull/1408)仍未合并，本任务尚未验证该PR。详见[env-002](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261020-latest-stack-migration/optimize/env-002.md)。

当前最新接入见 [adapter-002](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261020-latest-stack-migration/optimize/adapter-002.md)：删除 split SwiGLU-OAI 独立 dispatch 注册、CachedOp 和 backend 转发，由 MoE 激活入口按原 env/名单策略直接调用 FV 统一 MoE API；融合路径去掉该 manager key 依赖，保留参数、库融合和两步回退。220 CPU 单测、真实安装/registry/源码及 Git-native 全量与增量反向检查通过；FV/FG/FlagTree/启动及 Thead patch 均未改。物理8–15仍由 Qwen 占用，设备/graph/模型最小验证 incomplete，未启动新服务或评测/性能；监控保持 PAUSED，旧正式 gate 不复用。

[adapter-003](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261020-latest-stack-migration/optimize/adapter-003.md) 修复新增INT8 backend在FV关闭时误用FG FP8-only scaled_mm的接入缺陷：将原FV开关作为registry可用条件，关闭/未设直接选择原生INT8 reference；开启时的FV优化保持。真实FG CPU输入拒绝、strict/非strict实际registry选择及原套件共230单测通过；三库/启动核验与两份补丁回退检查通过。设备/graph/模型仍待空闲卡，无新gate或性能。

运行问题边界：[原8035请求健康排查](../20261019-minimax-m31-flash-ppu-tp8-accuracy/README.md)核实根service.log来自minimaxM3.1-opt-20261008，11处500为非对象请求体触发vLLM schema的str.get异常；CPU复现闭合，具体外部编码来源未确认。不是本迁移容器的运行记录，本轮未改其代码、设备或验证状态。

当前激活参数接入以 [adapter-004](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261020-latest-stack-migration/optimize/adapter-004.md) 为准：完整删除install_fl_w8a8_activation_config及其vLLM方法包装，选中的FlagGemsW8A8Experts直接从该层FusedMoEConfig读取参数、存入自身gemm1字段并透传；共享quant_config及原方法不改。235 CPU单测和重复注册/安装/补丁审计通过；设备/graph/模型因8–15占用仍incomplete，原8035/其他负载未动，无新gate或性能。

[tests-001](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261020-latest-stack-migration/optimize/tests-001.md) 完成测试收敛：新增文件11→2，删除9个拆分文件，通用用例归入已有激活/量化/MoE文件，保留模型及Thead两个新增文件；生产源码不变。显式排除gpu后184 CPU通过，9项PPU/GPU相关用例仅收集。旧adapter-004的235项已更正为234CPU+1GPU量化测试，前述“纯CPU”标签不准确；各旧实验追加真实范围，不改变通过总数或补齐模型/graph门禁。
