# op-001-mixed-stall-localization：定位 prompt 填充与 Mixed 慢轮

- 状态：diagnosed_partial；分类：framework（诊断，尚无代码候选）；当前正式目标 P1024/D1024/C64/N128。
- milestone：P1024/D128/C64/N128，保持输入、并发和请求数，缩短输出；结果不冒充正式目标。

## 优化方向与瓶颈依据

用户历史 P4K 候选第二轮250s、其余约143s；旧对照也有第一轮290s。新服务保持公共MoE与既有buffer复用，在冻结seed/采样和三轮预热下，P1K milestone三轮耗时20.905959/24.556033/52.198794s，输出吞吐783.7000/667.2088/313.8770 tok/s。三轮中位ITL50.2948/50.2373/50.3215ms，平均TTFT2061.69/2886.69/12361.78ms。稳态窗口波动70.42%超过5%，原生工具停止且没有正式测量轮；基线为incomplete，不事后删轮或改判。

Prefill视图是TTFT与准入/排队代理；Decode视图中位间隔接近，但TPOT包含Mixed停顿；Mixed视图表现为长暂停，并非所有token都等幅变慢。原服务日志慢区间prompt填充非常缓慢，尚未证明是编译、主机、通信、GDN、Attention或MoE。

## 优化内容与适用边界

本点先做`inference-profiling` capture→analyze，代表场景P1024/D128/C64/N128，两rank、最多24个engine iteration，记录shapes、关闭stack/memory，前端不采集。使用维护版vllm_profile.py，两轮预热、一个采集轮；保留完整客户端与worker证据。CPU/GPU时间按类别及可靠iteration/shape边界拆分，未知边界保持unknown。Profiler耗时不计为端到端收益。

用户限定本轮不得通过关闭FlagGems算子优化；保持当前服务FlagGems接入/白名单，不把vendor/native替换当作候选。后续只考虑不关闭算子的框架组织调整或FlagGems/FlagGems-vllm自身operator/improve。

模型/source/采样/graph保持现有基线；基线准备已追加有界profiler配置，仅在采集窗口启用。本点没有修改MoE buffers、算子或新增其他推理参数变量。下一步只有在trace收敛后才分配实现实验，按最窄扩展点选择配置、Plugin或Gems；vLLM源保持只读。

## 正确性与路径命中

当前source926a5544与初始快照一致，C1/C8十题请求健康通过；两worker分别观察到64次mcGraphLaunch，graph护栏通过。Sanity输出1024token截断只作健康观察，不作为正式精度分数。GPQA198题来源两次一致、threshold0.8、正式预检通过，正式198题GPQA已启动，分数待测。

## 性能效果

只有上述预热诊断数据，没有candidate/revert和稳态测量。首个客户端预检30s超时未发请求；120s探测预算版本本地工具测试199项，3项可选测试跳过，之后正常执行本轮预热。工具变化是控制面修复，不计模型优化收益。

## 决定、风险与回退

进入baseline-recovery并停止基于失稳结果的性能晋级。保留所有三轮；不增加一组改动后把慢轮自然消失当作收益。采集失败或rank/phase覆盖不足时保持incomplete；最多一次有依据的采集修正，避免无限重试。后续实现必须有同配置baseline/candidate/revert及数值/graph回归。

## 外部证据

远端目录：`/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current`。

- `results/performance/anchor-p1k-short-001`：客户端预检失败，零测量轮。
- `results/performance/anchor-p1k-short-002`：三轮预热及失稳回执，零正式测量轮。
- `accuracy/graph-replay-check.json`：两个rank实际graph replay及trace SHA。
- `manifests/anchor-service.json`、`manifests/anchor-runtime.json`：当前绑定身份与初始源码快照。
- 本点profile契约和维护版命令将在`commands/`保存后执行。

## 已采集 trace 的阶段证据

两个rank覆盖完整，SHA写于原生diagnostic.json。24个实际GPU模型迭代标记拆为1个纯Prefill（M1024）、8个Mixed（7次M8192、1次M7393）和15个Decode（1次cached1、14次cached64）。模型外采样等活动单列，未把累计kernel时间当作关键路径。Mixed中MoE占kernel活动约35%，Decode约42%；纯Prefill首步rank0通信等待显著，不能据此泛化Prefill稳态。当前Mixed采集的平均TTFT1.94s未重现此前12.36s停顿，profiler停止/导出导致端到端测量污染，47.03s仅作诊断。

