# eng-053：Plugin 正式 PR 候选收敛

- 状态：源码/测试/交付包已收敛，53项CPU契约通过；10请求最小回归及终态CPU审计通过，pr_readiness=needs_revision（父PR格式/CI待处理）。framework / 工程整理，不测新性能。
- 目标：把当前实际生效的自有 Plugin 变更整理为可独立评审的最小补丁、测试、依赖说明及验证矩阵。
- 范围：PPU-07、qwen3.8-flash-opt-ppu07-20261015；后续新授权仅8010一次重启及10请求回归，不访问8035、不提交/推送或创建PR。以下未加载记录为较早阶段。

## 优化方向与瓶颈依据

用户2026-10-20明确要求按正式PR标准收敛Plugin修改。当前acc017已通过177/198（89.39%）且有精确绑定gate，但仍有7条60K reasoning-only；该结果只证明原运行组合，不能继承到整理后代码。四正式性能场景尚无当前组合baseline/candidate/revert，不能用正确性修复声称性能加速。

## 优化内容与适用边界

先将冻结main a696859b与PR455 head3cb373b1的既有合并内容同自有补丁分开。当前私有Plugin047没有.git；以原env035合并index为祖先，对比实际源码字节与AST，恢复原文件风格/许可证，避免把上游模型适配和整文件AST重排当新增贡献。重点复核模型专属FP32 attention/MoE late TP归约、实例绑定/幂等/非BF16与SP/EP行为；诊断观察器和固定调优不进入公共代码。

优先模型已有扩展点，不改vLLM类或公共collective，不修改FlagGems/FlagGems-vllm。保留i64、QSA M16、PLE CTA修复为跨库依赖，明确原始上游/已提交PR与实际私有实现差别。所有源码整理只在新候选副本，不安装、不切换导入路径、不清缓存或恢复服务。

## 正确性与路径命中

计划：目标仓库CPU/mock单元契约、重复安装/原路径/TP1/dtype/tuple/SP/EP/错误传播测试、语法/风格/补丁应用及AST语义审计。真实设备graph、C8和正式精度需候选加载后另行验证；当前不授权重启/推理，不用原acc017 gate冒充新候选通过。CPU/mock不代表硬件通信或跨平台实测。

## 性能效果

not_run：无新请求/benchmark，当前任务是PR工程整理。Prefill/Decode/Mixed收益及FP32通信开销未补测，不给speedup。

## 决定、风险与回退

源码工程整理成功条件已达到：自有差异可审、测试可复现、无诊断泄漏/无关格式化，依赖/未测项明确。新树已通过本篇10请求graph/C1/C8回归；pr_readiness仍为needs_revision，父PR455的格式/临时CI绕过待处理，正式精度和性能仍未测。原始运行源保留，可回退但不能自动重启；原gate只属旧源码/实例。

## 执行前冻结：独立候选与CPU检查

原env035 index tree固定为d1a32bdb0540cf37e7ffb5ace6c0af8b51dc888e（main＋PR455，不含自有unstaged FP32）。只读逐文件与AST比较确认：运行源仅model.py/qsa.py两份tracked文件不同，另加tp_reduction.py和构建生成_version.py。model.py包含FP32改动＋6处diag043 tap及AST整文件重排；qsa.py只新增带4处diag047 tap的投影采集方法。候选直接从原index还原风格/许可证，不拷诊断方法/tap/_version.py。

本地暂存`/private/tmp/qwen38-plugin-pr-053.XRRym2/candidate`；自有diff仅model.py最小3调用修改、typed tp_reduction.py与CPU/mock单测。无平台SDK/环境开关/Host/路径选择，MoE实例方法保持原SP/TP/EP/pre-reduced/truncation守护、非BF16委托native，不能改公共类。正式架构缺乏accumulation-dtype注入点，因此仅在本模型构造后幂等绑定runner；API不兼容明确失败，不静默fallback。

先在新E保存`commands/verify-candidate.py`再执行，仅CVD空的独立CPU PyTorch pytest、collective为mock，明确`--noconftest`避免平台探测。脚本核原API精确start/argv及运行3文件SHA前后一致，检查日志落E/checks-001（排他创建、不覆盖）。准备操作只在新E/candidate从冻结tree解包，再以已保存候选文件覆盖新副本；不安装/切换PYTHONPATH、不触碰运行源。Ruff0.14.0置于本地独立临时工具env，符合目标pre-commit版本，不改当前项目/容器依赖。

## 外部证据

