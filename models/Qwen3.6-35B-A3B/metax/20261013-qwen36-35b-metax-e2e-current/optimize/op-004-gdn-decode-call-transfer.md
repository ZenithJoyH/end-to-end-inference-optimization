# GDN decode 调用完善

用户 2026-10-14 要求停止此前全部优化工作，并参考 mx-59 的 `qwen36-27b-fa-opt-20261012` 容器中已完成的 FlagGems-vllm GDN decode 调用，完善当前 `qwen3.6-35B` 环境。后台 `qwen36-35b` 已暂停；旧实验保留，不记为失败。

先只读确认两容器真实源码、revision、dirty diff、导入路径与调用契约。参考容器只读，不复制其模型/服务配置，不修改 vLLM、权重或 tokenizer。目标沿用已有 Plugin 扩展点，Gems 负责实现与平台分发；完整 FlagGems 白名单、attention、MoE workspace 复用保持。修改前备份受影响文件，变更后验证能力/旧版本兼容、目标调用和最小数值回归。graph/正式模型精度及性能的未完成项明确记录；磁盘修改不等于当前进程已加载。

当前状态：按用户后续要求已对齐27B decode源码；代码保留，服务不重启。前序决定和证据保留在下文。

本轮使用本地 `inference-accuracy-evaluation` 的 `minimal-regression` 方法（`e2e/accuracy`）。此前 E2E 计划不恢复，不发起旧 GPQA、benchmark 或 CPU observer。

| 项目真相 | 冻结事实 |
|---|---|
| 参考生效源码 | `/workspace/FlagGems-vllm-gdn-20261014`，HEAD `29e80363b43bce4a25929989641015c1e734c9e3`，MetaX recurrent 文件 SHA `5d15461a87db9b61adf6bbf52b576b9941fda9ed1e653ec98826926f0470a253` |
| 目标生效源码 | `/workspace/FlagGems-vllm`，原 HEAD `05d0ff0547dc9cc7cce18f47c6f57cc9d04f0777`，editable；Plugin HEAD `8b059122e32b9ac47b9820a9c7b1bb95077481a4`，已有 dirty 修改保护 |
| 修改边界 | 不升级整个库、不迁移参考容器 attention/sort/manager，不改现有 vLLM、MoE、attention 或服务参数 |
| 验证 | 目标仓库 GDN dispatch 单测与单独进程数值回归；服务 graph/命中/全 GPQA 为部署后待验证，当前服务不重启 |

| 调用契约 | 范围 |
|---|---|
| packed non-MTP | 公共 `fused_recurrent_gated_delta_rule_packed_decode`；原始 mixed QKV、gating 参数、output、V-major paged state 直接传递，返回原 buffer 对象 |
| recurrent MTP | 新 MetaX 公共 recurrent API 直接传递 accepted-token 和二维 page index；原库缺新 ABI 时保留旧适配与原调用策略 |
| state 与 padding | `[pages, HV, V, K]`，K 连续，支持 hybrid cache 页 stride；索引 0/负数为 padding，不更新 state；有效页索引唯一、范围有效由 vLLM metadata 保证 |
| 兼容与异常 | 公共 packed API 缺失不选择新实现；transitive import 与已选择 kernel 的错误上抛；stateful 调用 strict，禁止执行出错后重试导致二次更新 |
| 未承诺范围 | 其他硬件未测；非连续且超过 64 packed tokens 的 recurrent 明确 unsupported，避免照搬参考文件中通过 Torch contiguous 补洞的分支；不改变正式 GPQA 契约 |

| 路径设计 | 接入与调优 |
|---|---|
| fast | 新公共 packed GDN API，Gems runtime 分发至 MetaX 融合 kernel；无 Plugin QKV split/layout/output copy |
| general | 新公共 recurrent API；复用参考 MetaX V-major 实现，旧接口兼容逻辑保留 |
| unsupported/compatibility | KDA 保持既有契约；旧库保留既有可用实现，不用新宽泛异常吞掉执行故障 |
| autotune | 本轮迁移已完成 MetaX kernel，不新开发 NV kernel；参考 BV16/32 调度保留，不宣称其在 35B 上有性能收益 |

原库 `workflow.md`、目标 AGENTS 已读取；其引用的 `optimization.md` / `deep_opt.md` 在目标与参考中均缺失，记录为工程规范缺口。本轮不做新的 tile/算法性能调优。

最终状态：用户明确选择“先保留代码，暂不重启服务”。代码留在当前容器，8010 保持原 PID 944104 / birth 490527206；本任务客户端均退出、running/waiting 均为 0。后台和所有旧实验继续暂停。