本次可以选择MoE做限域实现调优；不能认定它导致随机慢轮，也不认为慢轮问题已解决。GPU模型窗口无超过10ms无kernel区间，不能排除窗口外主机停顿。接下来op-002先用真实阶段shape做有界tile扫描，同时保留慢轮定位。

- 原生诊断：`results/prof-001/qwen36-35B-begin-novllmconfig-addattention-fusedmoeopt/diagnostic-d859a56768364b21a91e28fbc373b057/diagnostic.json`。
- 阶段结果：`results/prof-001-phase-analysis.json`，初步类别/空闲区间：`results/prof-001-analysis-initial.json`。

## 历史精度阻碍与决定（30000上限旧轮，现已由65536达标gate解除）

原服务未改动，完整GPQA strict-match为149/198=75.2525%，低于冻结0.8；198唯一题及两个filter/结果provenance验证通过，未签发gate。本点候选未进入当前服务，不能归因于尚未部署的优化。暂停新增性能改动，先按inference-accuracy-diagnosis核验。API原生198响应中30个finish_reason=length且completion_tokens=30000，其中25没有原生answer标记；168个正常stop都有标记。这支持输出预算阻碍，但尚未证明扩展预算会达到80，不把健康症状单独当作score失败规则。

当前新65536预算proposal只改max_gen_toks，保留全部198/严格metric/0.8/其他采样/模型source。两次provenance一致、命令和contract已准备，尚未执行；等待用户确认变更已冻结契约。原低分及所有历史原始数据保留。额外发现12题选项被原生helper去括号改写、171题出现重复选项；未自行改helper/filter/数据。

证据：远端accuracy/anchor-failure-evidence.json、anchor-output-budget-diagnosis.json、anchor-evaluation-diagnosis.json；proposal见accuracy/proposed-g64k-{config,contract}.json和commands/proposed-g64k-full-command.json。

2026-10-14：新anchor精度164/198达标后重测P1K/D128/C64/N128 baseline003。3warm全部128成功、各P131072/D16384，原生轮次验证均通过；duration20.1208/29.9917/20.3598s，吞吐814.2816/546.2844/804.7245tok/s，spread33.303%>预冻结5%，0admitted测量轮，native record失败/业务incomplete。第二轮106个client ITL>1s、max4.6387s；第一/三轮0个、max0.4730/0.4761s，中位ITL49.86/50.63/50.71ms。这收敛到偶发长间隔，尚不是纯设备kernel时间或CPU/GPU根因证明。全轮和长间隔保留，先no-stop低开销定位与三阶段基线；不丢慢轮或以两个快轮报收益。证据results/p1k-baseline-003-terminal-20261014.json、native run-record SHA ccbd478116e5e3064b4872627e8eb9f0934fe48cf7d3501d070c503eba96e91d。

2026-10-14 12:01 CST：不停止服务的阶段基线契约已冻结，Skill mode=baseline，parent P1024/D1024/C64/N128。Prefill为P1024/D1/C64/N128（仅消除decode loop，保留队列/网络/调度/首token采样），Decode为P1024/D512/C64/N64（单波请求突出循环，保留初始prefill与fill/drain）。各自3warm/window3 spread<=5%/3measured、600s/round，同当前服务/FG/采样，不与不同workload算加速比。正式目标未缩减或完成；所有原始计划/比较/preview位于remote results/phase-*和logs/phase-*，metadata manifests/phase-baselines-contract-20261014.json。

2026-10-14 12:11 CST：按当前原生client源码验证start_times+ttfts+累积itls的重建方法，baseline003第二轮长间隔收敛到三簇：相对起始0.682–1.861s（8请求）、11.262–15.904s（42请求）、19.097–23.695s（56请求）。后两簇同簇起止分散仅约3–4ms，说明请求流出现集中暂停，尚不能区分服务执行、设备、客户端接收/CPU或网络；不能直接归因MoE/buffer。证据results/p1k-baseline-003-gap-overlap-20261014.json、manifests/p1k-native-client-timing-source-20261014.jsonl；命令SHA b7dec85b2887b8eba8c7c2dd7df0ef933cf2f57f2000eca34c2578fd56ca423b。Prefill已启动4177835/start489043763，04:07:59UTC，启动前全源码/配置/模型连续性与原生精度gate再次通过。

