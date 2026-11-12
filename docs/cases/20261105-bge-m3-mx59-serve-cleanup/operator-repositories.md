# FlagGems / FlagGems-vllm 仓库整理与审查

2026-11-05，用户追加“flaggems和flaggems-vllm的库也一起处理下”。范围沿用 mx-59 / BGE-M3 私有安装目录，恢复可审阅源码仓库、核对完整 diff 和开发规范、清理本任务不必要改动并完成相关验证。不提交、推送或更新远端 PR；不升级运行时依赖，不修改共享副本/权重/vLLM/FlagTree或其他容器。

**最终状态：`local_repositories_and_fixes_validated`。** 两库Git历史、缺失仓库文件及正确审阅基线均已恢复，实际安装绑定不变。FG完整diff3 files/+191/-1，FGV7 files/+617/-12。FG24、FGV133、优化解释器60、Plugin80及两库完整diff适用pre-commit均通过；FP16固定批次before/current/revert全部10240项逐位一致，FP32原108628项原阈值通过。原FP16异步HTTP对照因实际合批shape不一致判为measurement-invalid，失败证据保留，未放宽阈值。所有临时服务已退出，未执行生产回退、提交、推送或依赖重装。配套FG/FGV公开版本未落地，`pr_readiness=experimental`。

## 修改前事实与执行方案

- inventory 与 `./scripts/connectivity-check --limit mx-59` 已验证。两套安装均 editable：`FlagGems/src/flag_gems` 为 `0.0+g4897cc306`，`FlagGems-vllm/src/flaggems_vllm` 为 `0.3.0.dev1`，根均为容器内 `/workspace/bge-m3/tune-src/` 下真实私有目录，无 `.git`。
- FG 根只有 `src/` 及上一轮新增的 `tests/test_metax_linear.py`；FGV 只有 `src/`。不能仅初始化 Git 后把镜像省略的测试/文档/配置误当成业务删除。
- 镜像清单固定 FG `4897cc306cd83390c95b83b50df28f7edb1684c5`、FGV `60f1d386c94d1084f3f5f02f71714b7bc6581e6b`。GitHub connector 已核对精确提交：FGV 后者父节点 `1d5284da12220a0c946084da3658cad94611c0c5`，初次 FP32 支持的父节点 `7417158440a80753fb21dab3a124c1be388ab7eb`。不以当前最新主线作为原始审阅基线。
- 准备阶段：在容器独占 `/tmp` 创建任务产物，保存控制工具、逐文件内容/权限/owner/group/链接清单及安装绑定；在临时副本中 fetch 精确公开提交、恢复缺失非运行时仓库文件，保留所有现有文件。缺失 `src/` 不静默补齐，先核验是否存在；不将来源不明的改动伪装为干净基线。FG HEAD使用固定原基线；FGV保留固定安装头的来源分支，审阅 HEAD 放到首次特性之前。
- 正式写入前核对源码无漂移、Git对象完整、普通diff包含新增文件、staged内容为空并预览差异。发布只添加经精确提交确认的缺失仓库资产和自包含 `.git`，不覆盖任何现有文件、不重装、不重启服务。对全部既存文件内容/属性和真实导入重复比较；新增资产和元数据逐项记录，提供仅针对本轮新增路径的回退。
- 完整 diff 再按算子规范第0/1节及适用 A1–B5/C1–C8/D1–D6/E1–E7/F1–F6 复核。代码变更若有必要，先记录精确文件、理由及回退；相关数值测试真实命中公开入口，不能以mock或历史性能代替当前硬件验证。跨仓库公开交付和固定版本未完成时继续标记 experimental。

控制工具计划保存为本地 `/tmp/bgem3-operator-repos-20261105.py`，上传唯一容器 `/tmp` 后先执行 `prepare`；生成预览和执行路径后再记录 `publish <case>` 命令。产物仅在目标容器私有目录，不新增挂载或共享目录依赖。