25 项 CPU/mock GDN 单测通过；GPU6 默认 stream 的 14 项数值测试通过，包含 batch1/8/64、FP16/BF16/FP32、零/负 page padding、padded page stride、MTP accepted-token/二维索引、空 batch 与 output/state 对象复用。独立 CPU reference 比较使用冻结的 atol/rtol，未宣称 bitwise。当前公共函数确认为 MetaX backend 导出；真实模型进程的调用命中、graph capture/两 replay、C1/C8 与新的全量 GPQA 尚未执行。来源已改变，原 82.8283% 的历史 gate 不可绑定到这批新源码。没有新的性能数据或 E2E 收益。

首次单测 19 passed / 4 failed 是旧 mock 使用 `object()` 缺少真实 OpImpl 的 `is_available()`；修正 fixture 后完整复测通过，生产错误处理未放宽。首次终态检查误将原 manifest 排除的 ignored build/version 文件当作源码新增；按原 git source 集合重验，12252 文件（原12249加3新增）无非预期源码漂移。失败原件保留。

原始证据：`/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/results/gdn-transfer-{applied,fix-applied,numeric,unit-v2,terminal-v2}-20261014.json`；terminal SHA `55425f48ebc811f41a3cdaed9d0911a4c93acf542801d946486be28884b56a8e`。逐文件 SHA 与补丁/备份见同目录 state 的 `gdn_call_transfer`。

2026-10-14 后续明确指令：GDN decode 调用与 27B 保持一致，删除额外旧接口兼容分支和超过64 token限制，只保留代码，不重启服务。该指令取代上一版本保留旧 ABI/限制的决定。恢复参考文件中非连续 QKV 大于64 token时的 `.contiguous()` + large-token kernel 原路径，是用户要求的参考一致性例外，优先于目标 workflow 默认禁止 Torch 计算/复制补洞的限制；不将该路径称为新优化或纯无复制路径。

本次仅替换 backend 的3个decode相关方法、GDN调用hook、MetaX recurrent文件和对应导出/测试。Prefill方法、MoE与attention保持原样。公共API缺失/不可用时的常规dispatch选择保留，与27B一致；已移除旧 `paged_gdn_update` 调用、state pack/unpack、旧类方法patch、speculative旧ABI分支以及64 token拒绝条件。未删除用户已有的旧helper文件，它们不再导入/调用。

本轮完成：MetaX `fused_recurrent.py` 和 GDN hook 与最新读取的27B参考逐字节一致；backend `fused_recurrent_gated_delta_rule_fwd`、`gdn_decode`、`gdn_packed_decode` 三个方法 AST 一致。常规可用性检查与 stateful strict/no-retry 保留；额外旧 ABI 路径已删除。完整 Prefill 方法未改，MoE/attention未改。

本轮18项公共路由单测和15项GPU6默认stream数值测试通过；新增65-token非连续QKV的测试通过，原14项亦保留并复测。此版本的graph/服务命中/C1C8/正式GPQA仍未执行，不复用前版数值或历史精度回执作为新服务通过。

終态 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/results/gdn-align-terminal-20261014.json`，SHA `051de61936353e8d39fa1ec3a99cc7257655c8af7ae6c51aaef6622ec9f1efb5`；12252源码文件无非预期改动，API仍944104/birth490527206，running/waiting0，本任务客户端退出。回退脚本 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/commands/rollback-gdn-align-20261014.py` 只恢复本轮7个文件到前一版暂存代码，不重启服务；原始baseline恢复入口保留为历史，不直接重放旧脚本。

启动脚本只读检查：`/public-flash/jinghao/qwen3.6-35B/start-model-flagos.sh`，SHA `6f93eaccac1f7a8a8d30033bb4a114c7a9c5d6cb03e7092764086a7412d1f6cb`。原白名单不含 `gdn_decode` / `gdn_packed_decode`；注册端按 `use_flaggems_op(impl.op_name)` 过滤，因此需在原完整白名单后追加这两个名字才能选择本轮公共 GDN decode 实现。`VLLM_PLUGINS=fl` 可显式指定Plugin。仅decode不需要调整prefill/其他算子开关或新增vLLM CLI参数。本轮只给出调整建议，未修改启动脚本或重启服务。

用户手工启动GDN并提供新P1K/P4K CSV后明确恢复E2E优化。当前两个TP rank真实packed函数命中与FULL capture完成已经日志核验；新acc004正式精度在跑。CSV全部三轮保留：P1Kallmean1106.05vs旧1139.59(-2.94%)，SUMMARY1096.37vs1140.97(-3.91%)；P4Kcurrent911.15/910.72/915.88，而旧524.27慢轮导致summary比较夸大。不能据此签发“无回归”或GDN精确收益；当前GDN作为用户指定候选保留pendingprecision。

2026-10-14T15:35:26Z用户已加载的GDN组合已独立fullGPQA198通过，strict-match164/198=82.8283%；新原生schema3回执SHA6852c4ed948413acbfe8d1594a8fce04959114aff5cfa17c028f19be50b6dac0绑定当前952702/birth491055395。两个rank packed MetaX hit与FULLcapture已证；直接replay计数仍unknown，非最终验收。继续op001同组合原生P1K mixed诊断，未在本轮改算子或重启服务。
