# accdiag-015：C64持续更替与大block-ID索引受控复现

状态：128/128完整，局部未复现原模型症状、证据已冻结、heartbeat已确认暂停，等待用户方向（存在调度间断）；大池FP32测试仍deferred；分类 accuracy-diagnosis/execution-mode；不运行formal GPQA，不产生gate，不叠加性能优化。

## 授权与范围

用户在accdiag-014终态后明确授权继续C64持续请求更替及大block-ID索引受控复现，重点非法访问与reasoning-only。仅PPU-07、容器qwen3.8-flash-opt-ppu07-20261015、8010/物理卡8–15。卡0–7/8035不触碰。服务保持原实例、argv/env、Gems/compiler/blacklist和源码；不重启、不补跑正式198题、不改旧127/198或无gate状态。

采用本地 inference-accuracy-diagnosis；索引实验采用 key-operator-analysis 的CPU oracle、真实源码和逐阶段同步方法。上一轮188小池检查及8题C1→C8→C1共24请求正常，只提供反证，不证明修复。旧驱动明确_index_jit_function非法访问，nonzero是同步上报点，首个非法输入/机制及与空最终答案的因果关系未确认。

## 冻结方案与停止条件

远端case为 `/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-012-full-gpqa-ppu07-c64-master-20261015`，新证据根 `case/diagnostics/accdiag-015-c64-churn-large-index-20261015/`，不覆盖任何旧产物。

先CPU预检身份、完整源码/import/model/tokenizer指纹、健康idle、原客户端退出及目录权限/空间。再独立进程单卡8大索引测试：FP32 `[N,6,128,128]`，N=6000/22000，stride0=98304/102400，int32/int64，B=1/8/64；固定合法且唯一索引，覆盖末页及2^31元素地址附近。native Torch int64 gather和CPU行标签共同验证初始化；分别Gems gather→布尔清零→scatter，每步同步。清零mask none/alternating/all；scatter验证所选整行及全池每行首元素。构造数据可重建，非线上真实tensor。最大单进程显存12GiB、分配前至少保留5GiB余量，空间不足记incomplete，不冒险分配或停止模型服务；独立SQLite调优库。若非法访问/不一致，停止后续阶段与C64，冻结后报告；不自动切实现/修复/恢复。

大索引通过后，C64最多128请求、零重试、持续完成一条补一条，不设两批间屏障。112条原有非空响应背景请求按doc_id升序选择并排除8个目标；前56背景+8目标进入首64，后56背景+相同8目标作为替换。目标仍142/144/149/155/151/0/1/2，因此120唯一doc/128请求，不等同198题正式评测。所有payload从冻结原生样本构建，prompt hash、temperature1/top_p.95/top_k20/min_p0/presence0/repetition1/seed1234/stop/max60000不变；仅沿用return_token_ids/return_prompt_text响应取证字段。请求清单在启动前离线冻结SHA。

保存逐请求raw JSON、精确payload和序号/doc/response-ID、HTTP/finish/stop/token IDs、think-end/EOS、content/reasoning与最终文本；监控running/waiting/KV/preemption及日志新增错误。首次空最终content、length cap、HTTP错误、服务异常或身份漂移立即停止补位，已在途请求只收集不重试；不把None占位当真实网络超时。8小时分发预算、单请求HTTP超时7200秒；不能把客户端C64上限当实际设备batch64或graph命中证明。无运行时插桩，不声称得到实时block-ID或首个张量分歧。

## 执行前命令记录

脚本放入case/commands并记录SHA后执行；prepare/micro/run各排他锁，已有进程只监控，不重复启动。具体SHA及原生回执在下文持续补充。需要服务重启、代码或运行时埋点、Gems/compiler切换时先报告，不混入本轮。