已知基线：容器内`/opt/qwen38-plugin-pr455-20261019`（HEAD a696859b、PR455 staged merge、原本地FP32 unstaged/untracked）；运行源`/opt/qwen38-accdiag047-fixed-tune-qk-state-20261020/plugin`。远程产物计划置于用户原BASE下`engineering/eng-053-plugin-pr-cleanup-20261020`，创建前检查路径、权限、空间、不覆盖。完整源码/补丁/测试日志外置，不进入模型记录目录。

## 收敛结果

最终自有补丁只有**3文件、+257/-3行**，不把PR455模型适配、其他平台修改或算子修复重复包装为本次贡献：

| 文件 | 变化 | 归属 |
|---|---|---|
| `vllm_fl/models/qwen3_8_flash_next/gpu/model.py` | +4/-3；导入helper、模型构造绑定MoE实例、2个外层collective改调用 | 模型专属数值边界 |
| `gpu/tp_reduction.py`（同模型目录） | 62行；typed BF16归约前转换/FP32 collective/原dtype返回，原生MoE guards与裁剪；重复绑定幂等，ABI不符明确失败 | 最窄模型适配器，无公共类/collective patch |
| `tests/unit_tests/models/test_qwen3_8_flash_next_tp_reduction.py` | 191行；53项CPU/mock契约 | pytest unit CI目录，数值/边界/生命周期/异常传播 |

从运行版本剥离6处diag043 tap、diag047 Q/K采集方法及AST-unparse整文件重排；恢复基线许可证和相邻风格。QSA文件与冻结PR455 index逐字相同，不进入自有diff。没有新环境开关、vendor导入、路径/端口/PID条件、定时/同步探针、版本文件或备份文件。两条实际数学函数`qwen38_tp_reduce_fp32`和`_moe_late_reduce_fp32`去注解/docstring后的AST与运行原件完全相同；构造时唯一额外行为是不可调用原方法时在部分安装前明确TypeError，不静默丢失保护。

### 已执行验证与未测矩阵

| 范围 | 证据/结果 | 限制 |
|---|---|---|
| BF16 cast位置、非BF16 native、empty/nonaligned/转置输入 | 实际CPU PyTorch tensor、mock collective，executed_passed | 非PPU/NV实际通信 |
| SP/TP/EP/pre-reduced组合、truncation | 53项总矩阵内，executed_passed | 模型现有SP入口仍不支持；不新增支持声明 |
| 幂等/peer隔离/不兼容ABI/错误传播 | executed_passed；不改公共类、无失败重试fallback | 不替代worker启动和graph覆盖 |
| 无vendor环境的helper导入 | isolated module＋mock vLLM distributed，executed_passed | 不是完整Plugin/所有平台硬件导入通过 |
| Ruff0.14.0 lint | 三个changed Python文件executed_passed | 未称全仓CI通过 |
| Ruff format | 新helper/test通过；原model.py基线与候选均失败 | 保留父PR原格式，避免无关整文件重排；合入前与父PR处理 |
| patch apply/内容 | 冻结base `git apply --check`通过，远端payload SHA逐文件一致 | 不自动rebase浮动main |
| 新候选graph capture/至少2replays、C1/C8 | executed_passed，见本篇终态 | 原生graph统计而非逐rank callback；两C1完整tokens一致 |
| 新候选正式GPQA | not_run | 本轮明确禁止，新源码不继承旧gate |
| Prefill/Decode/Mixed稳态BCR | not_run | FP32通信/转换成本及收益仍需同契约实测 |

CPU测试耗时1.39秒，53 passed/0failed；工具回执`E/checks-001/report.json` SHA3412239c3d559407ccd66cb4402aab08128ef6d227d611ff81a8a04803d73470，完整命令/输出见同目录pytest.log。未用mock伪装graph或硬件验证。

父PR455自带`model.py`格式债务及`.github/workflows/_lint.yml`临时`continue-on-error: true`，均非本次引入。本次不修改这些公共CI以掩盖错误，PR说明已明确合入前必须解决；不宣称上游CI绿灯。初次创建E时缺少engineering父目录，命令退出且未写源码；补建父目录后排他创建成功。tar忽略macOS provenance扩展属性，随后内容SHA全部相等，不影响候选字节。

### 交付路径与依赖

E=`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/eng-053-plugin-pr-cleanup-20261020`：