2026-10-14 12:14 CST：Prefill三轮128请求/131072输入/128输出全部原生验证通过，duration7.9460/7.1048/7.1064s，total-token throughput16511.46/18466.30/18462.34tok/s，p99TTFT4232.05/3680.65/3677.05ms；warmup spread10.59%>5%，0admitted测量，native check_run按失败拒绝。不能丢首轮或放宽门槛。terminal results/phase-prefill-terminal-validation-20261014.json，run-record SHA e6eaa967082415d5371f60c05d5cb2ce83771ed85ff9021a4e8bc2f1526649b5。随后Decode在全源码连续性和精度gate再次核验通过后启动4181414/start489078923，04:13:50UTC；未改服务。

2026-10-14 12:37 CST：Decode终态三轮64成功/65536输入/32768输出、原生全部验证通过；duration30.4701/56.6803/52.2610s，output1075.42/578.12/627.01tok/s，meanTTFT2240.56/22408.47/18857.93ms，medianITL52.73/52.46/52.59ms，maxITL.4715/9.0929/9.3810s。spread79.31%>5%，0admitted测量。来源/source/model/env/profile-off终态复核通过；run-record SHA ff0031b6509c4f555a67d5ca964fd9aa7a92b4a3a76e4f704e99b7b4afdc4758。CPU间隔并集在r2初始.693–27.801s，r3初始.427–18.810s和后段21.122–25.700s（57请求同暂停）；不是单kernel设备时长。全部9个native轮次日志和server末段无queue/OOM/异常提示，私有Stream失败与端到端暂停关系不明。

review-003已完成，保留anchor/无累计收益，最高优先级捕获集中暂停。按Profiling Skill capture冻结prof-002 P1024/D512/C64/N64，warm1+profile2、每capture最多24iterations、期望TP0/1两次共4新worker traces，phase按实际model marker/shape分InitialPrefill/Mixed与EarlyDecode，未知仍unknown。原生dryrun已核且再次gate/source连续性通过；host controller25069/start489217942，于04:37:00UTC启动，日志logs/prof-002-20261014.log，manifest manifests/prof-002-controller-20261014.json。命令SHA 3b9be96619aab3e9f47adad08ba3ec6ad0a87b7b5894686b5cf59a8f9088fc09。profile时间不报收益；missingrank/未捕获暂停保持incomplete，最多这两轮，不盲重复/不停止服务。

2026-10-14 12:47 CST prof-002终态：native diagnostic UUIDa5b11bfd6f8046c6b32b094d19c4896b三轮均验证通过，两轮共4新trace SHA/parse/rank通过；各rank每轮24step=1Prefill/8Mixed/15Decode，15次mcGraphLaunch。设备窗口4.66–4.72s，未见known kernel/memcpy/memset union内>10ms gap；最长Mixed span约460–473ms，最长单copy/event-sync/memcpy约270ms。原4–9s失稳没有被复现，CPU累计copy5s可重叠，不能当criticalpath或根因。两profile轮客户端58.95/59.04s，64请求共同在4.752/4.800s开始暂停至33.25/33.22s，单长间隔28.50/28.42s；它紧邻24step停止导出边界，属于profiler扰动，不能替代无profiler慢轮解释或收益。后续不重复同一首24窗口；先冻结完整时间线低开销CPU/driver观测或延后capture控制方法，再做新假设实验。

终态source/模型/启动env/精确服务实例再次核验通过，manifests/g64k-post-prof-002-continuity-20261014.json，04:45:35UTC，profiler OFF/API0；原服务和全部Gems路径未变。analysis results/prof-002-phase-analysis-20261014.json、export context results/prof-002-export-context-20261014.json，raw/traces继续留远端。当前formal accuracy仍有效anchor、最终performance incomplete，无部署改动或累计收益。本地git diff --check通过；仓库全量records审计被其他案例既有链接/进程产物迁移债务阻挡，本次不修订其他案例、不删除证据。

cpuobs002实施前：当前service905636/birth489464369映射hostAPI82533，EngineCore82992/ns905907/birth489468142，TP0/1host83365/83366/birth489470994；CLOCK_MONOTONIC/time namespace一致。旧cpuobs001从未执行且旧PID作废。先20s/5Hz纯CPU读取/proc（aggregateprocess CPU、main-thread schedstat/wchan/syscall/ctxswitch）和1Hz既有metrics/cgrouppressure，0生成、0GPUquery、无ptrace/stop。测量前冻结observerCPU<=.05core、p99sample<=20ms、missed<=1%；不通过不启动完整测量/不事后放宽。主线程采样不证明所有线程或设备criticalpath。observer SHA507eeb9b32b4b4437dbae2914076340f1c6c669884e87ba21d959631d695c324、pilot-config SHA20a7a2e115180b3e7402bbcbe8d132f48393a41f896d8be6b07c10751b68ea0d。完整nativeperf仍须新plan/comparison、native dry-run与当前实例/gate/源核验；尚未发P1K请求。