控制器 `case/commands/accdiag015-controller.py` SHA `bcda01eeb220d1c164f3c0016ff7cd05936bae652101787925346604f1970199`；设备脚本 `case/commands/accdiag015-large-index.py` SHA `2bb48b8079b7aa9f71472c6e2f94f8228582c53c3e0686d0dcf6f52b1b1d57c3`。本地AST语法校验通过。顺序命令为 `python3 case/commands/accdiag015-controller.py --case case --mode prepare`、`--mode micro`，仅在其FINISHED exit0且健康idle/源码相同后才 `--mode run`。大索引先int64参考再int32，以便故障时仍保留同shape正常对照。微测不与C64重叠。

21:09–21:12只读检查恢复服务PID/start ticks/argv未变、health200、running0/waiting0、KV0、累计prompt8541/completion184805，无上一轮以外的推理流量；源指纹将在prepare复核。PPU-SMI驱动1.28/2.1.1-rbd225；其简化查询参数不支持，未以失败查询猜测余量，设备脚本将以物理8的实际mem_get_info作硬准入。当前通用index源码的cur_index乘stride路径未见显式64位扩展，作为待证伪地址溢出假设，不当成线上根因。

prepare已exit0：完整源码/import/model/tokenizer指纹与原候选一致、原实例idle且累计token未变化。128请求/120唯一doc清单SHA `62407c39c06f33e1456f4309f4ad5e6ea202ba0a72055dad3f79c3acabc66ec8`，PREPARED.json保存命令SHA、目录owner/权限/剩余空间。micro以Ansible async一次性启动（控制面最长14400秒，仅允许现有单个子进程）；C64尚未启动，必须等待微测终态并核验门禁。

## 微测结果与用户更新的执行顺序

21:19:18–21:19:24：N6000的contiguous/padded、int64/int32、B1/8/64均完成native-reference、Gems gather、3种mask clear、selected scatter和全池行首检查，共84项逐位匹配；无非法访问或数值不一致。随后N22000 contiguous需要8650752000字节，mem_get_info显示可用7931821808字节，**分配前**被5GiB余量检查阻止；micro wrapper exit1为资源门禁而非算子报错。初始free13037515760字节，跨布局测试后可用下降也已保存，不把缓存/引用残留猜测当模型泄露结论。8010原实例仍health200、idle0/0、token计数不变。

用户随后明确要求“显存不够先不要动当前服务，先按128请求上限跑C64持续更替”，因此原“所有大池测试通过才启动C64”的自设顺序被此指令覆盖；保留micro-001失败/资源证据，不追加GPU微测、不减服务显存、不重启。C64仍采用同一PREPARED清单及SHA，且必须核验micro已退出、资源阻断原因确为headroom、84数值检查完成、源指纹和服务身份/idle/token计数不变。

新增独立控制器 `case/commands/accdiag015-c64-v2.py` SHA `545ad8eca2358ccfcfbd6dbaba3bebebd70bd932ac7d40464558b22b1e9b9dd2`，不覆盖原控制器/清单。启动命令 `python3 case/commands/accdiag015-c64-v2.py --case case --mode run`，Ansible async最长43200秒；客户端自身8小时停止补位预算、每请求7200秒、128总数和64并发上限不变。首次异常排他保存FIRST_ANOMALY、first-anomaly.json、对应原始response raw（含完整token IDs）/请求清单及service-first-anomaly.log完整快照；HTTP错误原始body和完整Python traceback独立保存。只停止新派发，已在途请求继续收集、不重试。服务日志增量从log-boundary.json的冻结偏移开始完整保存，原始服务日志不清理、不截断。

## C64启动与客户端自身错误（模型结论分开）

21:28:02实际启动，Host客户端PID2063127、async job j983796444627.2062972，原8010身份/源码门禁通过。21:28:23已派发64、返回0，服务running44/waiting20、health200、preemptions0，不能把客户端C64上限冒充设备实际batch64。