- 完整独立候选：`E/candidate/`（原挂载内可见；新授权后通过独立PYTHONPATH选择，未覆盖旧源码或全局安装）。
- 三文件补丁：`E/delivery/plugin-fp32-tp.patch`，SHA5b3cef74d9a30e1b9def8ac2acd73405506f65c6ccc179cf47184c2d7fdf290d。
- 逐文件base/after SHA与父版本：`E/delivery/manifest.json`。
- PR问题/设计/作用域/验证/风险/回退说明：`E/PR_DESCRIPTION.md`，SHA18bda437234d9dc3bc85eabed98d3b43659fb165731b8614bc49f30962fbe92e。
- 执行副本与回执：`E/commands/verify-candidate.py`、`E/checks-001/`。
- 本地可审阅副本：`/private/tmp/qwen38-plugin-pr-053.XRRym2/candidate/`、同级delivery/PR_DESCRIPTION.md；原始完整基线保留于baseline/。

依赖按仓库分开：Plugin a696859b＋PR455 head3cb373b1为本次父树；vLLM0.24 MoERunner ABI；本补丁没有新增FlagGems/FlagGems-vllm符号依赖。当前模型仍使用env041 Gems i64/randn与旧fused导出、FGVLLM b4d3382的QSA M16＋051私有PLE i64/CTA（已提PR959），它们不被复制到Plugin。本次不自动升级/删除这些依赖，也不把私有树版本号当未修改上游版本。

### 在线保护与下一门禁

19:41:17（北京时间）完整运行source重新CPU核验仍等于acc017 before；API593716/start519643298/argv未变、health200，running/waiting0。prompt83322/generated2389260与正式终态相同：0新增模型请求、0GPU测试、0重载/停止、0次8035访问。i64/QSA M16/PLE和FP32保护未动，acc017旧gate保持原绑定；没有提交、推送或创建PR。

后续若授权加载clean候选，必须同时去掉实验sitecustomize/PYTHONPATH诊断bootstrap，不将旧047 hook套在删去采集方法的新树上；保留数学修复及正确依赖、冻结独立启动/缓存配置，先仅8010 capture＋2replay/C1/C8/同前缀，再根据源码变化重新执行正式gate。需要重载或新增推理前先向用户说明并取得方向，本次不自动执行。

规划复盘`eng053-pr-boundary-review`已写state：原env035→FP32→env041→047→051→052→acc017依赖链可追溯；当前原组合有有效精度gate，但没有当前四场景可比性能累计收益。排序为完成本次工程收敛→受控新树正确性→有新gate后才评估性能；暂缓广泛collective/QK融合重构，未定义或未测的收益仍为null。

## 用户新授权：收敛候选最小回归（执行前冻结）

2026-10-20用户明确授权仅重启8010一次加载收敛候选，graph capture/至少2次replay及2C1＋8C8；保留FP32、env041 i64/randn、QSA M16、PLE051，不访问8035、不重跑完整GPQA、不提交推送。此授权替代上文“候选不加载”的旧边界，不扩大到其他服务。模式为inference-accuracy-evaluation minimal-regression；原acc017 gate继续保留历史绑定，不适用于新源码/实例。

新产物`E/model-regression-001`，执行副本`E/commands/eng053-control.py`；先prepare（无服务变更/请求），再排他launch唯一driver。只向精确匹配的旧API593716/start519643298/argv5744d999发送一次SIGTERM，等待已冻结子树自然退出；不追杀、不停容器，不成功则停止而不重试。新启动沿用原argv和依赖/缓存，仅增加vLLM原生`--cudagraph-metrics`。去掉旧probe047/model/QSA/逐层采集bootstrap；为不意外改变调优策略，隔离保留原pin047逐字版本，仅安装同一Inductor固定调优策略，不导入probe047。固定调优日志和bootstrap均外置，不进Plugin补丁。

复用052固定payload，seq0..9为doc2/2/0/1/2/142/144/149/155/178，最多10条、并发8、0重试/隐藏预热，原温度/top-p/top-k/penalties/seed1234/stop/max60000与完整token返回不变。两C1完整token应一致；两类capture7/7与C1产生的原生FULL graph执行计数至少2后才进入8条C8。原生指标来自已完成输出的graph调度统计，结合已capture的native wrapper replay分支证明；无独立逐rank callback，不能冒充旧observer八rank逐次replay计数。缺证记incomplete，不追加推理。CLI仅可观测项变化及无旧张量hook意味着时序不同，不做性能结论。

