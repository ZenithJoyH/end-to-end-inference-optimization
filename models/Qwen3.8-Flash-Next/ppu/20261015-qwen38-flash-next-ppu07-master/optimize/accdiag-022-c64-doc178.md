# accdiag-022：同实例C64持续更替与doc178提前EOS受控复现

状态：2026-10-17终态，22:05全部128返回/127唯一doc、客户端退出；4条reasoning-only为60K length截断，早晚doc178均正常最终A、旧提前EOS未复现。一次CPU终态审计及857文件SHA/大小核验通过，根因未隔离；accuracy diagnosis / minimal-regression，非formal GPQA、非性能测试。唯一变量为并发/持续更替负载，保持现有8010实例、源码、i64地址计算、QSA M16、graph/采样/stop不变。共128、并发最多64、零重试、零重启、零新增模型埋点；8035/物理0–7未操作。以下在途快照为历史，终态结论见文末。

## 假设与既有证据

原acc014 doc178在63Decode+455Prefill的C64首Prefill后24token提前EOS、无think-end；没有旧首轮hidden/logits。accdiag021 C1正常A3341，runtime002 Mixed C8正常A2164，8rank有效输入/384输出/96QSA/264实际prob-noise核验正常。不能凭小范围正常宣称原C64已修复。本实验只定位C64持续负载能否再次触发症状，不能生成新正式分数或性能收益。

## 现有环境与观察边界

PPU-07，`qwen3.8-flash-opt-ppu07-20261015`，8010/TP8物理8–15；API2623908/start494912777/argvSHA5744d999…。8035保护4161238/start487889425/argvSHA91849d0b…。只读核验双health200、8010 running/waiting/KV/preemptions0，3607prompt/38423generation与R2终态完全相同，旧driver/client已退出。镜像/挂载与当前案例核验，实际源码按当前私有021-v2/017 Gems/6568039 FGVLLM和installed vLLM确认。

现有observer仍写`accdiag-021-prefill-layer-sampler-20261017/runtime-002/runtime`，服务日志仍为其`service-diag.log`。R2固定报告及terminal/post-controller冻结副本不变；活跃journal后续会追加，本轮保存开始byte/SHA/step边界及独立终态新副本，绝不把旧R2 marker或旧Prefix误当新异常。

当前逐层/logits定点观察器只匹配上一轮opaque focus前缀且要求7Decode peers。**不为C64伪装旧前缀、不改配置/埋点规避guard**。本轮新opaque ID使用已有通用GDN索引/边界/状态/graph、rank0实际sampled-token-prefix、所有请求原始HTTP/完整API token和首次异常已有8rank state freeze。没有新C64逐层/logits全向量取证，不称“全程逐层完整因果”。若定位需要这些额外埋点或重启，先报告并等用户方向。首异常无法返回的HTTP/token、不完整GPU冻结和shared-pool last-writer限制如实记录。

## 冻结负载与停止条件

