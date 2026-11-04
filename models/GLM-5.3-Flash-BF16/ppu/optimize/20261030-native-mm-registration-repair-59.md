# 20261030-native-mm-registration-repair-59 原生 ATen MM 注册边界修复

- 状态：CPU/设备及原300完整模型回归通过；原生单次163/198保留。用户授权21题统一补跑后，合并172/198=86.8687%≥86%，补充口径达标，未签发新单次全量gate。分类 `operator/replace`，当前目的为精度运行修复；服务于P1K目标及全量精度前置，不是稳态性能验收。
- 精确范围：PPU-13 / glm5.3-flash-opt-20260911 / 8011；依赖[点58](20261030-upstream-refresh-58.md)官方三库与必要兼容。

## 优化方向与瓶颈依据

点58临时RPC1200的P4096/C1/C8/C64已全部通过并停止。恢复原300后的FULL11/11、P4096/C1/C8、P1024/D64/C1通过，P1024/D64/C8于20:24:13发生sample_tokens RPC300超时，控制器已精确清理，正式GPQA零请求。20:23:07精确自有TP11栈落在Torch Inductor→FG mm_out/general_mm→Default调参bench→Triton make_hgbin等待编译。该快照含短时debugger暂停，不能把全部超时作无观测干扰的因果证明，也不将旧版本点51候选预算直接搬到新版本。

## 优化内容与适用边界

唯一候选：在当前私有安装的现有 `vllm_fl/dispatch/config/thead.yaml` 的flagos_blacklist追加mm和mm_out，沿用公共get_flag_gems_whitelist_blacklist→flag_gems.enable(unused=...)链路，执行前保留ATen原生PPU MM。没有新增平台文件、模型专属执行分支、数值kernel、配置开关或异常后跨后端重试。现有显式白名单/黑名单与append的优先级不变。

此配置影响该安装的PPU平台默认ATen MM，其他平台文件不变；专用FGV router_gemm及MoE/MLA等显式算子不等同于ATen MM，不随此候选替换。原TP16/BF16/MBT32768/maxseq64/maxlen80000/FULL_DECODE_ONLY/关闭prefix、RPC300、生产DB URL/策略与用户脚本均不变。

## 正确性与路径命中

变更前冻结原配置SHA及全树/index，确认精确服务OFF/16卡空闲、唯一安装与镜像挂载。先在独立设备进程按真实公共配置/注册入口启用FG，证明mm与mm.out保留原生dispatch表，而其他FG注册实际生效。用独立CPU FP64参考验证BF16/FP16/FP32、mm/out、转置/非连续/offset和空/不对齐边界；真实graph至少两次改变输入、输出哨兵覆盖。设备产物使用独立诊断DB，不复制/回退生产DB。再跑现有CPU相关套件及完整原300模型回归，无GDB/临时MM策略/新profiler。通过后一次198题C64 GPQA，strict≥.86，原采样契约不变。

## 性能效果

未运行ABR、无稳态性能收益数字。点58冷请求或临时1200诊断耗时不作分母；该候选先证明默认300下可运行与数值正确，再讨论后续性能。

## 决定、风险与回退

当前源码与运行现场保留用于诊断，正式分数未过，不晋级性能或宣称正式保留。数值/graph/必要回归失败即停止晋级，按精确候选SHA回退这一个YAML，保留其他用户dirty/index与上游更新。退出条件：FG当前PPU MM冷bucket搜索/编译得到有界修复，并在不排除MM的原300完整回归中通过，再移除或收窄排除项。临时工作项以本实验与点58证据可追踪；尚未代用户创建上游issue，PR硬件/新gate均待验证，不声称PR就绪。

## 外部证据

`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261030-point59-native-mm`。当前故障原始证据保留在点58根的restored-rpc-02及original300-smoke-c8-stack-v1结果；大体积日志/请求/原始回执留远端，不建history。

