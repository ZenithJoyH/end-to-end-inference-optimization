# op-002：自动 split0 完整精度验证

用户要求保持其他配置和 prefix cache 开启，在独立容器切回 split0，先验证正确性和 graph，再完整评测 GPQA（64分）与 ERQA（40分），结束后恢复原 split1 服务。此授权仅覆盖本轮精度验证，不包含性能测试或其他分片。

## 范围与冻结

- mx-104，仅 GPU4/5、TP2、18977；源容器 `qwen3vl-pr943-split1-mx104-20261023`，独立容器 `qwen3vl-fixed-splits-mx104-20261024`。
- 单变量：MetaX native kvcache Attention 的 num_splits 1→0；其他推理源码、gems-opt、MoE、采样、黑名单、权重/tokenizer、启动参数不变。原服务源码和正常 helper 不修改。
- 使用本项目 inference-accuracy-evaluation 的 minimal-regression、formal-gate；完整 Skill bundle 已冻结。
- GPQA Diamond 198，strict-match≥64，C32；ERQA400，原 native accuracy≥40，C8，同时报告全部400计错口径。两数据集各完整一次，合法低分不阻止另一数据集运行。
- 最小回归使用原 FP64 参考容差、实际 paged layout 与短/长 KV/query shape、graph capture/至少两次 replay、服务 smoke/C8。模型跨 batch 逐位相等不作为额外精度门槛。
- 全部原始产物保留 `/public-flash/jinghao/qwen3-VL/20261024-qwen3vl-metax-fixed-splits`；新脚本/配置使用 formal20 唯一名，不覆盖旧证据。

## 执行与回退

执行前要求：仅在镜像谱系/挂载/运行源码、精确服务 PID/idle、GPU 归属及评测数据来源验证后临停本任务源服务。单控制器串行运行组件→独立模型 graph/C8→GPQA→ERQA；finally 停自己的候选模型并恢复原 split1/prefix ON/原 argv+env，重新核验当前 graph/C8/source/launch。其他服务不动。

## 结果与边界

正式结果见下文。不沿用旧主机或 split1/16 的精度 gate，不把恢复后的原服务绑定到 split0 测量分数，不产生新端到端性能结论。

准备命令已归档：`commands/formal20_prepare.py` SHA `0ae874a24bb08cf9846c4cc83289510a759e4d2f3d595b007d8516dcff30e839`，`commands/formal20_component.py` SHA `76fedf14941c5e3fbeaecd3da665cac42108b0b3882d4d654a63da69fbe15200`。Skill bundle 清单 `configs/formal20-skill-bundle.json` SHA `40605374230efd02ad9b4ba62f379c2b7038d5f9c00025d3c00de3194a34c538`。准备阶段只验证/归档并创建独立 CPU ERQA 评测容器，尚不停止源服务。

执行前冻结：`commands/formal20_controller.py` SHA `15eb1c4f877a990a28efc4ec0202a1ef34d50d525a4a7d10f24018366870da82`；启动器 SHA `319c5cff50b92b46ba1bcf431ebde820d1616bea3e926fcc4694ea6a85c42cdc`；执行契约 `configs/formal20-execution-contract.json` SHA `103323e1be4b906535530f7db64442dd599172d4c4d6c028f6ab42aeb5e6be7f`。CPU预检、AST单常量变更、镜像/挂载、原服务当前身份和ERQA数据/图片/源码/参数同源检查通过。split0源码 SHA `52a27033fc0248c1334d12577ff978161e592918a72b8b486a9bc22910ae7698`，正常split0 helper SHA `ad2649a329542c7c5d441ddb43beabb8bf5e5a85153abee1dc3b51c43802ce4e`。复用30分钟 heartbeat `qwen3-vl-gpqa-erqa` 已启用，仅关键变化通知。

2026-10-25 02:31:07 UTC：唯一控制器853560/startticks1120621371启动；02:31:39已临停原split1服务并开始72项split0组件回归。尚无正式分数。

02:32:37 UTC：72项组件回归全部通过（BF16/FP16，KV1/233/1024/8192/65536，Q1/9，B1/8/32/64，8项graph各5次回放及变更输入复验）。结果SHA `8249ca1b3a7488b33c9a193e7b83200c4e45b8bd537114b332c7ecc6be94275c`。模型独立实例 `qwen3vl-fixed-splits-mx104-20261024:597820:1120630424` 开始加载；组件通过不是正式分数通过。

02:36:11 UTC：当前模型双rank native0/FlagOSMoE路径、graph capture及至少16次回放、smoke/C8、source/argv/env核验通过；minimal SHA `ee4fe8cf4fd246cab7bf12e956f61cd51df6f5710146a4cc69c73f9f90f74136`，service SHA `c912546540d26cb6087321e968c74807caa86bc0eaf92f10ff5a2d0044c74b22`，runtime SHA `32f53e9c56d3fcc39f6a57167c25eb0af43d132c364597fe31ef0d64ee452aa7`。

02:36:19 UTC：GPQA正式预检通过，完整198题开始；原始runner run UUID `7f5bc6c9c8184d49abd3afc79a834742`，响应cache使用独立空目录。ERQA待本轮GPQA结束后串行执行；当前仍为评测进行中，没有分数结论，也尚未恢复源服务。唯一控制器853560负责完成和finally恢复，已启用持续监控。