新目录：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-014-full-gpqa-ppu07-c64-qsa-m16-i64-20261017/diagnostics/accdiag-022-c64-doc178-20261017/runtime-001`（R22）。脚本预存同CASE的`commands/accdiag022-control.py`和CPU调度测试副本，执行前补SHA。

总128请求：126个背景唯一doc+doc178两次，共127唯一doc，不是198全量。背景按旧native strict-match doc_id升序选前126个，预先排除原7个空final doc79/88/90/127/145/164/178，避免已知60K尾部先耗尽预算；此选择降低原负载忠实度，结果只属于该局部cohort、不外推原完整GPQA。背景错答记录、不因普通错答提前改负载；目标doc178错答或任一空final/提前EOS/length/HTTP错误、真实索引/状态/非有限值、服务或保护绑定漂移立即停止新派发，在途自然收集、0重试。coverage/admission不满足归incomplete，不算模型故障。

seq63为早期doc178；seq119为晚期doc178，后者至少在118背景已分发后投入，尾部8背景保留用于持续更替维持负载。各目标只在最新实际batch恰有63个本轮在途请求、均computed>0的Decode时提交；新目标首Prefill实际slot/63Decode+455token/graph模式还须用相同步journal独立核验。若目标因余量耗尽未触达，不追加/重复目标，报告not-covered。最大在途64，全局128硬上限覆盖所有请求，无隐藏warmup/health生成请求。

payload逐题来自原formal native samples，沿用原temperature1/top_p.95/top_k20/min_p0/presence0/repetition1/seed1234/stop/max60000，return_token_ids/return_prompt_text不变。不改模板/权重/seed或缩生成上限。graph沿用capture1/2/4/8/16/32/64，本轮验证实际FULL64 replay及目标Mixed实际绑定，不以capture日志或客户端C64冒充命中。

## 执行与证据

执行前脚本冻结：`accdiag022-control.py` SHA `f848326c027cea2ee01bb6b5585cfab70d1c0e1d683d008d5555503577326aa3`，`accdiag022-cpu-test.py` SHA `54d1cc94f3ccebe2e70464e69543c0464d77e3fb5c4bba9c00268801ae7abc23`。本地py_compile和21项stdlib CPU检查通过：63Decode准入正反例/过期绑定、早晚目标预留/补位硬上限、API精确ID与engine带后缀ID区别、首marker排他/不重复、固定字节复制、旧focus前缀隔离；无GPU import/模型请求。准备期核对缓存raw发现API id为精确header，而engine journal另有随机后缀，已在执行前明确分开匹配，不以错误的HTTP后缀断言制造客户端伪异常。

远端命令（均先保存以上副本并核SHA，再执行）：Host `python3 CASE/commands/accdiag022-cpu-test.py CASE/commands/accdiag022-control.py`（CPU-only）；`python3 CASE/commands/accdiag022-control.py --case CASE --mode prepare`（仅冻结/门禁）；门禁通过后同脚本`--mode launch`仅一次，唯一子进程`--mode run`执行全部预算，无其他driver/客户端；终态FINISHED/FINAL_EVIDENCE齐全且原客户端退出后，`--mode audit`仅一次，只读旧HTTP/token和新增observer窗口，排他写terminal-audit.json并核验/补冻8rank日志末尾、已有state manifest、计数差、目标真实Mixed绑定与rank0实际采样前缀。audit无推理/恢复功能；脚本没有重启/kill/改埋点模式。

prepare只读门禁、排他新建R22、冻结请求/源码/服务/observer与日志起始边界；不改源、不重启、不发推理。CPU-only调度/预算/头匹配/旧prefix隔离/首异常单次标记测试通过后，唯一`--mode launch`→`--mode run`。单一客户端内持续补位、实时已有marker/health/精确8035守护，首异常仅向已有observer的STOP_DISPATCH写排他取证通知，触发已加载冻结逻辑，不注入新模型代码或改采样。客户端不得停止/恢复服务。

首异常先保存原始marker、完整已有日志和每个已返回rawHTTP/token；已有8rank first-state异步取证待补齐，不伪造未返回内容。终态只复制已有rank journal的固定结束长度及新窗口、state、全部raw与服务/可读driver日志，SHA manifest和实例/源码/计数复核；缺失明确列出。复用原heartbeat，只读监控既有客户端、实质变化/目标分发完成/首异常/终态通知，无变化安静，终态暂停。

## 结论边界与回退

20:09:56+08 prepare门禁通过：两服务绑定/idle/counters不变，真实CPU测试21项通过；Plugin/Gems/FGVLLM/installed vLLM完整tree与R2一致，i64双SHA/probe/M16核验不变、image/mount parity passed。PREPARED SHA `99bc04213ac07b9e02340304a357fd8b5076fee7486f13c2191e6ad5612ecc59`，requests SHA `1aecdecaa4b7d8583729f7b0ca27e183d36f16583bdbfd5afb4b36aec7a26c76`，observer-boundary SHA `fb370f66bf2d201729c5e5265993227cddcbd9973250b8a06f3879a4aaebba7d`。128行/127唯一doc，背景实际0–129去79/88/90/127共126；目标seq63/119两份prompt SHA均`399792ba67157ac9bba93892de4e9750ba1aecb5c45bdc494044dcfb8929a6b3`，full prompt参考455 IDs已冻结。此时0新请求/0重启/0埋点更改，下一步仅按已保存launch命令一次启动。

当前not_run/incomplete；模型代码无改动，故无回退操作。新首次异常保留后不自动修复/重启/扩大范围；未复现不能证明修复。旧acc014176/198历史gate不改写，不绑定诊断源码；本轮无新formal gate，性能not_run，pr_readiness不适用。

## 已启动（20:11:32+08）

唯一launch成功，client Host361028/start495491890，`RUN_STARTED`20:11:32.514602；脚本与requests SHA同准备回执。初始63背景请求已派发、0完成/63在途/errors0，目标63/119尚待fresh63Decode准入，无首异常/控制错误。服务沿用原实例，无重启、源/埋点/采样更改。复用heartbeat原ID，产品确认ACTIVE、30min只读监控实质变化/目标分发完成/首异常/终态，绝不重复prepare/launch/run。当前早晚目标尚未实际覆盖，不提前报C64复现结果。

20:14:11只读核查：77派发/13真实完成/64在途/errors0；当前running64/waiting0、KV9.09%、preemption0，暂无R22或observer首异常/控制错误。早期doc178 seq63已派发，engine ID`chatcmpl-accdiag022-q063-94592141`；**8rank实际首Prefill均step16422/slot63/computed0，63个peer computed>0、batch descriptor518tokens、graphNONE，即63Decode+455Prefill**，随后新窗口每rank FULL64 replay>690。目标此时尚未返回HTTP，晚期seq119尚未派发，不能用在途无正文当reasoning-only，也不提前认定修复。现有opaque定点logits仍未扩C64，仅使用通用新窗口取证。

20:15:08快照84派发/20真实完成/64在途/errors0。早期doc178 rank0实际post-sampler、non-discard前缀已1068tokens，首token1596，尚无248069或EOS；HTTP尚未返回。这里只报告真实采样前缀，不把它当完成的API usage或“只有reasoning”的已完成故障；原24token提前EOS目前未复现。晚期目标仍待冻结准入，不追加范围。

## 20:47只读监控：两次目标已完成，剩余自然排空

使用项目`inference-accuracy-diagnosis`与accuracy `minimal-regression`方法，只读原客户端/HTTP/observer新增字节窗口，不启动或追加任何请求。20:46:08为128派发/91完成/37在途；20:47:30核验93份真实结果（92唯一doc）、35在途、errors0。93份已返回raw SHA均匹配结果记录；先前91份还逐份验证token长度等于usage、think-end后正常EOS/最终content，后续完整终态审计继续覆盖所有返回。普通背景错答doc13/17/21/106/129保留原件，不当输出健康故障，不计算正式GPQA分数。尚无FIRST_ANOMALY/CLIENT_ERROR/FINISHED/FINAL_EVIDENCE，不能执行终态audit或宣称本轮完成。

| 目标 | 完成时间 +08 | 实际首Prefill（全部8rank） | 原始结果 |
|---|---|---|---|
| seq63 早期doc178 | 20:22:44.033306 | step16422 / slot63 / 63个computed>0 Decode＋455Prefill / total518 / graphNONE | 最终A，4440tokens，think-end位置4011，EOS248046，finish=stop |
| seq119 晚期doc178 | 20:36:50.955611 | step22487 / slot63 / 63个computed>0 Decode＋455Prefill / total518 / graphNONE | 最终A，5226tokens，think-end位置4900，EOS248046，finish=stop |

两份完整prompt455 IDs均与冻结原题一致；raw HTTP SHA分别为`9e4f353e0f4c9e1d7e71e404f25f0b3ce55bbdc07ea822d0048b42540ad9e073`与`1fc51c72969cb7bbc6646a1d4126283b085c3ffcd6313499fa5b1edec2c8119b`，原件R22/`req063-doc178-response.raw.json`、`req119-doc178-response.raw.json`及对应result。两份完整API tokens与rank0 non-discard实际采样前缀逐token相等；各有一个额外post-sampler token198出现在API EOS之后，只是bookkeeping之前的观察尾部，**不称其已发给API客户端**。两次首token均1596，均未复现旧24token提前EOS、无最终答案或reasoning-only症状。

新增窗口8rank均已有6993条真实FULL64 replay绑定。generic gather/scatter最大实际int32索引17044（step23198），pool shape[67753,6,128,128]、stride[102400,16384,128,1]、effective_address_bits64且verified_i64_load_before_multiply=true；i64与反事实i32 row offset同为1745305600，byte区间[6981230080,6981623296)，storage27751628800bytes，合法且无回绕。clear最大21、stride98304、row offset2064384，合法。packed本来i64路径的真实device indices最大16665（step22712），各rank invalid_indices=0、selected_state_nonfinite_pre/post=0。新窗口operator-post mismatch=0、anomaly/forward-exception=0，observer排他FIRST_ANOMALY/STOP_DISPATCH均不存在。**generic 20972仍not-covered**，不能以packed/scheduler高ID冒充覆盖，不追加请求强行跨界。

20:46双服务health200，8010/API2623908/start494912777、8035/4161238/start487889425及两argv SHA不变；客户端361028/start495491890仍在运行，controller SHA仍f848326c…。8010 running37/waiting0/KV34.45%/preemption0（该指标快照早于93完成快照），产物持续推进；新增服务日志233871bytes未发现ERROR/Traceback/illegal-memory/RuntimeError/AssertionError，磁盘约7447GiB空闲。只读日志扫描未返回驱动全历史因果，不替代终态完整可读日志冻结。

保持原heartbeat ACTIVE，仅监控剩余在途自然返回及首次真实异常；全部128预算已派发，不再有补位。终态需原客户端退出、CLIENT_FINISHED/FINISHED/FINAL_EVIDENCE齐全后才允许预存CPU-only audit一次，核补8rank完整尾部与SHA/token/state/counter。当前结论仅为“目标早晚真实C64下未复现、根因not-isolated”；没有新C64逐层hidden/logits全向量，不声称原故障修复或正式精度通过。未重启、未新增埋点、未影响8035、未跑全量GPQA。

## 21:14只读监控：108完成，20仍在途

21:14:09读取progress最后完成21:11:55：128派发/108真实完成/107唯一doc/20在途/errors0。逐份核验108个原始HTTP SHA及完整token长度=usage均一致，输出健康异常、空final、length cap和HTTP error文件均0；已返回最大completion28353tokens。普通背景错答新增doc113，累计13/17/21/106/113/129，仅记录局部答案差异、不计算正式分数、不改变原负载。早晚doc178结果沿用上节已核验原件，未再次请求。

8010 API2623908/start494912777、8035保护4161238/start487889425和各argv SHA均未变，双health200。唯一客户端361028/start495491890仍在，controller SHA f848326c…不变；没有CLIENT_FINISHED/FINISHED/FINAL_EVIDENCE/首次异常或冻结错误marker，终态CPU audit门禁尚未满足，未执行。8010 running20/waiting0/KV37.2417%/preemption0，prompt累计53903、generation累计1333054；相对20:46 generation918471继续推进，日志/metrics持续更新，不能因最后单题完成相隔约2分钟就认定停滞。已耗时约62分37秒，不估ETA；磁盘空闲约7446GiB。

21:14:36起只读扫描本轮新增observer窗口，8rank各自扫描截止step48533/48546/48556/48566/48577/48587/48597/48608（顺序读取的时点不同，不视为rank落后）。generic gather/scatter最大仍17044、stride102400、有效地址64位且load-before-multiply核验真；i64/i32 row offset同1745305600、storage合法，clear最大21。packed实际device index最大仍16665，各rank invalid/state非有限/mismatch/anomaly均0。generic20972继续not-covered，不追加请求。新增服务日志404211bytes中未检出ERROR/Traceback/illegal-memory/RuntimeError/AssertionError。容器只读sha256sum再次核验probe `f7c50b23…`、Gems index `15ddfe41…`/index_put `d8422ca2…`、QSA PPU M16 `3bb3d083…`均与冻结值一致；未改文件或导入新模块。

维持同一heartbeat ACTIVE，仅监控既有20条在途自然收集；禁止重启、补发、改埋点或全量GPQA。当前仍是非终态、症状not-reproduced、根因not-isolated；无新formal gate/性能结论。没有新C64逐层hidden/logits，shared-pool last-writer和已采样未发出尾token限制不变。

## 21:44只读监控：122完成，6条长推理仍在途

21:43:59读取progress最近完成21:43:09：128派发/122真实完成/121唯一doc/6在途/errors0。122份原始HTTP逐份核验SHA及完整token长度=usage均一致，无空final、length cap、HTTP错误或request-error文件；已返回最大completion49225tokens。普通背景错答累计doc10/13/17/21/30/69/76/102/106/113/129共11，只记录原始答案，不变更范围、不计算正式分数。两次doc178正常最终A及其原始证据不变。

21:44:25开始的8rank新增窗口扫描，截止step67238/67292/67308/67325/67341/67357/67373/67389；各rank generic gather/scatter最大17044、stride102400、effective地址64位且load-before-multiply已验证、storage合法，i64和反事实i32 offset同1745305600；clear最大21。packed实际device index最大16665，invalid/nonfinite/operator mismatch/anomaly均0。generic20972仍not-covered，不为覆盖追加请求。新增服务日志591648bytes无ERROR/Traceback/illegal-memory/RuntimeError/AssertionError。只读sha256sum复核probe f7c50b23、Gems i64 index15ddfe41/index_putd8422ca2、QSA PPU M16 3bb3d083均未变。

rank0已采样、non-discard、尚未返回HTTP的6条前缀：seq18/doc18=50824tokens，seq32/doc32=50823，seq72/doc71=50205，seq92/doc94=48636，seq113/doc115=45539，seq125/doc126=44218；各前缀尚无248069或EOS。**这是在途长推理，不是已完成空final或reasoning-only，不拿前缀当API completion usage**；未改max60000或超时，不提前中断/追加/重试。

21:43:59双服务health200，8010/API2623908/start494912777、8035/4161238/start487889425及argv SHA均不变；client361028/start495491890仍运行，controller SHA f848326c一致，无FIRST_ANOMALY/CLIENT_ERROR/冻结错误及终态markers。8010 running6/waiting0/preemption0/KV17.4017%，prompt53903/generation1554581，较21:14的1333054持续增长，最近完成和日志持续推进，尚无明显停滞证据。已耗时约92分27秒，磁盘7446GiB空闲，无可靠ETA不估。

继续原heartbeat ACTIVE和原客户端自然排空；尚不满足原进程退出＋CLIENT_FINISHED/FINISHED/FINAL_EVIDENCE齐全的CPU审计准入，未执行audit或暂停监控。首真实异常仍由已有客户端/observer排他记录并停止新派发（全部128已派发），在途自然保全；不修改旧marker，不自动修复/恢复/重启或扩大范围。当前结论非终态、原doc178症状未复现、根因not-isolated，无新formal gate/性能结论；没有新C64逐层logits/hidden全向量，shared-pool last-writer限制不变。

## 终态：4条60K reasoning-only，doc178提前EOS未复现

22:14首次本轮heartbeat核查到终态后，立即向用户报告首异常事实与R22目录，随后仅执行已冻结、获准的一次CPU `--mode audit`。原client361028已退出、controller SHA f848326c不变，CLIENT_FINISHED/FINISHED/FINAL_EVIDENCE齐全，且此前无terminal-audit/post-controller目录，准入通过；没有再次调用prepare/launch/run、重启或新增推理。原运行22:05:12.575922完成全部128响应（127唯一doc），22:05:35.668096结束冻结，耗时约1小时54分；首次marker为21:58:18.552233，内容和原始时间未改写。客户端状态`stopped-on-first-marker`表示发现异常后停止新派发；当时128已全派发，在途自然收集至结束，0重试。

| seq / doc | 原始响应完成时间 +08 | HTTP / finish | token / think-end / EOS | 最终content |
|---|---|---|---|---|
| 18 / 18 | 21:58:18.547568 | 200 / length | 60000 / 0 / 0 | null |
| 32 / 32 | 21:58:18.968673 | 200 / length | 60000 / 0 / 0 | null |
| 72 / 71 | 21:59:12.671631 | 200 / length | 60000 / 0 / 0 | null |
| 113 / 115 | 22:05:12.562925 | 200 / length | 60000 / 0 / 0 | null |

4条raw原件分别为R22/`req018-doc018-response.raw.json`、`req032-doc032-response.raw.json`、`req072-doc071-response.raw.json`、`req113-doc115-response.raw.json`，对应请求与冻结payload逐字段一致。SHA依次为`1b86f1d71dda76b4eadd01eefd3b3719237d7854e5c4aead7650cd8a9ef29edf`、`9fd585aedf7a44953deb682ef7078a0fc60f828ff555a82634df903ecb6dc390`、`b5948a3a7e997f60fda9c6f2760fabb9d1b1230957efe37d5de777b52966da20`、`744f6ef5da7b092229bd8cf738c9f38b570562317b563b307d822ebc43ad2664`。reasoning长度分别212995/186914/179910/205882字符；均有完整60000 API tokens，与rank0 non-discard实际采样前缀全量相等，无额外尾token、无248069/248046/248044。故**这4条无最终答案的直接机制已核实为未结束思考就触及生成上限，不是提前EOS、网络超时或评测器TIMEOUT占位**；为何持续长推理仍未隔离，不能据此归因GDN、QSA、graph或i64。

其余124响应有最终content；最后两条原在途doc126在21:52:44正常B49711tokens（think-end49377），doc94在21:59:54正常输出B58945tokens（think-end58648、goldA，属于普通错答）。12个正常final背景错答doc10/13/17/21/30/69/76/94/102/106/113/129保留原件，只记录范围内差异，不把本轮非全量cohort计算成正式分数。两次目标doc178仍为正常A4440/5226tokens，prompt455精确匹配、完整API token匹配采样前缀，两次真实63Decode+455Prefill全部8rank已确认；**原doc178 24token提前EOS未复现**，不宣称修复。

### 冻结与独立审计

- `FIRST_ANOMALY.json` SHA `06cc4e22cc80065372aa9206264a5260cd4924f50eef62c3cbe61f81b5b9b981`，类型request-output-health-or-target-answer、seq18/doc18；R22/first-anomaly-existing/PREFIX_SAVED.json及原始prefix日志在，已有observer STOP_DISPATCH保留，无新的device FIRST_ANOMALY。
- `FINAL_EVIDENCE.json` SHA `a23b55a4c6a7bee83c98a33b741c431e48f35229c1d5da46e459c1ed0d344c6b`：857文件、7524574419bytes；CPU逐文件独立读取SHA/大小，无缺失或不一致。首次marker、原始HTTP/token、状态PT及完整可读日志均在其冻结范围；后加audit/补冻副本由独立审计SHA绑定，不篡改原manifest。
- 一次预存`--mode audit`成功，`terminal-audit.json` SHA `5d1af3ac2584d06e0acb3026b4ea89882350ce8c246c287daf2b964cd2f025e1`；128raw SHA/token usage全部一致，prompt总50296/completion总1576267与服务counter差精确一致，无HTTP失败/网络超时。两次doc178完整token前缀相同，额外post-sampler198尾token仍不称已发出。
- 全8rank frozen journal均为live完整日志的精确prefix，终态后再次只读补冻日志尾部，8rank append_after_original_freeze均0，parse error0、max实际请求64、每rank6993次FULL64 replay；新post-controller-complete-logs与audit保留，不重复audit。
- 8rank各36份state PT（共288份），每rank copied_tensor_bytes56229888、预算134217728；manifest与实际文件均在、无capture_error，文件SHA/大小通过。**冻结step76415、reason peer-or-client-first-anomaly，实际req_ids仅seq72/32/92/113；首个doc18已完成退出该batch**。这只证明首异常通知后的可用有界selected-row/last-replay状态已保存，不是doc18最初数值偏离时的全池或36层独立因果历史，也没有新C64逐层hidden/logits/probability全向量。不能把36个PT名字当成36份独立pool历史。

### 索引、运行环境与结论

终态新增窗口8rank generic gather/scatter最大实际int32索引17044、stride102400、shape[67753,6,128,128]；地址64位、load-before-multiply已核真，i64/i32 offset同1745305600、字节区间[6981230080,6981623296)在27751628800bytes storage内。clear最大21、stride98304。packed原i64真实device index最大16665，全部rank invalid/nonfinite0；operator mismatch/anomaly/forward-exception0。**20972边界本轮not-covered**，未为覆盖额外派发。未记录新的非法内存访问；不是对所有未观察路径的排除证明。

服务新增窗口无ERROR/Traceback/illegal-memory/RuntimeError/AssertionError；可读driver ring约2399993bytes，在本轮时间窗口未匹配error/fault/illegal/exception，但不保证全历史完整或独立服务归属。终态完整Plugin/Gems/FGVLLM/installed vLLM源码树与执行前一致；i64 index15ddfe41/index_putd8422ca2、QSA M16 3bb3d083、probe f7c50b23均保留。22:14双health200，8010/API2623908/start494912777、8035/4161238/start487889425及argv SHA未变；running/waiting/KV/preemption均0，服务counter53903prompt/1614690generation与旧baseline3607/38423＋本轮usage精确相等。无影响其他服务、无重启/补发/新埋点/全量GPQA。

最终分类：request-output-health；本轮复现4条长思考达到60K导致reasoning-only，但没有稳定对照/单变量机制闭环证明其底层原因，root_cause_confidence=`not-isolated`。doc178提前EOS未复现，generic大索引边界未覆盖；不外推正式198题分数，不签发gate，不作性能结论。按终态约定暂停原heartbeat（产品确认待补），保留当前服务与全部旧证据，等待用户方向；不得自动恢复、扩范围、加埋点或重跑。下一步若要新的C64逐层/logits或服务重载，须先说明范围并取得用户授权。

产品回执已确认：`qwen3-8-ppu07-gpqa-c64` 更新成功、status=`PAUSED`，原名称/目标会话/周期/提示保留，无重复automation。未停止或重启模型服务；终态后不再自动推理或扩展范围。