21:29:14首个返回seq63/doc2为HTTP200、最终答案B、reasoning非空、253 tokens、think-end位置232、末token248046，raw SHA `f9685915d4caf424bd35296d1faefa5972a8b3c281235ac0374032dc45f2b8c1`。保存正常raw/result后，**我编写的诊断客户端**event()把rec已有的at再次作为dict关键字传入，触发 `TypeError: dict() got multiple values for keyword argument 'at'`。这是已确认的客户端日志错误，不是模型/HTTP异常，原FIRST_ANOMALY保留。失败计数在完成计数之后再次增加，不能将二者相加，也不能把这些TypeError算成模型超时。原客户端停止补位，但保留既发64个请求继续自然返回，不停止服务/客户端，不重发seq0–63。

受控恢复仍在用户同一128总数/64并发授权内：新脚本仅承接尚未派发的seq64–127，使用同一requests.json。每次补位前读取原inflight（原客户端只减不增）并加新pending，合计必须小于64；原dispatched必须始终64。原结果出现空最终content/length或非日志TypeError的真实错误，立即停止新补位。新脚本采用独立 `remaining64-001/` 和排他marker，不覆盖旧错误/响应；新first-anomaly专指新的输出/服务异常。原progress的completed+failed重复计数不用于进度，按全局seq去重raw/result，最多128次真实模型请求。

新脚本 `case/commands/accdiag015-remaining64-v3.py` SHA `b737ab0cf3f7fc6dbc004684f99342eea9c592fee65b9dde98e50b1d07852d1e`；启动命令 `python3 case/commands/accdiag015-remaining64-v3.py --case case --mode run`，Ansible async最长43200秒。启动前核验原脚本SHA、原first-anomaly确为日志字段错误、已完成原请求不存在真实输出/HTTP异常、微测进程退出、源码及服务身份不变；无需/不得等待idle，因为正在收集原64请求。修正event()使用setdefault保留已有at，提取实际函数进行CPU complete/error含at两例测试，均通过；AST语法检查通过。

**本次已有明确调度间断，不能描述为自始至终无间断C64，也不能作性能数据或正式评分。** 这是客户端执行条件差异，不隐瞒、不重置证据、不追加到128之外。原始服务代码/采样/实例不变，目标仍定位原模型异常；无修复/根因声明，原正式gate/分数不改。

## 21:36只读运行核验与监控交接

接续客户端21:35:48.815906实际启动，Host PID2252021、async job j943414442736.2251936，`remaining64-001/RUN_STARTED`为唯一启动证据。21:36:50两客户端均存活：原64派发/39份raw结果/25在途；接续40派发/1份raw结果/39在途；合计104/128派发、40个不同全局seq响应、40唯一doc、64在途。39条原TypeError均与已存正常result配对，无其他error类型，不能计为39个HTTP失败，更不能算成78个已完成请求。40个返回unhealthy=0，尚未复现空最终content/60K截断或真实HTTP错误，接续FIRST_ANOMALY尚无。

21:35:58服务health200、running64/waiting0、KV9.7988%、preemptions0，原身份和源码不变。该时点actual running64可核验，但不抹去21:29至接续前的调度空档，也不证明每步设备graph batch64。

首轮8目标中已完成5条：doc2 B/253tokens、doc0 D/603、doc151 B/2009、doc149 B/3865、doc144 B/3898，均非空最终content和reasoning、finish stop/stop null、token计数与usage一致、含think-end并以248046结束；完整raw SHA写入state，对应 `cohort-001/reqNNN-docNNN-response.raw.json`。doc142/155/1尚在首轮生成，晚期目标未派发，不能预填结论。这不是GPQA得分，原127/198不变、无有效gate；不估ETA。