cpuobs002纯CPU20s pilot通过：100samples，CPU0.008406core、p99sample10.325ms、missed0/metrics errors0，全部在预冻结准入内。观测本身可用但完整P1K测量未启动；acc003私有标准回归失败后只继续诊断，不发新的性能请求。无source/FG/服务变更，原native计划与5%阈值保持。

2026-10-14 GDN当前版本恢复：先acc004新fullgate，随后使用新冻结gdn-p1k-cpuobs计划，不复用历史namespacePID。已完成当前API/Core/TP hostmapping与原生dryrun，测量尚未开始。请求时间线CSV未提供，不能用summary替代native详细结果；每轮保留、不放宽5%稳态准入。

2026-10-14T14:39:43Z客户端身份wrapper纯CPU6检查通过，原生CLI逻辑未复制；exec前写独占identity文件，重复启动/契约和来源漂移先拒绝。远端commands/gdn-cpuobs-native-identity-20261014.py SHA318c175d3c0cb5df9226698fdca7de887af5738251e4ca4b0471cb696c82e9d5；results/gdn-cpuobs-native-identity-smoke-20261014.json是占位执行协议证据，非E2E测量。acc004仍运行，observer配置/controller与真实native identity contract待gate后fresh核验，0新性能请求。

2026-10-14T15:40:14Z新同源GDN精度gate通过后，已启动原生baseline gdn-p1k-cpuobs-001（host supervisor562770/birth493197277），真实native client namespace963425/birth493197384。运行入口为原生vllm_perf.py，identitywrapper只记录身份后exec；FG/clientplugin保持。冻结P1024/D128/C64/N128/temp1/ignoreEOS/seed42/range0，3warm/window3spread<=5%/3measured/600sround；scope为P1K正式父D1024场景的mixed milestone，非四场景formal或收益。独占GPU6/7仅435799/800、APIidle/currentPID/sourcefiles12252/gate再核后才发流量，没有source/server改动。

observer代码SHA507eeb9b32b4b4437dbae2914076340f1c6c669884e87ba21d959631d695c324，当前config SHAc4d00bca7be2250c92a4bb0b71853f76c84dfbb96c666ac1e46c8b7f150c3aeb；launchcontract SHA0ce6082defb9480523b5e290477017eefa80ae8b39ac686ef453db22f1c3858c，supervisor SHA1cd9b206ee1ec0cbb1eaaffa4e9f7f365d19de54727023cd4319c01ede37fd6a，启动script SHA1179a9e762d6c2348d8c67f849a4d1cd744f17a2811c7cb1000c2686a72813d2。只读monitor SHA56d63ea9923fe6ef0fbb974fd1ab9fe37f9ff4342bc1f4d0bfd52f73d714d402。真实负载overhead待终态CPU<=.05core/p99<=20ms/missed<=1%检查；main-thread样本不当设备criticalpath，不能将client初始化或旧queue故障直接当慢轮根因。

review009在acc004终态决策边界复盘：GDN当前组合新全量精度债务已解决，累计E2E收益仍未证。唯一当前首要实验为已运行gdn-p1k-cpuobs-001，等native稳态/轮次与observer实际overhead和时间线关联；不从旧profiler首24steps或privateStream故障推出慢轮根因。第二私有samplerM1FP32负边界/完整benchmark（需增量迁移到当前GDN，不替换旧整包）；第三MoE真实routing，均延后。新Prefill/Decode阶段证据、直接replay计数、四full与A/B/R仍缺，acceptance保持incomplete。下一复盘由P1K终态/准入失败/热点归因触发。

2026-10-14T15:44:40Z gdn-p1k-cpuobs-001已终态：native_exit1，run-record failed errors=[Errno28 No space left on device]，rounds=[]，client-probes.json 0bytes，未发任何性能请求/无预热或admitted measured。observer_exit0，81.20s/406samples、CPU.01298core/p9911.664ms/missed0准入通过，仅覆盖clientpreflight不宣称model-load overhead通过。全部原生失败与观察保留，不重放原run-id/不取快轮。