准备完成：控制入口 `/tmp/bgem3-operator-repos-20261105-r8m2k6.py`，独占产物目录 `/tmp/bgem3-operator-repos-20261105.ewdv1kyz`。FG完整可达历史4362提交，需恢复2965个缺失非运行时文件；完整diff为3 files/+192/-2，仅上一轮公开Linear整理/测试（AABS小维度guard原已存在于公开基线，不是额外本地差异），SHA `c1b1ebdfaa6d7e4f05302400096d4899a01d79b4b66bd081249f3d4a951597d0`。FGV历史284提交，需恢复676个文件；完整diff7 files/+496/-7，SHA `076a36b75392fadcc54158c070593a790211dff1a848bab358bb875de3fee209`。两套均无缺失运行源码，现有源码/安装绑定逐项未变，Git fsck/diff-check/空staged通过。恢复资产均来自各自原安装精确提交，不从新主线取文件。

正式发布命令：`ssh mx-59 'docker exec BGE-M3 /flagos/bin/python /tmp/bgem3-operator-repos-20261105-r8m2k6.py publish /tmp/bgem3-operator-repos-20261105.ewdv1kyz'`。执行前对两套库一起做漂移/路径预检，再逐库添加恢复资产并原子移入`.git`；任一既存文件都不覆盖。回退工具保存为 `commands/rollback-operator-repos.py`，只在后续无漂移时将本轮新增资产与Git移至独占备份，不删除原文件。

发布已完成：两套 `.git` 均自包含，无alternates；既存源码/权限与 editable绑定逐项不变。源提交与审阅提交分别保留为 `bge-m3-source` / `bge-m3-review`，普通diff与准备补丁逐字节一致，staged内容0、新提交0、服务重启0。原生结果 `fg/FINAL_REPORT.json` 与 `fgv/FINAL_REPORT.json`。

恢复后验证脚本执行前保存为 `commands/baseline-checks.sh`：GPU2（已重新核验无进程），先对FGV目标测试collect-only，再运行 `pytest tests/test_flash_attn_varlen_func.py -k 'metax_fp32 or swap_qg'`，随后在FG真实仓库配置下运行 `pytest tests/test_metax_linear.py`；回执独立命名，不覆盖上一轮验证。

## 完整diff复核与必要整改

恢复后FGV **118 passed /432 deselected（50.06s）**，FG **24 passed（6.01s）**；相关测试均通过真实安装入口，未修改容差/reference/kernel/config。FG完整diff仅公开Linear wrapper、MetaX YAML及单测；FGV完整diff仅FP32公开接入、IEEE计算/资源限制、context配置、配套测试/benchmark。没有将原有FP32功能或必要资源保护当成冗余删除。

准确发现两点：FG上一轮在不完整临时树上跑isort造成一处无关import分组；完整源码树上的原hook会恢复原分组。FGV新增FP32路径复用了公共`assert`校验，QKV dtype/device、out dtype及cu长度metadata在`python -O`下缺少可靠执行前校验。仅在FP32分支增加显式ValueError，不改有效输入的计算和调度、半精度或其他平台路径；新增15种非法metadata用例，launcher只设置拒绝探针，禁止非法输入真正发射kernel。另以独立脚本在普通/优化解释器上记录旧行为；探针在发射边界抛出，不对非法输入执行数值计算。

FGV恢复出的`AGENTS.md`与`workflow.md`已完整读取；后者引用的`optimization.md`/`deep_opt.md`在该精确提交中不存在，当前是仓库维护及执行前契约修正，无新kernel/调参或深度优化，不使用文档中与用户任务无关的conv1d示例。适用协议表如下，所有kernel、原数值oracle、容差、benchmark和配置冻结只读。

| 项目事实 | 当前约定 |
|---|---|
| API/授权 | `flaggems_vllm.flash_attn_varlen_func`；用户当前BGE-M3两套库整理授权 |
| 可编辑 | FG仅linear.py导入分组；FGV仅ops/flash_api.py与既有test_flash_attn_varlen_func.py |
| 构建 | 纯Python校验修正，沿用editable；不重装或改编译依赖 |
| 验证/超时 | FGV原118项+15项metadata；再用`python -O`运行15项metadata及45项独立数值用例；FG24项；Plugin80项与两profile功能对照。单组预算600s，临时模型服务沿用上一轮240s readiness/120s请求限制 |
| Benchmark/profiler | 本次不改变有效输入kernel/config，不开展调优或性能验收，无新加速比；历史PR性能仅作历史证据，不能当作当前测量 |
| Autotune/fallback | 原MetaX配置保持不变，NVIDIA无新增路径，不新增其tuner；无torch compute fallback，非法metadata执行前抛出 |