变更前已保存完整执行命令与SHA：bootstrap-v1.py `b5eb5cd7a3a0bc830db4c1b8640a55da290bede663f4fe8a12a46c8bea6e1530`；prepare-validate-v1.py `e18af0519e1194a4d22613422060504d7c409760b41576fa7a56e6a4cfe89824`；native-mm-device-v1.py `7fccec305e96ede778f798164749e750ea27e5b1a3de996fe0cab64c39ddcfff`。先暂存点58 commands 的point59前缀命令，再校验复制到新点59根并执行零变更prepare；通过后唯一派发配置修改/验证。保存原YAML/候选/patch与全树/index staged语义、唯一安装、同镜像/挂载、RPC300和生产DB指纹。Git index以ls-files stage及cached binary diff防止改变暂存内容，允许只读Git命令刷新stat缓存。

设备冻结12组、mm/out各一次共24次，覆盖BF16/FP16/FP32、M1/8/64/1024/8192、实际模型K4096/N1536投影及非对齐、offset、空M/N；独立CPU FP64抽样32行/32列而K完整。三组真实graph各两次更换输入及NaN哨兵。CPU与设备验证各用独立测试DB，不改生产DB。测试只验证替换路由/数值/graph，不作性能或TP16模型结论。任一失败按精确SHA只回退该YAML。

21:00:29 prepare确认原源码冻结/唯一安装、同镜像挂载、RPC300、目标OFF和16卡空闲后通过；验证控制器唯一派发PID2308847/start608103922，接下来仅该YAML候选及CPU/单PPU验证，尚无模型/GPQA请求。

21:02验证完成：现有CPU GLM/dispatch/whitelist套件495 passed/4既有skip，12组24次MM调用与独立CPU FP64参考一致，三组graph六次变化输入回放通过。真实公共configure_flaggems后mm/mm.out dispatch表仍为原生、其他FG注册变化，验证被测替换实际生效；生产DB未变、其他库全树与index暂存语义未变、16卡退出空闲。YAML原SHA `a60a6ae8f9a79ced2b3820088e4b2b874c68db833deb81a3a703c3520ad0a965`，候选SHA `fb390fbeab97553d8f251451ad5b8209151803bc6a83281c420d4d36da56e224`。尚不是TP16整模或性能结论。

保存原300完整模型/一次条件式GPQA/最终只读审计命令：`commands/model-v1.py` SHA `a4338ae13ba5f5f1bda26aee0fd14e649d72c76d4e420590bdc716c2f5abb477`；`commands/formal-v1.py` SHA `4770fcc5e6b2dd17de46e7da4a1b4761967d290f276a94665a278ca2fe05c7d1`；`commands/final-audit-v1.py` SHA `0b153068c4d5dff08dcc45b7ca0d75e43c9e4f460062078998ffc8a035b163b5`；`commands/dispatch-model-formal-v1.py` SHA `b27bddd125aa064f81913d4c792fed59edf7110ed0cde16ee7a2c39e8c72902e`。模型先原C1/C8、P1K D64 smoke、三16K边界、11答案、C64/FULL与生效配置核验；无GDB/profiler/MM策略hook，客户端900和原RPC300/MBT/脚本不变。模型任何必要失败不派发GPQA；正式只在完整模型通过的同实例以198题C64/strict086运行一次。

21:14:27原300模型控制器唯一派发PID2595095/start608187696，21:14:28正式条件控制器2595546/start608187792仅等待模型全过；原生GPQA尚无请求。测试工具已按原SHA复用并复制到点59，独立UUID缓存/198题/64并发/strict086不变，不使用旧分数。

21:30:14实例ready，身份PPU-13:glm5.3-flash-opt-20260911:3267540:608188946，FULL11/11完成。RPC核验默认300、API/Engine无覆盖；公共配置得到mm/mm_out，API白名单/替换黑名单/append/超时覆盖全为空，生效文件SHA符合候选。该证据绑定当前源码和运行环境，结合设备真实注册证明；不将其冒称16rank模型MM profiler trace。C1于21:30:15开始，本轮无GDB/profiler/MM策略hook。