原heartbeat `qwen3-8-ppu07-gpqa-c64`已通过产品接口更新为ACTIVE/30分钟，只读核查两个已存在客户端及全局seq去重证据，实质进展/目标结果/真实模型或服务异常/完成才通知。禁止补发seq0–63、超过128、重启/停止服务、追加GPU微测或正式GPQA；已在途继续自然取证。原日志TypeError与新的输出/服务异常分开记录，终态冻结完整raw/token/服务日志/客户端trace后暂停。当前未修复模型代码，根因仍not-isolated，正式性能blocked。

## heartbeat 2026-10-15 21:59 +08：128已派发、98返回，早晚目标均有进展

本轮按 inference-accuracy-diagnosis 只读核验，不新增推理请求。触发时间21:57:52，主快照实际21:59:22：原客户端51份result/raw+13在途，接续客户端47份result/raw+17在途；两者均存活，已派发128/128，按全局seq去重98次返回、92个唯一doc，30在途。原51个TypeError与正常result逐条对应，无其他error类型，不将completed与failed相加。requests.json SHA仍62407c39…66ec8，各已完成raw SHA均匹配其result。

98个返回均HTTP200、非空reasoning及最终content、finish=stop、无length/60K cap；completion253–12067、raw token数量均与usage相等。原FIRST_ANOMALY仍仅为已确认的客户端日志重复at错误，接续无新的FIRST_ANOMALY；恢复服务日志未见新增ERROR、invalid-page、非法访问或worker异常。

| doc | 早轮最终字母 / tokens | 晚轮最终字母 / tokens |
|---|---|---|
| 142 | 仍生成 | D / 9426 |
| 144 | B / 3898 | B / 1973 |
| 149 | B / 3865 | B / 5704 |
| 155 | C / 5311 | 仍生成 |
| 151 | B / 2009 | B / 2987 |
| 0 | D / 603 | D / 669 |
| 1 | B / 7530 | B / 2520 |
| 2 | B / 253 | B / 461 |

14条已返回目标均有正常think-end248069和主EOS248046；6组早晚配对最终字母一致，不等于完整文本/token一致，也不是正式评分。早轮doc142、晚轮doc155仍未完成，不补填结果。9条新增目标raw SHA、think-end位置和tokens写入state；原始证据在cohort-001/req056–063及remaining64-001/req120–127对应result/raw文件。新增晚轮doc142在21:57:41正常结束D/9426，不能用它替代尚在途的早轮doc142。

主快照service identity的PID/start ticks/argv与原8010完全匹配，health200、running30/waiting0、KV20.5556%、preemptions0。原progress最近21:52:35，接续progress21:57:48，服务日志21:59:22；已耗时31分20秒，不估ETA。22:00:35补核时已有99份raw，全部含think-end、以248046结束且数量匹配usage；Engine和8个TP worker均存活，running29/waiting0，累计生成由901462增至924533，仍在持续生成，不将progress数分钟未刷新误判为停滞。此补核时间不同于主快照，不混报唯一doc数。

结论仍为进行中、未复现原模型症状，根因not-isolated；大池测试仍deferred，无新修复、无有效gate，旧127/198不改写。heartbeat保持ACTIVE，只监控现有在途请求，不追加/重启/停止/切实现或运行正式GPQA，保留调度间断及原C64负载不可等同的限制。

22:02:35末次补核：按已存result的全局seq去重已完成101/128次响应、95个唯一doc，全部最终content非空且unhealthy=0；原52响应/12在途，接续49响应/15在途，合计27在途。最新两条为seq47/doc53于22:01:05正常最终B/17100 tokens及seq95/doc99于22:02:28正常最终C/13997 tokens，均有think-end和主EOS。原failed计数升至52，不将它与52份响应相加；精确匹配日志TypeError的逐条核验快照为21:59的51份。首轮142及晚轮155仍在途，仍无完整16目标或128次终态结论。该新增进度与上文21:59快照时间分开记录，继续原heartbeat。

## heartbeat 2026-10-15 22:29 +08：16目标已完整返回，剩9条背景请求