启动/源/权重/tokenizer/容器mount及精确进程身份前后绑定；每条request/HTTP bytes/headers/完整token/usage/think-end/EOS/content/reasoning单独保存，首次异常停止新阶段分发，在途自然返回。完整可读服务/driver日志和源SHA冻结。缺失数据或startup失败不自动恢复。该10请求结果不替代正式198题精度、不签新gate。

执行副本SHA8c9c1e3485a12af2a5b1cc0a05cffc39bc77196411c8046ef9117d55767dd0f4；Skill bundle SHA6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2。`python3 E/commands/eng053-control.py --mode prepare`已成功冻结PREPARED、依赖完整源码、mount、原API/空闲metrics、10条payload和新launch；尚未重启/发推理。下一命令仅`python3 E/commands/eng053-control.py --mode launch`，排他启动一个controller，后续只监控其run，不重复launch/run。最初scp通道未写入远端，已用SSH tar排他传输并核SHA；首次准备未执行成功时无服务动作/请求。本地py_compile因系统默认pycache目录只读失败，改用内存compile语法检查通过，不影响远端源码。

19:55:29+08唯一controller2439787/start521315517发出仅旧API593716一次SIGTERM，19:55:31原子树全部自然退出；目标卡8–15逐卡检查空闲后只启动一次新8010，开始Plugin/worker初始化。PREPARED请求SHA4b80fe98aa18470c39b0e1773010cd19df0824369effa828a65ab9c517cca7d5、launch2f837dbe、固定pin61da24bb、轻量bootstrap9734f202已保存。原服务gate历史保留，但新候选current accuracy=incomplete/minimal待完成、formal performance不允许。heartbeat复用原ID改为eng053专用最小回归提示并ACTIVE产品确认（30分钟，仅实质变化通知），不保留旧formal启动指令。启动期已见旧FlagTune configs-key default-fallback告警，不据此判新模型事故。

19:58:31+08 READY：新API Host2441711/start521315854/argvSHAc146e2da4762690185e9b3573c5f48796a5cb42aa2037de0d08d9ada40595010，旧argv除新增native metrics开关完全相同；两类native capture各7/7，第一条C1已派发。19:58:41原生已完成输出统计FULL52次（无额外模型请求），结合本轮捕获完成与冻结native wrapper已有entry分支replay，至少2次覆盖成立；这是引擎统计而非八rank独立callback，且C1 HTTP尚未返回不能算成功题数。没有DRIVER_ERROR/FIRST_ANOMALY，不沿用旧实例replay数。

20:00:40+08：两C1均B503、完整token逐项相等，think-end/末EOS/final/usage均正常；C8前`GRAPH_REPLAY_CHECK`原生FULL统计下界821，阶段门禁通过，8条C8全部分发。共10已派发/4真实HTTP200/6在途/0错误：seq0/1 doc2 B503、seq2 doc0 D714、seq4 doc2 B518，诊断gold均匹配；不把在途无正文叫空final。服务running6/waiting0、日志持续推进；尚无FINISHED，不宣称10条回归通过。原唯一driver继续自然收集，不追加或重发。

20:01:46+08复查仍4HTTP200/6在途，8010精确新绑定不变、health200，无FIRST_ANOMALY/DRIVER_ERROR；native日志另有实际unpadded8/padded8/FULL26、208、209次，已证真实8请求batch执行，而非只以线程池并发配置冒充C8覆盖。余请求持续生成，heartbeat继续只读，终态前不签通过或新gate；不等待期间追加负载。

## 终态CPU审计（执行前记录）

20:27:44+08只读发现controller已退出，FINAL_SUMMARY/FINISHED完整，原生summary记录10HTTP200且10/10诊断gold匹配，无空final/length/异常marker，结束时间为20:05:47+08。8010仍为API2441711/start521315854、health200、running/waiting0。按授权仅CPU核验已有数据、补冻终态日志尾部，不重发模型请求。

审计副本`E/commands/eng053-terminal-audit.py` SHAfbddc89f5a238955e06dbb1650d1180d5699f13fe5c3330b8af1ca44937eb5f2；唯一执行`python3 E/commands/eng053-terminal-audit.py`，排他写`R/post-controller-audit-001`，已有目录则拒绝重复。它不调用controller任何mode：核controller SHA后只导入定义、调用CPU source_check（CVD空），比对当前全部源码/metadata/原before-after；校验原manifest、10raw/header/请求/完整token、think-end/EOS/答案、seq唯一/并发高水位、native graph/C8与服务counter精确一致，补存已退出driver完整日志与服务固定字节前缀。无GPU/推理、无服务信号、无8035访问，原证据/marker不改写。结果待实际审计确认，不以原summary替代独立核验。