21:35只读阶段核验：原300下P4096/C1/C8、P1024/D64/C1/C8、16383/16384/16385三边界全部通过，明确答案11/11通过；C64于21:34:02开始，本轮未附加GDB/profiler。该minimal-regression覆盖点58上游更新及点59配置；后续仅全部通过才按formal-gate运行原198题C64。当前不签新分数/gate，也不根据过程耗时计算稳态收益或无干扰因果倍率。

21:45:45 C64 64/64通过，21:46:10完整最小回归终态通过；本轮原RPC300，无GDB/profiler/MM策略hook，C1/C8/P1K D64/三16K/11答案/C64/FULL均过，未见RPC/OOM/非法访问。不能以本次源码与缓存均有差异的过程耗时计算ABR/稳态收益，原FG失败证据不删。现有评测容器为运行中的官方flageval-llmeval:v1（image bcefa10b…）、host network和/mnt挂载，接续同一模型实例正式198题C64预检/准备；原生开始生成仍以native-dispatched.json为准。

21:48:17原生正式GPQA已唯一开始（native-dispatched.json/controller PID2595546），198题/C64/seed42/temp1/top_p.95/maxgen60000/strict≥.86/独立UUID缓存/retries0，无补充或best-of。准备阶段两次provenance相同与preflight均通过，冻结SHA `67385d2a0bc86a70bdccef100f062fec3a34d5bb8292b27800e5f0b4edc787ab`，绑定原300的同实例3267540/start608188946。21:58只读确认仍运行，尚无原生run-record/终态分数；日志实际位于父根formal-model01-follow.log，不重复派发。

22:02只读进度为11/198（原生tqdm计数），服务health200，formal.exit/completion/gate尚未生成，未见Traceback/EngineDead/TimeoutError标记。正式进程2595546原start_ticks相符，继续原唯一任务；该计数不是准确率。当前本地YAML/差异格式检查通过，GLM记录检查0错误，其他模型既有375条记录问题未改。最终只读审计命令已保存但须原生终态后执行。

## 2026-10-31 原生终态核验与精度事件

07:56只读发现外层控制器于01:48达到14400秒预算，保留failure.json；容器内原生评测随后写出完整results/samples（文件时间03:22:53）。原生strict为163/198=0.8232323232323232，低于预冻结.86；两filter各198唯一doc0..197，共396条，21题timeout标记只是健康观察，不另设通过条件。没有生成可消费gate，不自动补跑或叠加性能优化。

按本地accuracy-diagnosis冻结事件`gpqa-upstream-refresh-59-20261031`：当前仅能确认分数低于门槛，不能将其归因为MM替换或数值kernel。原生进程退出码因外层超时未观察，不伪造formal.exit或process_succeeded记录。执行前保存`commands/terminal-evidence-review-v1.py` SHA `ff49aa4358541cd10ff18655c55737e33c15d9f85f2149d6fdaabb15b83f640b`：只核验既有结果/全部filter/冻结配置、task/data provenance及当前身份，调用已保存最终只读审计；零生成，不改原failure/分数/契约或签发低分gate。

07:59:31零生成终态复核完成：冻结输入全部SHA、原runner、config/contract、198唯一题全部filter、原题内容及原生results metadata/seed/endpoint/采样/独立UUID均匹配；当前重新采集task/data/evaluator provenance与冻结值一致。strict163/198=82.323232%，flexible68/198（不作为冻结门槛）。21个timeout标记在strict均0；usage明确达到60K的仅1题，不能将全部21题称为60K截断，也不据此确认超时机制或数值根因。外层01:48超时及未观察到的原生进程退出码保留，不补造formal.exit/run-record/process_succeeded或passed gate。原生完整结果可核验，低分拒绝门槛是唯一精度失败理由。

最终只读审计通过：同实例3267540/start608188946，三库源码/唯一editable、原argv/env/权重/tokenizer/设备与原脚本身份相同、RPC300、health200/空闲；审计无生成请求。生产DB开始55a0633a…→当前29bf36fe…如实记录，不归一化或改旧manifest；不对低分签发cache gate。`final-audit-v1.json` SHA `15eca4e1e252a0c937e57c4743db241c2a9669cf804b69d19ce4028043483165`；原results SHA `a31ebbd28ea64a791344d0f1ec1ab17d8480d6cb8d79dbff4b98e0e48f191875`，samples SHA `ecf446f69ce89e16ab78fd2746d4b35f7022b2c5ae0ea4a1803ad067b178d6f7`。汇总回执为父根`terminal-evidence-review-v1.json`。

