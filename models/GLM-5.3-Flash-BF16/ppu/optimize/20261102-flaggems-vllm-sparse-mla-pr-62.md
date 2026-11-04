# 点62 FlagGems-vllm Sparse MLA正式PR整理与提交

状态：准备；用户明确授权整理当前FlagGems-vllm并向官方仓库提交一个PR。

目标仅PPU-13 / glm5.3-flash-opt-20260911 / 8011。当前安装FGV基线9f6a0ef，内容d6cbf04f…；当前Plugin45c95631…，原服务3917036/start622443729、原脚本/MBT32768/启动参数保持。本次在独立PR副本操作，不升级或切换生产服务，不改用户dirty/index，不发模型请求。

## 范围与契约

完整盘点6文件差异：Sparse MLA通用/thead/现有测试3文件、MNNVL可选依赖1文件、SQL单表反射及测试2文件。本PR聚焦公开flash_mla_sparse_fwd的H4与graph能力接口，SQL/MNNVL是独立主题，保持容器原状并列为未提交项。基于官方main be0001631b1c3ec605a93a90022b372079c97812；从原补丁迁移必要最小改动，新增支持BF16/HQ4/DQK512或576/DV512、紧凑输出、空SQ；保留原HQ64/128路径。生产禁止Torch计算fallback；框架metadata及workspace不迁回FGV。

遵守算子规范A1–A4/B1–B4/C1–C7/D1–D5/E1–E6/F1–F4/F6及实际仓库AGENTS/workflow。optimization.md/deep_opt.md以实际存在性核验；本次能力交付不宣称性能验收G6。对继承autotune作最小修改并说明豁免，不进行无关框架重构。

## 执行前验证计划

先保存精确原补丁与源码SHA，核验最新主线/用户fork/已有PR。独立副本格式/lint/pre-commit、rule-check/CI路由、公开导出/无Torch计算审计、构建检查。测试按公开入口核对真实命中、BF16小head与64/128守护、512/576、stride/offset/尾块/无效索引/可选sink及length/空输入与报错，独立CPU参考。graph至少两次更新输入与所有输出哨兵，验证三返回值；如设备/导入限制不能完成，准确写未测且以draft交付，不伪造硬件通过。小型合成算子测试不触发模型请求，不争抢正在运行的任务；生产服务和DB不写。

提交只包含公开代码、测试与必要benchmark/metadata；测试/构建日志在批准远端唯一目录resume-20261102-point62-fgv-pr，本地仅记录/摘要。无模型题目、权重、原始日志/设备私有信息上传GitHub。先完成具体可评审结果，再创建用户fork唯一分支和官方PR；明确未测平台、性能及当前模型分数不代表本PR gate。

执行前命令冻结：远端`commands/prepare-validate-v1.py` SHA `e6b34c815d7d26c85a6b0978461417e29d53ab445ddb50cac09396872ac32b4b`。独立未安装源码副本继承当前运行时（包含未提交本PR的SQL/MNNVL修复），仅覆盖本PR5文件，核验导入与公开注册；33项预计用例以原生实际收集/通过数为准。不会把该组合运行等同fresh main整库安装。仅PPU0，服务空闲且空闲显存>256MiB才运行小型合成测试，独立测试DB，不发模型请求、不重启。失败保留不盲重试。

准备v1在复制/覆盖5文件后摘要步骤失败，未进入GPU或模型请求；只读逐文件确认原副本1137文件完整且仅候选5文件不同。保存`commands/resume-validation-v2.py` SHA `28b1a578347a4b5fcf77191223a681ead0a676d3a0aa2a394c981d5d604fe8d8`，仅复用逐SHA匹配的副本并执行尚未运行的测试，不重复复制或重跑用例；原失败保留。

条件式算子microbenchmark命令`commands/benchmark-v1.py` SHA `45ed1bb6930ed6b48a8b54258f7c3891140f14309fb621fddb0be96794ae8f03`，仅上一步真实数值/graph全部通过且服务空闲才运行：复用仓库Benchmark与cudagraph计时，12个SQ1/8/64×DQK512/576×TOPK17/128、SKV256、BF16，baseline为H4补零到64含copy与公开调用、candidate为紧凑H4，统一warmup10/iter30。没有原生H4 baseline，不称旧版本速度提升或E2E收益；其余平台及形状待CI。

