# 20261104-dsv4-metax104-plugin-review / optimize

<!-- e2e:summary:start -->

- 案例：20261104-dsv4-metax104-plugin-review
- 当前状态：op005_recheck19_完整BCR及独立审计完成_稳定性通过_32K收益未达5%_整改容器未改
- 当前候选：main025-reuse-op004-ref008-ref009-ref010-whole-adaptation-convergence
- 下一步：FGV验证与规范复核已完成：9个PR Ready、3个SDK性能/继承稳定性门禁未过而Draft；设备CI/review待上游，不自动部署或操作模型服务。

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| op-005 | milestone完整；原target SDK TTFT11.63%超限保留；诊断确认Mixed准入排队约0.48秒步长；recheck19全新B/C/R完整，稳定性/漂移通过，SDK32K收益3.11%不足5% | current安装版 vs SDK反事实，P1K/P32K原负载 | [op-005.md](op-005.md) |
| refactor-011 | 9_ready_3_draft_performance_blocked; combined527pass18skip | FGV-upstream-operator-PR-series | [refactor-011.md](refactor-011.md) |
| refactor-010 | retained_source_convergence_user_authorized_no_service_action | whole-adaptation-convergence | [refactor-010.md](refactor-010.md) |
| refactor-009 | installed_cpu_config_equivalent_no_restart | model-scoped-compilation-defaults | [refactor-009.md](refactor-009.md) |
| refactor-008 | user_requested_direct_source_application_before_gpu_validation | public-api-family-consolidation | [refactor-008.md](refactor-008.md) |
| refactor-007 | retained_api_alignment_bounded18paths_user_service_restored | public-api-contract-alignment | [refactor-007.md](refactor-007.md) |
| op-004 | retained_bounded_correctness_fix_requested_suite_complete | prefix-on-kv-gather-correctness | [op-004.md](op-004.md) |
| refactor-006 | retained_current_candidate_full_gpqa_passed_same_instance_service_kept | p32768-d1024-c64-n128 | [refactor-006.md](refactor-006.md) |
| review-001 | retained platform-default YAML and3export startup script per latest user request; external dependency superseded; full adaptation still needs_revision | code-review-config-boundary | [review-001.md](review-001.md) |
| refactor-001 | paused_by_user_candidate_only_no_B_R_comparison_or_source_delivery | p32768-d1024-c64-n128 | [refactor-001.md](refactor-001.md) |
| refactor-002 | paused_by_user_candidate_only_no_B_R_comparison_or_source_delivery | p32768-d1024-c64-n128 | [refactor-002.md](refactor-002.md) |
| refactor-003 | paused_by_user_candidate_only_no_B_R_comparison_or_source_delivery | p32768-d1024-c64-n128 | [refactor-003.md](refactor-003.md) |
| op-001 | paused_by_user_candidate_only_no_B_R_comparison_or_source_delivery | p32768-d1024-c64-n128 | [op-001.md](op-001.md) |
| op-002 | deferred_not_installed_inherited_path_no_runtime_causal_proof | p32768-d1024-c64-n128 | [op-002.md](op-002.md) |
| op-003 | final115PluginGPU+9FGV passed,8production and3standardtestfiles installed,7FULLcapture and22minimal passed; no formalGPQA/performance claims | p32768-d1024-c64-n128 | [op-003.md](op-003.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1024-c64-n128 | candidate | output_throughput | 1180.8772 | tok/s | performance04 三正式轮中位数；用户暂停，未与B/R比较 |
| p1024-d1024-c64-n128 | candidate | median_ttft_ms | 2225.367 | ms | performance04 三正式轮中位数；用户暂停，未与B/R比较 |
| p1024-d1024-c64-n128 | candidate | median_tpot_ms | 51.7164 | ms | performance04 三正式轮中位数；用户暂停，未与B/R比较 |
| p32768-d1024-c64-n128 | candidate | output_throughput | 217.5425 | tok/s | performance04 三正式轮中位数；用户暂停，未与B/R比较 |
| p32768-d1024-c64-n128 | candidate | median_ttft_ms | 8679.7708 | ms | performance04 三正式轮中位数；用户暂停，未与B/R比较 |
| p32768-d1024-c64-n128 | candidate | median_tpot_ms | 274.3108 | ms | performance04 三正式轮中位数；用户暂停，未与B/R比较 |

<!-- e2e:summary:end -->

- 2026-11-05：按用户要求统一整改容器FGV暂存区与当前C20+op003 revision05工作区。38项全部暂存，未暂存/未跟踪均0，1078项指纹/链接核验、HEAD与源码不变，health200。备份`refactor01/git-index01`，详见[op-003](op-003.md)；不提交推送。

- 2026-11-05 refactor-004: FlagGems-vllm adaptation migrated onto official main `27011d53` and editable-installed from `/opt/dsv4-sources/FlagGems-vllm-main-20261105`, branch `refactor/dsv4-main-20261105`. 38 staged status entries, clean worktree; original source retained. Existing API unchanged/health200. Source/install migration only; new-mainline GPU/graph/formal/performance not_run. See [refactor-004](refactor-004.md). No commit/push.

- 2026-11-05 [refactor-005](refactor-005.md): FGV source convergence on main27011d53,38->35 staged entries, added lines6144->5649. Removed inactive experiment and independent unused gather patch, retained active tests;34 CPU dispatch equivalence cases and unchanged retained JIT ASTs. Installed source branch `refactor/dsv4-main-slim-20261105`; original API unchanged/health200. New-mainline GPU/graph/formal/performance pending, no commit/push.

- 2026-11-05 [refactor-006](refactor-006.md)：逐项对照最新 main `025f3181`，独立候选共享主线 MQA JIT 并补薄 BF16/mask 入口，移除两份重复 prefill kernel；dense/V32 委托主线公开 API，参考实现归回 Plugin reference backend。13份迁入kernel保留11份原AST；不兼容的量化舍入、MODEL1 scratch/头布局及Top-k契约暂不替换。FGV补丁34项/+5223/-515；新候选仅CPU/静态/格式检查通过，8原reference graph用例完整迁移、8新MQA用例已准备但未运行。产物 `refactor01/reuse01`；未安装、未改当前35项暂存区和editable路径，独立核验原服务身份未变/health200。无新精度、性能或收益结论，不提交推送。

- 最新授权 GPU 交付：[refactor-006](refactor-006.md) 的 lease09/gpu07 完成335/335数值/graph/dispatch、22/22模型检查、7FULLcapture及单FULL区间257；已切换整改容器到 main025-reuse 私有源码并恢复原服务，独立1188FGV/5PluginSHA与health200核验通过。34项暂存、工作区干净，旧35项slim仓库完整保留。上方静态阶段“未安装”为历史事实，当前状态以本条和首段为准；不自动跑GPQA/性能，不提交推送。

- 用户新指令：收敛版本全量GPQA/C64已于2026-11-06T07:55:04.214626+08:00开始；独立UUID`864a98b62c6647efba80865b6181596c`，观察唯一完成10/198、无最终分数，heartbeat`deepseek-gpqa-c64`每30分钟跟踪。只完成本次精度验证，不自动继续性能或源码改动。

- 最新全量精度终态：GPQA/C64完整198题，strict160/198=80.8081%，达到80%阈值；396条样本两filter各198唯一，nativegate/check、前后source/data/instance及独立核验均PASS。原生协调器约23m40，当前服务health200且原参数不变；heartbeatdeepseek-gpqa-c64已删除。旧“59/198/运行中”条目为历史进度，无新性能或收益结论。

- 2026-11-06: 用户重启prefixON后确认全量GPQA198+MATH500500/C64串行；新accuracy02准备中，旧OFF80.8081%保留，暂未发新正式请求。详见refactor-006.md与state prefix_on_accuracy_suite_20261106。

- 2026-11-06 10:14BJT: accuracy02 prefixON正式GPQA198/C64已开始，MATH500500随后串行；原生preflight/22minimal/graph通过，独立新cache，当前无最终分数。monitor deepseek-prefixon-gpqa-math500-c64 ACTIVE/30min。

- 2026-11-06 10:15BJT **accuracy02 incomplete**: prefixON/C64触发运行时gatherkernel非法访存，服务退出；仅28/198真实响应、170超时占位，原生92.86%=26/28不代表全量精度。MATH500未启动、未发gate。日志/59assets/sourceafter/客户端退出已独立核验；见refactor-006 incident与state。

- [op-004](op-004.md)：prefix cache 开启后 gather 非法访存定位；先独立 GPU/graph 验证，模型重启由用户执行，完整精度暂未重跑。

最新accuracy03（2026-11-06T03:20:33Z）：GPQA57/198唯一完成，C64/prefixON/.85，已运行2分48秒；MATH500待串行启动，当前无OOM/非法访存。不是最终精度结果。

2026-11-06T03:44Z：GPQA完整160/198=80.8081%（strict，阈值80），396行两filter各198唯一，gate/identity/独立审计通过；MATH500唯一66/500，C64/prefixON/.85，服务健康无OOM/非法访存。尚未完成整个套件。

最终accuracy03：GPQA strict80.8081%（160/198），MATH500 exact_match95.4%（477/500）；64并发、prefixON/.85，合计45分34秒。0超时/OOM/非法访存，逐题/原生门禁/源码身份审计通过，服务保留，监控已删除。详见[op-004](op-004.md)。

## acc-001：与2026-10-29的85.35%逐题对照（2026-11-06）

见[acc-001](acc-001.md)。198题输入/选项/提示词/目标/原生提取规则及有效API采样相同，均C64/prefixON；隔离原生AST证明do_sample表面差异被API adapter丢弃。169→160为17对→错、8错→对，其中12对→错和4错→对来自正确字母EOF缺标点导致strict正则漏提取，净解释8题；其余选项/预算差异净少1题。生成变化的底层原因尚未隔离，不归罪某个kernel或简单宣称随机波动。原85.35%/80.81%和gate不变，未重跑、未改评分/服务。独立回执见remote `reuse01/accuracy-diagnosis01`，review SHA `e387c237ac29e9a3cf3e72139dfa2b4421ea3846b6d4fe9e38cbfb83b22185fe`。

**输出健康更正**：原生`truncations=0`只是该检测字段输出；逐题usage+原文显示旧/新各12题达到30k预算且未结束thinking，均保留分母，不改变原生门槛/分数。此前“0截断”应由此具体观察覆盖。原始回执不覆盖。

### acc-001用户授权EOF规则离线重评分

[acc-001](acc-001.md)已完成两轮完整198题统一重评，无模型重跑。新规则`strict-match-eof-v1`只增加字母后直接EOF兼容，旧轮169→174/198（87.8788%）、当前160→173/198（87.3737%），新口径差1题。原85.3535%/80.8081%、样本、results和gate均完整保留，不被新分数替换。派生每轮396行及独立审计见remote `reuse01/accuracy-diagnosis01/eof-rescore01`；summary SHA `ca19cb1681ed1ff70e780f7ea1843e4dabe59dc15bafb975c200bebd2a43760d`，review SHA `2b4469a7e32517eadfaf72261f106875cd0f6119960c633e0fdb9eca999bb8d7`。未改服务或安装历史任务源码修改，未来正式采用需新契约冻结。

## refactor-007 接口收敛候选

见[refactor-007](refactor-007.md)：独立候选优先复用主线公开API，当前服务/安装目录不改，GPU验证未执行，不提交推送。

refactor-007当前：新增FGV公开ID 8→4，复用4项主线接口；18CPU通过，1410JIT AST和171common/NV文件不变。独立候选已归档，未安装，当前服务未动，GPU/graph/模型验证待执行。详见[refactor-007](refactor-007.md)。

## refactor-010 全适配源码收敛已交付

[整体记录](refactor-010.md)：实际整改容器三库27路径完成收敛，删除3个过渡模块、清理死路径/重复封装，未增加数值kernel。安装前后各162 CPU通过，8,444普通文件+4既有链接及HEAD/index独立审计通过；工作区/暂存区统一，不提交推送。保持18001无服务状态，无启动/重启；新组合GPU数值/真实dispatch/graph/模型验证仍待执行，无新性能结论。

2026-11-09容器维护：用户授权重启整改容器，僵尸进程223→0；同容器/镜像/挂载，容器running、模型服务未启动。独立回执及保留的首次即时状态检查见[refactor-010](refactor-010.md)。

2026-11-10：[FGV逐算子分析](refactor-010.md#2026-11-10当前fgv逐算子优化机制分析)已核实际1189文件与ref010一致，按14项解释阶段/机制/代价/主线复用及验证边界；没有新算子测试、服务操作或速度结论。

[refactor-011](refactor-011.md)：FGV按算子12个上游PR已完成主体数值/dispatch/graph与三轮micro验证；9个已正式，mHC末轮复核中，动态量化和Decode Top-k性能/稳定性阻塞保留Draft。最终组合核心520pass/18原参考skip，不代表E2E验收；容器安装源码/服务未改。

- op005阶段更新（2026-11-11T07:21:25.571933+00:00）：Decode SDK D256/N64两场景完整，输出吞吐中位相对current：P1K+5.49%、P32K+0.95%；量化/Prefill小幅差异见[op-005](op-005.md)。全部等待current回测与原D1024/N128，不宣称整体整改退化/无退化。

- op005 milestone完整B/C/R（D256/N64）：输出SDK增益量化+1.06%/+0.48%、Prefill-0.21%/+1.07%、Decode+5.49%/+0.95%、组合+8.21%/+2.54%（P1K/P32K），B/R漂移通过。原D1024/N128三角色已开始，见[op-005](op-005.md)，尚无原目标结论。

- op005终态（2026-11-11T22:35:11.706087+08:00）：单项milestone完整B/C/R；原始P1K观测SDK组合output+9.57%，原始P32K观测+3.26%，但SDK TTFTspread11.63%>10%，已按冻结规则停止、原targetR未做，整体target=incomplete。48prep+104native共12544主请求0失败；18GPU测试/数值graph通过；独立只读审计、源/安装源码/脚本不变、8卡空闲，无部署/提交推送。详见[op-005](op-005.md)。

- op005 TTFT续查（2026-11-12）：三批同实例A/B/A完整384/0，逐请求Engine时间线确认同A输入63个后半请求少等一个约0.48秒满预算调度步，TTFT约8.39→7.89秒；Prefill执行段基本不变。历史唯一原因仍保留边界。正准备无观察器、统一原负载的全新B/C/R，原慢轮/11.63%incomplete全部保留，整改容器不动；见[op-005](op-005.md)。

- op005 recheck19当前基线P1K 5warm+3formal完整1024/0，中位output1184.87tok/s、TTFT2273.27ms、TPOT51.33ms，三指标spread<10%；32K warm2保留132.58s TTFT异常（API CPU饱和/新请求集中），warm3恢复8.11s。32K正式、SDK和R仍未完成；不提前宣布稳定或收益，详见[op-005](op-005.md)。

- op005 recheck19基线两场景已完整原生check/admission/identityafter通过：P32K三正式output218.4074/219.1522/219.0115tok/s、TTFT8164.0702/8317.5656/8153.3660ms、TPOT274.6856/273.5786/273.3531ms，spread0.3401%/2.0112%/0.4871%。SDK已ON/OFF新实例门禁通过、正在准备，C/R最终比较仍未完成。所有warm2异常保留，不与正式混算。

- op005 recheck19最终（2026-11-12）：原P1K/P32K D1024/C64/N128完整B→SDK→R，18prep+48native共8448主请求0失败，132minimal分列，全部轮次保留；三指标正式spread和B/R漂移均通过。SDK相对当前安装版output中位P1K+8.6258%、P32K+3.1101%；32K未达5%收益线，native比较仍failed（唯一原因），不冒称收益验收。32K TTFT B/C/R三轮中位8164.070/7932.664/8156.772ms，组内spread2.011%/6.294%/5.559%。确认约0.48秒Mixed预算准入量化影响，132秒预热异常的具体Python热点仍未知。独立审计20全部SHA/native/identity通过，原整改容器和启动脚本未改，测试进程清理/8卡空闲，无部署或提交推送；详见[op-005](op-005.md)。

- 新一轮算子追平实验（2026-11-12）：[op-006 Decode](op-006.md)、[op-007 INT8](op-007.md)、[op-008 Prefill](op-008.md)，静态准备/未有新性能结果；独立私有副本，整改容器不动、无提交推送。

- op006/007/008阶段：Decode复用既有TLE显著缩小差距；Prefill大形状优于SDK但小形状未齐，radix-final错误分支拒绝；quant多个配置/行分组负结果保留，当前共享原数学helper候选待完整验证。均未更新整改容器或提交推送。另已串行并入[refactor-012](refactor-012.md)的侧聊授权PR-review记录，仅新条目未覆盖本轮数据。

- [refactor-013](refactor-013.md)：侧聊已授权的12PR非force同步最新主线并解决冲突；未动安装源码/本轮私有数值候选，远端新head尚无GPU验证。


2026-11-12 op006/007/008：仅独立回归容器内私有候选。Decode/Prefill复用已有MetaX TLE selector，无新数学kernel/公共名；最终candidate05数值边界30、真实dispatch/graph16、禁用fallback2全部通过，Black/isort/flake8通过。INT8多种launch调优未全shape达到SDK×1.05，全部量化代码已回退原版，mixedNaN参考规则错误及继承的allNaN/subnormal SDK差异完整保留。当前等待最终micro B/C/R审计，模型阶段CPU预检已过但尚未发模型请求；原整改容器与安装源码/服务不动，本数值任务不提交推送。完整结果持续写[op-006](op-006.md)/[op-007](op-007.md)/[op-008](op-008.md)，不得把micro收益当端到端改善。

候选10完成71 native通过/1原生skip、补充82算子tests/37CPU参数合约、真dispatch/graph和B-C-R20shape各3轮；最大B-R漂移3.57%。Decode6/9达到SDK×1.05，另3项仍慢约11%；Prefill1/4达到，余3项仍慢8–52%但优于baseline1.50–2.52倍。量化全部改动撤回，不称三个算子均追平SDK。tile256/1024两反例保留且恢复10，完整源SHA20b74f...。模型仍0请求，model04/commands05 CPU预检中，旧model01/02/03未启动不复用。原整改容器及本轮PR未改。

PR CI侧线见[refactor-014.md](refactor-014.md)：#1145环境依赖下载超时，未执行算子测试；需上游Actions写权限重跑。与当前私有算子候选独立，无本机GPU或源变化。

规划复盘03：几何11/12两次有结果但均退步，停止tile扫描；保留唯一数学/规范均通过的10，量化无保留改动。Prefill仍有共享scratch内canonical排序/归约成本，Decode full-valid仍约11%SDKgap；未通过真实模型前不叠新算法/编译器改动。phase当前仅micro及历史op005 Mixed证据，新的模型Prefill/Decode/Mixed代理和累计收益须由model04实测补齐，不将26–39倍短Decode micro与其他单点相加。首个证伪为sameFGVsource8rank实际canonical命中+new正式GPQA，任一无效停止BCR；通过才缩减Mixed3角色全轮。model04为相同代码的验证，不是新优化点。

诊断op006-model-long15：model04完成22请求，20短/C8正确，两个长prompt(3618/14370tokens)均output2048/finishlength/contentempty，非OOM。未进入GPQA/性能；原结果保留且自身服务已精确清理。调用accuracy-diagnosis，required minimal失败阻止晋级；不通过加max_tokens/删case/改判断追通过。新外部diagnosis15，same源码/ON/.85/TP8/graph/22精确请求/seed1234/temp0/max2048，baseline→candidate各fresh实例，完整44请求有界复现，允许记录预期断言rc1但不当correctness pass/不跑性能。两侧完整graph/8rank真实path/sourceidentity核验，原整改容器不动。执行前SHA {"diagnosis-coordinate15.py": "3ceb28be949325db6273ec19b27c778ccfc2eaa1ff0e6d82f36077ec0c790355", "diagnosis-supervisor15.py": "2da8049ab0c9c00c629fb0fd4d014e99b4d753384de04ad000e425c2cb19c028", "diagnosis-launch15.py": "627cd7c179423d1c927b692820cde87dae54bc8a380459b3020b96f810de98a3", "diagnosis-stage15-inner.py": "0f79c7957890edf1d9a22c537473bc6ea8d35d53cfbd69319d75a76d3a8137fd"}。

诊断15复现完成：baseline22/22pass，long输出62/54tokens；C再次20pass+2long空输出2048截断，与model04同症状，44请求全保留/图及8rank身份通过/精确清理。不能按预算不足处理，源差异相关已复现但具体prefill/decode/诊断器边界未隔离。下一diagnosis16三角色各fresh22精确请求：先fullC+原无observerPlugin控制，再prefill-only（C common/helper/publicprefill+原Decode）和decode-only（C common/helper/decode+原publicPrefill完整AST）；原candidate/baseline不改，仅新私有包副本，3角色统一原Plugin。66请求仅定位、不跑GPQA/性能，无模型参数/阈值放宽，无新数学kernel。实际8rank CachedOp/source身份/7capture和单FULL>=2分别核验；不以无hook的CachedID替代已取得的C内核证据。执行前SHA {"bisect-coordinate16.py": "0f076ebcb270c279cdc78af5caa8b112035ec25f1add21e16cecd19b0b897dcc", "bisect-supervisor16.py": "3dd29b573120d7fe83575489a700e80a84be22d602d921063fda2c2e77807f94", "bisect-launch16.py": "c2ee0f30bc234d74272e94ebcd8faf81c8af1f6441fecfdc51d4bceb79e36f81", "bisect-stage16-inner.py": "8626764bd327db47d25eb02b9eff507dc16525109bc46b35af7d304c5e98937d"}。

最新模型诊断：原baseline及Decode-only均22/22通过；完整候选与Prefill-only各20/22，两long2048截断空输出。新Prefill路径已隔离为足够触发边界，原语/索引消费机制仍待真实tensor定位，未发新GPQA/性能，不部署。合成实际shape的C8/8数值graph通过并不替代模型正确性；B在额外I64元数据形状出现旧编译类型冲突，单独保留。按新AGENTS5.5核验mx104 dsh入口未发现，已限域回退内置两子Agent（GPU真实tensor/CPU消费者分析），主Agent负责协调/验收。

2026-11-12 Decode PR更新优先：仅授权更新[#1145](https://github.com/flagos-ai/FlagGems-vllm/pull/1145)，精确当前head570da31的五文件最小补丁CPU检查通过，GPU28正在验证，尚未提交推送；保留Draft和全部262K历史慢轮。新Prefill仍未通过模型；baseline捕获22已22/22正确并保存真实[3618,904]/I32元数据，全部自身模型清理、8卡独立核验空闲；离线逐tensor比较排在Decode发布之后，不重复捕获或发GPQA。原整改容器/安装源码/脚本不改。见[refactor-015](refactor-015.md)及[op-008](op-008.md)。

Decode PR[#1145](https://github.com/flagos-ai/FlagGems-vllm/pull/1145)已非force更新到`9dd07431`，两生产文件/五文件最小增量，精确测试树与发布tree一致；仍Draft。29quick/15focused及支持域graph/dispatch/初始化sentinel通过，8继承输出layout失败完整保留；fixed9 B/C/R所有三轮均齐，两口径6/9达到SDK×1.05，fullvalid仍慢10–12%，原full11新33点仍全部慢SDK，全部历史/新慢轮保留，无模型/GPQA/E2E冒称。GPU28清理/8卡idle，原整改容器不动；已开始op008新40min真实tensor离线对照任务，不自动重发模型。见[refactor-015](refactor-015.md)。