## 终态：收敛候选10请求最小回归通过

本轮20:05:47+08自然结束，20:29:56+08一次CPU审计通过。controller已退出，8010保留API2441711/start521315854/argvSHAc146e2da，无第二次重启/推理重试或额外模型请求。结果为**minimal-regression passed**，不是formal-gate或性能结论。

| seq / 阶段 | doc | 最终答案 / gold | completion tokens |
|---|---|---|---|
| 0、1 / C1 | 2、2 | B / B（两次） | 503、503（完整序列相同） |
| 2 / C8 | 0 | D / D | 714 |
| 3 / C8 | 1 | B / B | 2783 |
| 4 / C8 | 2 | B / B | 518 |
| 5 / C8 | 142 | D / D | 5844 |
| 6 / C8 | 144 | B / B | 2315 |
| 7 / C8 | 149 | B / B | 6476 |
| 8 / C8 | 155 | C / C | 4669 |
| 9 / C8 | 178 | A / A | 2318 |

10请求/8唯一doc均HTTP200、非空final、finish=stop，完整token长度与usage一致，均含think-end248069并以EOS248046结束。诊断答案10/10匹配，0空final/60K截断/真实HTTP超时/错误/提前EOS；服务日志未见新增非法访存/worker故障，未声称完整逐层数值或状态reference比较。事件seq恰0..9一次，高水位并发8。服务counter累计prompt3607、generation26643精确等于10份API token数，零隐藏请求；末态health200、running/waiting/KV/preemption均0。

PIECEWISE/FULL capture各7/7，C8前原生FULL821，controller终态7386、CPU冻结最新前缀7482；其中真实unpadded8/padded8/FULL517，满足至少2次replay及真实C8执行路径。native scheduler已完成输出统计结合SHA冻结wrapper捕获entry分支证明，不是八rank独立callback；没有新worker函数对象hook或完整逐层/QK/logits/state采集，大索引/旧C64/60K症状是否解决仍未覆盖。

原manifest共86文件全部SHA/大小通过；source-before=after=本次CPU当前完整Plugin/FG/Gems/native graph及权重/tokenizer元数据，关键FP32/i64/randn/QSA M16/PLE051/blacklist保留。旧冻结service/driver日志是前缀，审计未改原件：另存service固定393806 bytes（补1852）与已退出driver完整9523 bytes（补9016），新文件SHA已核。

证据均位于`R`：`req000..009` request/response raw JSON、headers/result、`C1_REPEAT_CHECK.json`、`GRAPH_REPLAY_CHECK.json`、`native-graph-stats-after.json`、`FINAL_SUMMARY.json`、`FINISHED.json`、`manifest.json`及`terminal-evidence-001/`。摘要SHA c23933f7255d310e4bd5acdcd68724c06dfe9e3b1d4dcdcb6e0b086a217bb8c8；原manifest SHA9b1287caf93068f4ad611ff2ad6067e0e90ec72ffad7f40af82f9291264f1043。

独立CPU报告`R/post-controller-audit-001/report.json` SHA60aa8f3e3810f6d6a5caf0fcb8838cbf44bf9ed182644906ebd1e62deb10b5b4，审计manifest SHA2a3fda798db25db33aa39d93910e18843c8a5a9ad2385a32f7a3422251a43005；同目录保存current-source、终态metrics、完整driver与服务固定前缀。没有新formal gate，旧acc017177/198及其7条60K记录不改写/不继承到新树。未访问8035、未跑全量GPQA、未提交推送；本heartbeat终态暂停，保留8010运行并等待用户方向，不自动升级、回退或追加正式评测。

## 二次整体设计review：可收敛与复用边界

用户在最小回归终态后要求整体review，不要求本轮实现。检查范围为已冻结candidate完整模型目录、Plugin distributed/OOT MoE factory/CachedOp/默认与vendor backend、相邻测试和PR说明；对照本项目Plugin设计规范。仅额外只读容器内三个vLLM源码文件，未查询8035/其PID/设备，也无推理、服务操作或代码改动。以下是工程改进与证据缺口，不据此推翻已通过的10请求回归，也不宣称发现新的数值事故。

### A. 自有FP32补丁：优先收敛契约，不上移全局collective

