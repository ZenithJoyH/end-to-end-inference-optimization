# accdiag-025：仅目标实际Mixed C64首Prefill取证

2026-10-18用户明确授权缩小埋点，仅抓doc178实际Mixed C64首Prefill，背景仅轻量元数据；仅恢复8010，总请求<=128、并发<=64，保留017 i64、首次异常证据，不影响8035、不跑全量GPQA。采用inference-accuracy-diagnosis和accuracy minimal-regression。旧024全部81347文件已独立校验，300秒RPC超时/7未提交PT/目标未派发原证据不改；原正式acc015164/198 failed-score/no gate不改。

## 对象、假设与范围

PPU-07 / qwen3.8-flash-opt-ppu07-20261015 / 8010物理8–15。旧024 API1932757和driver1940573已退出、8010未监听；本轮只启动一次，不向任何旧PID发信号，不重启容器。8035物理0–7为其他任务，保护API4161238/start487889425/argvSHA91849d0b77b52d602a9ffc0ce9dbb608667ce127ce61cc8a0474883e334ffc0c，当前health200。连接已按inventory限定PPU-07并验证passed。

CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018。新D=CASE/diagnostics/accdiag-025-target-only-Mixed-C64-20261018，R=D/runtime-001，private=/opt/qwen38-accdiag025-target-only-20261018；创建前owner/空间与挂载/image/source再核，路径不得已存在。完整旧Plugin字节复制，三仓/engine/权重/tokenizer/采样不改，仅私有观察器范围改变；无新性能优化、pr_readiness=experimental-diagnostic。

假设：024初始背景全面转储约366GiB导致观察器干扰与300秒RPC超时。缩小范围应先让初始63条自然进入Decode；只有冻结的两个opaque目标请求实际computed0、455prompt且同批63peer computed>=各自prompt长度、scheduled1、真实64行/slot63/graphNONE，才激活完整首Prefill捕获。未满足只留元数据并记录not-covered，不通过修改marker/采样/追加请求绕过。背景不落逐层hidden/QSA operands/GDN整块状态/logits PT；保留请求映射、实际索引/边界、bounded graph设备记录及rank0采样token轻量日志。目标保存actual input/positions/query/logits-row/ngram、48层4frontier、36GDN/12QSA、实际首32及EOS logits/prob/noise/RNG、完整HTTP/token；首异常原有stopfill/在途自然收集和8rank bounded state freeze保持。

## 请求契约与门禁

沿用024语义计划，换唯一opaque header：128=2C1 doc2+8C8 docs0/1/2/3/4/5/6/178+118C64（背景0–115，doc178早晚seq73/119）。C1/C8只轻量护栏，不完整张量转储；两C1 tokens一致、8rank graph两类7/7并至少2真实replay才入C64。目标准入需提交前fresh63Decode，实际覆盖另用8rank模型输入确认；尾部预算不够则not-covered不扩范围。原温度1/top_p.95/top_k20/min_p0/presence0/repetition1/seed1234/stop/max60000/返回完整token与prompt不变，零重试。背景普通错答只记录；空final/EOS/length/HTTP/目标错答/实际input-state-index-prob异常停补位，在途自然收集。

每rank捕获预算16GiB，超过报观察器错误、不得静默丢证据；只抓两个目标小于旧全128范围。仍有CPU同步/graph recorder/新缓存时序差异，不据未复现称修复/正式精度通过/性能结论。源码字节、导入、精确身份、graph与目标真实Mixed验证缺一则incomplete。保持默认RPC300秒，不以延长时限掩盖取证设计问题。

## 执行前命令

临时脚本先由apply_patch创建、本地py_compile和CPU正反例验证，再存CASE/commands，核SHA后执行。顺序prepare（私有部署，0请求/0恢复）→核PREPARED/launch/source→一次recover（8010空端口、残留/设备门禁通过才启动）→一次launch唯一driver，自动wait→C1→C8→C64→freeze。existing marker拒绝重复，无自动重启/恢复/请求重试。SHA和最终脚本命令在执行前补记；尚未执行部署/恢复/推理。

复用原heartbeat ID，运行后只读实质变化/首次异常/终态通知，终态暂停。任何需要再次服务重载或新埋点均另告用户。本轮不签formal gate，原精度阻塞继续。

### 冻结执行副本