| 契约 | 范围 |
|---|---|
| 输入 | FP32 Q/K/V同一目标device，三维packed接口原样；K/V同dtype、支持原GQA/head/layout；cu为同device一维连续int32向量、非空且batch数相同 |
| 输出 | dtype/device/shape与Q一致，保留原非重叠token-major out与不alias约束 |
| 数值/边界 | FP32 IEEE QK/PV、输出/LSE和空序列原契约不变；有效FP16/BF16路径不变。cu内部值仍按既有调用方契约，不增加GPU→CPU同步读回 |
| 不支持 | FP32 backward、paged/causal/window/ALiBi/softcap/dropout/split等原显式错误保留 |
| Reference | 只在tests/benchmark；原独立CPU FP64 oracle及容差不改 |

| 路径 | 处理 |
|---|---|
| early/error | FP32 metadata显式校验后报ValueError；不发射计算或修改输出 |
| fast/special/general | 所有有效输入沿用原公开接口、dispatcher、kernel与原调优配置 |
| unsupported/external | 沿用原NotImplementedError；无新增外部库或Torch fallback |

远端校验证据脚本将先保存为 `commands/fgv-assert-proof.py`，普通/优化解释器分别保存原生JSON；必要变更采用逐文件SHA校验备份后部署，具体执行命令另记。

安全复现确认缺陷：`fgv-validation-before-normal.json` 中两项非法dtype均由AssertionError拒绝；同样输入在 `fgv-validation-before-optimized.json` 中均到达发射边界，被LaunchReached探针拦截，没有发射非法kernel。候选对FP32 QKV device/dtype、out dtype、cu dtype/device/rank/连续性和batch一致性增加显式检查；cu内部值不读回CPU。15项新测试均要求ValueError、零launcher调用、输出哨兵逐位不变。

在**完整源码树**上两库原固定pre-commit均最终通过。先前部分副本导致的FGV错误import排序已在本地以真实源码复原，从未部署；FG真实树确认上一轮多余的一处导入移动应撤销。最终payload `contract-fix.tar` SHA `903f3834ebca52db3c29e94ea2b4ecbdfe89e6b06a161cdf5603b4d32ceba0e2`，仅三处文件差异和pre-commit日志；部署工具会先核对两库原完整patch SHA/HEAD/空staged及三处旧SHA，再完整备份和逐文件原子更新。

变更命令：`ssh mx-59 'docker exec BGE-M3 /flagos/bin/python /tmp/bgem3-operator-repos-20261105.ewdv1kyz/commands/contract-deploy.py'`。执行副本、清单与源码回退工具分别保存 `commands/{contract-deploy.py,contract-fix-manifest.json,contract-rollback.py}`；回退仅恢复这三处文件，不触碰Git与恢复的资产。代码回退后才可选择仓库资产回退，二者都会先拒绝后续漂移。

最终顺序验证保存为 `commands/final-checks.sh`：FGV原目标集加15项新用例、优化解释器15项错误+45项独立数值、FG24、Plugin80、安全复现复测，然后用 `commands/functional-smoke.py` 再测两个profile/全部8组合。脚本复用上一轮本任务独占编译缓存（不作性能比较），将原未修改源码功能baseline复制到新证据根并记录SHA；输出全部写入新目录，不覆盖旧回执。执行入口 `ssh mx-59 'docker exec BGE-M3 bash /tmp/bgem3-operator-repos-20261105.ewdv1kyz/commands/final-checks.sh'`。任何失败立即停止后续组，保留原结果后再诊断。

