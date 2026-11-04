# op-006：固定 MetaX kvcache Attention num_splits=1

用户授权：保持其他配置和 prefix cache 开启，在 Plugin 中固定本条 kvcache 调用的 num_splits，验证正确性和 graph 后重跑 GPQA，阈值64分。

设计：在现有 vendor/metax Attention backend 的 FlashAttentionImpl.forward 调用处增加 num_splits=1；不改 varlen/cascade/DCP、采样、MoE、gems-opt、vLLM、模型权重或启动参数。不引入新的 dispatch、配置或开关。此前 diag005 的相同完整 Q/K/V 重放已将批次相关数值差异收敛到 native 自动分割路径。该修改影响复用本条 MetaX kvcache 路径的调用者，不能宣称其他模型或平台已实测。PR 状态 experimental，性能未知。

验证契约：本地 accuracy Skill minimal-regression 与 formal-gate。先用可信 FP64 Attention reference、同输入C1/C8及目标KV布局进行代表性检查，服务 capture 和至少两次 replay，smoke/C8 与实际 num_splits=1 命中证明；失败停止晋级。通过后只运行一轮完整198题 GPQA Diamond，C32，输出预算18000，temperature0.7/top_p0.8/top_k20，任务seed42/API seed1234，strict-match阈值0.64。保留全部样本和失败，不挑选最好轮次。prefix cache 按用户要求开启；不用于性能收益结论。

范围：mx-59 / qwen3vl-pr977-20261022 / GPU0,1 / port18977；生产9999不变。复用已验证独立容器，执行前重新确认镜像与规范化挂载。改动前备份原文件和完整运行身份，回退为恢复该文件后按原配置重启目标服务。

远端产物：/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-kvcache-split1-gpqa

状态：本轮已完成，GPQA 131/198=66.16分，达到64分阈值；终态证据见本文最后一节。

执行进展：Plugin AST 校验确认只有现有 kvcache 调用新增 num_splits=1；文件 SHA 从 f81fa552667b3ed98d1cf141d2dee33ba10476cda9a997744495bdbc36289ef2 变为 2eaec0be03b16ad1d4b5e24851655eea53d0fb90db83a5ccaeff04011dcb3002。BF16/FP16 的12个FP64参考用例和两份真实rank输入重放通过，12次capture/48次replay，包含更新Q后回放。

测试设施问题均保留：完整/过滤环境字段比较、嵌套脚本引号在源码修改前安全中止；首版合成张量设备传输不满足 native last-stride=1，已用扁平存储传输和显式shape重建并逐项审计字节修正；首版有界profiling探针在预热中耗尽事件上限，故该轮服务未晋级，改为一次性真实native调用包装且立即还原后重新启动同配置服务。不是模型正确性失败，未启动GPQA，也未关闭任何FlagGems算子。

监控：qwen3-vl-gpqa-erqa，30分钟，ACTIVE，仅终态/关键变化通知。

服务门禁通过：service-v2 两 rank 均实测 native num_splits=1，Plugin SHA 与补丁一致，取证包装在首次调用时立即还原；每 rank capture+16 replay，smoke/C8通过。原生函数来源仍为已冻结 MACA flash_attn 接口，SHA a0ce682debda2e3b0457d3716e3c4bdc905d7d759238800494a5619f5a1d37c6。正式流程已启动，先重新采集两次任务/数据provenance与preflight，再执行唯一一轮完整GPQA，不进行特殊GPQA预填充或挑分复测。

工程复核：参数只在现有 MetaX backend adapter 中指定，因为当前 CLI 未暴露此 native 调用参数；未新增注册、环境开关、公共依赖或模型名判断。共享此入口的其他 MetaX 模型会采用相同固定split策略，尚无其正确性/性能结论。PR readiness 为 experimental，不做提交或推送。

| 场景与版本组合 | 模型结构、平台与有效输入 | 预期路径/模式 | 证据类型与结果 | 证据与未测范围 |
|---|---|---|---|---|
| 当前 PR943 a1570df MoE、Plugin024plugin-opt+单行补丁、gems-opt c3c5f5a、torch2.8.0+metax3.7.0.7/FlagTree3.6.0 | C550，GQA Q16/KV2/D128，BF16/FP16，C1/C8，Q1/9，KV1/233/1024/8192，真实rank KV stride/page布局 | vendor.metax native kvcache，num_splits1 | hardware executed_passed | results/gpu-correctness-graph.json；12参考用例+2份真实rank输入，12capture/48replay |
| 零token、varlen、cascade、DCP等未修改分支 | 当前相邻实现 | 原路径 | static executed_passed；额外硬件 not_run | configs/plugin.patch 与全文件AST只差单个调用kwarg；不以静态检查替代这些分支的新增硬件覆盖 |
| NVIDIA/其他平台、无MetaX SDK | 未连接其他Host | 原导入/选择路径 | static executed_passed；hardware not_run | 没有新增import或通用层变更；其他平台硬件交由对应CI，当前未实测 |
| 当前 Qwen3-VL TP2 graph 服务及 worker 生命周期 | GPU0/1、BF16、prefix cache ON、FULL_AND_PIECEWISE、最大capture64 | 两rank均实际kvcache split1、FlagOS MoE保持 | hardware executed_passed | service-v2/graph、service-v2/results/service-minimal-raw.json：capture+16 replay/rank，smoke/C8；一次取证后原函数立即恢复 |