| CASE/commands文件 | SHA256 |
|---|---|
| accdiag025-control.py | dc77a8f101e8559feb158afb725cc60d44b18adf576e0d4d848af458bc82ddbe |
| accdiag025-probe.py | 620ae14b741c49fd256b00377f3bc5826a2d61a576b24d5a09e1f223825f1149 |
| accdiag025-deploy.py | e0fc03b1825befec87a522657b04e3b5ced09ab53bb5e9d49e289f62ab4b44a0 |
| accdiag025-cpu-test.py | 1c3b207fb3ac1895f9880a6528e0e8da07732a9bdc59c871eb586cd3ef5e0d4c |

本地15项CPU gate/scope正反例通过（非设备证明），py_compile指定/tmp cache通过。首次未指定cache时因本机Python默认写受限Library Caches失败，属本地验证路径问题，无远端动作；未据此放宽运行门禁。复制后先核远端SHA，再`python3 CASE/commands/accdiag025-cpu-test.py CASE/commands/accdiag025-probe.py`；同control以`--case CASE --mode prepare`、`--mode recover`、`--mode launch`依次各一次，无自动重复。recover验证端口空、旧024进程已退、目标容器无模型进程且物理8–15各显存<1024MiB，保持8035精确原身份；不对旧PID发信号。客户端解析HTTP错误先存原始body及状态，不再让旧KeyError覆盖首HTTP失败分类；正常生成契约不变。

新probe SHA限定复用旧024/021/017观察器；仅目标ARMED gate通过时启用原张量取证，背景generic索引仍按真实i64实现/边界守卫、记录state-byte-check not_performed而非mismatchFalse。原bounded graph device记录/索引、rank0完整采样prefix及首次异常selected-state保留，不把它称为全池/逐层历史。只改私有observer和当前诊断controller，不修改三个仓库数学实现或vLLM。

## prepare已完成（0恢复/0模型请求）

远端四脚本SHA及15项CPU检查通过，私有Plugin完整字节同021-v2，model eb9f096d/runner c3537353/017双i64/M16及原source树一致；image67309a95、原mount-parity逐项通过。PREPARED `aede45dd1f35e95ba42ee41366b6c300b42c1beb0c774577e6c6a9f53813ee89`，requests `60359366283cf4eac5b28f74b81f9ffe4d59d41d9dd9a86b6be86572865aab56`，probe-config `63658d1e2e04595ec27daa794292f4d5c4b5c99893393eff383e1f789ce3af4a`，DEPLOYED `2f6a7e70e97f8b1341bd04c6047738a950e1211716fbdad5f6c38155647d9fb0`，launch `de9b84942d219ef44b3dc8a178abb2fc68737c4ca4285bdef94018b11349ce87`。config full-capture只允许seq73/119两opaque前缀，63Decode gate及16GiB/rank已冻。

launch实际最终PYTHONPATH为025私有观察器+Plugin与017 Gems，前部原无效旧export被后部覆盖，不用其推断导入；GPU物理8–15/TP8、QSA-only/HC-PLE关闭、M16/i64、原CLI及RPC300保持，0源码数学改动。目标容器docker top只见3个shell，无模型进程。accuracy minimal-regression完整bundle6e94a080已inspect/verify通过，沿用已保存bundle而非只冻SKILL.md。接下来只执行已冻结一次recover和launch。

## 唯一恢复已执行 / 等待READY

15:54:54+08恢复空端口8010一次，signals_sent=0、无容器重启；恢复门禁原8035精确绑定不变，物理8–15各119MiB、0–7原保护负载不动。15:55:18唯一后台driver/client Host3101938/start502594453进入wait，CLIENT_PID/DRIVER_STARTED/WAIT_STARTED原件齐全，0模型请求；未重复launch/run。正在加载/编译/graph，日志既有vendor native扩展缺失fallback警告不当新算子故障，也不据警告声称QSA已命中。实际新API身份以READY/listener为准，不以启动日志namespace PID代Host身份。

原heartbeat qwen3-8-ppu07-gpqa-c64已产品确认更新ACTIVE30min，名称“Qwen3.8 PPU07 accdiag025 目标Mixed C64取证”，仅监控原driver/当前R，首次异常/实际目标覆盖/阶段/实质结果通知，无变化安静，终态暂停。后续严禁再次恢复/重启/埋点变更或额外请求；等待现有driver自动验证8worker来源/graph两类7of7再执行既定C1→C8→C64。