正式PR已提交为Draft [#1044](https://github.com/flagos-ai/FlagGems-vllm/pull/1044)，head7dac5f76e085e2b6a860f7a80bb413d92ce39ff5，basebe000163…，5文件/1提交；33项PPU0skip通过，8capture/16变化输入回放。benchmark12形状原生执行完成但2项SpeedUp<0.9，G6未过，不能写性能passed。保留局部功能交付，不自动安装生产。归档/最终只读命令`commands/finalize-v1.py` SHA `a2ab334370950de521bb926aecf5112fbcb287c72769965f1623925c970f3fc3`，submission-artifacts SHA `b4c3e2f5f2012aed3b8cb8b3c8dcae1075d1ddfb41f6681b7066b9dcaf8b4961`，仅证据归档与当前身份复验。

## 已提交的最终改动

[官方Draft PR #1044](https://github.com/flagos-ai/FlagGems-vllm/pull/1044)，分支`ZenithJoyH:glm53-sparse-mla-h4-20261102`，提交`7dac5f76e085e2b6a860f7a80bb413d92ce39ff5`；官方base `be0001631b1c3ec605a93a90022b372079c97812`，1提交/5文件/+282−13。GitHub逐blob与本地检查副本一致，tree `bb79fb3117d1d18b87f2f17312b78d4f62257425`，完整patch SHA `bc78a883aa19917667b6dc6f9ae8ae2c62eb6750bfdcc4cfe9ca241f4f6e43d8`。

- 通用Sparse MLA新增H4的BH16合法候选与head mask，不分配64-head的Q/output；64/128保留原候选和key，SQ0返回空三元组。
- 既有thead backend仅H4转发通用kernel，64/128原planner/kernel不动；补标准首行debug命中日志。只有选中provider声明已验证singleton decode graph；通用入口保守False，未加入通用平台名称排除或新开关。H4本就不满足TLE64-head条件。
- API签名与返回ABI保持；不支持head显式ValueError。纯metadata仍在Plugin；无Torch计算fallback、库外私有加载或模型分支。
- 复用现有测试文件/公开注册与独立FP32参考，更新已有metadata描述并扩展同名benchmark；SQL与MNNVL两个独立主题未提交、容器原补丁保留。

## 实际验证及范围

| 验证 | 结果与界限 |
|---|---|
| PPU算子回归 | 10:35:27终态，33passed/0failed/0skipped；JUnit SHA `1522187ad8fb04b00f5708dd1b8d0952a0eb323294c77d1cd6a4e45b0f39a8bb`，log SHA `c08982870c600005fb7b9500e37fbc1c8c5d0607d611be020b5e1fca137b716f` |
| graph | 8组capture、每组两次新Q/KV/index/length/sink，共16replay；三个输出先填NaN、全部独立参考对拍 |
| 定义域 | BF16/H4/DQK512、576/DV512；空/非空、TOPK尾部、非零storage offset的连续view、无效index/length/sink±inf、紧凑输出/输入不变、拒绝非法head；64/128守护 |
| 容差 | 沿用上游严格标准，output atol8e-4/rtol3.01÷128；maximum/LSE atol1e-6/rtol2.01÷65536；未放宽或删除断言 |
| 环境 | 精确PR5文件覆盖未安装的9f6a0ef源码副本；运行时保留独立SQL/MNNVL补丁。不是完整最新main/fresh install验收；官方main只多一笔FLA/GDN无关提交#1033 |
| 工程 | 原仓库7项pre-commit全部通过、54 CI helper单测通过、pin检查与增量metadata/export/marker/benchmark/CI选择通过；wheel构建成功且生产op字节一致，wheel SHA `e77ab67381c0cafb210baa306f56ec327d475390425c4c17f9b447bf18937c3b`，未安装 |
| 全仓标记 | 全量marker扫描发现其它已有算子缺测试；本次增量检查passed，不隐藏全仓失败、不扩大修改 |
| Hosted CI | head7dac5f76的rule-check41379010607、basic CI41379011002、CLA均success；code style/CI helpers/selection成功；NVIDIA和matrix硬件job为skipped，不能当硬件通过 |
| 模型与性能边界 | 不运行新模型请求、GPQA、整模回归或E2E；没有新的精度gate/正式四场景结果；非PPU硬件未测 |

## 算子benchmark：执行完成但性能门槛未过

仓库原生Benchmark/cudagraph、相同warmup10/iter30、BF16/SKV256；对照为Q补零H64/copy/公开调用/slice，候选为紧凑H4。12形状全记录，输出仅算子诊断，不是原生旧H4 baseline或E2E。原生日志SHA `b6d71a8017da23f0e7b63cafdaf9930c153e0217c581547b49096b7a0e5f6b72`，原生结果SHA `7d3d625b173a82aefbc1b3c16f720c774f59a3fd5b0dd08098da82d98bf6243a`。

| SQ | DQK | TOPK | H64对照us | H4候选us | SpeedUp |
|---:|---:|---:|---:|---:|---:|
| 1 | 512 | 17 | 9.182 | 6.192 | 1.483 |
| 1 | 512 | 128 | 8.980 | 12.739 | 0.705 |
| 1 | 576 | 17 | 9.760 | 6.384 | 1.529 |
| 1 | 576 | 128 | 9.541 | 13.985 | 0.682 |
| 8 | 512 | 17 | 13.652 | 7.391 | 1.847 |
| 8 | 512 | 128 | 13.377 | 13.005 | 1.029 |
| 8 | 576 | 17 | 14.333 | 7.488 | 1.914 |
| 8 | 576 | 128 | 13.727 | 14.389 | 0.954 |
| 64 | 512 | 17 | 43.169 | 19.766 | 2.184 |
| 64 | 512 | 128 | 43.036 | 26.828 | 1.604 |
| 64 | 576 | 17 | 46.551 | 20.195 | 2.305 |
| 64 | 576 | 128 | 46.297 | 29.322 | 1.579 |

9形状快于对照、3形状慢于对照，其中2个SQ1/TOPK128低于0.9，另1个约0.954仍达到0.9；合计10形状达到门槛。原生exit0只说明采样完成，G6=`not_passed`，不称性能passed。PR已完整披露两项退化并维持Draft，未自动展开新调参或将候选安装生产。workflow引用的optimization.md/deep_opt.md在该checkout均不存在；记录能力交付limited，不能伪造deep_opt完成。

## 算子规范复核与终态

| 条款 | 结论 |
|---|---|
| A1–A4 | vLLM数值契约归FGV，metadata/workspace留框架；公共/既有thead薄适配，无新平台副本 |
| B1–B4 | 公开导出/注册/marker/benchmark保持完整；继承局部triton.autotune作为明确窄域豁免，不为此重写公共tuner；SQL/MNNVL分离 |
| C1–C7 | BF16/连续ABI，按原stride与offset访问；新head mask覆盖Q/tail/sink及全部输出，无越界强行截断；显式非法head错误、空SQ支持 |
| D1–D5 | 执行后不跨backend重试、无Torch compute；不持有跨请求buffer、graph由调用方管理；原tuning key/大head候选保持，H4不走TLE |
| E1–E6 | 独立CPU FP32与严格容差、公开入口/真实provider、输入不变、更新输入+全部输出哨兵、RNG fixture恢复；其它backend未测而非虚报通过 |
| F1–F2 | 原生同口径12形状benchmark与负结果保留，2项未过0.9，性能验收未完成 |
| F3–F4、F6 | 已配齐API/metadata/测试/benchmark/构建/格式/英文日志；新vendor入口首行命中日志；仅局部PPU验证，fresh main和非PPU/整模仍未完成，Draft needs_revision |
| FlagGems专用条款 | B5/C8/D6/E7/F5不适用，未修改FG或ATen注册；SGLang B6不适用 |

10:44:18最终只读审计通过，生产三库/engine、实际导入根/index、原实例3917036/start622443729、argv/env/权重/tokenizer/thead/DB/安装均保持，health200空闲，原MBT32768/脚本/FULL/RPC300不变。当前Plugin45c95631…、FGVd6cbf04f…，DB仍eda5cc0b…；生产源码变更/重启/模型请求均0。原始准备失败、全部回归/benchmark及最终PR回执均保存在远端点62；不建history。

`completion.json`记录Draft提交与性能limited，`submission/`保存补丁、manifest、PR正文/回执、pre-commit和本地检查摘要；更新CI后的PR正文由GitHub版本及`PR-final-receipt-v2.json`保留。任务完成的含义是已整理并提交PR，不是性能/模型正式验收完成；未自动改Plugin依赖锁定。点60原164与补充174/198仍按历史口径保留。

终态回执SHA：completion `e1a121e6d2d86befb463b3c5ed92d385f667d7c4bfc8beefe0abee67f8e096ad`；最终service manifest `a935de690d56713f3a2ded4639d1528e31834d21a126d279cb42bd8f28c203b7`，runtime `47250a49568fb3c3d404738ce55f13f79ac415028c1c1d0049c9cd9cfc4ca908`。本地结构、历史分数/空gate、冻结参数、链接及范围检查通过；文档空白检查通过。