只读容量定位：public-flash NFS100%/显示可用约1.2GiB，case内首个4KiB写入即errno28/0bytes，排除了“只是大profile文件写入”假设；/tmp/rootfs/shm/inodes均有空间。只能证明NFS案例写入失败，具体quota/server机制待管理员，不归因GDN。/data已有同映射RW挂载约28TB空闲，拟议新暂存目录/data/qwen36-35b-e2e-staging/20261013-qwen36-35b-metax-e2e-current未创建，已询问用户是否允许改产物目录或先释放原位置（AGENTS5.3）。

review010把恢复可写产物路径放首位，operator方案不叠加；旧001与所有旧失败保留。当前API952702/birth491055395继续运行，源码/FlagGems/服务参数本轮无变更；新GDN82.8283%gate保持当前已核身份。native/observer已退出，automation暂停等待存储选择。后续获准后新独特run、fresh gate/source/idle/GPU6/7与容量检查，不修改旧契约或重新GPQA。

2026-10-15T01:48:17Z用户指出原目录df现有22T可用后重新核验：host/container可用约23.18e12bytes，原case内分别精确4KiB/64KiB/1MiB写入+fsync成功，API952702/birth491055395、boot、args/selectedenv仍匹配已评测实例，APIidle。原存储障碍已恢复，之前4KiB目标写入errno28证据保留，不能用当前df反推当时未失败；未定位谁释放空间或具体NFSquota机制。无需/data方案、未创建暂存目录、未清理文件。

新gdn-p1k-cpuobs-002准备完成，原3warm/5%/3measured及P1024/D128/C64/N128口径不变，新唯一run与20261015控制文件；原生dryrun/gatecheck通过、10GiB空间headroom守护。恢复已授权优化，失败001不重放/不覆盖，下一步fresh source/gate/资源核验后启动002。

2026-10-15T01:50:21Z fresh四repo12252/source/PIDbirthboot/selectedenv/gate/idle/仅GPU6,7指定worker守护通过，已启动新gdn-p1k-cpuobs-002，host744934/birth496857987。客户端FG与graph/白名单不变，无source变更/重启；native+observer使用20261015新配置和日志，原失败001全部保留。launchcontract SHA89923e4ff484398cc53af9ae290b67bb4c34d3ed6bc01b8f85b91ccba9279e83，startscript SHA1bb37e9f5dd3aeba642ca8f89c62474b37eef21e03373f93917cf3bc320f42ff，monitor SHA3ed04fd961477de5caff0823e53f09651c9a0a7d4702e8f13bca68772d6302f0。恢复原每30分钟跟进。

2026-10-15T01:53:39Z只读进度：002 supervisor仍alive，原生clientidentity964014/birth496858097，API64running/0waiting，已越过此前ENOSPC的client-preflight阶段进入原生负载。run-record未终态，不能声明steady/admitted或收益。原每30分钟automation已恢复ACTIVE。

2026-10-15T02:01:38Z 002终态：native complete/check_run通过，6轮各128success/0fail，131072input/16384output；observer500.20s/2501samples、CPU.01459core/p9912.08ms/missed0/errors0通过。3warm输出663.03/667.23/653.06tok/s，spread2.136%通过；3measured295.87/808.22/664.34tok/s，duration55.38/20.27/24.66s，TTFT13.31/1.88/2.08s，TPOT112.71/64.52/80.22ms，maxITL8.93/.47/4.69s。测量spread77.12%，projectsteady结论incomplete；native验收证明完整有效证据，receipt passed_baseline_only不代表稳定性/项目通过。不丢首个慢measured，不把D128与用户D1024的1100tok/s直接算回退。

review012关键定位：native start_times+ttfts+cumulativeITL与同namespace CLOCK_MONOTONIC CPU观测对齐，常见56-58请求共同4.53-4.69s停顿内，两TP主线程约3.0-3.4s在do_wait/syscall61(wait4)，主线程runqueue近0；API/nativebench多epoll，EngineCore多poll。停顿末端有6-8首token，与batch/新请求处理有关，尚非设备阶段归因。等待子进程是证据，运行时编译/缓存是优先假设，具体子进程/算子仍未确认。旧observer只捕捉nativeclient后代，未保存TP瞬时childargv；事后TPchildren空。因此下一步仅扩展CPUobserver捕捉自有TP子进程身份/argv/生命周期并关联wait4，不先修改GDN/MoE或归咎driver。