跨仓库依赖：未改FlagGems-vllm、FlagGems或vLLM；依赖现有MACA flash_attn_with_kvcache接口支持num_splits参数。尚未测试其他模型、ALiBi/sinks/window等额外组合，也没有本点端到端性能结论。

## 本轮最终结果（2026-10-23）

GPQA 131/198=66.16分，达到64分阈值。198题、冻结strict-match指标、逐题计分与原生汇总一致；任务/数据/config/服务来源验证通过。只运行一轮完整评测，不覆盖之前失败记录。服务身份 `qwen3vl-pr977-20261022:580939:562348465`，prefix cache开启；完整语义环境、启动argv/cwd、MoE bbc2edded、gems-opt、采样及vLLM均保持。Plugin AST只增加num_splits1，文件行842，SHA 2eaec0be03b16ad1d4b5e24851655eea53d0fb90db83a5ccaeff04011dcb3002。

两rank真实命中、服务graph capture+16replay、smoke/C8，12参考用例+2份真实输入，以及12capture/48replay全部通过。最终容器镜像和挂载再次核验一致，9999仍healthy；没有回写生产或修改主启动脚本。

正式gate：{"path": "/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-kvcache-split1-gpqa/results/accuracy-gate.json", "sha256": "9e50ac8b35973f625b95366c2e88eaddb66bab3c4a2abe01a34ab6d09e7614c5"}。

终态核验：`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-kvcache-split1-gpqa/results/terminal-audit.json`，SHA `4a3e11465803c0dc2086978af71f1bbe826263ac74fc79b6c2322e4bfbbce5b8`。完整原生分数/样本/冻结输入与命令索引见该文件引用的`results/completed.json`。

结论：保留当前独立服务中的固定split1改动，本轮GPQA达到阈值；仍不代表多轮得分稳定、全模型严格batch不变或端到端提速。此前acc003的PR316正式分数属于不同代码/实例；不计算本点纯因果收益。ERQA和端到端性能未重测，整体项目验收状态不变。监控`qwen3-vl-gpqa-erqa`已PAUSED，30分钟监控终态已停用。

## 2026-10-23 补充验证请求

用户要求保持其他配置和prefix cache开启，补齐ERQA（阈值40），再对比split0/1稳态端到端性能。明确选择先测P1K/D1K/C64/N128，并增加缩减P64K长KV哨兵，发现回退后再扩大。本次沿用op006，不创建新的优化点或每轮文档；原始材料保存在 `/public-flash/jinghao/qwen3-VL/20261023-qwen3vl-split-erqa-perf`。精度模式沿用本地formal-gate的原生400题ERQA适配；性能模式targeted/performance_only，不声明最终全场景验收。用户本次指令覆盖Skill默认prefix cache OFF要求，双方恒定ON，另冻缓存准备与实际命中证据。

本次性能冻结初稿：targeted/performance_only。主场景P1024/D1024/C64/N128；长KV哨兵P65536/D128/C8/N16，对应最终P64K/D1K/C64/N128，明确缩短输出和减小请求/并发，不能外推完整P64K结果。temperature0.7，top_p/top_k由相同服务默认0.8/20继承，ignore_eos固定输出，random长度ratio0；原生客户端代码已核验不默认覆盖top_p/top_k。角色B1(0)/C1(1)/R1(0)/B2(0)/C2(1)/R2(0)，每角色独立服务实例，五轮预热，末三轮输出吞吐散差<=5%方可准入；三轮测量全部保留。主输出吞吐允许3%工程回退容差，总吞吐守护3%，mean/P99 TTFT和TPOT守护10%；测量/进程离散上限10%，baseline/revert漂移上限5%。报告原始轮次及实际散差，不把工程容差当统计置信结论；失败/不稳定不挑轮。两边prefix cache均ON且按同一原生客户端预检/预热策略准备，独立记录命中。完成后恢复split1并核验graph/C8。

执行状态：ERQA原生400题已启动，CPU evaluator `qwen3vl-split1-erqa-20261023`，原生镜像/data630图/source SHA与此前冻结版本一致，响应缓存关闭，服务仍为已通过GPQA的同一实例。日志中有SDK重试，但服务持续生成且无已记录终态错误；完整结果尚未生成，不按已派发数冒充已完成数。性能控制器PID380482/startticks566448529，当前只等待ERQA通过，不切换代码。冻结输入与脚本SHA见state.follow_up.frozen_artifacts；控制器会保存全部原始轮次，并在结束或失败时尝试恢复split1和原有有界取证器。若存在外部改动、繁忙服务或恢复异常则停止并保留证据，不覆盖外部改动。监控`qwen3-vl-gpqa-erqa` ACTIVE，30分钟，仅关键变化通知。

用户2026-10-23明确要求暂停并迁移到mx-104。精确停止两个控制器和ERQA客户端，110为已派发数，部分原生items保留，未签发ERQA分数；性能未启动。暂停回执`results/paused-for-migration.json`位于新补充验证远端目录，监控PAUSED。随后只读发现源独立容器已不在running状态；没有重启它，也未对其历史PID执行停止。迁移从其当前停止状态快照，跨Host结果另建案例，不直接复用旧Host精度gate。

迁移去向已验证：mx-104新案例20261023-qwen3vl-metax-mx104-migration，物理GPU4/5/TP2、容器qwen3vl-pr943-split1-mx104-20261023、18977。完整快照/源码/挂载与新服务两rank graph16/C8通过；ERQA400在新Host重跑，性能仍待精度通过。旧GPQA分数/原生gate证据保留，但不是新Host当前实例的有效绑定，跨Host不rebind。
