# accdiag-017：GDN索引64位寻址修复与仅8010受控回归

2026-10-18后续组合正式结果：[acc-015](acc-015-full-gpqa-current-i64-qsa.md)完整198题164/198=82.83%<.88、failed-score/no gate。017 i64修复保留且实际generic32884、stride102400、i64偏移3367321600/storage合法，packed32775；未见索引/state/nonfinite/新非法访问故障，仍有22无final（11提前EOS/11个60K）和12其他错答。不能据此宣称全部精度问题已由i64修复或归因该修复；完整source及服务前后相同，token/日志已冻结。原heartbeat PAUSED，无新重启/推理/修改；正式失败阻止继续叠加性能优化，等待诊断方向。

后续组合终态（2026-10-17）：[acc014正式评测](acc-014-full-gpqa-qsa-m16-i64.md)176/198=88.89%通过0.88，gate已绑定当前i64+QSA M16带诊断8010并复验有效。实际generic索引36088及packed设备索引36081已覆盖，未见新illegal access，但仍有7条reasoning-only（6条60K截断、1条24token提前EOS），因此不宣称输出健康已修复或索引缺陷解释全部旧故障。gate只证明组合正式分数，不覆盖无埋点/单变量精度或性能。旧017局部记录不改写，monitor已暂停，无额外请求或服务操作。

后续acc014正式运行观察（2026-10-17）：当前i64实现真实generic索引已达到36088，合法storage/无记录的非法访问；但doc178出现24token reasoning-only后直接EOS，说明输出健康症状尚未消除，不能以索引地址修复宣称reasoning-only已解决。8rank现有状态/日志/原回复及token已冻结，根因未隔离，详见[acc014](acc-014-full-gpqa-qsa-m16-i64.md)。旧局部017终态事实不改写，无新受控请求或服务操作。

## 授权、假设与边界

用户2026-10-16明确授权修复索引64位地址计算、仅恢复8010做受控验证、保留索引/状态/token，不影响其他服务，禁止全量GPQA。使用`inference-accuracy-diagnosis`、`key-operator-analysis`，精度操作模式明确为`minimal-regression`，不是formal-gate，不测性能/不签gate。原acc013危险index23520、i32×102400溢出现场及此前所有原生分数/故障证据保持不变。

主要变量：FlagGems通用index/index_put生成器的**加载索引先提升tl.int64再乘stride**，不改变传入index dtype、state布局、清零语义、调度、graph模式、采样、权重或vLLM。当前gather/scatter源码SHA分别88faa12ea63a30663cd155f5b8097aece39e6dffe5d130897921c28f99fc36cd与acf250823e7afd93da643d62c6aa1614703086ad8d26b514540c5a83e03396f2。

只在优化容器未挂载的私有`/opt/qwen38-accdiag017-i64-20261016`从原私有16副本复制；保留原16、原Plugin/Gems工作区和所有共享源，FGVLLM/vLLM只读。诊断guard必须核对实际修正版源码SHA后识别有效64位地址计算，仍记录“若按i32会溢出”的反事实偏移，保留真实index/storage/重复slot/mismatch/nonfinite拦截。首次成功跨边界的gather/scatter输入输出与state另存，不把正常跨界当异常，也不只绕过guard而不修kernel。

## 冻结验证范围

1. 先CPU源码/生成代码检查；不对已知不安全旧kernel发起大索引内存访问。用安全的“仅计算offset、写到小输出”的算术探针比较旧i32/fixed i64，与CPU整数oracle对照。
2. 恢复前在空闲物理卡8做算子最小回归，卡0–7/8035禁用。资源门禁必须确认无其他使用者、空闲内存足够，最多占卡8显存的一半；覆盖真实FP32 pool shape/stride/storage_offset、20971/20972/21845/21846/23520/末合法行、int32/int64和小池/空索引/stride/邻接保护、gather→clear→scatter、graph capture及至少两次changed-index replay。CPU/narrow合法行引用逐元素或逐位对照，不能只验证“没崩溃”。不通过则不恢复模型。
3. 算子/IR验证通过后仅恢复8010原argv/env语义，切换私有源码及独立构建缓存/证据根；保留TP8/物理8–15、BF16、80K、FULL_AND_PIECEWISE、capture sizes与blacklist。8035前后精确身份校验，不操作其他卡或服务；不存在8010实例时不发kill/stop，不重启容器。
4. 模型请求总上限128、并发上限64、零重试；同一冻结prompt/seed1234/stop/temperature1/top_p.95/top_k20/min_p0/presence0/repetition1/max60000，返回原始HTTP bytes/完整token IDs/prompt text。顺序为2条C1 doc2、8条固定C8、110条原C64持续补位、排空后8条C8固定目标，以观察分配池复用后的大索引。8目标为142/144/149/155/151/0/1/2；按原计划payload复用，不按答题对错挑选，不运行198题原生formal入口。
5. 首个真实异常停止补位、在途仅取证，保留每rank索引/mask/storage/slot/request/graph、selected state与token/EOS，禁止自动重试/再恢复/扩范围。边界若只在算子微测覆盖而模型128范围未触达，分别报告not-covered，不能相互替代。