首轮补充回归为 **128 passed /5 failed /432 deselected（50.36s）**，后续组未运行；5项CPU/device非法输入在公开`attention.py`的旧assert先报错，尚未到新增底层ValueError校验。没有删除用例或放宽异常断言。补齐公开入口的FP32显式device检查，非FP32分支保留原行为；底层独立校验仍保留。另按算子F6在已导出的MetaX `launch_attention` 首条可执行语句补 `GEMS_METAX FLASH_ATTN_VARLEN_FUNC` debug日志，并在原12个真实context路径测试中断言命中一次；无数值/调优变更。

这轮范围修正为FG导入1处、FGV公开入口/内部参数校验/厂商launcher/原测试共4处。完整树原pre-commit再次通过。保存 `commands/{contract-refinement-deploy.py,contract-refinement.tar,contract-refinement-manifest.json}`，执行 `ssh mx-59 'docker exec BGE-M3 /flagos/bin/python /tmp/bgem3-operator-repos-20261105.ewdv1kyz/commands/contract-refinement-deploy.py'`；工具先核对当前两库完整patch SHA再备份本轮3个关联文件至 `contract-fix-002/before`，首轮失败回执改存 `fgv-final-attempt1.xml/log` 后重跑。源码总回退需使用合并两轮manifest的工具，避免覆盖后续漂移。

第二轮已部署，FG完整diff为3 files/+191/-1，SHA `d5aa1dbee7bce2b6c9862638d11b853636fae8665f4a4ef22f873c8231bbb7e8`；FGV为7 files/+617/-12，SHA `e2afb78b80c84978e231fd2667cd71f896ccab52f7c9d6830b23a1eecc3ee731`。15项metadata预检全部通过（0.26s），随后重新执行完整最终组。独立 `kernel-ast-audit.json` 已归档：与本轮前实际安装源码相比，FG Linear kernel、FGV公共attention模块中6个JIT函数、direct模块两个kernel的AST完全一致；direct.py整文件逐字节不变。新修改仅输入校验、日志、测试和导入整理。

最终封存工具 `commands/final-report.py` 将核对两轮manifest合并后的**全部**仓库文件/权限快照、绑定、HEAD/来源分支、完整patch、空staged、fsck、四组JUnit、普通/优化解释器前后复现结果、两个profile输出对照及原pre-commit日志。合并源码回退工具 `commands/contract-all-rollback.py` 校验无后续漂移后从各路径最早备份恢复5处源码；保留Git与恢复资产，不执行服务操作。必要时先运行该工具，再单独考虑 `commands/rollback-operator-repos.py` 的新增资产回退（移动保存，不清空原目录）；两者均未执行。

完整最终组的算子/Plugin部分已通过：FGV **133 passed /432 deselected（16.82s）**，优化解释器 **60 passed /505 deselected（1.36s）**，FG **24 passed（0.83s）**，Plugin **80 passed（20.11s）**。`python -O`下pytest关于生产assert被禁用的预期warning保留；被测生产代码确实以优化模式导入，独立数值oracle与pytest重写的测试断言仍生效。普通/优化解释器安全复现复测均返回ValueError，不再触达launcher；原功能baseline SHA `f7371952155cb24be74341cde3da7b8a8d2067dd3a282d75587c2af945d81a26`。两个模型profile对照随后顺序运行。

事实修订：上一轮尚未恢复FG完整仓库时，将AABS guard列为可能的镜像额外修改；本轮用精确公开Git对象逐文件比较，确认它已经存在于`4897cc306`原文，不属于本地diff。采用当前精确对象比较证据，FG没有额外未解释的生产源码修改。

## issue-oprepo-fp16-001：功能数值对照差异（定位中）

最终服务接口、维度、有限值及全部8种joint组合均通过，但整体严格数值对照失败；未签发最终通过回执。保留`candidate-functional.json`、两个服务日志与准确argv。FP16 native2048个数值中1586项超出原atol1e-5/rtol1e-4，max_abs0.00031127；与上一轮已通过候选比较同样失败。FP32全部108628项仍通过原阈值，max_abs2.3841858e-7。两个临时服务已正常结束。此项阻止本轮最终验收，不进行新性能优化、不放宽阈值。

