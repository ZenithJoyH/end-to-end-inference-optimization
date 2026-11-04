# 点43：上游 Plugin + PR454 / FlagGems-vllm 优化迁移

后续状态：用户要求收敛后，[点44](20261019-minimal-patch-consolidation-44.md)已于2026-10-19安装精简版并通过最小回归。本文点43源码、实例、169/198与补充171/198均作为原身份的历史证据保留，不表示当前精简版获得了新全量分数。

最新结论（2026-10-19 17:58 +08:00）：用户授权的14题补跑已完成并独立复验，新增答对185、194，统一替换14题、保留其余184题后 **171/198＝86.36% ≥ 86%，按补充口径达标**。原单次全量169/198及失败结论保留；仍有10题触及60K上限，不增加精度门槛。当前服务健康且身份未变，不签发新的单次全量gate、不自动继续性能优化；详见下述补跑终态。

历史原生全量状态（2026-10-19 17:18 +08:00）：attempt06迁移版本已安装运行，最小回归通过，但新身份198题/C64正式GPQA **169/198＝85.35% < 86%**，原单次精度未达标；证据校验通过，未签发gate。此失败不覆盖后来用户授权补充171/198的结论，二者分开记录。下文各轮过程保留为历史。

## 范围与冻结约束

2026-10-19 用户明确要求更新优化容器内 Plugin 到官方上游并接入 PR454，更新 FlagGems-vllm 到官方上游，再迁移当前优化。仅 PPU-13 / `glm5.3-flash-opt-20260911` / 8011；沿用既有隔离案例，不改源适配容器、不改 vLLM/FlagGems/权重/tokenizer、不提交推送。MBT32768、maxseq64、TP16/BF16、FULL_DECODE_ONLY、关闭前缀缓存保持不变。