按精度定位流程只读取证，不发任何推理请求。触发22:27:52，实际快照22:29:11：128/128派发，按全局seq和raw SHA核验完成119次响应、111唯一doc，原61响应/3在途、接续58响应/6在途；两个客户端均存活，无终态marker。原61条error逐条核验均为正常result保存后的精确at重复TypeError，无其他真实客户端/HTTP错误，不将61 completed与61 failed相加。pending全局seq为8/11/27/85/86/89/90/111/117，不补发、不重试。

119个返回均HTTP200、非空reasoning及最终content、finish stop/length0/cap0，全部含think-end248069并以248046结束，raw token数量与usage一致；completion253–35096。服务日志没有新ERROR、invalid-page、非法访问或worker异常。恢复服务PID/start ticks/argv匹配，health200，Engine及8个TP worker存活，running9/waiting0、KV14.0844%、preemptions0；累计生成1257218，高于前轮924533，仍持续生成。已耗时1小时1分10秒，原progress22:28:12、接续22:26:01、服务日志22:29:11更新，无明显停滞，不估ETA。

此前在途的两个目标已正常结束：

- 早轮seq56/doc142，22:08:39.257374，最终正文答案D、21909 tokens，think-end位置21714（0-based）、末248046、stop/null；raw `cohort-001/req056-doc142-response.raw.json` SHA `9121979544967113b0f807b638a8579070ee0501b16d6c54fa1b8d44aaed3e0b`。
- 晚轮seq123/doc155，22:08:18.487206，最终正文答案C、15757 tokens，think-end位置15410、末248046、stop/null；raw `remaining64-001/req123-doc155-response.raw.json` SHA `a2918041765cd39634ee444c2590712973b69099dd086eb877ab0b72b4bc7511`。

因此8目标早晚共16次响应全部有最终content，8组最终字母均相同（142 D、144 B、149 B、155 C、151 B、0 D、1 B、2 B）。这仅是响应比较，不是8/8正式评分；完整token轨迹和长度不同，不当作首个数值分歧证据。目标范围未复现reasoning-only，但剩余9条背景仍在生成，不能提前宣告本轮终态或排除原故障。

根因仍not-isolated，生产源码/服务/采样无改动，无新修复或gate，旧故障污染127/198不改写。保留客户端调度间断、局部128/120doc与原正式C64不可等同、大池FP32未覆盖的限制；heartbeat继续ACTIVE，只监控现有9条，不再派发任何请求，不追加GPU微测或全量GPQA。全部终态后再冻结完整证据并暂停本heartbeat。

## 终态取证命令（执行前记录）

22:59:11只读核验全128个seq/120唯一doc/raw SHA完整，两客户端均退出、原native rc1（仅日志TypeError）及接续rc0，原服务health200且idle。CPU终态冻结脚本将保存为 `case/commands/accdiag015-freeze-terminal.py`，SHA `5895216451cb44f8736cf44c82bb387c2e3dbf9baab6f0930a6d31684992762d`；执行命令 `python3 case/commands/accdiag015-freeze-terminal.py --case case`。本地AST检查已通过。

脚本只读校验scope/原始raw哈希、全部seq绑定、最终答案/token/think-end/EOS、原始错误类别、两客户端退出与native回执、当前运行身份/idle、包含前24请求的服务累计token计数、完整源码/import/model/tokenizer指纹；随后仅排他创建 `case/diagnostics/accdiag-015-c64-churn-large-index-20261015/terminal-freeze-001/`。保存全部两段raw/result/error/事件/身份/配置、命令源码、资源门禁日志和native客户端**完整**stdout/stderr；不复制带连接细节的完整Ansible调用元数据。活动服务日志保存固定字节前缀快照，原日志继续写入且不被截断/覆盖。生成manifest/report及SHA，不给原cohort补造FINISHED，不触碰旧正式分数或gate，不新增推理请求、GPU测试或服务变更。

## 终态结论（23:05:48 +08冻结）