分析commands/analyze-gdn-p1k002-cpu-timeline-20261015.py SHA0324bac283aa210693fef810777b677925f601d7fc9c36f1b2e7360dc24b9197，results/gdn-p1k002-cpu-timeline-analysis-20261015.json。run-record SHA90921a313f4349642e4df3148d2ac30cf3305de604874bc58108d820db3d64e0，observer data SHAa999e9a0da760b8b0a9a8a91b6ca25098130edd749c6e406ecedc45b64ac5da2。compile-facts v1因目标无名triton distribution元数据而utility失败，0请求；v2 find_spec不执行包、读取缓存源码/指定env成功，未观察到强设TRITON_ALWAYS_COMPILE，TORCHINDUCTOR_CACHE_DIR=/tmp/torchinductor_root；事后事实不能代替停顿时编译器证明。本次未部署source变更/重启服务/启动新GPU实验。

2026-10-15用户明确要求继续抓停顿子进程/编译命令并确认预热后编译条件，保持FlagGems。新观察器cpuobs003 SHA6e7953a03232ef64f950d1e77a683a5cf0854590b535f15a0bfe0fb02b3c31aa，在既有1Hz coarse收集本服务后代，记录PID/birth/PPID/exe/选定compilerargv及wait4目标PID；不采完整env/syscall地址，不ptrace/GPUquery。仅编译输入文本最多4×64KiB/child，总16MiB片段，保留prefixSHA与原size，不把prefix当全源hash。

纯CPU20s pilot-v2：6项协议检查通过（cgroup/timeNS后代、compilerargv、父子关系、wait4目标匹配childnamespacePID、源码前缀、开销），CPU.01606core/p9916.77ms/missed0；synthetic stub不是真编译/模型/GPU验收。v1 actor wait(timeout)为WNOHANG，不能测试阻塞wait4，保留失败；v2只修syntheticactor为固定4s阻塞wait，观察器SHA未改。prepare003原生dryrun/gatecheck通过；独特run-id gdn-p1k-compileobs-003、launchcontract SHA47e00d905ed6a2f802ec89d0466f93ea108fe8b918d1dc8641fa00692c66a063，拟按相同口径一次诊断，先fresh source/gate/idle/6,7独占。未部署模型改动，不重跑旧002，不追加未证kernel方案。

2026-10-15T02:14:56Z已启动003原生baseline诊断，host supervisor801480/birth497005554，native namespace971215/birth497005664。fresh source/current gate/idle/仅6,7本worker核验通过；新observer/compilerinputs已启用，最大4200s，source与服务无变更。monitor SHA263077611f82309751299981bfba36152016368f82d0bb9849e622ba408e9044；02:17:29UTC仍running，尚未发现compiler事件，不能把没发现当未启动或编译假设通过。目标容器rg缺失的只读sourcecontext utility失败保留，改Python有限regex成功，不安装依赖。

003终态：三warm各128成功0失败，输出787.373/808.199/664.576tok/s，spread18.2408%超5%，native failed、0admitted measured，不重复。observer.01594core/p9913.41ms/missed0通过。第三轮57请求最大共同4.596s停顿实际捕获双TP wait4→shell→mxcc --fatbin→lld，LLVM/cached LLIR证明flash_varlen_fwd_d256_tn_kernel；非GDN/MoE归因。154cachekeys优化TTIR/编译选项相同，后续见[op-005-attention-compile-key-normalization](op-005-attention-compile-key-normalization.md)。终态/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/results/gdn-p1k-compileobs-003-terminal-20261015.json；run-record SHA3671b10d55a86b6d933fb0eb6a14fb18dd70fa843b3f0ffd7811076ce3d54c7d。所有轮保留，生产无改动/无重启/无收益。

2026-10-15 review019：完整P1K006已结束，4warm稳定后r6再次捕获自有TP编译；12rootmxcc=8SplitKV attention+4moe_align_block_size_stage1，13请求共同8.90094s/TPwaitchild6.60与6.40s。三测量1133.427/991.227/1146.247tok/s、spread13.677%>10%，incomplete。所有轮与原始输入保留、源/gate无漂移；详见op005 review019。下一步CPU解析真实SplitKV参数和MoE函数owner/输出bounds的constexpr，不重跑006/扩大预热或关闭FG。

review020：残余编译已定位为边界SplitKV的TAIL_ROWS和Gems-vllm MoE stage1两mask长度的值专化。B13/21 prefix/tail各IR仅仿射workspace stride不同；MoE两真实LLVM仅两个mask界限不同。Q_TILES/NUM_SPLITS仍有语义，不能固定。计划op006/op007为独立私有验证，无生产改动/新GPU测试；详见op005 review020及独立规划文档。