精度事件现为门槛阻塞、根因unknown；本轮未重跑、未替换样本、未改源码/启动参数或停止服务。86%在198题中至少需要171题，当前差8题。后续先按既有usage/timeout与执行证据分类，确有定位/修复后再以原契约验证；不凭旧源码173分或最小回归宣称本轮已通过，不自动继续性能优化。

终态汇总`terminal-evidence-review-v1.json` SHA `3dcf7e90ab364a9f3664e9989b897bed0cf2e0b899781070e2acfdc2ca5c271f`；终态manifest SHA `d34787e7b91a0ebc418feeb99ab1c21b495f2c13debb6c4b488dc3fdbcc48e30`。本地YAML/差异格式与GLM记录检查通过，其他模型既有记录问题未改。

## 用户授权21题统一补跑 rerun21-01

2026-10-31用户要求将全部21道timeout标记题统一重跑并补充计分。冻结doc_id=[8,12,15,32,47,48,55,64,69,71,75,76,79,81,88,90,93,94,121,130,190]，不只选择60K题；原21题strict均0，保留原生163/198不改。新结果全部替换这21题，其他177题原样保留，无best-of或自动重复。补充分数=(163+本次21题新答对数)/198，至少新答对8题即可≥.86；仅是用户授权混合轮次补充口径，不伪造成新单次全量C64 gate。

使用本地accuracy技能minimal-regression显式21题范围，bundle SHA `1ed06a57f1f6e1ef39fb7fd872f579122b098a18f0255ade0a1160d6432c2b66`。沿用原任务/data/model/endpoint/seed42/temp1/top_p.95/maxgen60000、API客户端14400秒及0 retries；C64上限/实际最多21并发，独立UUID响应cache。原MBT32768/maxseq64/TP16/BF16/FULL/RPC300/源码/启动脚本/生产DB URL与策略不改，不重启停止服务。

执行前保存`commands/rerun21-v1.py` SHA `90671689e7266494071b325e8a1008107766c63cf34eab13f00e22f6b19d593d`，参考已验证点43统一14题补跑原命令但重新核验当前身份、原runner和provenance。唯一子目录`rerun21-01`；先零生成prepare并检查冻结请求契约，再唯一dispatch到原生lm-eval --doc_ids。规划21600秒，避免以4小时短外层timeout杀docker exec而留下未观察原生进程；API超时/生成参数不变，不自动重试。实际是否已请求以dispatched.json/native-start.json/native-process.json为准。

只读预检已确认当前原实例3267540/start608188946，原argv/源码/thead及RPC300，health200、running/waiting0，补跑目录不存在。结束必须验证21唯一题/两个filter、原doc/target/arguments、冻结task/data/生成参数、其余177题不变及当前实例/源码/环境/DB策略；原生结果、合并样本与summary留远端，原失败证据不覆盖。

17:01（Asia/Shanghai；评测容器09:01+00）零生成准备通过。request-contract SHA `ba678bbe203666577320bcf64a9d6f4cc34dafdfc4e7b39f392dd179db651bfa`，prepared SHA `a95b33ad2165dc92b12e56bdfab8ec5cab31ffc8ce02df0ca4d606caef2b9310`，独立run_id `3bcdef9211bf463fabb27e00b4873fb5`；原runner SHA `82cf6e8304cb6f9eb8ca48fe4055f6bbb2054a7b6a90d56de3d6b7a08e90c61e`，cfg/ID/采样/21题过滤已核验，当前无dispatched/native-start。下一命令仅运行已保存SHA命令的`dispatch`模式，一次原生调用；禁止重新prepare或重复dispatch。

17:02:52唯一派发补跑控制器PID1906230/start615318214，回执`rerun21-01/dispatched.json`。控制器先复核同实例/空闲与冻结契约，再在原评测容器原生执行该21题；不会重复派发，不重启模型、不改RPC/MBT。当前尚无补充分数，实际开始以native-start/native-process回执为准，终态以score-summary及completion的身份/证据valid字段为准。