## READY与最初护栏（16:01只读核验）

15:59:16+08 READY，新8010 API Host3094123/start502592140、原argv SHA5744d999不变；8worker实际新probe来源与SHA匹配，两类graph各7/7。READY SHA `e8864eb5b263ef3f0fc1b2095546522013d6661a4988073ae18ba21595c78992`，RUN_STARTED SHA `ef974b1929377e8d38be734849537f9a08118c55b3d9a85178889349498c80d3`。两C1均HTTP200/正常stop/最终B/538tokens，完整token序列逐一相等、prompt/usage/think-end/EOS核验正常；all8rank IndexFunction与IndexPutFunction实际implementation verified_i64_load_before_multiply均True，至少2次FULL实际回放已由GRAPH_REPLAY_CHECK确认。

16:00:44进入C8-guard，10派发/2成功结束/8在途/errors0，全部focus PT为0，符合背景不作完整转储设计。不把C8在途当reasoning-only终态，也不称C64或目标Mixed边界已经覆盖；现有唯一driver待护栏排空后才自然接续既定C64。8010/8035双health200，8035精确原绑定不变；未再重启、改源、重发或扩大请求。538不同于旧024的487仅是不同观察器/新实例环境的观察，不作单变量数值归因或性能收益。当前结果in_progress、无formal gate，监控继续仅实质变化/首次异常/目标覆盖/终态通知。

## 16:35只读heartbeat：早晚目标真实Mixed C64均正常完成

唯一客户端已派发全部128请求；最新82条成功返回/71唯一doc、46在途/errors0。82份raw SHA、完整token/usage和prompt IDs均已独立核对，未见HTTP失败、空final、提前EOS或60K length；此前79响应检查时最大8390tokens，后续不据该旧上限估计在途输出。无FIRST_ANOMALY/CLIENT_ERROR/FINISHED，仍运行而非终态，不暂停监控。双服务精确PID/start/argv与原记录一致、health200，running46/waiting0/preemption0/KV28.97%，日志和8rank推进；服务新窗口illegal access/RPC300超时/WorkerProc异常/ERROR均0。probe/i64双文件/QSA M16当前SHA与冻结值相同。

两目标**实际**首Prefill均8rank覆盖：早seq73 `chatcmpl-accdiag025-q073-97111aae`，16:11:59/step9328；晚seq119 `chatcmpl-accdiag025-q119-89f7b586`，16:22:01/step13414。均64唯一请求、slot63、target computed0/scheduled455、63peer实际Decode scheduled1且computed满足冻结原prompt长度、graphNONE，总518tokens。不是仅依据ADMISSION或客户端并发推断。两次48层output taps每rank均齐全；设备实际输入与冻结prompt SHA均`fb91d24ed5b42c3c23d43d0cd915b44b00439fb908355c7f2fc66fed1481f4c5`，输入/位置/行绑定审计issues空。两首Prefill捕获各约19秒，仅为观察器执行时序，不与旧8192token/262秒异形工作负载计算性能收益。

| 目标 | HTTP完成时间(+08) | 最终答案 | completion tokens | think-end位置 | EOS | raw SHA256 |
|---|---|---|---|---|---|---|
| seq73早期 | 16:22:32.616274 | A | 4183 | 3979 | 248046 | 95f5008586a9d8e72a7ca277ab62e8456778568f9a24744132ad93144dde6052 |
| seq119晚期 | 16:32:05.486868 | A | 4829 | 4410 | 248046 | 552af5127046172f094d79392116c8566e9c7fe200259dac9dbc163c208ee614 |

两份完整API token均与rank0 non-discard实际采样前缀逐个相等；各另有一个post-sampler/pre-bookkeeping token198，不属于API输出。原早EOS/reasoning-only症状在这两个目标未复现，不证明原问题修复或原正式分数达标。C8 doc178先前16:09:37正常最终A6583tokens（非本轮完整PT目标），不与两个C64目标混计。

当前已提交5168份目标PT（每rank646、每目标每rank323），两CPU线程分块独立重算SHA与大小全部一致，tensor bytes每rank3,635,413,256/总约27.09GiB。PT仅属于早晚两个冻结opaque目标，无背景逐层张量转储。每rank含两组48层四frontier、36GDN/12QSA、输入/输出与首32及EOS sampler；哈希一致证明保存字节绑定，不是独立逐层数值reference或终态完整性结论，最终日志尾部和是否有未提交PT仍需自然排空后核验。无异常因此没有新GPU first-state，不称完整全池历史。