根因状态仍是：实际溢出条件已确认，旧非法访存和reasoning-only因果未隔离；局部修复通过也不能代替正式精度。后续如需再次重启、不同变量或超出范围，先报告并等方向。

## 执行前记录

Host inventory及PPU-07 connectivity-check通过。模型容器`qwen3.8-flash-opt-ppu07-20261015`内无API/TP worker、8010无监听；其他8035仍监听3466314，物理0–7占用约76GiB/卡，8–15空闲约98GiB/卡，不能触碰0–7。正式acc013所有客户端已退出，monitor PAUSED。

本轮远端目录：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-013-full-gpqa-ppu07-c64-diagv3-20261016/diagnostics/accdiag-017-index-i64-fix-20261016`；命令位于其父case的`commands/accdiag017-*`。准备脚本先保存/校验SHA，再执行`python3 case/commands/accdiag017-prepare.py`，排他创建新目录、复制私有代码、保存源码快照、设备与8035身份；不导入GPU库、不恢复服务。随后才形成补丁、CPU测试、资源门禁及GPU微测。

## 当前状态

### 17:02旧客户端自然终态：1条60K截断，仅既有证据核验

用户随后授权env018包更新及op019新算子接入准备；未恢复原heartbeat、未重启或另发请求。op019加载前只读检查发现原客户端已自然退出，FINISHED为17:02:53.493415+08，派发/完成120、110唯一doc、errors0、inflight0，stage=stopped-on-anomaly，tail seq120..127八条未发送。原119条有最终输出，seq10/doc32 HTTP200，completion_tokens60000，finish_reason=length，content=None、191706字符reasoning，完整API token无248069/248046/248044，末token561；不是网络TIMEOUT或异常EOS停止。新019源仍未加载，不能归因新算子。旧非法访存与本条长推理截断是否同因仍not-isolated，不能宣称i64修复已解决输出健康。

按inference-accuracy-diagnosis冻结现有raw请求/回复/结果、完整token、8rank全部events、实际rank0前缀、服务首次异常及终态固定日志前缀，保存于op019证据`preload-old017-incident-001/`（绝对路径见state.yml）；report SHA `813fbf0f58fe3eaf04bc86bab022540eaada7a41e6a66d4dcadb7ab8cefb800c`。8rank generic gather/scatter最大18736、stride102400、i64/i32 offset均1918566400、storage合法；模型generic20972仍not-covered，尾部未执行不补发，不以微测代替模型覆盖。selected last-writer快照不等于每层状态，未新增driver日志或伪造完整因果现场；后续冻结复核由op019同一记录链接。原整体minimal-regression保持incomplete、正式分数/gate不变；下文进度属于历史快照。

补充复核SHA `2b9a0d5dcb599942afb317c88ed6018ebe6000aea1f40a81eb14dd8a13afac76`：120份raw/token usage核验，doc32 rank0原始采样60000 token与API逐个一致。8rank已记录packed实际max18729、invalid/nonfinite/operator mismatch0，固定服务前缀严格ERROR/非法访问匹配0；但每rank75165条actual_indices=None未重建，不称独立全量索引/所有状态覆盖。该length案例不能靠“reasoning parser漏分正文”单独解释，因为原始token没有think-end；是否源于数值或模型长推理行为还需受控对照，根因不升为confirmed。

### 16:19用户要求停止：自动化已暂停

用户明确“你先停止吧”。按人工暂停流程暂停Agent自动监控与后续动作；产品工具确认原heartbeat `qwen3-8-ppu07-gpqa-c64` 为PAUSED。未进行新的远端检查，未发送服务或客户端停止信号，不主动中断当前模型服务或在途受控请求，因此16:02:33之后运行进度未知，不能把暂停当作客户端终态或验证失败。现有日志/资源保留；整体minimal-regression仍incomplete、无正式gate。等待用户明确继续，恢复时先重新核验当前实例、客户端/原始证据与范围，不重复启动任何工作负载。

### 仅8010恢复与受控客户端执行前记录

micro-small-001 exit0，8种dtype/layout/index组合共24算子检查通过；实际命中LinearizedAdjacentIndexFunction4次、generic IndexFunction4次、IndexPutFunction16次，包含replace与accumulate；峰值322635264字节。连同真实大布局的36项链检查、三次changed-index graph replay，允许进入模型最小回归，但不代表模型精度通过。

恢复控制入口`commands/accdiag017-control.py` SHA `9b5cc85945afcb90e2787c05241a9839f953113a9a3f58b520dc446d7e559855`，AST通过。依次执行`python3 case/commands/accdiag017-control.py --mode recover`、`--mode wait`，就绪后更新原heartbeat再`--mode start-client`；不重复recover。它先确认CPU/两项GPU回执pass、8–15无人占用、8010无进程/监听和8035当前保护身份，再保存唯一128请求清单SHA与启动脚本，保留原argv/设备/blacklist/graph，只切换私有017、独立cache/日志根。原tuning DB通过SQLite只读backup得到新私有数据库，保留已有选择、不共享可写旧库；保存snapshot SHA。没有kill/stop/restart容器命令。

`wait`核验health、原argv、8worker实际诊断SHA e9c633c7及device buffer、FULL/PIECEWISE各7/7 capture；缺失不派发请求，不以header或capture冒充模型两次replay。前两条C1用于验证真实replay/token，然后C8→C64的110条→排空后C8的8条，累计128，不追加formal。首真实异常保留原始HTTP（失败也保留bytes）、索引与有界state/完整token/实际rank0前缀，停止补位、自然排空，无自动重试/重启。guard读取实际算子模块SHA而非只认环境变量；成功跨20972时额外保存first-i64-boundary前后文件，真实bounds/mismatch仍会触发FIRST_ANOMALY。

14:48:56.320867+08:00已一次性恢复，未执行stop/kill。launch SHA `1c526d6b367c3341238c6a76382d8c251d3863efef4caabfa96f7f858cb186e7`；新tuning DB快照 SHA `ea9a32ff5397b450400044b5bb34e876e31f34a8f9a16c93672aa05d6fd1b6da`；冻结128请求SHA `a8771e6bd26dc3926ec926178d5fda5ee2f6d4f8f72a897ea92700f5603595e3`。API Host2235393已启动，8worker初始化/通信中，READY尚未生成、模型请求仍0；仅继续现有wait，不重复恢复。补丁`pr_readiness=experimental`，未实测其他平台，正式精度/性能尚无通过声明。

当前服务源码/权重/tokenizer/引擎绑定沿用CPU-only文件探针，适配新私有路径的`commands/accdiag017-source.py` SHA `e7d682afdf742d05bbc683028c8fe44017515b262b53215da7833ad052ddbe1b`，AST通过；从实际API进程仅提取PYTHONPATH供独立CPU进程find_spec与文件SHA，不导入GPU库或热修改worker。保存runtime-001/source-before.json；权重仍采用131个文件名/大小/mtime+配置/index内容指纹，不冒称逐字节重哈希约360GB权重。

### 14:57恢复就绪

14:57:32.296511+08:00 readiness通过，API2235393/start484916288，原argv逐项一致，health200、running/waiting0、prompt/generation0；8worker实际诊断SHA和device-buffer证据齐全，FULL/PIECEWISE各7/7 capture，8035与恢复前1948536/start484833646一致。首次冷缓存主图compile约120秒、warmup约155秒，期间shm60秒提示后有实际ppu-llc/gcc子进程及日志推进，没有将其误判死锁或重启。模型请求此前0，不以capture当两次真实replay。

新source-before SHA `838f990b047eef8dfdfae62cb73c881d46eac9303243123baa4ec3f321c8e39d`，actual imports为私有017 Plugin/Gems；模型与tokenizer指纹仍942e6ab7…/3b0d6337…。启动客户端前保存`service-manifest-before-client.json`和`runtime-evidence-before-client.json`（此时graph_replays0/pending）；随后C1实际证据独立写回，不修改旧绑定回执以凑通过。

原heartbeat已复用并通过产品工具确认ACTIVE/30分钟，仅本轮实质进展、跨边界/首异常、失败/完成通知，禁止重发/重启/全量GPQA。完成/失败后冻结与暂停。用户新授权范围只包含这一次128请求，不自动追加。

### 15:00两次C1正常、C8运行中

唯一客户端Host2627674/start484977108于14:59:04.631340+08:00开始，未启动formal入口。15:00:48快照为分发10/完成2/在途8/errors0，阶段c8-controls；两条完成均doc2最终B/243tokens、think-end位置234、末EOS248046、HTTP200/stop，raw SHA与result一致，**本轮两次完整token IDs完全相同**。C1首回复raw SHA `6c532662b2b587762ad6bfbbb0fbc5ced2cf1c98517d840f7f777a36aa846061`。

8rank均已记录实际IndexFunction和IndexPutFunction源码路径/新SHA且verified_i64_load_before_multiply=true，说明修正版实际命中，非环境变量声明。rank0有489条FULL binding和489条device-replay-observation，包含真实graph对象与device counter变化；generic模型现场最大571，**模型大索引边界尚未覆盖**，不能用微测87528代替。无FIRST_ANOMALY/STOP/CLIENT_FAILED，health200，C8/C64/排空后tail仍待完成，不宣称模型修复或精度通过。

与旧v3单独C1的441tokens相比，当前轨迹为243tokens；记录差异而不声称跨候选token一致。虽采样/argv不变，新私有编译/cache根也是预先声明的运行差异，仅凭轨迹变化不能归因i64修复。当前两次重复一致只证明本候选的局部重复结果。

纯CPU现有证据审计脚本`commands/accdiag017-controls-audit.py` SHA `07034ae83850ab9a9063135a8a4e08470f3251751d25724c2e3e14735e19465d`，AST通过；执行`python3 case/commands/accdiag017-controls-audit.py`，新建runtime-001/controls-evidence-001，保存两条raw及8rank完整行的固定日志前缀/SHA、源码命中与真实replay证据。只给passed-scoped-C1-controls-only，整体minimal-regression仍incomplete，不改写before-client回执或发额外请求。

controls-evidence-001/report.json SHA `60685a92d3a2a936e73fa3b17a408defdfbbc36a57cadefb3189d2c360b2434f`，8rank实现SHA与FULL/device counter推进均通过；审计结束progress为派发10/完成4/在途6/errors0，仍C8。该回执不将正在运行的C8计为已通过；后续仅监控现有客户端，C64和tail未完成前整体保持incomplete。第一处真实异常/正常跨大索引会按原计划保存并通知，监控终态停用，无自动重复恢复或全量GPQA。

### 15:15只读状态：9条正常完成，大索引仍未覆盖

按精度定位流程核验当前runtime-001，未追加请求或改动服务。15:15:48+08:00仍为C8对照阶段：派发10、按seq去重完成9、7个唯一doc、在途1（doc155）、错误0；C64持续更替尚未开始。8010/API与客户端身份不变，health200、running1/waiting0、preemption0，8035保护身份亦未变。剩余请求仍约13 tokens/s生成，FULL graph/device counter持续推进，不能把尚未返回的请求算成reasoning-only或停滞。

逐行读取8rank当前events，实际generic gather/scatter最大索引均571，packed decode实际device indices最大也为571；无first-i64-boundary文件或跨界事件。generic实际pool shape为[66758,6,128,128]、row stride102400、storage_offset1920、storage27344076800字节；571对应i64/i32 row offset均58470400，字节区间[233889280,234282496)合法。因此**本轮模型尚未触达20972，更未覆盖其以上边界**；此前GPU微测通过23520/87528不能替代模型现场覆盖。8rank实际IndexFunction/IndexPutFunction均命中新SHA并verified_i64_load_before_multiply=true。

9份已完成原始HTTP均校验SHA及完整token数与usage一致，均非空最终content、finish_reason=stop、含think-end248069、末token248046，无60K length cap。C8已完成目标142/144/149/151均产生最终答案；155尚在途。当前未发现非法内存访问、真实索引越界、state mismatch/nonfinite或FIRST_ANOMALY/STOP/CLIENT_FAILED。该结论仅适用于已检查的运行窗口与9条完成回复，不代表128条最小回归已通过，更不能证明此前reasoning-only或非法访问已被完全修复；继续由既有客户端在原128/C64上限内执行。

原始证据仍在runtime-001/progress.json、metrics.ndjson、req*-response.raw.json/result.json、runtime/rank0..7/events.ndjson和service-diag.log。本次是只读观察，未新建或改写远端回执，旧controls-evidence-001仍仅C1 scoped通过。

### 15:28阶段切换：C8完成，C64持续更替进行中

本次heartbeat按`inference-accuracy-diagnosis`及`inference-accuracy-evaluation/minimal-regression`只读监控原客户端，没有新推理或服务变更。doc155于15:21:25.959546+08:00正常完成：最终C、14894tokens、think-end位置14700、末EOS248046；因此8条C8 controls均已正常结束。15:21:26进入冻结的110条C64持续更替阶段。

15:28:19+08:00快照：总计派发79/128、15条完成（10个唯一doc）、64在途、errors0，耗时约29分15秒；C64已完成5条，其中目标151/0/2均有最终答案。15份完成原始response SHA及token数与usage全部吻合，均非空最终content、stop、含think-end并以248046结束，无HTTP错误或60K截断。客户端、API/engine和8workers存活且身份不变，health200、running64/waiting0、preemptions0；KV约14–15%，生成及8rank device counter持续推进，无明显停滞。8035保护PID/start/argv SHA仍匹配。

8rank实际generic gather/scatter最大索引升至**8848**，packed decode实际device indices最大5033；仍未达到20972，无模型first-i64-boundary文件/事件。generic row stride102400，8848对应i64/i32 offset均906035200、差0，storage字节区间[3624148480,3624541696)合法，pool shape/storage与15:15记录一致。两类实际算子新SHA和i64 load-before-multiply在全部8rank核验通过；当前无anomaly/forward-exception、operator mismatch、device invalid/nonfinite标记或服务ERROR/非法访问。

阶段切换属于实质进展，通知用户；原heartbeat继续ACTIVE，仅监控原128范围，不估ETA、不扩大范围。当前最小回归仍incomplete，不能以尚未跨界和已完成15条正常回复宣称旧故障修复或正式精度通过。

### 15:34继续监控授权及当前覆盖

用户再次明确继续监控，重点为模型实际跨20972和首次非法访问/reasoning-only，保全证据并通知，不重启/不全量GPQA。复用原heartbeat，产品工具已确认ACTIVE、每30分钟、仅实质变化/首边界/异常/完成通知，不新建重复监控；现有observer/client持续保存每次请求及边界证据，heartbeat负责核验和通知，不承诺实时推送。

15:34:46+08:00仍C64-churn，派发93/128、完成29（23个唯一doc）、64在途、errors0；29份raw SHA及完整token/usage一致，全部非空最终content、stop、think-end及末248046，无截断/空最终回复。8010与客户端身份不变，health200、running64/waiting0、preemption0、KV约22.5%，8rank replay均持续推进，无FIRST_ANOMALY/STOP/CLIENT_FAILED。

8rank实际generic gather/scatter最大14776、packed实际device indices最大10559，均未跨20972；generic i64/i32 offset均1513062400、差0、row stride102400，字节区间[6052257280,6052650496)合法，storage仍27344076800字节。实际修正版bits64/verified命中，operator/device异常记录0，尚无模型first-i64-boundary文件；保持not-covered与overall incomplete，不以当前正常输出宣称完全修复。后续仅现有冻结请求继续推进，128范围耗尽仍未覆盖则如实报告，不自动扩范围。

### 15:58 heartbeat：C64全部派发、94条正常完成，尚未跨界

依精度定位/minimal-regression流程只读检查既有客户端。15:58:22+08:00累计派发120、按seq去重完成94（84个唯一doc）、26在途、errors0，约59分17秒。两条C1和8条C8均已完成；110条C64全部派发、其中84完成，排空后8条C8尚未派发，不新增/重发。C64八个目标142/144/149/155/151/0/1/2已全部正常最终答案，依次D/B/B/C/B/D/B/B，completion_tokens依次7784/5279/3918/7078/972/834/10591/546。

94份已完成raw response SHA与result一致、完整token数与usage一致，全部非空最终content/stop/含248069/末248046，无空content、length截断或Unicode replacement character；客户端无error文件、CLIENT_FIRST_ANOMALY、CLIENT_FAILED或FINISHED。8rank实际generic gather/scatter最大**18736**，packed实际device indices最大18729；generic stride102400，i64/i32 row offset均1918566400、差0，字节区间[7674273280,7674666496)位于27344076800字节storage内，仍未跨20972，无模型first-i64-boundary文件/事件。

8rank实际IndexFunction/IndexPutFunction修正版SHA和verified_i64_load_before_multiply通过，operator mismatch、device invalid/nonfinite、anomaly/forward-exception记录均0。API/engine/8worker与唯一客户端身份不变；8035保护身份仍匹配。15:57:52 health200、running27/waiting0、KV27.6%、preemption0，随后客户端完成数增至94/在途26；日志至15:58:22仍推进，服务strict ERROR/非法访存行0。证据文件系统空闲约8.1TB。当前是实质进展而非终态，heartbeat保持ACTIVE，既有请求自然排空后执行冻结tail；不估ETA，不因接近边界加请求。结论仍overall incomplete/模型大索引not-covered/未复现旧reasoning-only，未签精度gate或宣称完全修复。

### 16:02用户重点明确为排空后8条对照

用户再次要求只监控原计划排空后8条对照能否触达20972以上，首次跨界或异常保存完整已有证据并通知，禁止追加请求/重启/全量GPQA。产品工具已更新同一heartbeat并确认ACTIVE，明确tail为原128清单seq120..127，绝不另起客户端或代发；首次跨界原始回复尚在途时如实标记待齐，不能称完整证据。

16:02:33+08:00只读快照为派发120/完成98（88唯一doc）/22在途、errors0，C64已完成88/110、尾8尚未开始。98份完成raw SHA/token usage及最终content/stop/think-end/EOS核验正常。API2235393/start484916288、客户端2627674/start484977108不变，health200。8rank generic gather/scatter仍最大18736，packed18729，正常64位地址及storage边界不变，无cross事件/边界文件或operator/device异常，FIRST_ANOMALY/STOP/CLIENT_FAILED/FINISHED均无。仅按原客户端自然推进到tail，整体incomplete、大索引仍not-covered；本次没有服务或推理变更。

### 真实布局微测通过，恢复前补充小池路径

micro-001 exit0，report SHA `05d73be5407a16d05f2beadd581d488411bacc72bd0c96901d0c509e7de2b84f`。12组链共36算子检查、empty-index API、三次changed-index gather/scatter graph replay均逐位一致，padding未变；GPU峰值36159097856字节、小于48%门限。安全offset探针实际复现旧i32负值并得到fixed i64正确值，旧危险内存kernel执行0次。当前缓存保留116份生成代码/IR（38 TTIR、38 TTGIR、38 LLVM及2生成py），已读TTIR明确`tt.load ptr<i32> → arith.extsi i32 to i64 → arith.muli ...i64 → addptr`。首次成功跨界before/after状态在micro-001/observer/rank-1/first-i64-boundary，rank-1表示单进程微测不是TP rank。

补充`commands/accdiag017-small.py`，SHA `c19905f8743ade65de813e1eb5a051ee69599ab47c950b32cb2dc26fc630be63`，AST通过；在恢复模型前仅物理8、CUDA_VISIBLE_DEVICES=8、显存fraction0.05、相同私有017/import/cache运行。新目录micro-small-001，检查48行连续/带padding、FP32/FP16、int32/int64的public gather/index_put_(replace及accumulate)、邻接保护，并记录实际IndexFunction/LinearizedAdjacentIndexFunction/IndexPutFunction命中。不是性能测试或模型请求。

CPU测试exit0，6种generic生成签名的cast、两类stride算术边界、已知源码SHA识别、gather/clear/scatter及padding、真实越界拦截与人工异常保全通过，确认无GPU context；不能替代设备通过。修复已仅落入新私有017的3文件，原16/共享源码保持不动。

GPU微测脚本`commands/accdiag017-micro.py` SHA `96121b43a956bb1281b171fea54f284d21ffa17915d95d28f209e676f5b492dd`，AST通过。执行前核验CPU回执、8035身份和8–15无其他设备进程，仅设CUDA_VISIBLE_DEVICES=8。命令为`docker exec -e CUDA_VISIBLE_DEVICES=8 -e PYTHONPATH=<private017>/plugin:<private017>/gems/src:<private017> -e QWEN38_DIAG016_ROOT=<D17>/micro-001/observer -e QWEN38_DIAG017_MICRO_OUTPUT=<D17>/micro-001 -e FLAGGEMS_CACHE_DIR=<private017>/cache/micro/gems -e TRITON_CACHE_DIR=<private017>/cache/micro/triton qwen3.8-flash-opt-ppu07-20261015 python3 case/commands/accdiag017-micro.py`。原始stdout/stderr保留micro-001/run.log；不触碰其他服务缓存。

首次micro启动前检查发现8035原PID3466314已退出，FileNotFoundError在任何HOST_STARTED/GPU分配之前拒绝，micro实际未启动。本任务未停止/重启/修改该服务。只读重查它现为PID1948536/start484833646/argv SHA91849d0b77b52d602a9ffc0ce9dbb608667ce127ce61cc8a0474883e334ffc0c，0–7约74.6GiB、8–15无其他设备进程；只保存`other8035-rebaseline-001.json`作为本次操作前保护，保留原before事实，不推断外部改实例的原因。后续再次变化须重新安全检查，不以旧PID直接操作。

显存门禁：max fraction0.48，需空闲大于35851878400+8GiB，否则拒绝分配，不缩服务显存。12组dtype/索引stride/M2-M6-M64的gather→clear→scatter链，合法高索引23520和87528、两侧padding保护；空索引API与三次changed-index graph replay独立检查。原i32与fixed i64只在写小输出的offset探针比较，绝不对原错误地址做读写；保留实际新编译代码/IR和第一次成功跨界state文件，不能拿历史缓存当当前命中。

### 私有副本与补丁准备（执行前）

prepare已成功建立私有017和源码逐文件SHA基线；8035保护身份为PID3466314/start484027971/argv SHA b47c1b8fd2ad0d684998f076e2b74ebb4f5214184855e869296eb2c02cea8a8f。未恢复8010、未运行GPU。补丁在本地临时快照用apply_patch生成：generic gather与scatter加载索引后`.to(tl.int64)`，并覆盖同文件linearized gather的load；mask、采样、状态语义和输入index dtype不变。

| 文件/入口 | SHA256 |
|---|---|
| commands/accdiag017-index.py → 私有gems/ops/index.py | 15ddfe412f1b121c19583e0145231876a7aaf574d351ad555b4046553f1fcfa1 |
| commands/accdiag017-index-put.py → 私有gems/ops/index_put.py | d8422ca29589ae93e11129578ffd881a96b90671f73037230b2bfb7b42355a01 |
| commands/accdiag017-diag.py → 私有diag016.py | e9c633c7fbf2ed7222ae5746331a6cd252c9b8930374d926338d8cfad591a8c8 |
| commands/accdiag017-deploy.py | b8e41f3ba23aa90a910e4bbc06a69ffe1aa53bb505a04b3c9d8cada99ff8a15f |
| commands/accdiag017-cpu.py | abb44db6bb73ceb133398c102f9658190f673c99f3e93f35cb75307de26e5720 |

全部AST通过。部署命令`python3 case/commands/accdiag017-deploy.py`只覆盖新私有017内的3份已存快照文件，保存unified diff和source-after，不写原16或共享源码。随后执行CPU测试：`docker exec -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/opt/qwen38-accdiag017-i64-20261016/plugin:/opt/qwen38-accdiag017-i64-20261016/gems/src:/opt/qwen38-accdiag017-i64-20261016 -e QWEN38_DIAG016_ROOT=<D17>/cpu-hook-001 qwen3.8-flash-opt-ppu07-20261015 python3 case/commands/accdiag017-cpu.py`。CPU人工invalid-index异常单列，不能当模型事故。测试生成器6种签名的i64加载、两个stride算术边界、guard SHA识别、gather/clear/scatter/邻接padding和真实越界执行前拦截/文件保存，明确不创建GPU context。

准备脚本`commands/accdiag017-prepare.py` SHA `f2db2b2d96b435412b931cdfe6839d35815544b2704feddbebfb11f2a88eb8ac`，AST通过；执行前核验新脚本/目录不存在，保留既有故障产物。

planned，尚未应用修复/恢复服务或发起新推理；正式score/gate不可用，性能保持blocked。进度监控待受控客户端实际准备完毕后复用原heartbeat，30分钟/仅实质变化，终态暂停。