17:03:26原生21题开始，评测容器PID62609/start615321598，native-start/native-process回执完整。17:04只读0/21、health200，未见Traceback/EngineDead/TimeoutError；这是本次补跑的真实开始，不是重复全量198题。原生输出仅在远端run.log/独立results与cache中，尚无score-summary/completion。

17:07:48只读跟进：服务已接纳21个运行请求、waiting0，控制器PID/start匹配且存活，原生0/21尚在生成；未见Traceback/EngineDead/TimeoutError，暂无补充分数。当前累计token指标含先前完整评测，不将其当本补跑吞吐/耗时结论。本轮无需重启、改参数或重新发请求，继续唯一原生任务及既定终态合并。

18:11:31用户查询进度：只读核对原生3/21，尚无results/samples/native-exit/score-summary/completion；原控制器PID1906230/start615318214仍存活，health200，run.log无Traceback/EngineDead/TimeoutError。当前不能给出21题最终答对数或补充后精度；继续原唯一原生任务，未重发请求/改采样/源码或服务。

18:12:20当前API仍3267540/start608188946，18个请求运行中、waiting0，累计生成计数已高于17:07观察；这说明仍在处理，不能以客户端3/21误判整体卡死。累计计数包含旧请求，不作为本轮性能或精度分母。

## 2026-11-01 终态查询：补充口径172/198达标

补跑于2026-10-31 20:12:09（Asia/Shanghai）结束，原生21/21、退出0，控制器退出0、completion.valid=true、无异常。21题答对9题，原21题均0，因此全部统一替换后的strict为(163+9)/198=172/198=0.8686868686868687，高于预冻结.86。其他177题原样保留，没有best-of、补到过线或改变阈值。仍7题timeout标记，空/乱码0，不作为附加精度条件；不自动再次补跑。

终态控制器核验同实例3267540/start608188946，源码/argv/env/权重/tokenizer/原RPC300及镜像挂载相同；DB正常写入29bf36fe…→1cb5d4bb…，起止值保留，不改旧manifest或伪造绑定。原生单次163/198、原4小时外层失败及其完整原始结果继续保留。172/198是用户授权的混合轮次补充评估，不是新单次198题/C64评测或新正式完整gate，无新性能收益/四场景验收声明，不自动继续优化或提交推送。

关键证据均在同根rerun21-01：score-summary.json SHA `07c79e91dae36ccc55f4eab9e55c55c9411cc16abadff069e979e2f9328864b5`，completion.json SHA `e31a41dc74b2068476124add38515fd197bf20952671331768fb3558d24b369a`；原生results SHA `0dfbaa368c5c1ada44a54f2fb22751089721f33037fedc1cf9a22a8c04b4a2ba`、samples SHA `2e1457a5d027d9483fa5b44802c4b14d977e9887cddda571324f3a02c1d3677a`，merged-samples.jsonl SHA `82d9766d05251507427b0c4ec5eff8bd48e540c832f4f19d511a25557c5bae03`。11-01只读确认当前health200，原补跑控制器已退出，未重新发请求。

11-01 09:24:18独立零生成复核：21题42行、合并198题396行均唯一完整；当前21题每filter全部来自本次新样本，其余177题逐行值完全不变；原doc/target/arguments、全部冻结SHA、task/data/metadata/seed/采样/独立响应cache均一致。新增答对ID=[12,32,47,48,55,64,90,93,121]，剩余timeout ID=[8,15,71,79,81,88,130]。当前仍原实例3267540/start608188946、源码/原参数/RPC300/thead匹配，DB仍1cb5d4bb…；终态runtime-after SHA `e572325de41441c2cc50f4e27a66eb71e20db72298db78ca48ec243f288a514e`，service-after SHA `ea9714fb6d2b75f476bdfe346032528b8abad28e77dbdff9612b5c65fda6d18e`。补充计分172/198通过，无额外请求/代码或服务变更。