本次producer manifest前缀SHA（r0→r7）：`085830e632c93d06a3c0cee0e8e29669e2816a641773a9cfbee7cfc8ff6a3db3`、`f54e946311cdfb3740886c4e7bb02481848375d26537a8a3c57827d87f520f88`、`004ac889c9f96fa4bfadd4c737e9d303f4c49c3c6c050faa3cfed99df9f8547e`、`60bfcf94e075c13dfe039ee75cf97d87f4bdab6c0285de284d1431b71e0049d5`、`32f2c5d908bdf000c734eca7297ebb769c5d0f4595804d5d4919b71f2ef21895`、`76f19b3151bdf3550afc903850c196295db8daf5b9a8683542db03fcba9332da`、`b8a2e73649b00763428fdba6d0b74719a9a57771633e6b6c819001a376564faa`、`5f64bbc8cb174a5fcfdcaff47c635eae07b6961af82d5b9c4367aa5617abc7a6`。这些为当次前缀，不改写原文件；未新增远端审计或推理客户端。

8rank generic gather/scatter最大12604、stride102400、i64/反事实i32偏移均1290649600，byte[5162606080,5162999296)在storage27751628800内、真实i64实现已核；packed实际device索引最大10813。20972未覆盖，不追加请求。背景generic state-byte-check明确not_performed/mismatch=null，不据此说状态比较通过；目标首步保留原完整检查，未记录异常。扫描各rank日志按当时byte-prefix截取，非同时刻step快照，不把扫描中的step差异当rank漂移。首次输出过大导致工具展示截断，仅报告读取问题；随后以紧凑只读扫描补齐全8rank，非模型事故。

本轮心跳0新请求/0信号/0服务或埋点变更/无全量GPQA。保持原monitor ACTIVE，仅现有46请求自然返回，首次异常按原规则取证；终态再核FINAL/日志/PT/raw/身份并暂停。root-cause confidence仍not-isolated，原164/198 failed-score/no gate及性能阻塞不改。

## 终态首次检查与CPU审计计划（18:41+08）

客户端17:57:17完成128条并自然退出，17:58:13 FINISHED/FINAL_EVIDENCE齐全、FREEZE_ERROR/CLIENT_ERROR无。completed128仅代表结束，已发现5个HTTP200/length60000/contentNone/no-think-end的输出健康异常：doc32/71/79/81/88，非网络超时或提前EOS。最早排他marker为17:54:55.194172+08（doc32响应17:54:55.184797），raw SHA `c361379a83dfec48ccb8c4f580085fa89a6ab6a945cbdc56f737a41dc187c4c6`；FIRST SHA `e6d9374a3011f21a02209488bcb512fa0181f75f0c798a893367e15f8f0fb5b4`，FINAL SHA `17c4baea34cadb5691c6a410f1a7ecad76404e762664ba78c1904dd23ad809fd`，FINISHED SHA `d234dbc885bf6028ed282f69d2de5ce381f19aac298b69287ec6ddb335cd35c1`。两目标doc178此前正常A结果不改；双服务精确原绑定health200、8010running/waiting/preemption/KV均0，未重启/补发。

原driver已退出后，仅一次新CPU审计：保存 `CASE/commands/accdiag025-terminal-audit.py` SHA `b2a8c6efa8f81d2785667491ee21195c1663f7d5602563d5d5261773d197ae16`；执行 `python3 CASE/commands/accdiag025-terminal-audit.py --root R`。只读既有6349项FINAL文件、rawHTTP/token、8rank完整日志/PT/first-state及source-before/after，两CPU线程分块重算SHA；排他创建R/post-controller-audit-001，已有则拒绝，不重跑失败审计、不导入Torch/GPU/模型、不改服务。背景无逐层完整张量/状态字节比较；首异常state的step69322只剩doc79/81/71/88，doc32已完成，不能称首异常请求全池现场。所有结论待审计补齐，原正式164/198不改，无新gate/性能结论。