调用本地[inference-accuracy-diagnosis](../../../skills/inference-accuracy-diagnosis/SKILL.md)。当前是BGE embedding维护回归，不存在GPQA正式分数或gate；定位和回执放在本案例及独占外部目录。模型/权重路径、seed、精度、TP1/eager、服务argv及实际`vendor.metax` attention backend日志与上一轮一致；源kernel AST一致。FG新增conf/operators.yaml仅用于可选精度记录跳过列表，不应直接改变正常算子计算，尚不能据此归因。动态batch/实际shape与配置加载均作为待证伪假设，不将怀疑写成结论。

下一步使用保存脚本准备私有诊断Plugin副本，仅给BGE embedding入口增加实际token数量日志，不修改当前安装Plugin；构建本轮前两库的source-only副本（从准备时冻结的candidate/src复制，保持原无仓库资产布局）用于单变量before/current对照。先用相同HTTP请求重复/单句复现并记录真实M，再按同一冻结批次/执行条件做before/current/revert；所有原失败输出保留，不能挑选偶然通过结果。

复现已经分离出执行边界：同一份当前代码/同一服务（`repeat-functional.json`、`repeat-fp16-service.log`），首次两句合批的实际token_count=26，输出与失败候选逐位一致；随后3次相同HTTP输入被拆为12、14-token批次，三轮输出及两次单句输出均与原baseline逐位一致。初始token_count=2是启动dummy。只读metadata日志来自私有诊断副本，原安装Plugin未改。此证据否定“必须更改数值kernel才能恢复输出”，确认原HTTP数值比较没有冻结实际batch shape；FP16 batch-size数值差异被误当成源码回归，分类`measurement-invalid / execution-batch-shape`。首批失败与全部重复结果均保留，不放宽容差、不挑选通过批次。

修正验证契约：原输入、模型、seed、dtype、TP1/eager和阈值保留，**before/current/revert三轮都冻结max_num_seqs=1**，输入仍是两句同一HTTP数组；每轮保留首次、随后3次相同数组及两次单句（10240个数值），全部纳入对照，不做事后丢弃。before/revert使用准备时冻结的原source-only FG/FGV副本，current使用实际安装两库；三者均使用未修改的实际安装Plugin，逐轮用find_spec校验路径并存`commands/controlled-*-bindings.json`。不是性能比较，不把新执行配置冒充原max_num_seqs2对照。

执行工具 `commands/fp16-controlled.py` 已保存；依次执行 `python .../commands/fp16-controlled.py controlled-before`、`controlled-candidate`、`controlled-revert`（通过mx-59/docker exec，PYTHONDONTWRITEBYTECODE=1），只使用GPU2且每轮结束自身服务；之后汇总新配对结果，并与旧FP16 baseline分别核验全部轮次。原FP32108628项通过回执继续保留。

修正契约的汇总与封存执行副本为 `commands/{controlled-report.py,final-report-v2.py}`，先汇总三轮的全部10240项及before→candidate/revert配对，保存 `functional-comparison-controlled.json` 与 `batch-shape-diagnosis.json`，再封存 `FINAL_VALIDATION.json`。旧 `candidate-functional.json` 不被新结果覆盖；新回执明确区分FP16受控max_num_seqs1与FP32原配置，以及原FP16 HTTP对照的measurement-invalid状态。执行顺序为 `docker exec BGE-M3 /flagos/bin/python <case>/commands/controlled-report.py`，通过后再执行同目录的`final-report-v2.py`。

三轮受控对照已完成：before/current/revert每轮10240项与原FP16 baseline均逐位一致，before→current/revert全部10240项配对max_abs=0；未丢弃首次、重复或单句。FP32原108628项max_abs2.3841858e-7；`functional-comparison-controlled.json`通过。`batch-shape-diagnosis.json` SHA `b209afd54c876a2a81bbfb1af8300486219e8f402d43b4814b99a8adf82da0b5`。所有临时服务已退出，GPU2无进程。