1. `gpu/tp_reduction.py:30–43`复制了native late-reduction条件及truncation。当前真实MoERunner方法逐项一致，故未证实当前版本错误；但`tests/unit_tests/models/test_qwen3_8_flash_next_tp_reduction.py:35–45`的Runner只记录调用和裁剪，不是native方法，测试预期又复写同一predicate，无法检测上游升级漂移。优先补实际vLLM native方法＋mock collective的契约矩阵，涵盖SP/TP/EP/pre-reduced、dtype、None/0裁剪及shape/stride/alias/调用次数；保留既有CPU独立单测，不以mock替代硬件。
2. 本次只读核验纠正接口描述：native `FusedMoE`已有`runner_cls`/`runner_args`，Plugin `FusedMoEFL`已通过`*args/**kwargs`原样转发；不存在的是accumulation-dtype选项，以及当前继承的`Qwen3NextSparseMoeBlock.__init__`向factory透传runner选择的参数。长期可用显式模型专属runner类替代MethodType安装；短期若必须复制上游约120行构造或做全局context/class patch才能注入，反而扩大兼容面，不建议。native路径复用还应保留cast/truncation顺序与返回layout，不能把`native(states.float(), trunc).to(BF16)`未经检查当零风险等价简化。
3. 原生方法/工厂/模型源码的本轮SHA分别为d11a841e24f46a14884d36334b83387370cd8232679d8569a6a06eb3a6918eb2、c0610b61c199f6d77cf0ee0a939fa1dc85e9ac157803df3cfd9df762dc6ce617、885ce3244d069871bd8df93e67d94e4f394259c951f6a778947743d4a57b7fa5。未以静态9月分析文档替代当前ABI事实。

### B. 父PR455已有代码：单独整理，不混入三文件FP32补丁

1. `common/hyperconnection.py:38–43`由common反向导入gpu leaf并触发custom-op注册，且捕获ImportError后forward仍调用torch.ops。common因此并非独立数值reference；FGVLLM符号缺失也可能被延迟为后续注册/属性错误。建议GPU入口负责注册，common只保留HC数学/布局语义，能力选择和实现交给既有dispatch；不要再造common→gpu依赖或另一套可选依赖机制。
2. `gpu/ops/hyperconnection.py:5–14`、`ops/qsa.py:8–16`、`ops/ple_fusion.py:5–11`目前直接绑定FGVLLM，默认/reference/vendor的实现选择没有复用CachedOp，NVIDIA fast paths又在模型侧选择。可把纯数值实现的选择下沉既有registry/backend（FlagGems默认、reference和真实vendor能力），custom-op fake/mutates_args仍由模型边界维护；QSA request-slot/cache事务/graph workspace和PLE checkpoint/ngram语义继续留模型。当前catalog没有这些对应项，迁移需要明确注册与路由/strict/fallback/graph测试，不是改一行导入就宣称复用完成，更不能在状态写入失败后宽泛重试reference。
3. `gpu/model.py:490–500`对同一GDN构造函数连续做两次同样signature检查，可在构造局部计算一次支持标志复用；这是P3工程简化，不是稳态性能收益。类似两行设备谓词也可局部复用，但不足以新建全局capability缓存或框架。

### C. 交付文案与不应抽象的内容

冻结`E/PR_DESCRIPTION.md`仍是部署前版本，写着新树未推理/未选择、回退无服务动作。正式提交前应生成更新版PR说明，纳入这轮10请求和graph证据，明确无新formal gate、当前回退需另行服务授权；原冻结文案/SHA保留，不在本轮静默覆盖。父PR格式与临时CI continue-on-error仍是已知待处理项，不应借本次review更改CI掩盖。

本次10请求仍保留独立pin047固定调优bootstrap。它不是公共Plugin补丁的一部分，也不意味着未带固定调优的标准部署已验证；PR说明需区分必要数值修复与实验环境依赖，不能把外置pin悄悄包装成新的全局调优机制。

不建议把BF16→FP32 collective策略上移到全局`distributed/communicator.py`或默认FusedMoEFL（会改变其他模型/平台）；不把i64/randn/QSA M16/PLE CTA kernel复制回Plugin；不把模型KV/状态事务拆成可任意fallback的零散算子。只有第二个真实调用方且语义完全相同后，才考虑把模型局部helper提升为公共能力。

建议顺序：先真实native契约测试＋更新交付文案，再评估最窄runner_cls透传；父PR的common依赖与算子dispatch迁移拆成独立工程变更。当前三文件candidate/补丁/在线服务及既有通过证据全部不动；本轮无测试重跑、无新gate、无提交推送，pr_readiness保持needs_revision。