一次CPU审计已完成，report `8404b79e5138a71b26c70f0591cdee4d7da2889f881ba6fbff90622d869c445d`、manifest `e8b8d1b4ab766c2534b54d1318b8b25875ce2af9220b8698a2ed0648a8428f4e`。6348项大小/SHA精确匹配；另1项service-diag.log为活服务继续追加，不能声称6349整文件均匹配。128raw全部HTTP200/117唯一doc、API完整token均匹配rank0真实non-discard前缀，123健康/5length；sum prompt50231/generation1410270精确匹配终态服务counter。各rank646目标PT无未提交项、36首次state真实文件与manifest匹配、完整rank日志冻结后无尾差、真实FULL回放71011。原source-before/after全树一致，当前probe/model/runner/i64/QSA关键字节另只读核验一致。

不修改或重跑原审计，新增一次CPU补充脚本 `CASE/commands/accdiag025-terminal-addendum.py` SHA `63ffd1e62c6039bbe1cfde8d687cf7aa33c4ca092d1dd83cc52ceaa6babdd126`，执行 `python3 CASE/commands/accdiag025-terminal-addendum.py --root R`。排他创建post-controller-audit-001/append-only-addendum-001，只核原service-log冻结长度前缀SHA、分别保存原前缀与新增尾部，检查所有已SHA绑定PT的ZIP目录/data.pkl存在，不把ZIP有效当数值reference。先前scp通过当前连接的SFTP路径不可见失败，未写远端；首个执行尝试仅SHA门禁报文件不存在、未运行审计或创建输出。随后SSH stdin排他传输脚本、核SHA后审计仅执行一次；无模型事故、无推理重试、无服务操作。

## 终态结论与证据边界

128/128 HTTP200、117唯一doc（护栏/目标重复不冒充全量198），123健康final、5个reasoning-only均length60000、无think-end/末EOS。5条API完整tokens都与实际rank0 non-discard前缀一致；不是API丢final、真实网络超时或本轮提前EOS。doc81推理尾部已有选择D的语句仍未切出reasoning；不能据此替代正式content评分，也不能仅凭推理内容判算子根因。早晚doc178均实际MixedC64正常A，原提前EOS未复现；本轮无新非法访存/RPC超时/索引越界/state mismatch/nonfinite记录，目标输入/位置/行映射issues均0。generic12604/packed10813、20972仍not-covered，未追加预算。背景未做状态字节比较，不称通过。

8rank每rank646目标PT已提交且无未提交PT，各有36份首次state（共288、另外冻结副本288），step69322剩4请求；首例doc32已经退出，不是其首Prefill逐层/logits现场。每rank两组48层output和实际目标设备输入均齐全；有限/哈希一致不能证明数值正确、未设独立reference。8rank完整事件日志与终态冻结副本SHA完全一致，sources-before/after全树相同、当前probe/i64/QSA关键SHA再核一致。API sum prompt50231、generation1410270精确等于服务counter；8010/8035原绑定health200、idle、driver已退，未发信号/重启/补请求/全量GPQA。

补充审计report `88712ff0105ccd1a29ed5e0344eb0416116b640f012026cfa72e889a7edffa3d`、manifest `e7c3d7e86c50a894bd9ca17dff50124d6c885bca0006b3798d16aab6d5e749bb`。原service-log冻结1,062,653字节前缀SHA `83d29599188e29758abf5131ab58b95fe71267f275220c51d0dd020a1a8b5010`与FINAL吻合；另404字节追加尾单独冻结SHA `d2a9c400c3ed77596d26199c02b1062402c231c3045e957d8992b669f2f489b2`。6348项精确全文件匹配+1项原前缀匹配，不隐瞒原audit的size mismatch；5744份已绑定PT的ZIP目录/data.pkl均存在，无ZIP失败，不等于CPU逐张量数值reference或全池历史。

判定：本轮执行及证据保全完成；doc178提前EOS not-reproduced、背景60K reasoning-only reproduced、机制not-isolated。无模型修复/正式精度通过/新gate/性能结论；原acc015164/198 failed-score/no gate保持。仅停止监控自动后续动作，服务保持原样，等待用户方向；任何新埋点/服务重启/扩大复现必须先告用户。

原heartbeat `qwen3-8-ppu07-gpqa-c64`已由产品工具确认PAUSED。终态原件位于R/FIRST_ANOMALY.json、req042-doc032-response.raw.json及其余4异常raw/result、runtime/rank*/first-state与focus、terminal-evidence；独立核验回执在R/post-controller-audit-001及其append-only-addendum-001。暂停的是监控，不停止8010/8035，不自动启动下一轮。