最终全文件快照门禁额外拦截两份`accuracy_result.json`：原仓库conftest的pytest_terminal_summary无论`--record`都会生成，确认是本轮新文件、旧快照不存在且仅含本轮目标test节点。未忽略漂移或把结果混入diff；保存 `commands/archive-test-results.py`，逐文件SHA与schema校验后移动至独占 `native-test-results/{fg,fgv}-accuracy_result.json`，不删除数据/覆盖原文件。未来复现可用原生 `--record json --output <独占路径>` 将此回执直接重定向。移动后重跑封存，生产源码和测试内容均不变。

## 最终规范复核与交付

| 范围 | 结论 |
|---|---|
| 算子A1–A4/B1–B5 | FG仅ATen Linear内部调优与原公开注册；FGV沿用既有flash_attn_varlen公开导出/分发/MetaX配置。没有Plugin私有数值launcher、模型名选择或新Torch compute fallback。两个完整diff均无额外不必要生产修改；FG无关import排序已撤销。 |
| C1–C8/D1–D6 | 本轮只修FP32执行前metadata错误及日志，不改数值kernel/调优参数、返回类型、有效输入行为或半精度路径；不重试数值执行错误。非法dtype/device/cu metadata和out不变性在普通/优化解释器下验证。cu内容值仍按原调用契约，不宣称新增GPU内容值验证。 |
| E1–E7/F4–F6 | 独立FP64参考、真实公开/ATen命中、原FG graph capture+两次更新输入replay、原FGV FP16/BF16/FP32及context命中测试均通过；厂商日志在真实入口验证。格式/lint按完整源码树的原固定hooks通过。原失败用例/reference/容差未削弱。 |
| F1–F3及Plugin D3 | 当前维护回归不作新性能结论；不是正式精度/性能验收。FG/FGV本地配套改动未公开发布，必须与Plugin补丁成对交付，PR前仍需先公开算子改动并固定公开依赖版本。模型graph、多卡和其他厂商未新验。 |

最终`commands/final-report-v2.py`封存通过：所有库文件/权限与合并部署清单一致、没有未解释源码/资产漂移；Git fsck、普通diff/空staged、HEAD/来源分支和安装绑定均正确，Plugin完整patch仍为原`146758d9…`。容器仅保留原两个Bash进程，GPU2无进程，测试服务已全部退出。

证据根为 BGE-M3 容器内 `/tmp/bgem3-operator-repos-20261105.ewdv1kyz`：

| 产物 | SHA256 |
|---|---|
| `fg-final.patch` | `d5aa1dbee7bce2b6c9862638d11b853636fae8665f4a4ef22f873c8231bbb7e8` |
| `fgv-final.patch` | `e2afb78b80c84978e231fd2667cd71f896ccab52f7c9d6830b23a1eecc3ee731` |
| `plugin-final.patch` | `146758d9791c8e6ceb7bb51695925215ca4d50ba2563c7dfaa4f99d2e935db42` |
| `FINAL_VALIDATION.json` | `2cef66de1740e3c6a5ae498cd18a8682c9d8f57b4dbec55990d1e91360f2625a` |
| `batch-shape-diagnosis.json` | `b209afd54c876a2a81bbfb1af8300486219e8f402d43b4814b99a8adf82da0b5` |

四组最终JUnit、原pre-commit日志与各自SHA见最终JSON。备份在`contract-fix/before`和`contract-fix-002/before`，恢复资产清单与原始源码快照在`fg/`、`fgv/`；所有失败结果、普通/优化解释器安全复现、受控before/current/revert、真实batch日志与原生测试JSON保留在外部证据根。回退脚本只供需要撤销时使用，不曾执行，且都先检查没有后续人工漂移。

三库补丁与小型验证包：[bgem3-three-repos-20261105-delivery.tar.gz](/tmp/bgem3-three-repos-20261105-delivery.tar.gz)。其中`README.md`写明三个精确基线、FGV全量patch不可重复叠加到特性头、跨仓库发布限制和依赖容器原备份的回退边界。临时目录产物需在回收容器/清理临时文件前另行归档。

交付包46959 bytes，SHA256 `3a46afcb12921046ace767d1efa44fbe6dc4da81a13319e9768611790849275c`；已从本地取回包重新校验三份patch与最终回执SHA，均一致。未把大体积源树、完整服务日志、模型输出或权重放入包或当前仓库。