## GPQA 正式结果（2026-10-25 02:54:43 UTC）

完整198题，126正确，strict-match **63.6364分 < 64分，未通过**。原生results分数0.6363636363636364与198个唯一per_doc的126正确交叉核验一致；source前后未改变，未签发gate。失败结果保留：`model/formal20-split0/results/formal-completed.json` SHA `dd4da943a892de47b2a5be17dd1cd4ac94fa01727e09284dae18e6c7c8ea9d78`；原生result SHA `f3537c29dc069fedabef37471af23ca6be46b004ee84c5e14f897940dc33e9ce`；samples SHA `ba378da3ddd5c5b8478b23eb8706c4052295e5999b8b18220ce451a14ccb6368`。

调用本地 inference-accuracy-diagnosis，登记 `accdiag-auto0-gpqa-002`：这是有效正式阈值失败，机制尚未定位，阻止split0晋级/新性能优化；不根据低分单独归因FlagGems-vllm或native kernel。CPU只读对照formal9 split1：198题题目/参数哈希一致，共同正确114、共同错误55、仅split1正确17、仅split0正确12；完整响应哈希相同4题。此为描述统计，split0仅一轮，不能据此证明稳定根因或采样波动已排除。

02:54:48 UTC：按照用户明确要求，控制器继续完整ERQA400（阈值40），不因GPQA合法低分取消另一数据集，也不重跑GPQA。当前ERQA进行中，源服务仍临停；finally恢复原split1的计划不变。监控首次SSH短暂断连后，项目connectivity-check重新通过，已恢复只读跟进，未影响远端控制器/服务。

04:00 UTC监控发现：ERQA原生评测已结束（returncode0），raw/evaluated均400个唯一ID，176正确，原生accuracy44.0，零拒答。随后采集器在无拒答分支访问不存在的 `reject_info` 报KeyError；这是结果采集schema问题，不是推理失败。原失败完整保留，未重跑推理。控制器finally已03:43:49 UTC恢复原split1服务 `1108035:1121036731`，graph16/C8/source/argv/env通过，后续容器内PIDticks及modelsHTTP200/正常helper cfa实查通过。

执行前归档 `commands/formal20_finalize_existing.py` SHA `db061c7200c8832a1bfa5ca0f3662c2ebb21d70338e66bee9becf20c86ff0e20`，仅使用原始400结果/原nativefilter验证零拒答分支、复核数据图像源码及静态模型/源码身份，记录明确offline postrun快照与精确PID停止回执；不伪称已停止候选仍有live post-ERQA快照，不发模型请求，不改写原生输出或旧失败。复核后再关闭监控。

## 最终结果及恢复（2026-10-25 04:05:59 UTC核验）

| 数据集 | 正确/完整样本 | 分数 | 阈值 | 判定 |
|---|---:|---:|---:|---|
| GPQA Diamond strict-match | 126/198 | 63.6364 | 64 | 未通过 |
| ERQA native accuracy | 176/400 | 44.00 | 40 | 通过 |

ERQA零拒答，全部400计错口径亦44.00；沿用原生filter/判分，400个唯一ID、数据/630张图/评分源码和分数已复核。`op002-erqa-zero-reject-schema` 已通过原生零拒答分支验证解决，旧控制器失败与原始输出全部保留；恢复只生成新的验证回执，没有重发任何推理请求、改写原生分数或伪造live postrun快照。ERQA结果 `model/formal20-split0/results/erqa-completed.json` SHA `8d6beb46142d020ebe0bb4aff9e9a4075d86fc9737cdce841d03fbf0fb703c6f`；采集恢复 `results/formal20-collector-recovery.json` SHA `c53744575739e80ece2e105fcd6148e9fccb0ffbf4c07885d10093aab36e2a54`。

原split1服务已03:43:49 UTC恢复：`qwen3vl-pr943-split1-mx104-20261023:1108035:1121036731`，prefix cache ON，原argv/env/所有源码/模型与tokenizer保持一致，当前进程与modelsHTTP200复核通过，双rank graph capture/至少16次回放及C8通过，正常helper cfa保持不变。恢复回执 `results/source-restored-formal20.json` SHA `92e50b30522fef93adf05a1d99574e9a900e0ac9415ae8749d866670a587cbd1`；当前复核 `results/formal20-restored-current-check.json` SHA `40950973b9de4152258dec99f00d134f56d948ca1a5eb34874b0d25c885af00c`。旧候选模型、评测进程和控制器均已退出；独立容器只保留sleep，其他服务不动。

综合回执 `results/formal20-completed-recovered.json` SHA `c3f34f2decec73654812247b35859d8d61c67216533cb98fe9cb50b38508b46e`。本轮用户要求全部完成，split0因GPQA低于64不晋级，未签发其GPQAgate，恢复服务不承接候选分数；无新性能测量或收益结论。监控 `qwen3-vl-gpqa-erqa` 已删除。后续若继续精度定位，应另行冻结最窄诊断，不自动重跑或试其他分片。