128/128个全局seq均有逐SHA核验的原始响应，120个唯一doc，零缺失或重复发送证据。最后一条为早轮背景seq27/doc32于22:56:29.114354完成，正常最终B、57530 tokens、think-end位置57324、末token248046；raw `cohort-001/req027-doc032-response.raw.json` SHA `b3f02db3e658f8050fcd6aab6fff9ce7e1a3f8649fb40460224c64ef1e7749e8`。请求窗口从21:28:02.181758至最后返回，5306.932596秒（1小时28分26.933秒），不把控制器准备/归档时间算作请求耗时。

全部128响应均HTTP200、非空reasoning和最终content、finish stop，均含think-end并由248046主EOS结束，token数量与usage相等；length0、60K cap0、空最终content0、真实HTTP错误/超时0、非法访问/服务新ERROR0，单次253–57530 tokens。本轮completion总1172480、prompt总48968，与服务累计generation1357285/prompt57509扣除上一轮24请求精确一致，没有用原客户端重复failed计数凑进度。

8目标早晚16次响应完整，8组payload及prompt_token_ids相同、最终字母相同（142 D、144 B、149 B、155 C、151 B、0 D、1 B、2 B）；生成轨迹/长度并不相同。最终字母仅作响应比较，不是8/8正确率或198题GPQA分数。原先reasoning含答案但无最终content的doc151，本次早晚均正常给最终B；四条原null目标142/144/149/155均在早晚轮有正常最终正文，仍不能外推原正式完整负载。

最早异常边界为客户端自身事件日志：21:29:14 seq63/doc2的HTTP200正常原始最终正文包含 `The best answer is B.`、253 tokens保存完成后，event()重复传at触发TypeError。全部64条原error均逐条与正常raw/result对应；原控制器最后native rc1、22:56:29.165187退出，没有FINISHED，不伪造或补造。接续控制器native rc0、22:55:05.436472退出，自己的FINISHED于22:54:53已记录64/64；彼时原请求尚剩1条，故全局终态按两段合并证据而非接续FINISHED单独判断。当前两客户端均退出，Engine/8 worker存活，8010原身份/argv/源码/import/model/tokenizer指纹均一致，health200且running0/waiting0/KV0；服务保持运行。

终态证据已排他冻结于 `case/diagnostics/accdiag-015-c64-churn-large-index-20261015/terminal-freeze-001/`，共368个manifest条目，含全部raw/token/result/error/配置/事件、命令、完整native客户端stdout/stderr、资源门禁日志、源码指纹及活动服务日志固定字节前缀。`report.json` SHA `10eef46d1d79921fce2217c18b468a2f644f91633476192de600af2ba2662b29`；`manifest.json` SHA `7d948e0c4946820a45307bcc55a7ccd068ba4e2ad617ba0be826fbc128ac29dd`。原canonical日志与正式产物不覆盖，不包含连接密钥/完整环境。

依 inference-accuracy-diagnosis 的根因证据标准，结果为 **complete / original-model-symptoms-not-reproduced-in-scoped-run，root-cause not-isolated**。此次只修正客户端日志，不存在模型修复或新精度gate；旧故障污染127/198保持不变，正式性能仍blocked。限制包括日志恢复导致的分发间断、120唯一doc非原198完整负载、新返回token取证字段、大池N22000未覆盖，以及未捕获线上state/index/stride/bounds或首个数值/graph分歧。不能以128条正常宣称原模型问题已修复，不能归因为nonzero或清零接线缺口。

下一步仅等待用户方向；若继续，需要另行冻结真实索引/状态/graph取证或其他单变量范围。不得自动追加请求、GPU微测、埋点、代码修改、切Gems/compiler、重启或重跑全量GPQA。终态记录同步后，产品接口已返回原heartbeat `qwen3-8-ppu07-gpqa-c64` 为PAUSED；8010保留运行，不再自动跟进新实验。