外部根：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261019-point43-upstream-migration`。所有变更命令先保存并记录 SHA，再执行；新源码使用容器私有真实目录，原源码和 dirty 内容完整保留。

## 设计与假设

这是版本迁移（framework / operator），不是新增性能收益实验。按当前代码的 dispatch/backend/config 边界适配；已经上游化的算子不重复覆盖。保留有必要的 PPU 数值兼容、算子接入、形状特化和配置；点40未安装候选、点41未保留阈值及点42无收益调度器不迁入。逐项形成迁移清单，并测试目标形状、fallback、可选依赖及 graph 生命周期。首先在不切换安装、不停止服务的情况下准备和比较源码。

## 修改前事实

只读核验服务健康、空闲，原 argv 未漂移。Plugin 私有源码 HEAD `95b04f7f321d94b2a21425bfc93cb34adcc0b7d0` + dirty；FlagGems-vllm HEAD `f7443e776fc078318685dc8456ef5a8b2281d0f0` + dirty。FlagGems `9c9bff3979a6f90ef0d0c78aa6a1da2262723f31`、vLLM `0.24.0+empty` 保持不变。

PR454 核查时 head `f7696963c44425fdf6603054248cc8256783b4c7`，base main `a696859b9aa528dfd5b21f5da3403fdc16bac4cd`，open / mergeable；精确安装身份以实际 fetch 为准。

## 验证、效果与回退

`e2e/accuracy` 显式模式 `minimal-regression`；迁移涉及模型/算子语义时追加 `formal-gate`，不得复用旧得分签发新 gate。最小回归包含实际导入与 dispatch、受影响算子测试、graph capture/至少两次 replay、固定 smoke/C8。当前全部待执行。历史补充精度173/198与原生169/198不变，均不证明此新版本。

性能：not_run；旧版本数字不归属新版本，不宣称迁移加速。回退以原两个私有目录重新 editable 安装并按原 argv 启动，仅影响目标服务。

## 进度

- preparing：已完成当前服务及 PR 元数据只读核查；尚未切换源码或服务。
- 已拉取官方 Plugin main `a696859`，证明是 PR454 `f769696` 的祖先；官方 FlagGems-vllm main 为 `b4d3382`。两个旧库完整工作树及 dirty 补丁保存在外部根目录，原私有目录未动。
- 设计差异：PR454 公共 GLM 路径为 FP8 indexer、portable sparse MLA eager boundary，不能冒充当前已验 PPU BF16 路径。按 vendor 边界保留现有 PPU GLM/cache/graph 兼容实现及其必要薄包装；其他平台保留 PR454 新模型和 activation plan。此兼容层仅为迁移保真，`pr_readiness=experimental`，不是纯净 PR454 的 PPU 验收，不作为新增收益。
- 迁移命令：`commands/port-v1.py`，SHA `56d775526b23e1eb60f4fde87ce560f37e9481f53449481679722339697c1ae2`；安装前在新私有副本应用保留优化及匹配测试。
- 源码回归已通过：`plugin-cpu-v4.log` **30 passed**，`moe-smallm-cpu-v3.log` **22 passed**。首次失败及v2/v3均保留；修复了旧Tensor/limit与新self/x的clamp双接口、开关/策略及可选attention导入耦合。
- 历史未启用的P4K测试引用已放弃函数，新旧版本均20失败，原版本对照在`old-p4k-stale-control-v2.log`；仅移除误迁入新副本的重复测试并先保存到`not-migrated-p4k-abandoned-test.py`，原仓库不动，不重新启用该失败优化。v2跨文件系统rename失败属于归档编排问题，v3复制/校验后处理，未掩盖原失败。
- 切换命令：`commands/switch-v2.py` SHA `d95e0155555be2cfd8875e351a470b15be8cee07cdb6b5d3a8fb56eded5a3837`；设备回归：`commands/device-v1.py` SHA `266171f952e81bedacd93e4b07f1658ff0a13526cc0015be857dca2f24806272`。前置核验原服务空闲和两库原内容指纹一致；只切换两个私有editable，`--no-deps --no-build-isolation`，vLLM/FlagGems不升级，任一失败恢复原安装及原服务参数。
- 设备回归通过：44组align（M1/9/10/16/24/32/40/48/56/64/65，BM16/32，含EP map）与旧实际实现逐位一致；M16/32/64 BF16 GEMM2逐位一致，各2次填毒graph replay通过。仅正确性，不是性能加速。
- 第一次启动因新GLM worker的早期导入使TileLang CUDA stub先于FlashInfer绑定而失败；`comm-before-glm`通过、`glm-before-comm`复现相同`cudaDeviceReset`异常，确认导入顺序机制。`fix-v5.py`仅在PPU兼容路径保留原worker初始化顺序，非PPU仍保留PR hook；30项合同再通过。原安装/服务恢复及最小回归通过。
- 第二次启动越过通信，但PPU Prefill重命名路径及上游默认CUSTOM注册冲突，模型加载前失败；旧安装/服务再次完整恢复。`fix-v6.py`修正实际路径，仅允许替换PR默认provider、保护其他CUSTOM/非GLM；注册、重复调用、非目标和不相关provider保护检查通过。
- 当前新尝试：`attempt-03`，`commands/switch-v4.py` SHA `65022f2f0889e3c186f9572d2512cfd0a247681953ccea32195d976f274b35e2`。未修改算子后复用既有设备证据，不复用失败服务结论；所有旧轮保留。
- 第三次启动因兼容注册表遗漏上游新增`apply_rotary_emb`而被预热阻断，原服务恢复及最小回归通过。`fix-v7.py`通过公共OpRegistry组合新旧表，保留PPU ABI、合入缺少的新项；30项合同及35个已加载CachedOp预解析通过。
- mHC包装的旧模块名引用导致候选静默回落reference，在启动前选路核查发现并修复。`routes-v9.py`对照原版40个op：**40/40 selected impl一致**，新表41个op、保留`apply_rotary_emb`。v8先枚举未初始化懒注册表得到空结果，属于工具证据问题；v9先调用正常resolver初始化，无额外模型请求。
- 当前为`attempt-04`，命令`commands/switch-v7.py` SHA `10b2579538f5db97ded9e571228158f9a840f394d922bf7c11df0ee484027539`。权重已进入加载/编译，旧编译缓存因模块重命名自动失效重编译；未清空缓存、未改变SDK/启动参数。模型graph/minimal仍待完成。

## 迁移核对表（截至模型启动验证阶段）

attempt04已启动graph服务并通过C1/C8，但16K边界最小回归失败：新上游MQA host显式要求FP8/FP4，当前PPU BF16 Q/K被拒绝后，dispatch切reference产生8GiB的[M,H,N]临时张量并OOM。`attempt-04/rollback-completion-v1.json`确认旧安装/服务及最小回归恢复通过；不降低MBT/显存比例规避。完整精度未派发。

下一次受控切换为`attempt-05`，`commands/switch-v8.py` SHA `26694d51c9ec82e48d138d5b762e7340985f8c75d927ece8d50b6af6a8e79e39`。安装新副本后、模型占用显存前先执行MQA设备正确性测试，失败仍自动恢复旧版；沿用原argv及已完成align/GEMM2证据，不改变测试门槛。

MQA新增验证已通过：7项CPU合同；6组设备边界/空维度，4组非空输出与旧实现逐位一致，独立分块FP32 oracle最大绝对误差`3.2425e-5`；变更输入并填毒输出后2次graph replay通过。实际公共函数来自新vendor wrapper，tuner配置数1且与本包runtime一致；`mqa-device-regression-v1.json`及`attempt-05/mqa-device-regression-v1.log`保留。当前仅证明兼容正确性，模型长输入和正式分数尚待完成。

后续只采用attempt05：源码审计`commands/audit-v2.py` SHA `b03b8f33ebedae2acfc85e42962cfc966769508eb4e5484fd9f08be66a87b2a9`；正式命令`commands/formal-v3.py` SHA `3647327ec4e2c168c6109ffabf41873ccb0e9fbbf9e4b4d77aaa06dbeb78554a`。旧audit-v1/formal-v1/v2仅保存未执行，不能把其预期成功前提当证据。

### attempt05文本oracle诊断与事前重冻结

本轮原始`m.minimal` C1/C8及16383/16384/16385边界通过，三个边界输出与旧版完全相同。额外增加的“历史自由续写C1/C8逐字相同”断言失败，自动回退；原失败不改判。只读对照已保存的旧版point42和attempt04 rollback，未变更原版C8输出自身已有不同的文章前缀/续写，证明它不能充当逐字稳定oracle。新版9条固定续写都含“北京”，但不据此宣称零回归或模型精度通过。

在新增请求前冻结同配置明确答案回归：3个C1（首都、1+1、2+3）及8个并发首都问题，chat final content必须包含对应答案；seed42、temperature0、max_tokens256、无重试。先在恢复旧版执行同一合同，通过后才能在同一新源码重启版本执行；保留原C1/C8、长输入和graph要求。正式GPQA仍198题、strict≥.86不变，不改已有分数或丢样本。

命令`commands/semantic-v1.py` SHA `c486831968567129457f06c5db91f81207149f948694d6cd8cb5af2772cf81d0`，下一次`commands/switch-v9.py` SHA `ffc0c03374cf00eb0673fba6532a4f9f7e1e4af99e5937959f39c61eceae5842`，唯一新目录`attempt-06`；只修正测试oracle，不再叠加源码优化。上述audit-v2/formal-v3也未执行，后续须绑定真正通过的新实例。

旧版11/11明确答案通过，均输出北京/2/5（`semantic-baseline-v1.json`），服务及源码身份稳定；attempt05 rollback完成。现按同一冻结合同启动attempt06。只为新实例准备`commands/audit-v3.py` SHA `f6305603111c4c8b8233d8c39c0de8230a7f3f727de69e8a0895b62c6cb5d1e3`及`commands/formal-v4.py` SHA `e37d661fa07371fedb32984aa3dbcb8812b9dc968c890ef88067c543492a9826`，最小回归不通过则不执行。

使用key-operator-analysis及accuracy-diagnosis定位此执行边界；后续`commands/fix-v10.py` SHA `5dc9e7b3aa4611c2838e954941870d03542a80f5e57f0d339a45fe8a76199733`限定PPU BF16 D128 host，先AST证明新旧实际tiled/clean kernel相同，再复用新上游kernel及本包单配置tuner；其他dtype仍调用原上游FP8/FP4接口。`commands/mqa-device-v1.py` SHA `1ee7e29e2b97dbf9dbc82ed9dd1544afa9e7f360ea6661614553c4855c3d4b65`验证非对齐、原故障shape、外层stride、空维度及变更输入填毒graph两次replay，对照旧实现及分块FP32 oracle。不把该兼容修复称为新性能收益。

| 项目 | 新版本处理 | 当前证据 |
| --- | --- | --- |
| Plugin官方main + PR454 | PR head包含冻结main，独立私有分支 | Git祖先关系通过 |
| 官方FlagGems-vllm main | `b4d3382` + 保留PPU算子/调参 | 新路径导入、实际公共函数来源通过 |
| small-M/M64 GEMM2、padded align | 按原shape guard移植，保留上游W8A8/workspace变化 | 22配置合同、44 align逐位、3 GEMM2逐位及graph通过 |
| 长Prefill KDA/conv、BF16 indexer/KPool | 保留PPU ABI，非目标平台保留PR路径 | 40/40原选路一致；模型回归待完成 |
| MQA调参、vendor sparse MLA、黑名单 | 保留并避免覆盖其他上游配置 | 配置及导入取证；新E2E未测 |
| 点40/41/42未保留候选 | 不迁入 | 配置threshold0、MBT32768不变 |
| vLLM、FlagGems、权重/tokenizer/DB、交付脚本 | 不升级/不改写 | 启动后审计待完成 |

早期未执行的完整精度计划采用`commands/formal-v2.py`，因attempt04失败没有派发；最终仅执行下述formal-v4，不能把多个保存的命令当作多次模型评测。

## 当前交付与新身份精度复验

### 用户新授权：统一补跑14题（事前冻结）

用户在本轮失败后明确要求重跑全部14道60K长度结束题，再补充判断精度。采用精度Skill `minimal-regression`的困难样本范围：doc_id固定`[8,15,32,71,75,76,88,115,127,130,145,147,185,194]`。保持原seed42、temperature1/top_p.95、maxgen60000、C64上限；仅14个请求，实际最多14并发。不改模型服务、源码、采样或停止语义。

一次原生lm-eval `--doc_ids`补跑，全部14题统一替换，其余184题保留原样，无best-of、不自动重跑到通过。原生169/198原样保留；补充后为`(169+本轮14题答对数)/198`，达到86%至少需要本轮新增2题正确。补充结果与原单轮C64完整评测分开，不签发伪造的全量gate。

远端唯一新目录`rerun14-01`；命令`commands/rerun14-v1.py` SHA `524f96d2303b54e2ae14038ba8f36b9823e3e6d2bd10b23709a97ce34c1d12dc`。先准备并冻结配置/provenance/原生命令及服务身份，再唯一派发；当前尚未发起模型请求。补跑前只读核验当前实例及所有源码/配置/权重/tokenizer/DB/thead身份与原全量后快照一致，health200、running0/waiting0。

准备已通过，原评测镜像ID未变；冻结请求合同SHA `6c38c771bf32dae1c26b974a450ecfe5f68da2483e66bacd109da7a142223e05`，独立run_id `eab1f28077704c23891b132e11156d2e`。17:27唯一派发控制器PID3045790/start_ticks511784474，证据`rerun14-01/dispatched.json`；日志`run.log`，原生结果在子目录`results/`。完成证据为该子目录`completion.json`、`run.exit`、`score-summary.json`与`merged-samples.jsonl`，不能把父目录已知formal.exit1误认为补跑失败。复用监控`glm-performance-20261018`已更新为本14题任务并激活，30分钟只读检查、无变化安静、终态停用。

#### 补跑终态与独立复验

17:52:03完成14/14、原生退出0，`completion.valid=true`、服务身份不变；17:58独立复验通过。185、194答对，75、115正常结束但仍错，另外10题（8/15/32/71/76/88/127/130/145/147）仍有60000-token长度结束标记。全部14题统一用本轮结果替换、184题及所有filter的原始字典逐项未变，strict合计`169+2=171`，分母198，得分`0.8636363636363636≥0.86`，按用户要求的补充精度口径达标。无best-of、未删除剩余长度结束题，未自动追加生成。

独立复验包括冻结artifact SHA、原始runner、native14题及每个filter恰好一次、原doc/target/arguments、task/provenance、seed42与生成参数、198题合并完整性、全部14题替换及其余184题未动。现场PID/start_ticks、源码/argv/环境、权重/tokenizer/DB/thead与原全量和补跑前后均一致、health200。原单轮169/198未改写，补充171/198不是新的一次全量C64运行，不调用formal gate签发；没有自动恢复性能优化。

证据均在`rerun14-01/`：completion SHA `b227b48b939cc024bb18cf92f4529d8ed8a53cccb1534e14c8a8b2eb31676e79`，score-summary SHA `cad06d2e6ee4dfe89a0732a59bab05b11044a7a1c73ee2d46e598a524f7fb2a0`，merged-samples SHA `ac2c3cb7603bac4570fb4b3b72fd4b789baa6ee769aec66cf5e2aefe0c56691b`；原生子集results/samples SHA分别为`417b41129ca51d75c67ff9e4e92923bbd984c501609c7c378aac2b2eac5c5829`/`b2a89ba6a31d4ab37eeb985c9c40188d5f13cff57e3c150c1673b505bafe1378`。具体原生路径及runtime SHA见state本轮条目。

本补跑终态和独立审计后，App已确认`glm-performance-20261018`为`PAUSED`。只关闭监控，不改动模型服务；本次没有新的性能测量或代码推送。

| 组件 | 当前运行来源 | 本地迁移分支 | 内容SHA256 |
| --- | --- | --- | --- |
| Plugin | 官方PR454 `f7696963`，包含冻结main `a696859b` | `e2e-glm53-pr454-migration` | `ee342873794a3d0039da4c213a72e7e373f7cd18cff8beef600152fb0c514473` |
| FlagGems-vllm | 官方main `b4d3382b` | `e2e-glm53-upstream-migration` | `9e32b67a03253cd46e2a6382e3bff8b8f7307b3faa44df63747bdfa097ae7955` |

两库分别位于容器私有`/workspace/e2e-opt/glm53-20260911/vllm-plugin-FL-upstream-20261019-p43`和`/workspace/e2e-opt/glm53-20260911/FlagGems-vllm-upstream-20261019-p43`，均editable安装，无PYTHONPATH覆盖。原目录和dirty未覆盖；最终完整树tar及diff已存远端，校验值在state。只保留迁移补丁，尚未commit/push；`pr_readiness=experimental`，非PPU硬件/其他模型未实测。

`final-audit-v1.json`确认原argv/环境、DB/thead、权重清单与tokenizer逐项未变，镜像来源与挂载校验通过。服务新实例`PPU-13:glm5.3-flash-opt-20260911:2836031:511304111`，8011健康；vLLM与FlagGems未升级。启动脚本SHA仍`5b1d0a52b129ada50cf38f2ba35194cb43d67a41901d2876e1150e4e7eef31ca`，现有脚本通过新editable生效。

精度模式`e2e/accuracy formal-gate`：两次相同provenance、数据/任务与原生预检通过，198唯一题、C64、seed42、temperature1/top_p.95/maxgen60000、strict≥.86，独立缓存，无补充替换/best-of。`formal-gpqa-01/dispatched.json`确认`commands/formal-v4.py`唯一派发；本轮已结束，`formal.exit=1`、`completion.json`确认身份不变，未生成run-record/gate，因为原生strict分数169/198低于阈值。不复用早期172/198、原生169/198或用户补充173/198证明新版。

后台监控`glm-performance-20261018`按30分钟周期只读跟进，终态审计后已由App确认`PAUSED`。不重复启动评测、不在评测中改源码/配置/服务；本轮不追加性能优化。正式性能及四场景验收仍未完成。

16:46只读跟进：`formal.log`原生API进度182/198；`formal.exit`、`completion.json`、run-record及gate尚未生成。控制器PID/start_ticks与唯一派发记录一致；当前服务与最终审计的全部冻结身份键一致、health200。未发新推理请求、未重启或改源码，监控保持ACTIVE。此进度不是最终198唯一题验收或阶段精度分数。

### 正式精度终态与只读诊断

原生结果：`formal-gpqa-01/results/GLM-5.3-Flash-BF16-upstream-p43-20261019/510bdd8e6f5f41198189b959573c8566/gpqa_diamond_generative_cot/glm5.3-flash-opt-0924/results_2026-10-19T08-51-25.150305.json`，SHA `d537f8b28c7598c4568c7e1c70bf9a813badc911f3075f14bb6feb20a98c56df`；同目录samples SHA `5605f3247f16c205d3078c8e7e6311c77e2bbe1fddb72f239521198613b7a4ba`。

原生strict正确169、分母198，分数`0.8535353535353535`，低于冻结`.86`（至少需171题正确）。396行样本分别属于strict-match/flexible-extract，每个filter恰为0..197各一次；strict逐题和与原生总分一致。只读调用原生验收器验证全部frozen SHA、原始runner、服务/配置/契约、provenance、原生metadata与198题内容均通过，唯一失败为score threshold。失败结果完整保留，不调用finalize/issue生成伪造回执。

14个`timeout=true`样本的实际`completion_tokens`均为60000，doc_id为`[8,15,32,71,75,76,88,115,127,130,145,147,185,194]`，当前strict均0；这是长度结束标记，不据此宣称HTTP超时或服务崩溃，也不单独作为精度门槛。没有自动补跑或替换。

已按`inference-accuracy-diagnosis`冻结问题`point43-native-gpqa-below086`，`gate_blocking=true`，根因未确认。只读对比迁移前原生198题，doc/target/arguments全部相同，旧版原生亦169/198；但7题旧错新对（27/61/90/94/134/157/158），7题旧对新错（15/24/47/102/185/192/194），不能按总分相同宣称零回归或归咎某算子。sampling variance及源码变化尚未隔离；历史统一补跑173/198未混入本轮。

终态当前实例、argv、环境、四个实际源码指纹、DB/thead、权重/tokenizer均与评测前一致，health200；控制器退出，服务保持原样。当前不继续性能晋级；后续需在明确授权范围内做忠实复现/二分或补充评测，再按相应正式契约核验，不能用小回归代替新有效gate。

本地文档`git diff --check`与GLM YAML解析/当前身份一致性通过。全项目`validate-local --records`因其他模型缺失点链接和过程产物策略问题失败；未删除或修改这些无关记录，不宣称全项目检查通过。
