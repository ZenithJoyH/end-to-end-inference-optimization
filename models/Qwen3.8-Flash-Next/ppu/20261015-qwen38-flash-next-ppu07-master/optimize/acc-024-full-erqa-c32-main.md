# acc-024 当前重启主线实例 C32 全量 ERQA

本次8题对照16/16完整、独立CPU审计及300成员回读通过，原driver和CPUwatch2均退出。xhigh5/8截断，medium0/8，8题medium输出均更少；仅限该选定单次C1范围，不是完整GPQA精度通过。原GPQA174/198仍未达88%，ERQA252/400终态保留；同BF168010健康空闲，未重启、全量复测或改默认策略。小时监控转终态后只读整体跟踪，不再派发测试。

当前终态：ERQA400题已完成，原生252/400＝63.00%（无阈值score-only），完整证据及独立CPU审计通过；GPQA重审有效174/198未达88%，原incomplete保留。8010同实例健康空闲。GPQA低分/底层原因未闭环，按用户要求保留小时只读跟踪，不自动复测。下方早期“运行中/未启动”均为历史，详细收尾见文末。

当前（2026-10-31）：JSON聊天审计映射已修复，已有GPQA重审有效但174/198未达88%；原incomplete保留。沿用同一8010的ERQA400/C32已于08:07:56启动，完整wire/真实ID进展与终态审计持续保存；不重启、不重跑GPQA。下方含旧快照，最新分析和接续见文末。

2026-10-29修复验证续验同样未进入ERQA：用户原脚本单次启动后，第0条minimal请求于22:52:23触发CPU RNG clone误分发并HTTP500，服务自然退出。正式续验草案保持禁用、未部署，无新ERQA请求/结果。详见同一acc023的新错误记录。

终态not_run：上游GPQA首批执行于2026-10-29 18:55:12触发当前8010 Mamba规格一致性断言后服务退出，原控制器自然失败并未进入ERQA；没有FORMAL_STARTED／wire推理或原生ERQA结果。保留已完成的400题/630图CPU preflight，不将它当精度结果。monitor已删除，不手动补启动／重启服务／重跑。故障证据和限制见acc023。

2026-10-29用户授权，串行复用[acc023控制器](acc-023-full-gpqa-c32-main.md)，在GPQA终态完整、同实例同源码健康空闲后运行一次ERQA400/C32。无新服务动作、额外smoke、8035或提交推送。

原生ERQA/test400唯一question_id、630图引用、113多图、最大16；dataset SHA c02963830b51a6103f07d4e2fa60c76ba566d7af88214bcb4545c7475658663c。新CPU flageval/mm-eval:v0.3.8_1，保留原生prompt/HttpClient/parser/BaseEvaluator，仅桥接固定采样并CPU旁录原始HTTP一次，不改变原重试。独立chat UUID、use_cache false、num_infers1、workers32、max60000/7200s，native最多5总尝试/题、整项一次，不借旧答案。threshold=null，报告正确数/400、原生分数及分项，不签ERQA gate。

E=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-024-full-erqa-ppu07-c32-main-20261029。原native data/source及16图payload零请求预检，正式保存wire bytes/headers/token及真实question_id-index映射、items/evaluated/result、source/runtime前后和终态manifest。未采逐层／设备kernel trace；历史C64/旧软件分数不作因果对照。当前preparing，尚未启动正式ERQA。

预检已完成：PREPARED SHA3c6409ff7efad912102361b7fbb7ae30e16badd61b0a9d3f7e2f63b55bc2fd61，652冻结文件清单SHA5af91175f4854cbc7da1cf9f2860eed7a0a6839ddfdd2f6a4d360f67203002e1。由acc023唯一控制器自然串行启动，不单独launch，30分钟只读monitor qwen-ppu07-c32-gpqa-erqa随两项全部终态删除。

### 新一轮原脚本验证授权

用户在明确“再用同一脚本启动8010一次，先完成10条最小回归，通过后继续C32 GPQA/ERQA”的问题后回复“允许”。新验证目录为 `acc-023.../repair-validation-002`，旧 `repair-validation-001` 与 continuation 首错完整保留。唯一新启动必须直接调用 `/mnt/nfs/users/jinghao/qwen3.8-flash/start-model.sh`（SHA `fc456e30929dc4cb7942405a59d083910e13acffa856c465964245c0aea61890`）；不修改脚本、不额外重启、不访问8035及物理0–7、不启用encoder graph、不提交推送。先2C1→8C8，独立CPU审计通过后串行GPQA198/ERQA400各C32；使用全新结果目录与响应cache。当前仅准备，尚未新启动或发模型请求。


### 2026-10-30 续验前置状态

GPQA/ERQA新正式队列均未启动。原脚本新8010已健康运行，两条C1完整成功，但R3因prefix hit=0停在护栏；源码AST复核得到6400-token对齐，原1620输入不足。保留首错与incomplete审计，待批准新增2条预算，以当前同服务完成6500-token C1×2及C8×8后再继续C32串行正式。每小时主动汇报已启用，不重启、不访问8035、不提交推送。


2026-10-30 00:53（Asia/Shanghai）每小时只读核验：PPU-07连接通过；当前API2288060/start600406479/argv SHA仍与R3 READY一致，health200，running/waiting/KV/preemptions全0，prefix queries3240/hits0无增加。原driver已退出，R3仍只有2条完整响应；validation-continued-001及两项repair-formal-001目录均不存在。用户脚本及Gems注册/Mamba helper/runner/native Mamba SHA与冻结值一致，磁盘余1939.9GiB。6500-token续验输入已备，新增2条预算批准仍pending，未派发请求或服务动作；每小时monitor继续ACTIVE。


<!-- hourly-monitor-current -->
2026-10-30 18:31:48+08:00 hourly read-only check: PPU-07 connectivity passed. Exact API1580148/start605206296/argv/listener unchanged, health200/running0/waiting0/KV0/preemptions0, RPC1800. Original validation driver/coordinator absent. Still2 original HTTP200 responses (757/553 tokens), prefix queries13000/hits6400,0C8 and no formal repair-formal-002 GPQA/ERQA directories. Script/critical SHA and25 original diagnosis members verified. Latest sampling-chain source/analysis manifests (21 and3 members) fully verified; all20 current source SHAs match, same API and request budget. Service-log inode stable, idle appends only, no new failure markers; disk free1930.92GiB. No new localization or validation this hour. Main supported cause remains RNG discarded-prefill rollback incompatibility: Gems advances31040 while Plugin rewinds4; CPU source replay supports mechanism but live request RNG/logits/state causality remains unobserved. Saved entry-offset restoration is the repair direction, not yet applied. C1 still failed; C8/formal pending a scoped repair and valid minimal regression. Monitor remains read-only/hourly active; no inference/GPU/compilation/source/cache/service action/8035/physical0-7 access.
<!-- /hourly-monitor-current -->


### 新增预算已批准，同实例续验

用户已直接批准“允许新增2条预算并继续”，覆盖同8010执行2条6500-token C1+8C8，新10+父2=12，0新启动/重启；通过独立CPU审计后续C32 GPQA/ERQA。未来命令将保存G0/commands/prefix-continuation-approved-v2，不改R3冻结文件和生产源码。controller SHA20f7a5ca0c431be4358868c0eb7a36826701c32f01190f986af0a1710ba02b6b；stager SHA07f2589678bc115e19ba0837cccc38b6057165f0a9f433ee9e8e7e37842fa08d；audit SHA54323648c6529c21da9ed08ebafc4bb450897fa0b2434729c0298ad9106dabb1。本地AST、重复/异PID、延迟stats与外部计数拒绝CPU检查通过。


续验已唯一launch：Host3491843/start603288178/argvSHA400cff7d5329a964503a110e34b94353120a212824c4d1150722d7576b14fbac；PREPAREDSHAa517568cf5f47cf276a541625a40045dea46be13abbf5aeb29066be4b89f3e70。当前第0条6500输入已派发，尚无完整响应，不计完成；同8010未重启。小时monitor已更新到新controller和已批准预算，不再索要同一许可。


2026-10-30 08:03前置续验CPU定位：acc023长shape的FlagGems MM首次编译/在线选参持续越过300s RPC队列预算，非客户端600s超时；细节及119成员冻结证据见同一acc023文档“RPC只读定位结论”。尚无单kernel卡死证据，缺故障栈/设备trace，修复未验证。ERQA仍0启动/0请求，无新分数；本轮仅CPU分析，不恢复8010或补启动正式。


2026-10-30 new explicit authorization: RPC1800 repair, one user-script8010 startup, new10-request minimal/audit, then C32 GPQA and ERQA sequentially. New formal dirs repair-formal-002. Native ERQA400/630images/score-only, sampling and retries unchanged; not started yet. See acc023 RPC repair plan.

R4 unique queue launched: coordinator Host1579334/start605206084/argvSHA29c3c2932a6ed7971cc172ca7bf4e7bab85737185fc770bac7a9374aa46118d1; driver1579336/start605206097/argvSHA948dc6a324074248999d216551630ef6f02864a9a0e5b46f090f718f89b2c669. PREPARED SHA074e8828f4449dcbbdc9feb539290645c29161fa1949e030599b0a90c66b81b3; source SHA668a4bcffc0b63ffc4bc34fb47009d772a0b096604be288abb148f2f9312064b;10 frozen requests SHAd9abbc6cdeff3f9633c38fee41960d4f4ee8fcd7a585d14a69942d21fb888e25. User start-model.sh executed ONCE at2026-10-30T12:57:16+08:00/epoch1793336236.386, exit0, new scriptSHA875788ff. Log inode27006868286/device41. Loading/capture underway; no READY/requests or formal yet at initial check. All subsequent monitoring must follow these exact original processes, no new launch or recovery.


R4 service is healthy but own validation evidence guard stopped before0inference; corrected using installed setproctitle CPU proof. Same-instance validation-only continuation R4/validation-continued-001 uses original10 budget/0new starts. Native ERQA400/C32 remains queued only after independent minimal audit and GPQA terminal; no formal input/metric/sampling changes.

Corrected same-instance validation dispatched once: R4/validation-continued-001 PREPARED SHA8841110db82f830a78a4fee1cf9aa6d425c95dfdd8025548c84d39535e760021, READY SHAda9f971baabcb595b686a6b1f4c95fa1ee03699fea1ff464ae1dd25fad0f85ed. Coordinator Host1940166/start605310201/argvSHAfcb848449d60f44366be769d7498542abba494fbfd0fbba1eafb44f0c07e24fe; driver1940690/start605310355/argvSHA39f037712fed5bc50854738c2e2742718576e74acd1268f93923bfb0224d78ee. RUN_STARTED1793337278.490; initial observation1dispatched/0completed,0newstarts. Same API1580148; no new model/math/source/cache-policy change. Original parent errors remain frozen; monitor tracks these exact new processes only.

2026-10-30最新：RPC1800通过用户脚本单次启动后，同实例长prefix最小回归两条HTTP200/goldB，但输出757/553token不一致，原队列停止；C8/GPQA/ERQA均未启动。repair-formal-002目录不存在，无新ERQA分数。源前后相同、8010健康空闲保留；证据及SHA见acc023最新段。完整CPU终态审计incomplete，不自动补队列或再次启动。

CPU localization update: discarded-prefill RNG offset accounting gap reproduced from real frozen function bodies using metadata mocks, not a model/device test. GPQA/ERQA remain not started; source compatibility proof does not pass the failed C1 guard. See acc023 RNG CPU evidence.

C1最新定位：原生align分块令prefix miss多一次被丢弃采样；Gems推进31040/Plugin回退4使有效采样随机流偏移不同，当前实例已有Gems exponential实际首次命中日志及CPU原函数体重放。主要原因strongly-supported，缺本次live RNG/logits/state因果现场；未应用修复/新增推理，ERQA仍not started。证据/完整限制见acc023 sampling-chain-analysis-001。


### RNG repair queue frozen before the authorized restart

A=G0/commands/rng-repair-20261030-v3 is frozen: SHA256.json=6d38913c0290be9fdeb4a2b9a2b4e8c17588cebaa1235bed8f9a8716b5e7ffc4. ControllerSHA7b494718eb63b63429e541221d810d0df50842c2e31f8c1ec6d7155084fd1a6c, independent auditorSHA02ad6f385d7d21b3c6f3c33bd922c229bf14c62abcf3bc6ec702db14c1371edb, coordinatorSHAdbf57f3617023cc8734a0f5fa27d1a41b32801f0bd7e0b9ed1c43587ae13a5bd. R5=G0/repair-validation-005 CPU stage completed with PREPARED SHAcd02e25408352ffa313ba597b1d9652282583ff750ec45f674c3674866676b54, requestsSHA6d3d7dcfb40fcb94b51d30b86cec141f3ca978ec40c5c3518592d84feadcfcd6, sourceSHA0a672c8fb3d7c253e04aaaae03739396cbdc87497ab8cf4758c3cda153b9a9b9. New request IDs only; original 2x6500 C1 +4long/4short C8 payloads unchanged. Native scriptSHA875788ff unchanged; RPC1800/HTTP2400; no cache clearing. Exact oldAPI1580148/start605206296 is sole SIGTERM target, wait all owned critical workers drain and physical8–15 free, invoke user start-model.sh once. No force kills or recovery. Prepared0 starts/requests; new restart budget stillunused before coordinator launch.

Execution command saved: python3 -B A/coordinator.py --mode launch. The unique coordinator launches R5 once, waits original driver exit, requires complete10 responses/second-prefix>=6400/C1 full-token equality/capture7/7 each/2 native FULL replays/actual unpadded8 FULL/source unchanged, then runs independent CPU audit once. Only allpassed stages new repair-formal-003 and one native C32 GPQA198→ERQA400 queue. Serialcap32, GPQA strict .88 formal-gate and ERQA native score-only, fresh UUID/cache and native retries preserved. Any failure freezes existing evidence and stops progression; no fake FINISHED, no automatic re-run/restart, no8035/commits/push. Existing hourly monitor follows this queue only.


2026-10-30 19:40:38–19:40:40+08 single restart executed: exactly one pidfd SIGTERM to oldAPI1580148; API/EngineCore/8workers naturally drained and physical8–15 free. User original script launched once at1793360440.7354064 withSHA875788ff unchanged, return0. New API READY pending; no inference sent yet. Unique coordinator1335508/start607626350/argvSHA4d65d25c584752e73e8cea459e4ad00d6ed84f5c473f32159eaa2ff98148eec9 and minimal driver1335510/start607626361/argvSHAd3100cf04476e5280b290cc3130b6beed57f5cf4dfbba6fd939565256d63bc34 bound to nativePID receipts. Restart budget1/1 used; no further recovery/restart. Existing hourly qwen-ppu07-c32 ACTIVE now follows R5/formal003 only; oldR4 history preserved. No8035/commit/push.


2026-10-30 19:43:09 read-only: newAPI1336953/start607626732/argvSHAc1b658b05137910a59f347c6fbb9048146d22f1274886b324b761803a9f30fbc READY at1793360586.326011, both graph captures7/7; first6500-token seq0 dispatched19:43:06. Old API no longer current. Single restart1/1, no furtherstarts; current health200. Native minimal is running, no complete response yet/noC8/formal.


2026-10-30 19:44:53 read-only: R5 two6500token C1 complete HTTP200/goldB/stop, output553/553 and native C1_REPEAT_CHECK tokens_equal=true; second prefix actual hit6400 (0→6400), FULL_delta1013 beforeC8. Seq0 elapsed40.37s/seq1 34.01s from native dispatch/completion events; not a controlled performance result. EightC8 seq2..9 dispatched19:44:20.916–.920, currently in-flight; no extra requests or retries. No formal/evaluator yet. New currentAPI health200, zero preemptions. This resolves the observed repeat-token guard in this bounded C1 case; formal precision and wholeC8 stillpending, no gate claim.


2026-10-30 19:48:32 R5 native terminal passed:10/10 complete HTTP200/goldB/nonemptyfinal/stop/EOS, no retries/length/RPC failure; C1 553/553 exacttoken repeat and secondprefix6400; C8 actualunpadded8 FULL_delta244, totalFULL1619; sourcebefore/after equal, API1336953 healthyidle/preempt0. FINISHED summarySHAe8a983cf2b6998c86cfc20e2bf28ec4e1071875e34785a727b1927f51909ebb7, manifestSHA07b335ee00201b76304703fc2096086d236cdb91a652e51d93dc0e1ac6929b50. Unique originaldriver/coordinator exited.

Original terminal-audit-001 failed only on overly narrow log regex `mamba_cache_mode...align`; dependent graph-path check then failed. All10 responses and other29 checks valid. Actual frozen service.log lines26/27 explicitly say native "Mamba cache mode is set to 'align'" and "Prefix caching in Mamba cache 'align' mode is currently enabled"; current SHA-bound native model_executor/models/config.py emits that exact wording. This is an auditor formatting defect, not a runtime/model failure; original audit/ERROR retained, no gate claimed yet.

Before CPU correction execution, save A2=G0/commands/rng-formal-20261030-v1: SHA256.json8bd53ca05996f4f0324ce84ff9fe464666d73fe654ad4e450ca3f10c38c96b4b, revised auditorae0f1f8db5c566e2eae0007724cb8ab05b1bb509d0dfd3aec0bd57b50fd986f9, coordinatorc0252affcf45227b276a7a80e5c4f1b49601ad08abe1daef91bd3c96a2989658. Only accepts exact native align log variants and binds original/future auditor separately;3 positive/4 negative CPU regex cases pass, all31 original checks retained plus explicit correction provenance. New CPU report terminal-audit-002, originalfrozeninputs/PREPARED/firstaudit unchanged. W2=R5/coordination-002 invokes onlynewCPUaudit, then original authorized formal003 stage/prepare/launch once ifpassed; neverlaunchesmodel/minimal/service. Command saved python3 -B A2/coordinator.py --mode launch. No extra model requests or restart, GPQA/ERQA still0formal untilnative markers.


2026-10-30 revised CPU terminal-audit-002 passed32/32 checks,10 valid complete responses, no new requests/devicework/serviceactions. Original terminal-audit-001/coordination-001 failure preserved. Unique CPU/formal-only continuation coordinator1653848/start607700868/argvSHA4abe3f7facd6c732ff351ee614c02483325fbbd7fc5bc19fb9cd3ba57ddf93e8 started once, W2=R5/coordination-002. Formal repair-formal-003 preparation is in progress; await CLIENT_PID/FORMAL_STARTED, no formal score yet. SameAPI1336953 retained; no secondrestart or minimal rerun.


### Sampling fix model minimal accepted; fresh native C32 formal started

2026-10-30 19:53:38+08 FORMAL_STARTED epoch1793361218.159551, GPQA198/C32,0new modelrestart/smoke. Native log19:53:52 confirms concurrent32/timeout7200 and Cached requests0/remaining198; no old answers reused. Fresh config/cacheUUID3153eafb4cc341e8a6230b6a2e653648; native strict threshold.88, original sampling/stop/max60000/eval_seed42 retained. Unique formalcontroller1666133/start607704298/argvSHA15cb2a3da1541b04377163791247809dc13cdc109f309f17304f4f434670e2f0, controllerSHAf253035e14b7c8cebcd0f0deb63751910dbd7113d8bbbd3689ef6e3886a4eb5c. BothGPQA/ERQA preflight/preparation passed, ERQA native400/workers32 is serial pending. No formal score/gate yet; score-only forERQA.

R5 independentCPU audit002 REPORTSHA c1a555aaec65dbf7d4c8d29b2038db6d3f9db339af3c5302d3d8a58ac75a4798, manifestSHA833dac3fbf9dcdbfaa2bebf3d32deee1daa4fe14b58c2f9061298896b5450ed7,32/32passed; originalaudit001fail kept. Current model sampling fix passes requested bounded2longC1→C8 and native graph guards, not equivalent to full formal accuracy or independent per-rank/kernel/RNGoffset trace. One8010 restart used exactly; same newAPI1336953/start607626732 retainsBF16/image16/encodergraphoff/allpreviousfixes and unmodifiedstart-model.sh875788ff. Wholequeue no commit/push/8035. Hourly qwen-ppu07-c32 remainsACTIVE onW2/formal003; terminal results/source/samples/native score/manifests and finalaudit must be complete before final gate report. Current GPQA underway, ERQA notstarted, no inference outsidefixedminimal and authorizedformalqueue.


19:55:54 final read-only check in this turn: same formal-boundAPI1336953/start607626732/argv unchanged, health200, actualrunning32/waiting0/KV0.0346896568/preemptions0. Currentformal newbyte/inode log window has noTraceback/EngineCorefatal/WorkerProc exception/illegalmemory/TimeoutError; no CLIENT_ERROR-v2/FREEZE_ERROR/SUITE_FINISHED. GPQA continues; no score yet.


2026-10-30 19:58+08 read-only monitor: originalformal1666133 and W2coordinator1653848 retain boundstart/argv and areactive; sameAPI1336953/start607626732/listener/argv, health200, running32/waiting0/KV0.0397878941/preemptions0. GPQA native progress has reached1/198; no samples/doc-cache mapping audited yet, so this is nativeprogress only, not an independently verified unique completion count or score. progress_score helper still0 and not used as score. ERQA400 remains serial queued. Newformal logwindow has nofatal/RPC TimeoutError, noCLIENT_ERROR/FREEZE/SUITE_FINISHED; diskfree1854.46GiB. User script875788ff, RNG3files/Mamba/Gems registration SHA, all3 repoHEAD/staged-content and audit002 report/manifest match frozenbindings. No newmodel/device/service/source/cache actions or8035. Recentmain update19:55 already reported current phase; no duplicate notification withinminutes, hourlymonitor remainsACTIVE. Nextstep observe originalGPQA thenERQA/terminalaudit; no manuallaunch/retry.


2026-10-30 21:01+08 hourly read-only monitor: current GPQA formal003 remains active C32; same boundAPI1336953/start607626732/listener/argv health200/running32/waiting0/KV0.4651420051/preemptions0. Original formalcontroller1666133 and W2coordinator1653848 active. CPU native-cache-key/full-prompt-doc audit independently confirms124/198 unique docs in the fresh SQLite cache and124 complete native parsed API objects mapped to exactly the same124 doc IDs. All124 stop, valid fulltoken/prompt usage, thinkend and EOS;0emptyfinal/60Klength/placeholders/transport error lines in this prefix. Raw198 and processed198 doc hashes exactly match frozen provenance; no partial/helper score treated as final. No GPQA results/samples/FINISHED/gate yet; ERQA400 remains serial queued. Currentformal newbyte/inode service window has nofatal/RPC TimeoutError; no newCLIENT_ERROR/FREEZE/W2ERROR. Diskfree1404.33GiB. Script/RNG3files/Mamba/Gems registration SHA and all3HEAD/staged-content unchanged. Nextstep continue original GPQA thenERQA and finalCPU audits, no manualrequests or service actions. Hourly notification due and sent with124/198 only, not accuracy/pass claim.

CPU progress evidence is G/diagnostics/hourly-progress-20261030T2058-v2: REPORT SHA0f2aaa22d21e9875224d12f802766eb1259c25c5bfe9e404366da3b083fe3699; post-process terminal-manifest SHAd3ec843eee79703cc21be6371861d2aa8e23b7a6a2b8908a018ad633560ed051,7 members independently hash-readback verified. Read-only original SQLite snapshot, original native hash_args, frozen task preprocessing/Template, complete native-log prefix, no evaluator/LM/device execution or score. Initial2058 CPU audit failed because it compared native source_tree canonical-entry digest against raw bytes; original exit/error retained, v2 uses exact original source_tree digest and validates raw/processed198 doc identities. Original v2 manifest records an in-process log snapshot; definitive terminal-manifest binds final audit.log/exit/report/originalmanifest after exit. This is CPU audit bookkeeping only, no production/source/runtime issue or extra inference.


2026-10-30 21:57:49+08 hourly read-only: GPQA formal003 remains active, CPU nativecache/fullprompt audit verifies195/198 unique doc IDs and195 complete parsedAPI objects with same docset;3in-flight.190normal completions,5doc32/71/79/88/127 reached60000tokens/finishlength/contentNone/no thinkend, no token/usage evidence mismatch. These are length-capped model outputs, not RPC/network timeouts; native helper excludesNone and is not formal score. First native UTC timestamps13:15:42,13:25:10,13:28:55,13:32:13,13:55:47 (local21:15:42 through21:55:47), retained full nativeprefix lines512/581/590/596/620. Original workflow continues natural collection with0manualretry. No finalresults/samples/gate/SUITE_FINISHED yet; ERQA400 stillqueued. SameAPI1336953/start607626732/listener/argv health200/running3/waiting0/KV0.1091191112/preempt0, originalformal1666133/W2coordinator1653848active; currentformal window nofatal/RPC TimeoutError and no newCLIENT_ERROR/FREEZE/W2ERROR. Script/source5critical/threeHEAD/staged-content unchanged; diskfree1403.95GiB. Nextstep await last3 then originalnative scoring/CPUaudit and serialERQA; no model/service/source/cache/GPU/8035/commit/push actions.

Current CPU snapshot G/diagnostics/hourly-progress-20261030T2155 uses new output directory and preserved currentcase only: REPORT058af997801588c4f9fda8ae6e295c950a932052817f133e7ed1d4cfa11dcbc7; manifest58ae95e6701254926673c8c5413121a79eecc0e37a1a88042f97198634135674 (in-flight stdout excluded); postexit terminal-manifestff26f46491b7705710883f445ecc8fe5f91e59e3c712fb065df4161557ec7723 independently verified. Native hash_args plus actualtask preprocessing/template and raw/eval198 doc SHA validation;195cachekeys and195 completeAPI objects map uniquely tosame195docs, fivecachevaluesNone/notstrings are output-parse values, not transporterrors. No newnative score calculated or fullgpqa_audit run bymonitor. All prior snapshots/firsterrors retained.


2026-10-30 22:59:47+08 hourly terminal review: native GPQA completed198 unique docs/396 strict+flexible rows; strict174/198=0.8787878787878788 < frozen.88 (24wrong:8length60000/contentNone→TIMEOUT placeholders plus16ordinary wrong). Eight lengthdocs32/71/79/88/127/145/147/185;190stop,0token/usage evidence issues or native transporterror lines. No RPC/device fatal in model service window. Native results22:20:41/43 saved, originalFINAL_SUMMARY/FINISHED verdict remainsincomplete: postrun native-audit at22:24:03 failed prompt_doc_binding, controller/W2 exited and didnotstartERQA400. No formalpass gate or SUITE_FINISHED, no optimization continuation. Same currentAPI1336953/start607626732/listener/argv health200/running0/waiting0/KV0/preempt0; script/5criticalsource/3HEAD/staged-content unchanged, free1403.75GiB. Originalformal/native-audit processes gone; evaluatorcontainer retained only tail -f /dev/null, no helper running. No restart/retry/source/evaluatorrepair/ERQAlaunch/GPU/8035/commit/push inmonitor.

Issue acc023-formal003-terminal-JSON-chat-binding-and-low-score (gate-blocking): original response_observations picks longest nativearguments string, which is serialized JSON chat in arguments.gen_args_0.arg_0[0]; searching it verbatim inside rendered prompt_text produces0/198 matches. PureCPU decoding that exact existing JSON yields198 unique nativeuser prompts, all198 API objects map uniquely and actualsample.resps agrees190content/eightTIMEOUT. This confirms auditor format/accounting defect, not model RPC failure. Native174/198 rawscore is independently verified but remainsbelowthreshold even aftermapping accounted for; original terminalincomplete is immutable and no gate is issued. Model low-score causal attribution/RNG/logits/Mamba-state trace absent; do not blameBF16/samplingfix or borrowoldscore. Futuremain work may repairCPUauditor binding and diagnose24wrong cases under separately scoped actions; monitor neverappliesfix or resumes stoppedqueue. Existing hourlyreport remainsACTIVE because user requested progress until entirefix/GPQA/ERQA task complete or userstop.

CPU-only terminalfreeze G/diagnostics/terminal-freeze-20261030T2253: REPORT3b78f72bd28dcb4865d1e50d79296db035d5b73905a9cbb29f38b5c6d2d91330/postexit terminal-manifest0280794368c207880f3148b9606650040e9e6ef61b20fde22b8df6676d1b6721. TerminalSQLite safe-string decoder returnsNone for198nonstring-decodable values; this is not198 networkfailures, finalAPI/samples establish8lengthonly. IndependentpureCPU terminal-evidence-review-001 script9e7c29bd709704115237dd5ba5883b9d648f2a89f41b89d49de837bdbcc20362, REPORTbe2bda34bdab6f6f8270c400b75ac186da718978e72e53048b568fc96b1ca661, terminal-manifestc43f6ed5cff56a5d6ce1073a60c46192d38de177fdd0b616e1af4e19e0dd8792 (13members readbackpass). Fivechecks passed:113originalmanifest members,56frozeninputs/provenancepair/sourcebeforeafter,198unique/396rows/samecontentperdocfilters,decodednativeJSON API/samplemapping198 and190content/eightplaceholderagreement, originalfailedterminal+ERQAunstarted/controllersexited. Originalmanifestc46561d7fffe2adbde034a2841f48596b4e811be99088b00218c2a1d5310b67f/summaryc85551cf524abc62cedcfa824bb140c110df8853c24ad336b1753b0b2cfaddce remainunchanged. Native resultSHA68a327b8030e2796219a522d49f08ce1ade823e2337930790358f884217f5c73; sampleSHA2a108a5cae861dc1741527ff29c7aa71e6ed1e4ad6462c7fffc6112a37add350. Existingcomplete rawAPIjsonlSHA8a0a214e606bdb9113ccd0d0900be852314151cd79123389c01fd0cb2d5e8f4c. Originalsuite-terminal-audit-001 report509cfef483c1c1975741de3204179705340c7c57b3caf23a3c2509976a9cc5a5=incomplete, retains staleR metadata repair-validation-005/validation-continued-001; newCPUreview usescorrectR5, nooriginalreceipt rewritten. Allfirsterrors/outputs retained; CPUreview isnot a newformalrun or originalgate repair.


2026-10-30 23:53:25+08 hourly read-only follow-up: no new execution, validation or diagnosis result this hour. GPQA native174/198=87.8788% remainsbelow88%; originalformal terminalincomplete and JSON-chat audit binding issue remainfrozen. ERQA FORMAL_STARTED absent, no newformal directory or SUITE_FINISHED; originalformal1666133/W2coordinator1653848 remainexited. ExactsameAPI1336953/start607626732/listener/argv health200/running0/waiting0/KV0/preempt0, no newmodel fatal/RPC TimeoutError in currentformal window. Key5source/threeHEAD/staged-content/userstartscript unchanged; originalsummary/manifest and13member terminalreview hash-readback unchanged; diskfree1403.68GiB. No newinference/GPU/CPUauditexecution/source/cache/service/8035/commit/push actions. Currentblocker remainsauditorJSONbinding plusnative low-score/8length; next main-task work must address those and ERQAcontinuation under its authorized scope, monitor doesnotresume/retry. User-requested hourlyupdates remainACTIVE; task incomplete, no formalpassgate.


2026-10-31 00:59:33+08 hourly read-only follow-up: no new repair/validation/diagnosis result. Originalformal/W2 remainexited, ERQAunstarted/noSUITE_FINISHED/no newformal directory. NativeGPQA174/198below88% and originalauditJSONbinding/incomplete remainfrozen. ExactsameAPI1336953/start607626732/listener/argv health200/running0/waiting0/KV0/preempt0, no newservicefatal/RPCTimeoutError;5criticalsource/threeHEAD-stagedcontent/userstartscript/originalsummarymanifest and13member CPUreview SHA unchanged, free1403.67GiB. No inference/GPU/CPUaudit rerun/source/cache/service/8035/commit/push actions. Blocker remainsCPUauditorbinding and low-score/8length; main-task followup needed, monitor doesnotrepair/resume/askduplicateapproval. UserhourlyupdatesACTIVE, no validformalpassgate.


2026-10-31 01:59:42+08 小时只读核验：无新增修复、诊断或验证结果。原GPQA174/198（87.8788%）及审计incomplete继续冻结；原formal/W2均退出，ERQA未启动，无新formal目录或SUITE_FINISHED。精确同一8010实例健康200，running/waiting/KV/preemption均0，无新RPC/设备fatal；关键源码、三库HEAD及暂存内容、用户脚本、原summary/manifest和13成员CPU证据SHA不变，磁盘余1403.41GiB。未执行推理、审计重跑、源码/cache变更或服务操作，未访问8035。阻塞仍为审计JSON映射及低分原因，待主任务继续处理；monitor不恢复队列，保留用户要求的小时汇报。


2026-10-31 03:02:05+08 小时只读核验：本小时无新增诊断、修复或验证结果。GPQA174/198（87.8788%）及原审计incomplete保持冻结，formal/W2均已退出，当前没有评测运行；ERQA仍未启动，无新formal目录或SUITE_FINISHED。精确同一8010健康200，running/waiting/KV/preemption均0，无新服务fatal/RPC错误；关键源码、三库HEAD/暂存内容、用户脚本及原冻结证据SHA不变，磁盘余1403.29GiB。仅执行不写远端文件的只读检查，未重跑CPU审计/推理/GPU、未修改源码/cache或操作服务，未访问8035。阻塞仍为审计JSON映射及低分原因，后续待主任务处理；监控保持小时汇报，不恢复队列。


2026-10-31 04:01:49+08 小时只读核验：暂无新增诊断、修复或验证。原GPQA174/198（87.8788%）及审计incomplete继续冻结，formal/W2保持退出，ERQA未启动，无新formal目录或SUITE_FINISHED。同一精确8010健康200，running/waiting/KV/preemption均0，无新服务fatal/RPC错误；源码、三库HEAD/暂存内容、原启动脚本及冻结证据SHA不变，磁盘余1403.24GiB。未重跑CPU审计、推理或GPU，未改源码/cache或操作服务，未访问8035。阻塞仍是审计映射和低分原因；后续待主任务处理，监控不恢复队列，保留小时汇报。


2026-10-31 05:06:22+08 小时只读核验：暂无新增诊断、修复或验证，GPQA174/198（87.8788%）及原审计incomplete保持冻结；formal/W2仍退出，ERQA未启动，无新formal目录/SUITE_FINISHED。同一精确8010健康200，running/waiting/KV/preemption均0，无新服务fatal/RPC错误；关键源码、三库HEAD/暂存内容、原脚本及冻结证据SHA不变，磁盘余1402.91GiB。未重跑审计/推理/GPU、未改源码/cache或操作服务，未访问8035。阻塞仍是审计JSON映射和低分原因，待主任务处理；监控不恢复队列，小时汇报继续。


2026-10-31 06:02:21+08 小时只读核验：无新增诊断、修复或验证结果。GPQA174/198（87.8788%）及原审计incomplete继续冻结，formal/W2均已退出，ERQA未启动，无新formal目录或SUITE_FINISHED。同一精确8010健康200，running/waiting/KV/preemption均0，无新服务fatal/RPC错误；关键源码、三库HEAD/暂存内容、原脚本及冻结证据SHA不变，磁盘余1402.89GiB。未执行推理、审计重跑、GPU、源码/cache变更或服务操作，未访问8035。阻塞仍为审计JSON映射及低分原因；待主任务处理，监控不恢复队列，保留用户小时汇报。


2026-10-31 07:07:47+08 小时只读核验：无新增诊断、修复或验证。GPQA174/198（87.8788%）及原审计incomplete继续冻结；formal/W2均退出，ERQA未启动，无新formal目录或SUITE_FINISHED。同一精确8010健康200，running/waiting/KV/preemption均0，无新服务fatal/RPC错误；源码、三库HEAD/暂存内容、原脚本及冻结证据SHA不变，磁盘余1402.81GiB。仅只读检查，未执行推理/GPU、审计重跑、源码/cache变更或服务操作，未访问8035。阻塞仍为审计JSON映射与低分原因，待主任务继续处理；监控不恢复队列，小时汇报保留。


### 2026-10-31 用户新授权：修复审计映射并接续 ERQA

用户明确要求修复 JSON 聊天参数到原生 prompt 的审计映射，仅用已有 GPQA 产物重新审计；证据有效后沿用当前同一 8010 执行尚未启动的原生 ERQA400/C32。并行使用已有证据诊断 GPQA174/198 和8题60K截断。保留 BF16 和全部生产修复，不重启、不重跑GPQA、不访问8035、不提交推送。

执行模式：本地 accuracy formal-gate 的已有产物 CPU 重新审计（不产生新GPQA请求），ERQA native score-only；diagnosis 冻结低分并继续既有证据分析，不叠加性能优化。原 GPQA FINAL_SUMMARY/FINISHED/incomplete 和首错均保留。修正审计不会改变174/198或签发通过gate。新资产计划 `acc-023.../commands/audit-map-erqa-20261031-v1`，重新审计计划 `repair-formal-003/diagnostics/audit-mapping-fix-001`；ERQA单项接续控制记录 `acc-024.../repair-formal-003/continuation-001`，不执行原双项suite。

已在07:57只读核同API1336953/start607626732/argvSHA c1b658b05137910a59f347c6fbb9048146d22f1274886b324b761803a9f30fbc，health200、running/waiting/KV/preempt全0；源、三库HEAD/staged和原启动脚本一致，ERQA确未执行。当前阶段：审计修复与CPU验证，尚无新ERQA请求。

CPU审计部署执行前绑定：新helper SHA `4213718f6230797ea57237449fdb57a8adc3ee09af6e6a614016a82972b3235a`，reaudit SHA `e4b9998364ac4348da4ca0206c3c636730181b7b557f1478351053120adba19f`；10项映射单测通过，完整 `scripts/validate-local --code` 通过（不含记录验收）。CPU命令固定已有GPQA评测容器、offline datasets/hub、CUDA_VISIBLE_DEVICES空，不调用原formal runner或模型；输出独立Q/audit.log和新parsed/native-audit。原件不覆盖。

重新审计完成：198unique/396filter行、198完整API唯一prompt映射，无token/usage缺证。Q/native-audit SHA `6df7dbd210266ef8846e6228437eb7ea875ae00eb5158c07c22346bd3ae604ee`，Q/manifest SHA `0a223a1132db20aa403b8491d78406b2c5bafb6b1a1bdf886541b41b9dec757f`。独立修订为valid-native-score/failed-score174/198；原incomplete/原manifest未变，无passgate。新ERQA-only controller SHA `c8cdf7d1bc44507aafa41509008627e140f784356e6adb972da9b278d4366ff2`，显式只调用原suite的只读身份/源/冻结输入核验函数、原native adapter/audit及原生单项命令，不执行原prepare/run_suite，不重复GPQA。先独占prepare检查同实例、空ERQA目录/原生源图像、原输入与新授权，再单次launch；新所有回执在EC，原准备controller SHA与新controller SHA分开绑定。

08:07:56+08 ERQA FORMAL_STARTED epoch1793405276.3363018，原生400/C32单项已启动；唯一controller4141102/start612110094/argvSHA d118f283b79d6918cf7c619c6f8f5fb7e82614a89aed7ca8b47b9d7b2dccdb28，控制脚本SHA c8cdf7d1bc44507aafa41509008627e140f784356e6adb972da9b278d4366ff2。首32派发时0返回/0真实绑定，派发不算完成。本次0GPQA新请求/0重启。CPU终态等待器预保存 `erqa_terminal_watch.py` SHA `3b86627c5f8840666d981f2af886b2732ef0759865a6d9a7cab2af318e3106c9`，只等该controller自然退出后核全部manifest/400原生评分与真实wire映射、同源同API、完整最终日志；不发推理或启动任何评测。独立EC/terminal-audit-001及COMPLETED/AUDIT_ERROR保存终态，原GPQA产物不覆盖。


2026-10-31 审计修复与ERQA接续已执行：修正CPU审计将serialized JSON聊天参数解码为完整原生user prompt，再唯一匹配返回prompt_text；拒绝重复doc/歧义和残缺API。10项新增单测、完整本地275项工具测试和`validate-local --code`通过，原始test资产11项SHA未变。已有GPQA离线重审198/198全映射、396filter行/完整token与usage有效，修订回执failed-score174/198（阈值.88，需175题），无通过gate。旧incomplete/原manifest/首错不覆盖。Q/native-audit SHA 6df7dbd210266ef8846e6228437eb7ea875ae00eb5158c07c22346bd3ae604ee，Q/REVISED_VERDICT SHA1535a648e6f118188f5015130962053e4b05cbf7ff23a13a50ff1791f543f0ee，Q/manifest SHA0a223a1132db20aa403b8491d78406b2c5bafb6b1a1bdf886541b41b9dec757f。

低分/截断的已有证据分析完成：24错=8真实length60000+16明确错误字母；16/16原生抽取与final明确字母一致，0解析误判/传输错误行。8题有15.2万–19.6万字符推理，均无thinkend/EOS/final，实际返回prompt含xhigh推理策略；反复检视化学结构/假设或枚举模式，不能等同固定token死循环。6/8无重复64-token窗口，全部未见1–512周期重复至少3次的尾部。190普通返回可正常终止，正确174题输出中位3873.5、最长58849tokens；16普通错答中位21984.5。原生注册OpenAIChatCompletion覆写payload字段为max_completion_tokens=60000，丢弃do_sample字段但保留T1；原API seed默认1234经self._seed传递，与评测seed42分层。继承parser仅取message.content，None由并发collector转TIMEOUT且保留usage，评分置0；不是RPC/HTTP超时，也不是审计映射导致失分。未改cap/采样/stop/评分或分母。

诊断报告 `G/diagnostics/gpqa-low-score-analysis-001/REPORT.json` SHA5343712fb85653dd42ee765b65fff67c8bb0af67b41a44eb0e8e2d97e467ff5b、manifest17d9042eb27adce6227352234f20a6ae840694cdabb6915b790e4c5c53996664，保存24失败题完整reasoning/final及原API引用。source-chain-001保留原生四源码，ACTUAL_REGISTERED_PAYLOAD.json SHA56ab5de5fcd249715032dd6c2a0af9d525580d6cbbc7eb84ebc4ffa573b1084d为实际注册子类/长度字段的权威说明；初始父类说明保留，不冒充wire（GPQA只有原生完整解析API）。

历史CPU对照：acc021旧175/198与当前198题doc/prompt/target hashes逐项全同、权重metadata/stat和tokenizer指纹相同；旧9题60K、当前8题，重叠doc32/71/145/147。7题由对变错、6题由错变对，不能用净差1题判定单一源码退化。两次并发64/32、源码版本、prefix策略、调优及服务均不同，非受控baseline；历史答案不复用、旧gate不绑定当前。history-comparison-001 REPORT SHAb8d4b3a0ffcaa1667666ab712f1bb823b157b171619f91612d63bf116bd4555b，manifest5ca563e3369490adaaee45ac4bc0e6229f37ccd6576a532a52f7b936c5d94fb8。现有证据支持“推理未收束而耗尽预算”为8题直接原因，尚不能证明底层BF16/RNG/Mamba数值因果或更大预算一定答对。

ERQA08:07:56+08已原生启动400/C32单次，唯一controller4141102/start612110094/argvSHAd118f283b79d6918cf7c619c6f8f5fb7e82614a89aed7ca8b47b9d7b2dccdb28。新CPU终态等待器76554/start612130549/argvSHA5431366423da028a9ba106df18d33e303bb48bff388c8144c63a335d9d63616a，只等原controller退出后审计完整证据；无新模型启动/GPQA/额外smoke。ERQA原native prompt/data/parser/BaseEvaluator/retry保留，完整wire及真实question_id-index-attempt逐项保存。当前尚无原生全量分数，不宣称通过。每小时monitor已更新到新授权/EC目录，仍只读不补启动。

最新只读进展 2026-10-31T08:15:34.151589+08:00：真实native question_id且完整末次HTTP证据核验 27/400；派发59attempt、HTTP200 27，0HTTP错误；running32/waiting0/preempt0。同一精确8010 health200，源与启动配置保留，磁盘余1402.71GiB。未重启/重跑GPQA/访问8035/提交推送。

证据收尾保护：CPU watcher仍运行时，其stdout不能被ERQA已冻结manifest提前绑定。预保存 `relocate_watch_stdout.py` SHA `f1afd093c5222f5a66fb465726aa2357e14782e3ec80f91904c3f3952f661bfe`，仅将EC/terminal-watch.log同inode rename到A/erqa-terminal-watch.log（在E之外、终态freeze前）；核精确CPUwatch PID/start/argv及fd1/inode/SHA，原openfd持续写新路径，0信号/0重启/0模型或源码改动。EC/CPU_WATCH_STDOUT_RELOCATED记录路径迁移，以免完成打印造成manifest成员后改；不是重跑watcher。

CPU诊断已收尾：CPU_CONCLUSION SHA cde65749efd54128aa964cf61e3925d1e0fa797da39cf9e9359e53ea18b019c5，terminal-manifest-001 SHA7a48f25a8cf2ab8a4d0e859f08e9734b121c08fb544cd021a7c94291d809ef48，READBACK_RECEIPT SHA0c6ba2cace98ff628aa70ab29211c8a510274b68d713b33c89658ee24f13802f，74成员逐项SHA/size通过；原GPQA113成员与旧summary/manifest未变，修正Q及三诊断manifest全部验同，当前完整source/runtime/原startscript相同。直接截断/评分原因已定位，底层模型数值因果仍未证实，不作RNG/BF16/Mamba单因归因。全198真实prompt230–2933，低于6400边界，但不能据此排除并发budget导致的短prompt部分prefill；无实时分支trace不声称回退路径未执行。

最新 2026-10-31T08:21:50.324979+08:00：ERQA真实native question_id完成59/400，派发91attempt，完整HTTP200 59、0HTTP错误；同API健康200/running32/waiting0/preempt0，完整源/三库HEAD-index/原启动脚本核同。全量尚未终态，无ERQA分数或pass结论。小时监控继续。

2026-10-31T08:27:13.861290+08:00 只读最终进展快照：ERQA native question_id唯一完成81/400，已派发113attempt/完整HTTP200 81、0HTTP错误；当前API1336953/start607626732同一listener/argv，health200/running32/waiting0/preempt0，source/runtime/user-script逐项相同，当前无FIRST_HTTP_ERROR/EC错误/终态flag。快照EC/readonly-progress-20261031T082713.json SHA979cfe2eeb1762507d3db326a9eb3cb91aba8630f622fba341342187bb14bb52，绑定observer-v2 SHA162d695aa95dfb98a80f53a463ae8ed32ebe6513f1a1842a4ccb26dae5fdf52c；只归档已读取快照，不发新请求。服务/生产修复/BF16不动，GPQA不重跑。继续原唯一ERQA及终态CPU审计、每小时汇报。

2026-10-31T08:30:21.426714+08:00 heartbeat只读：ERQA真实native ID完成98/400，派发130attempt，完整HTTP20098/0HTTPerror；同API/controller/CPUwatch精确身份active，health200/running32/waiting0/KV0.126349710/preempt0，完整source/runtime/startscript相同。E绑定service新inode窗口213102bytes无新fatal/RPC错误，无EC错误/终态flag。GPQA修正174/198结论未变，无新增诊断、修复或测试。距08:27主动汇报仅几分钟，正常推进静默；小时监控保持ACTIVE，未发推理/重跑/重启/改源cache/访问8035。


### ERQA完整终态及后续边界（核验时间 2026-10-31T16:48:27.496254+08:00）

原唯一ERQA队列及CPU等待审计已于 2026-10-31T10:17:40.864966+08:00 自然结束。400唯一question_id、400native items/evaluated、真实question_id-index-attempt和全wire完整，原生正确252/400，accuracy=63.00%。ERQA无预冻结阈值，只报告native score，不签ERQA通过gate。FINISHED/EC SUITE_FINISHED/COMPLETED及独立终态审计齐全，controller4141102和CPUwatch76554均退出；原native evaluator/helper均退出，容器仅保留。当前精确同API1336953/start607626732/argv/listener健康200，running/waiting/KV/preemption全0，BF16/全部修复/启动脚本及完整源/三库HEAD-staged不变，保留8010，不做服务操作。

401次HTTP尝试均200，0真实HTTP/网络/RPC/设备fatal，0token或usage证据缺口；400逻辑题并非400次HTTP。唯一原生自动重试是ERQA_240/index239：第一次HTTP200但60000token length、final=None/no thinkend/EOS；原native `_single_infer` 在拼接None时TypeError，日志UTC2026-10-31 02:06:58.158（本地10:06:58.158）before_sleep.py:64，`can only concatenate str (not "NoneType") to str`，原Tenacity等待2.28s后第二次9968tokens/stop/thinkend/EOS/非空final。该题真实binding HTTP_attempts=2，未超过原最多5总尝试；这是原生重试，不是monitor/人工请求或整项复跑。最终接受的400答案均stop、0空answer；原始两次raw/header/token和原生日志完整保留。不能把此TypeError叫HTTP/RPC超时，亦不修改原parser或评分。

原生分项：Trajectory Reasoning60.61、Pointing85.29、Task Reasoning65.79、Multi-view Reasoning62.16、State Estimation52.73、Action Reasoning69.44、Other28.57、Spatial Reasoning61.90（均原生百分数，保留其分项分母定义）。不与旧251/400的不同C64/版本/缓存组合计算因果提升，不报性能收益。

终态证据绑定：E/FINAL_SUMMARY SHA7f8afb3c739d9884e16123079d399b8b44292a8ac0913e51da376dc9e7795c3e；E/manifest SHA415e90b59788262e90dc1404b9c1cc1df26cbeaa5cd554d2b275be3fc34efff0（3098成员）；E/evaluation/native-audit SHA028d4791b8784da309f50afed3233cda89fb51389f5ec738081f5c0dcc6d7a34；原生result SHAa155f09dac1a8d5c798b4e57778b054abe6fb7935041dda4dfcfd563ac458824，evaluated SHA834a742ba881b8d225f41dd18bf60d8811fab849722f2ebde807aef99f79e157。EC/terminal-audit-001/report SHA3d79eb71634311ae8aaf8b6a77c87b8410e8dad47454d89cb7dd579b94b07ee2、manifest8522692ef8c43ac052785657acbfd1be35e824e7fef4c751991b515b1d7fb097；EC/COMPLETED SHAc753941cc4ba57a2e17f56c528b280fa1125f16214c2eedd8cc684250626a580，EC/SUITE_FINISHED SHAb64ad9c1c6c2f47d52914660a1f035ef33fcd530f746a0667953c46ac1170497。原等待器6项终态检查均通过；本次仅CPU再读/hash核ERQA3098、原GPQA113、新Q7和终态audit6成员全部大小/SHA，原G/incomplete/summary保持不变；当前service窗口无fatal/RPC错误。没有重跑固定输出旧审计、新推理/GPU/变更/重启/8035/提交推送。

本轮用户新增授权的审计修正、既有证据诊断及ERQA执行已结束；GPQA仍是有效174/198=87.8788%低于88%，模型底层原因未确证，无新GPQA passgate，性能继续冻结。依据用户明确每小时跟踪整体修复进展、低分失败也不自动停止的要求，monitor保留ACTIVE并切换为终态后GPQA低分后续的只读跟踪；不能继续报告ERQA运行，不能自行新增评测、修复、复测或恢复。无后续变化时按小时如实说明无新增进展；整体闭环或用户停止才停用。

2026-10-31T16:54:07.221174+08:00 终态后快速只读：无新增修复/诊断/验证结果。ERQA252/400（63.00%）及GPQA174/198未达88%均不变，旧controller/CPUwatch均已退出、无新formal目录或错误flag；精确8010同API健康200/running0/waiting0/KV0/preempt0，完整source/runtime/原script一致。10份关键summary/manifest/audit/suite回执SHA验同；仅扫终态后service新窗口761bytes，无新fatal/RPC错误；free1402.37GiB。未重解析401份wire、重复full audit、发推理/改生产cache/操作服务/访问8035。距16:48完成通报仅数分钟，保持静默；小时整体GPQA低分后续跟踪ACTIVE，不补启动任何任务。

2026-10-31T17:27:14+08:00：GPQA新增xhigh/采样/prefix纯CPU专项已收尾，详见同acc023。原ERQA252/400及401次HTTP/原生单次重试不变；无新ERQA、GPQA或服务动作。当前同BF168010健康空闲。共有xhigh非新prompt漂移、R5之后prefix命中增量0；align状态和并发数值因果未独立验证。整体GPQA低分仍未闭环，小时只读跟踪继续。

2026-10-31T17:56:13.307164+08:00 heartbeat终态后快检：无新增修复/诊断/验证。精确同API1336953/start607626732/argv/listener健康200，running/waiting/KV/preempt均0，完整source/runtime/start-model.sh相同；原ERQA controller/CPUwatch仍退出，EC无FIRST_ERROR/FREEZE/TERMINAL/AUDIT_ERROR。7份既有GPQA/ERQA/新xhigh专项summary及manifest/结论/回执SHA验同，free1402.35GiB；未重解析401wire或重复full审计，0新推理/设备/生产cache变更/服务动作/8035。174/198与252/400不变，底层因果仍未确认。距刚结束的专项报告不足1小时，无新可处理事项，本次静默；整体小时跟踪ACTIVE，不新增执行。只读快检脚本本地SHA7974fe83ef03b974a3acebad2905b41013e29552d40140f3f8e7041b4ae3df45。

2026-10-31T18:53:31.526681+08:00 小时只读核验：无新增修复/诊断/验证。精确API1336953/start607626732/argv/listener保持，health200、running/waiting/KV/preempt全0；完整source/runtime/start-model.sh一致，原ERQA controller和CPUwatch均退出，EC无新FIRST_ERROR/FREEZE/TERMINAL/AUDIT_ERROR。7份冻结summary/manifest/专项结论回执SHA验同，free1402.09GiB。GPQA174/198低于88%、8题60K及ERQA252/400均不变；共有xhigh与align/RNG数值因果未独立确认。仅快检，未新增推理/GPU/重复审计/生产cache变更/服务动作/8035/提交推送。按用户明确小时要求主动汇报无新增结果，继续只读跟踪，未补启动队列或扩展测试。

2026-10-31T19:17:32.393913+08:00：用户新授权仅8个GPQA截断题xhigh/medium固定seed C1对照已启动，详见同acc023。ERQA252/400终态不变，不新增ERQA；当前8010服务维持，原ERQA controller/CPUwatch均已退出。

2026-10-31T19:21:40.400867+08:00：同8010当前在执行新授权GPQA8题C1策略对照，原ERQA252/400终态不变；不是ERQA重跑，原ERQA进程退出。CPU等待器2健康，监控按新C1身份只读跟踪。

2026-10-31T19:54:50.414968+08:00 heartbeat只读：driver1079662/CPUwatch2 1202459精确active，同API1336953/start607626732/argv/listener及完整source/runtime相同，health200/running1/waiting0/KV0.0317558/preempt0，prefixhits32000不增。仅seq0/doc32/xhigh派发，0/16完整响应；generation_tokens由4926686增至4960720仅证明活动，不当完成/得分/ETA，未见FIRST_ANOMALY或watch2错误。首条继续原生收集，不补发或重试。快照本地heartbeat-20261031T1954.json SHAe736bf8338507424b5b55c2f95744a18449d12573180233af8b67e565d4e034d。距启动通报不足1小时，本次正常推进静默；下个小时继续用户主动汇报。没有新推理/源码或采样cache变更/服务动作/8035/提交推送。

2026-10-31T20:57:14.239735+08:00 小时只读核验：原唯一driver1079662与CPUwatch2 1202459精确active；同API1336953/start607626732/argv/listener、完整source/runtime保持，health200/running1/waiting0/KV0.00462930/preempt0，prefixhits仍32000。4派发/3完整响应/1完整pair；当前seq3/doc71/xhigh在途。首对doc32：xhigh52466token/stop/非空final，medium1452token/stop/非空final；两者均thinkend1+EOS248046一次，真实prompt均核对应expected SHA，prefixhits_delta0。原C32该题60K截断在本次xhigh C1未复现，不能把差异直接当原C32根因或正式精度改善。seq2/doc71/medium45740token/stop/非空final也完整，仍待该题xhigh，不能称medium统一短输出。

本次另做纯CPU只读独立回读seq0..2完整request/body/response headers/raw、token IDs和usage，冻结observerSHA核同、三份observation逐项相等，doc32两body去掉effort后全同；原始response.raw SHA依次005724c2b97d463f3687c866be1ed900bd37c9cc6dc2bbaf16c89c0decd34e49 / 635e070302842bd2a415fcbb0cf87e76a04029c416d45dee8225dd4f53bcec24 / 4467a742cf2cd4c5cc7fa6db2e1a801b2b58f443ea2c30e1818e263526126893。不是抢跑16条终态审计，无新POST/设备/重试/源码cache变更/服务动作/8035/提交推送。快照本地heartbeat-20261031T2056.json SHAa7293ef5b07f0a19be87f4848cbdc8ab35e55d84a35402ef1a7ceec7a591041f；无FIRST_ANOMALY/终态或watch2错误，free1402.05GiB。继续原C1队列和自然终态CPU审计，不扩预算或签gate。按用户小时要求主动报告3/16及首pair局部事实。

2026-10-31T21:59:32.224674+08:00 小时只读：5派发/4完整响应/2完整pairs，seq4/doc79/xhigh在途。新完整第二对doc71（medium先、xhigh后）：medium45740/stop/非空final/thinkend1+EOS248046，xhigh60000/length/contentNone/thinkend0/EOS0；两HTTP均200、prompt/output token IDs及usage完整无缺项、prefix命中增量均0。同API1336953/start607626732/argv/listener、source/runtime同，health200/running1/waiting0/KV0.00765938/preempt0，driver1079662/CPUwatch2 1202459精确active，prefixhits32000，无FIRST_ANOMALY/终态/watch2错误，free1402.04GiB。

纯CPU读取seq2/3原完整request/body、response header/raw并复用冻结observer回读，observation逐项同原结果，actualprompt核expected SHA；同题body除effort外完全相同。xhigh raw470581bytes/SHA5a0c2a1a156543369ccb69ff800c8220dbf269349e51ca5f60e89981bfc64cda、output IDs SHA850fb8b9cf3a029fd59e8b0145f0e8b41546ef61e9784313f369c1cd7e98eb00；medium raw330906bytes/SHA4467a742cf2cd4c5cc7fa6db2e1a801b2b58f443ea2c30e1818e263526126893。该题本次C1 xhigh复现60K，medium本次未截断，是单对照局部事实；doc32 xhigh C1仍正常stop，两题不能推成8题统一结论、正式精度改善或排除数值路径。60K/None是有效诊断结果，不是HTTP/RPC超时或新流程错误，原队列自然继续，不重试/停/扩预算。

快照本地heartbeat-20261031T2159.json SHAf016a81f561acd8204d293e3ce48e7c6f8cee8f91a1c9a0bdf6ee2d5c6411d92；未抢跑全16终态审计、未由monitor发POST/改源采样cache/操作服务/8035/提交推送，原唯一controller按已冻结16预算继续。按用户小时要求通知4/16及第二pair事实，保持ACTIVE。

2026-10-31T22:59:48.128243+08:00 小时只读：7派发/6完整响应/3完整pairs，seq6/doc88/medium在途；原唯一driver1079662与CPUwatch2 1202459精确active，同API1336953/start607626732/argv/listener及完整source/runtime相同。health200/running1/waiting0/KV0.0151624/preempt0，prefixhits仍32000，无FIRST_ANOMALY/终态/watch2错误，free1391.86GiB。新第三对doc79：xhigh49012token、medium2506token，均HTTP200/stop/非空final/thinkend1/EOS248046一次、prefix增量0。当前3pairs中medium均更短；xhigh1/3 length而medium0/3，仅报告当前选定3对，不当8题总体或正式精度/唯一底层根因。doc79的历史C32截断在本次xhigh C1未复现，与doc32类似；doc71仍是xhigh60K/medium45740stop的局部截断差异。

只CPU独立回读seq4/5 request/body、response headers/raw、实际prompt与expected SHA、完整token及usage，冻结observer回读逐项一致且两body去effort后完全同。xhigh raw318121bytes/SHAc4ed3ae63253c25bddf7e854ec76a627ba89f522d4ca6789a4e94d1c8374a612；medium raw16611bytes/SHA044afc55367045658634d34319c79eae4ba5b39162f938bfff2a382a2579fdd9。快照本地heartbeat-20261031T2259.json SHA9eed4080c15fae6315d6aaecdb17ef067c03aeb9bb1a7fa662a2f9bf1e6f1545。monitor没有新POST/重试/抢跑终态审计/改源码采样cache/服务动作/8035/提交推送，原16请求controller自然继续；按用户小时要求通知6/16及第三pair结果，保持ACTIVE。

2026-11-01T00:02:47.044214+08:00 小时只读：8派发/7完整响应/3完整pairs；seq7/doc88/xhigh在途，尚不能报第4pair结果。新seq6/doc88/medium完整HTTP200/29330tokens/stop/非空final/thinkend1/EOS248046一次、prefix增量0；纯CPU独立回读request/body、response header/raw、实际prompt与expected SHA、完整token/usage均与冻结observer原结果一致。raw217250bytes/SHA1a28e61eed5ecfcd6f4c9eabe6310e74948f5d3c2755da2d3f6ef2c4055b46b1，output IDs SHA6f97c932c00cd273433f27f523b3ebb2ec426b622e27c5ba247e23b657c4bc8d。

同API1336953/start607626732/argv/listener及完整source/runtime保持，health200/running1/waiting0/KV0.0409903/preempt0，prefixhits32000未增；driver1079662/CPUwatch2 1202459精确active，无FIRST_ANOMALY/终态/watch2错误，free1391.80GiB。累计generation_tokens从5149676增至5213772仅证明原任务活动，不能把在途生成计完成或估ETA。已完成3pairs局部观察保持，未推广8题或formal精度。快照本地heartbeat-20261101T0002.json SHA954deba378d42f5bfa2d00801738e75229a4b1700aa50a0c08345a84b09bc334；monitor未发POST/重试/抢跑终态审计/改生产采样cache/服务动作/8035/提交推送，原16请求队列自然继续。按用户小时要求主动报告7/16与下一步等待doc88/xhigh。

2026-11-01T01:06:15.616128+08:00 小时只读：9派发/8完整响应/4完整pairs（16预算完成一半）；seq8/doc127/xhigh在途。第4对doc88（medium先）：xhigh60000/length/contentNone/thinkend0/EOS0，medium29330/stop/非空final/thinkend1/EOS248046；两HTTP200、prefix增量0。纯CPU回读seq6/7完整request/body、response headers/raw、实际prompt与expected SHA、token/usage均与冻结observer逐项相同，两body仅effort差异。xhigh raw459166bytes/SHA256dfd230724bec1c538c3757782acf4cb919355c795552ecb28e72aecc89e5b；medium raw217250bytes/SHA1a28e61eed5ecfcd6f4c9eabe6310e74948f5d3c2755da2d3f6ef2c4055b46b1。

当前4完整pairs medium均更短，xhigh2/4 length（71/88）而medium0/4，只报告这4题单次C1局部事实；32/79的xhigh本次正常stop，不能推广为8题/正式精度或唯一底层根因。两个length目前均在medium先的不同题中出现；每题只有一种arm顺序，题目与顺序不可独立区分，不能归因为顺序，也不因此擅自补测或改变冻结顺序。普通60K数据自然收集，不叫RPC/HTTP失败。

同API1336953/start607626732/argv/listener及完整source/runtime保持，health200/running1/waiting0/KV0.0469062/preempt0，prefixhits32000未增；driver1079662/CPUwatch2 1202459精确active，无FIRST_ANOMALY/终态/watch2错误，free1391.77GiB。另只读核controller/observer/auditor/watch2/plan/PREPARED共6关键SHA未变，当前doc127服务新inode27006868286/offset5067128窗口471261bytes、SHA51cff833e17ff829e2a675ac202a41c04370a095d1937356855e58d866326bc1，无fatal/RPC/Traceback匹配。快照本地heartbeat-20261101T0106.json SHA4a15e943b777e545254bc8724ca1fe4cfdbbdccc59782bc6a25d747f39efc0c0；monitor未发POST/重试/抢跑终态审计/改源码采样cache/服务动作/8035/提交推送，原16队列继续。按用户小时要求主动报告8/16及第4pair。

2026-11-01T02:00:46.027166+08:00 小时只读：12派发/11完整响应/5完整pairs；seq11/doc145/xhigh在途。新增第5对doc127（xhigh先）：xhigh60000/length/contentNone/thinkend0/EOS0，medium30418/stop/非空final/thinkend1/EOS248046；另seq10/doc145/medium1544/stop/非空final/thinkend+EOS已完整。三HTTP均200、usage/token/prompt证据完整，prefix增量0。只CPU独立回读seq8..10 request/body、response header/raw、expected实际prompt及冻结observer结果逐项核同；doc127两body去effort后全同。raw SHA：seq8 d97da7c96a0c0eeb78d40ec56a7f062325013cefd916f2664cfc16ee014e4375（460041bytes）；seq9 5361a6ccb785611ed053335d11f7ae9ab895dec981e86e39806c6878ab42f57c（217054bytes）；seq10 618421ebbe132ab5759879c0a9ed6aaa6da237b13d8a6492322a6bbeeec5af2c（15140bytes）。

已完成5pairs中medium均更短且0/5 length，xhigh3/5 length（71/88/127）；只限这5个选定题的单次C1结果，不推广8题或正式198精度/gate/唯一底层根因。此前前4对length都发生medium先只是早期观察，doc127本次xhigh先也60K，该简单顺序模式已不普遍；仍无同题反向重复，不能因此彻底排除顺序/时间或数值影响，不补测。普通60000是有效诊断数据非RPC/HTTP超时，原队列继续。

同API1336953/start607626732/argv/listener、完整source/runtime保持，health200/running1/waiting0/KV0.0180482/preempt0、prefixhits32000不增；driver1079662/CPUwatch2 1202459精确active，无FIRST_ANOMALY/终态/watch2错误，free1391.77GiB。快照本地heartbeat-20261101T0201.json SHAf4449bb5135dd465404e152220094af78c7c68d57081d28b6f66b7f2b394a800。monitor未发POST/重试/抢跑终态审计/改源码采样cache/服务动作/8035/提交推送，原16预算唯一controller自然继续。按用户小时要求通知11/16及第5pair结果，保持ACTIVE。

2026-11-01T03:05:17.872349+08:00 小时只读：13派发/12完整响应/6完整pairs；seq12/doc147/xhigh在途。新第6对doc145（medium先）：xhigh60000/length/contentNone/thinkend0/EOS0，medium1544/stop/非空final/thinkend1/EOS248046一次；两HTTP200、prefix增量0。只CPU独立回读seq10/11完整request/body、response header/raw、actualprompt与expected SHA、token/usage均与冻结observer逐项同，两body去effort后完全同。xhigh raw453462bytes/SHA8c049d3dbca3e27930d44f810fdf6ad410fddfbd00ddb31feb57c233021064d9；medium raw15140bytes/SHA618421ebbe132ab5759879c0a9ed6aaa6da237b13d8a6492322a6bbeeec5af2c。

当前6pairs medium均更短且0/6 length，xhigh4/6 length（71/88/127/145），只限这6个选定题单次C1；不能推广全部8题、正式198精度或唯一底层数值根因。正常60000/None诊断结果自然收集，不当RPC/HTTP超时，不重试、改变顺序或扩16预算。同API1336953/start607626732/argv/listener与完整source/runtime保持，health200/running1/waiting0/KV0.0219441/preempt0、prefixhits32000未增；driver1079662/CPUwatch2 1202459精确active，无FIRST_ANOMALY/终态/watch2错误，free1391.76GiB。

快照本地heartbeat-20261101T0305.json SHAc7f2010128e814bb0dc307c9b94ac67dd88165aeb888ef5820f50867f7d13a98；monitor没有新POST/抢跑终态审计/改源采样cache/服务动作/8035/提交推送，原唯一controller自然继续。按用户小时要求主动通知12/16与第6pair事实，保持ACTIVE。

2026-11-01T04:03:46.527518+08:00 小时只读：15派发/14完整响应/7完整pairs；最后第8对的seq14/doc185/medium在途，xhigh尚未派发，不把15派发当15完成。新第7对doc147（xhigh先）：xhigh60000/length/contentNone/thinkend0/EOS0，medium22376/stop/非空final/thinkend1/EOS248046一次；两HTTP200、prefix增量0。只CPU独立回读seq12/13完整request/body、response header/raw、actualprompt与expected SHA、token/usage均与冻结observer逐项一致，两body去effort后完全同；另5份controller/observer/auditor/watch2/plan SHA验同。xhigh raw402915bytes/SHA08681a52bf2abc49b7b3299ed0ea61ef92071dfd651a872d3bf8bfbec3342179；medium raw144497bytes/SHA9db684ffec7328828d112ced3eee21665953a03d4475e1275308de6589749562。

目前已完整7pairs medium均更短且0/7 length，xhigh5/7 length（71/88/127/145/147），只限当前7题单次C1，不推广未完成第8题/正式198精度或唯一底层数值根因。普通60000/None原流程继续，无retry/预算或顺序修改。同API1336953/start607626732/argv/listener及完整source/runtime保持，health200/running1/waiting0/KV0.00520645/preempt0、prefixhits32000未增；driver1079662/CPUwatch2 1202459精确active，无FIRST_ANOMALY/终态/watch2错误，free1391.73GiB。

快照本地heartbeat-20261101T0404.json SHA8c36f5ba2f4a420399877c060857be8765b756a89701bc36e7d6b56a2fba91e1；monitor未发POST/抢跑终态审计/改源采样cache/服务动作/8035/提交推送，原16请求唯一controller继续最后一对。按用户小时要求主动通知14/16，保持ACTIVE，等原driver和独立CPU审计自然终态才报全范围完成。


### 8题effort C1对照完整终态（2026-11-01 05:10–05:12核验）

本次8题对照16/16完整、独立CPU审计及300成员回读通过，原driver和CPUwatch2均退出。xhigh5/8截断，medium0/8，8题medium输出均更少；仅限该选定单次C1范围，不是完整GPQA精度通过。原GPQA174/198仍未达88%，ERQA252/400终态保留；同BF168010健康空闲，未重启、全量复测或改默认策略。小时监控转终态后只读整体跟踪，不再派发测试。

2026-11-01T06:07:50.594645+08:00 终态后小时只读：本小时无新增诊断/修复/验证。16/16对照及独立CPU审计终态不变（xhigh5/8 length、medium0/8），原driver1079662/CPUwatch2 1202459保持退出；精确同API1336953/start607626732/argv/listener/source/runtime保持，health200/running0/waiting0/KV0/preempt0，generation5525333/prefixhits32000/prefixqueries313990均未增。7份关键summary/manifest/audit/GPQA修订回执/原启动脚本SHA核同；仅新增服务窗口inode27006868286/start7449116/end7449281/165bytes/SHA9bad384c2d4b96e8b76867e12532309087ece869a5356d551816874c2b0981a2，无新fatal/RPC/Traceback。未重读605838tokens/全300成员、未重复审计或发POST/改源采样cache/操作服务/8035/提交推送。快照本地heartbeat-20261101T0608.json SHA3f919664c84baefc7daadf13a0963791732ecf6cc2f4b9b9b41b0acdead8cb9e。原GPQA174/198仍未达88%，medium正确率/正式分未验证；保持用户小时只读后续，无新授权不开展下一项测试。

2026-11-01T07:06:52.825249+08:00 终态后小时只读：本小时无新增诊断/修复/验证。16/16小对照及审计保持完整终态，原driver1079662/CPUwatch2 1202459均退出；精确同API1336953/start607626732/argv/listener/source/runtime保持，health200/running0/waiting0/KV0/preempt0，generation5525333/prefixhits32000/prefixqueries313990未增。7份关键冻结回执与原脚本SHA一致；只读服务新窗口inode27006868286/start7449281/end7449446/165bytes/SHA877c20becf2f9c5833481c7a3881d648b6a1be927be15bdb598c15d17a1a2351，无新fatal/RPC/Traceback。未重新解析全token/300成员或重复审计，monitor未发POST/改源采样cache/操作服务/8035/提交推送。快照本地heartbeat-20261101T0707.json SHAee2b272686b59c0cf458c7c64a11bd95e820c4cf7d86814465172a86794009a9。GPQA174/198低于88%仍开放，medium正确率/正式分未验证；按用户要求继续小时只读后续，不自行开展新测试。

2026-11-01T08:03:27.965920+08:00 终态后小时只读：本小时无新增诊断/修复/验证。16/16对照及独立审计终态保持，driver/CPUwatch2均退出；精确同API1336953/start607626732/argv/listener/source/runtime不变，health200，running/waiting/KV/preempt均0，generation5525333/prefixhits32000/prefixqueries313990未增。7份关键冻结回执与原脚本SHA一致；服务新窗口inode27006868286/start7449446/end7449611/165bytes/SHAc507aee50ba9c3df0d817b3114a8f3dd4fe7a5282e2f9c2fbacf22bc750b58f2，无新fatal/RPC/Traceback。快照本地heartbeat-20261101T0803.json SHAfa597548e1437f0c9f9df1f9306bd451860e2cd4e2f99eaf6231104b91baa325。未重解析全token/300成员或重跑审计，未发POST/改策略源码cache/操作服务/8035/提交推送。正式GPQA174/198仍低于88%，唯一原C32模型根因未确证；继续用户要求的小时只读跟踪，不自行新增测试。

2026-11-01T09:10:56.413983+08:00 终态后小时只读：无新增诊断/修复/验证。16/16对照与独立审计保持终态，原driver/CPUwatch2均退出；同API1336953/start607626732/argv/listener/source/runtime保持，health200，running/waiting/KV/preempt均0，generation5525333/prefixhits32000/prefixqueries313990未增。7份关键冻结回执及原脚本SHA一致；新增服务窗口inode27006868286/start7449611/end7449776/165bytes/SHAcd713b395e04ecf3d36a53935517b9066f3ea31e420e1ef3b067c1fb5783a844，无新fatal/RPC/Traceback。快照本地heartbeat-20261101T0911.json SHAf17b8a65fab2737379d84ce99f04b820ca85d1ae2d8fda0d55e20d4967cefbee。未重新解析全部token/manifest成员或重跑审计；未发POST/改源码策略cache/操作服务/8035/提交推送。正式GPQA174/198仍未达88%，原C32唯一根因未确证；按用户要求继续小时只读跟踪，不新增测试。


2026-11-01T09:30:09.624303+08:00 GPQA已有8题final/gold离线复核完成：xhigh1/8、medium3/8；5截断缓解中3对2错、79对→错，不能推广全量或替换174/198。ERQA252/400终态不变。新增证据effort-answer-review-002，独立37成员冻结通过；4条反序复核仅方案未执行。本轮0新模型请求/源配置变更/服务动作。


最新用户授权acc023四条反序C1诊断，准备独立effort-reverse-c1-001；ERQA252/400已终态，无新ERQA/全量任务，不动服务。


2026-11-01T09:38:57.515734+08:00 四条反序C1已唯一启动：2026-11-01T09:38:28.473242+08:00派发seq0/doc79/medium，1派发/0完整返回，0完整pair。唯一driver1701290/start621293347/argvSHA82c3470d6bcaba67f7c6717197c8884a6e615cc96cae8967b2509e99e448fe2f；独立CPUwatch1701313/start621293357/argvSHA571cc4596afaa57595b8d710e350167acdf91001c0b2db41d6c4ec61487a4ea8，两者精确active。当前同API1336953/start607626732/argv/listener及source/runtime保持，health200/running1/waiting0/KV0.00116634/preempt0，prefixhits32000未增。已CPU按原terminal-manifest核14个唯一基线raw/body/input/result成员、4新body逐字节同原arm、strict-scoring-contract与前次002manifest绑定一致；原start-model.sh SHA875788ff同。新服务窗口无fatal/RPC/Traceback。完整证据写独立D=G0/diagnostics/effort-reverse-c1-001，A=G0/commands/effort-reverse-c1-20261101-v1；独占LAUNCH_ATTEMPT/RUN_ATTEMPT已消费，不重放。0服务/生产改动、0额外smoke/C8/全量/8035/提交推送，正式GPQA174/198与ERQA252/400仍原终态。原唯一driver负责剩余3POST，4条即停；watcher仅CPU等driver自然退出后审计，不能手动补发。快照本地progress-initial.json SHA afec93f3afd74c1f8fdd18e23c8ba3150235c9c658e24d9c5f70925676075ec0。


2026-11-01T09:42:17.089499+08:00 当前4条反序C1：2派发/1完整响应，seq1/doc79/xhigh在途，0完整pair。首条seq0/doc79/medium=2506tokens/HTTP200/stop/非空final A（goldD，错），原arm同为A/错；完整2506输出IDs和prompt IDs均同，reasoning/final文本完全同，prefix增量0。只是首个arm已回读，不泛化剩余3条/正式198。driver1701290/CPUwatch1701313精确active，同API健康200/running1/waiting0/KV0.00203208/preempt0/prefixhits32000，source/runtime同，无FIRST_ANOMALY或终态/watch错误。原客户端继续剩余序列，4条即停；monitor已更新新D/A/PID及只读快检，不重放launch。快照SHA e919df0dd0c79fb2552cbca606756720cdf81d122d4ae2d7e4e7d3e9b36b7b27，仍0服务/生产改动、0额外请求/全量/8035/提交推送。


2026-11-01T10:15:05.315515+08:00 小时只读：本小时无新增完整响应，仍2派发/1完整/0完整pair；seq1/doc79/xhigh在途，不能用生成token增长当完成或估ETA。seq0 medium2506stop/答案A对goldD仍错、同arm完整token/prompt及文本一致事实保持。精确同API1336953/start607626732/argv/listener及完整source/runtime保持，health200/running1/waiting0/KV0.027282783829930546/preempt0，prefixhits32000未增；原唯一driver1701290/CPUwatch1701313精确active，无FIRST_ANOMALY/终态/watch错误。8份控制/plan/PREPARED/原script SHA均核同，当前seq1日志窗口inode27006868286/start7471251/end7749273/278022bytes/SHA7e25925e149f9ad7c9903ada4695578d540aad318b5d681275ee04a7f3b4e3c9无新fatal/RPC/Traceback。free1391.53GiB。快照heartbeat-20261101T1015.json SHA682f91d6f01bbf21e0ca1bd83039dd0159f99c4dceb0784101bddf70350733c9；monitor只读，0新POST/重试/审计抢跑/源配置cache变更/服务动作/8035/提交推送。原4预算唯一队列继续、4条结束即停，下一步等待原xhigh及doc145两arm自然完成后独立CPU审计；正式GPQA174/198/无gate与ERQA252/400不变，保持用户小时汇报ACTIVE。


2026-11-01T11:10:05.045937+08:00 小时只读：3派发/2完整/1完整pair，seq2/doc145/xhigh在途，doc145/medium尚未派发。新完成seq1/doc79/xhigh=49012tokens/HTTP200/stop/非空finalD（goldD，对）；同arm全部49012输出IDs与prompt IDs、完整message/reasoning/final均与原轮一致，无首差。已CPU独立回读raw/header/body/actualprompt/token/usage并与冻结observer逐项相同，raw SHA41418f014cbb469320aa7c1deaa36444637b810b7fb775cc9e318eacb9fc2401。doc79反序后仍xhighD对、mediumA错，两个arm均逐token重现原轮（medium2506、xhigh49012）、prefix增量0；该题较短medium答案退化在本次反序复核重现，只限此局部，不推广doc145/全198或唯一原C32根因。

同API1336953/start607626732/argv/listener/source/runtime保持，health200/running1/waiting0/KV0.033198662915133625/preempt0，prefixhits32000未增；原driver1701290/CPUwatch1701313精确active，无FIRST_ANOMALY/终态/watch错误。8控制资产、plan/PREPARED/原script SHA核同，当前seq2新日志窗口inode27006868286/start7847971/end8192367/344396bytes/SHAcc131c3ec0fad131c29c04c2d3b8f97d53ed1f737ae0ec6a2c86dc2f062ef5b0无fatal/RPC/Traceback，free1391.53GiB。快照heartbeat-20261101T1110.json SHAcb1ea7413703da762086d7d90e69ab063b9cab57c614ed78f9124685ff447ff6；monitor只CPU读原返回，0新POST/重试/全4审计抢跑/源配置cache变更/服务动作/8035/提交推送。原唯一4预算队列继续doc145两arm，4条结束即停，再原CPUwatch独立终态审计；正式GPQA174/198和ERQA252/400不变，保持小时ACTIVE。


2026-11-01T12:24:23.599485+08:00 四条反序C1复核已完整结束/独立CPU审计退出0/原driver和watch退出，4/4全部与原同arm完整token及message一致。79 xhighD对/mediumA错；145 xhigh60K无final/mediumA对；本轮两arm均1/2正确，限定局部取舍，无新formal gate。ERQA252/400终态及GPQA174/198保持。BF168010健康空闲，未重启/新增请求，转整体小时只读后续。完整SHA见同acc023终态节。


2026-11-01T13:25:19.393088+08:00 终态后小时只读：无新增诊断/修复/验证。4/4复核及独立审计终态保持，原driver1701290/CPUwatch1701313均退出；同API1336953/start607626732/argv/listener/source/runtime保持，health200，running/waiting/KV/preempt全0，generation5638395/prefixhits32000/prefixqueries315314未增。7份关键冻结回执及原script SHA一致；服务新窗口inode27006868286/start8325262/end8325427/165bytes/SHAa41401b46c60bd6b146cb32c77c363f95f17e4053b323e243d1e2a7183da2bb1无新fatal/RPC/Traceback。快照heartbeat-20261101T1325.json SHAe0da562cbe80335305246752c1b05c534788f6f5db258211c76b22e41835ab60。未重读全113062tokens/95成员或重复审计，0新POST/源配置cache变更/服务动作/8035/提交推送。局部反序取舍与原正式GPQA174/198<88%结论保持，唯一原C32根因仍未确证；无下一批授权，继续用户要求的小时只读后续。


2026-11-01T14:29:47.846607+08:00 终态后小时只读：无新增诊断/修复/验证。4/4反序复核及独立审计保持完整终态，原driver/CPUwatch均退出；同API1336953/start607626732/argv/listener/source/runtime保持，health200、running/waiting/KV/preempt全0，generation5638395/prefixhits32000/prefixqueries315314未增。7份关键冻结回执及原script SHA一致；同inode27006868286日志窗口start8325427/end8325427/0bytes/SHAe3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855，本窗口无新增日志或新fatal/RPC/Traceback。快照heartbeat-20261101T1427.json SHA27a9091b3846324e6d44e2def4f64469f802d2e9e033e95b1f4f32c5e4ebf31b（记录时间以实际工具14:29为准）。未重读全raw/95成员或重复审计，0新POST/源配置cache变更/服务动作/8035/提交推送。正式GPQA174/198<88%及原C32唯一根因未确证仍开放；无下一批授权，保持小时只读跟踪，不新增测试或改变策略。


2026-11-01T15:28:09.954434+08:00 终态后小时只读：无新增诊断/修复/模型验证。4/4反序复核及CPU审计终态保持，原driver/CPUwatch均退出；同API1336953/start607626732/argv/listener/source/runtime保持，health200、running/waiting/KV/preempt全0，generation5638395/prefixhits32000/prefixqueries315314未增。7份关键冻结回执及原script SHA一致；服务窗口inode27006868286/start8325427/end8325757/330bytes/SHA912eb437ec245b2ad23c92babdff2a90383e985824295b45a6058e0f479be0c8无新fatal/RPC/Traceback。快照heartbeat-combined-20261101T1528.jsonl SHAcba22f1226280dc18efd3ae5f93179bd3384bf9a9179a54a895078e8eb069cbc。未重读全部raw/95成员或重复审计，0新POST/源码配置cache变更/服务动作/8035/提交推送。正式GPQA174/198未达88%、原C32唯一根因未确证仍开放；无下一批授权，继续用户小时只读后续，不新增测试或修改策略。


2026-11-01T16:32:20.991301+08:00 终态后小时只读：无新增诊断/修复/模型验证。4/4反序复核与独立审计终态保持，原driver/CPUwatch均退出；同API1336953/start607626732/argv/listener/source/runtime保持，health200、running/waiting/KV/preempt全0，generation5638395/prefixhits32000/prefixqueries315314未增。7份关键冻结回执及原script SHA一致；服务窗口inode27006868286/start8325757/end8325922/165bytes/SHAc74176c1a7a4aaaaddd3b84c6ffa8029b0c5d47c55b4606a95386f801325bf09无新fatal/RPC/Traceback。快照heartbeat-combined-20261101T1633.jsonl SHAa16dbd5a62e5217278c23704c94f87df2f21a3d5d055fcfcedf929a6b97de5a3（实际工具16:32）。未重读全部raw/95成员或重复审计，0新POST/源码配置cache变更/服务动作/8035/提交推送。正式GPQA174/198未达88%、原C32唯一根因未确证仍开放；无下一批授权，继续用户小时只读后续，不新增测试或修改策略。


2026-11-01T17:32:01.799146+08:00 终态后小时只读：无新增诊断/修复/模型验证。4/4反序复核与独立审计终态保持，原driver/CPUwatch均退出；同API1336953/start607626732/argv/listener/source/runtime保持，health200、running/waiting/KV/preempt全0，generation5638395/prefixhits32000/prefixqueries315314未增。7份关键冻结回执及原script SHA一致；服务窗口inode27006868286/start8325922/end8326087/165bytes/SHA64bcdaba91f18f916b10f02695847dcc2d968ad9645da6b71dc923fdb1994ab8无新fatal/RPC/Traceback。快照heartbeat-combined-20261101T1731.jsonl SHA525d6be4b19c819f9ca5c6ddb78ce9d02f25a024d63cb07d80825d58f046db0f（实际工具17:32）。未重读全部raw/95成员或重复审计，0新POST/源码配置cache变更/服务动作/8035/提交推送。正式GPQA174/198未达88%、原C32唯一根因未确证仍开放；无下一批授权，继续用户小时只读后续，不新增测试或修改策略。


2026-11-01T17:57:32.287735+08:00 acc023基于已有198产物冻结下一批未参加effort对照的8题方案：原对96/111/176/81、原错106/186/89/69，拟C1/seed1234/16POST，仅方案未授权执行，实际0新增请求。D=effort-heldout-plan-001、29成员独立回读通过；ERQA252/400及正式GPQA174/198保持，BF16/修复/服务未变。

2026-11-01T18:31:54.068578+08:00 终态后小时只读：无新增诊断/修复/模型验证。原4/4反序复核及独立审计终态保持，driver/CPUwatch均已退出；新8题方案仍未执行，未见RUN_ATTEMPT/DRIVER_PID/STARTED。精确API1336953/start607626732及source/runtime保持，health200、running/waiting/KV/preempt全0；generation5638395/prefixqueries315314/prefixhits32000未增。10份关键冻结回执（含新方案REPORT/manifest/proposed-plan）及原script SHA一致；服务新窗口inode27006868286/start8326087/end8326417/330bytes/SHAf2cecdb39ec163cff704daf7621878f210440ed5f522c3fa2c65b23933295915无新fatal/RPC/Traceback。只读快照heartbeat-combined-20261101T1832.jsonl SHA52a947c90f58f224c4ae73f402c9f39b0cd48af7f51b5522ed1513c5110b3035。0新POST/重试/生产配置或代码变更/服务动作/8035/提交推送，未重复全量raw/manifest审计。正式GPQA174/198仍未达88%，原C32唯一根因未确证；ERQA252/400保持。保留BF16及现有修复，继续用户要求的小时只读跟踪；下一批16POST仅提案，不自行执行。

2026-11-01T19:27:21.003778+08:00 已启动用户明确授权的新8题16条C1对照，当前1派发/0完整（首seq0/doc96/xhigh在途），不将派发或生成中token计完成。原4条反序任务已结束；新唯一driver798086/start624823628/argvSHA6e64aa494a9226ae1d951db1d385db0d733ea41762e2907c85620cc0f2b9ae25及CPUwatch798171/start624823639/argvSHA05e5a8cd4da698e4ddb0015011f84d28446707cace1e38f38e006976eaffa930精确active，当前同API1336953/start607626732/source/runtime相同，health200/running1/waiting0/KV0.001454921482336502/preempt0，prefixhits32000未增，无FIRST_ANOMALY/终态/watch错误。

本次执行D=G0/diagnostics/effort-heldout-c1-002，A=G0/commands/effort-heldout-c1-20261101-v2，16body逐字节匹配原提案，原正确4题96/111/176/81与普通错4题106/186/89/69保持；只effort变量，C1/seed1234/原采样/BF16/现有修复不变。主要安全信号是同轮paired loss，收益不可抵消损失；截断缓解与答对分别报告。原C32标签只作分层；严格native regex/gold/None计错固定8和组内4分母，不从reasoning补答。完整HTTP请求/响应实体bytes、解析头、prompt/output IDs、usage、reasoning/final、新service byte窗口及严格评分归档；CPUwatch仅等driver自然退出后一次独立审计，不发模型请求。

plan SHA14b917b4dd37cecd351c0103b79267f808fa537d55753cdb1dd61067a451a477、PREPARED ebaf467395fa3804d29f6363094aa8a221ea2b0855b42e1c8084951f987d79ea、assetmanifest cf84cfeec61136236ba656b0135ba2e297690a32bf014e1e876702af4df97c9e；只读快照progress-initial.json SHA766ecdcfa2b58b76966f8d5518470ade4a214fb863194bc6cc4cfaf6bb371340。首CPU预备001的字符串doc_id筛选错误和0POST首错保留，新002已归一并验证8条映射、16输入及显式xhigh prompt渲染；不是新模型事故。16请求结束即停，0重试/额外smoke/C8/全量/服务动作/8035/提交推送。正式GPQA174/198<88%及ERQA252/400保持，尚无新模型分数或修复结论。

2026-11-01T19:29:15.496972+08:00 新8题队列3派发/2完整/1完整pair，seq2/doc106/medium在途。首对doc96：xhigh585tokens、medium855tokens，均HTTP200/stop/finalB（goldB、均对）/thinkend+EOS，prefix增量0。2026-11-01T19:29:56.035270+08:00 CPU独立回读原raw/request/body/prompt/output IDs/usage/native严格评分有效，SHA8f1254f7ee47e7ae8e106990653da161d430b875c88da4e108fb539d97bf3c61；原始材料在D=effort-heldout-c1-002，未抢跑全16审计或新增POST。当前首对medium反而多270tokens，不能说medium保证更短或由1题推广8题；原doc96 C32 xhigh609→本轮C1 585，prompt IDs相同但输出第136个0-based token开始不同，仅描述历史C32/C1差异，不作为唯一数值因果。

同API/driver/watch精确active、health200/running1/waiting0/KV0.001743500949907384/preempt0/prefixhits32000，source/runtime同、无FIRST_ANOMALY/终态/watch错误；快照progress-after-binding.json SHAd77535949f092c1ab3ce4a6c030bdfe7dbd6a114096664796ba0d7171ce5d86e。原16预算继续，不重试/重启/8035/全量/部署medium/提交推送。当前处于定位验证阶段，尚未确认通用修复；完整结果将分别报告paired loss/gain、截断与正确性，正式GPQA174/198及ERQA252/400保持。

2026-11-01T19:31:34.958406+08:00 主回复后数分钟只读快检：6派发/5完整/2pairs，seq5/doc111/xhigh在途，driver/watch精确active、同API/source/runtime，health200/running1/waiting0/KV0.00116634201476562/preempt0/prefixhits32000，无FIRST_ANOMALY/终态/watch错误。新完成元数据doc106 medium942/xhigh525均stop并答B（goldA，两者错），doc111 medium1151stop/B对，尚无第3完整pair。此次只读metadata未独立重新解析新raw，不抢跑终态审计；原16预算自然继续。快照heartbeat-20261101T1931.json SHAe7f0e6cdc73d510b39da7a67a46213c39534ce3ac39d2e4c9ff5070756c91b29。距19:29主通知仅数分钟、无新故障，不重复打扰，下一小时仍按用户要求主动报告；0新POST/重试/服务或源码变更/8035/提交推送。

### 小时只读进展：15/16完整，末条仍在途（2026-11-01T22:15:34.363747+08:00）

实际工具核验为2026-11-01T22:15:34.363747+08:00，延迟heartbeat触发20:40不作为核验时间。新8题16条C1已16派发/15完整/7pairs，最后seq15/doc69/medium在途；不报告8题最终分或终态。新完成seq2..14共13份原response.raw/request/body/prompt/output IDs/usage/native严格regex及gold于2026-11-01T22:16:16.543776+08:00独立CPU逐项回读有效，8关键控制/plan/原script SHA核同，未重跑auditor或抢跑16终态审计。

| doc | xhigh：输出token/finish/答案 | medium：输出token/finish/答案 |
|---:|---|---|
| 96 | 585/stop/B对 | 855/stop/B对 |
| 106 | 525/stop/B错 | 942/stop/B错 |
| 111 | 984/stop/B对 | 1151/stop/B对 |
| 186 | 23938/stop/B错 | 6606/stop/D对 |
| 176 | 6777/stop/C对 | 1833/stop/C对 |
| 89 | 18448/stop/B错 | 5672/stop/B错 |
| 81 | 60000/length/None错 | 2738/stop/B错 |

仅对已完成7对：同轮paired gain=doc186（xhighB错→mediumD对，goldD），paired loss暂0；不是8题无退化结论。原正确doc81由历史C32 D对58849变本轮xhigh60000length/no final/无thinkend-EOS、medium2738stop/B错，两个C1 arm都错，不能单归因medium；medium消除了此题截断但未恢复正确答案。其他非length均stop/thinkend/EOS/非空final，15响应均HTTP200、prefix命中增量0。69只完整xhigh25848/stop/B错，medium不作完成或正确率推断。固定每arm8/原分组4分母保留，尚有缺项不报最终百分比，不拼原174/198。

同API1336953/start607626732/source/runtime，driver798086与CPUwatch798171精确active；health200/running1/waiting0/KV0.012132361782459133/preempt0/prefixhits32000。无FIRST_ANOMALY/终态/watch错误；当前seq15新窗口inode27006868286/start9562480/end9686195/123715bytes/SHAc12769ccdb458170b87374fbb593bbc8011c5dd05aa3d2c703c795e2fd006ed4无fatal/RPC/Traceback。快照heartbeat-20261101T2040.json SHA358e4f0d3cdf1352d5dbfdb5a33f9ea48a59cebd428ac23fdd2c393ad7602f1c（文件名是触发时间，实际工具22:15）；独立回读hourly-independent-20261101T2215.json SHA633fbd3d76044abb11fc0863f41851001c6370d1ff92186d231eebd8644eb143。monitor本轮0POST/重试/生产源码或配置变更/服务动作/8035/提交推送。原唯一controller继续最后一条，16完成即停并等原CPUwatch一次审计。BF16与现有修复保持；整体GPQA174/198<88%、原C32唯一根因未确证和ERQA252/400不变，继续小时ACTIVE。

2026-11-01T22:18:31.575083+08:00 距22:16主通知仅数分钟，只读快检仍16派发/15完整/7pairs，末条seq15/doc69/medium在途；driver/watch精确active，同API/source/runtime、health200/running1/waiting0/KV0.014152418055455307/preempt0/prefixhits32000，无FIRST_ANOMALY/终态/watch错误。generation上涨仅表示在途活动，不计完成或ETA。快照heartbeat-20261101T2218.json SHA50eab19a7660cfb11b58296e5ecf05314b424db518277c3ce365baf67f946b47；0新增POST/重试/服务或生产改动/8035/提交推送，不重复原7pairs通知，下一小时仍主动。

### 新8题16条C1验证完整终态（2026-11-01T23:15:21.167554+08:00只读复核）

原driver于2026-11-01T22:25:33.525621+08:00完成16/16完整HTTP200、8pairs、0retry；独立CPUwatch/audit于2026-11-01T22:25:35.291547+08:00完成并退出0，driver798086/start624823628与watch798171/start624823639均自然退出，16预算结束即停。2026-11-01T23:14:02.642167+08:00核同API1336953/start607626732/argv/listener/source/runtime、health200/running0/waiting0/KV0/preempt0/prefixhits32000；没有运行中评测或下一批模型请求授权。

| doc | native gold | xhigh：token/finish/答案 | medium：token/finish/答案 |
|---:|---|---|---|
| 96 | (B) | 585/stop/B对 | 855/stop/B对 |
| 106 | (A) | 525/stop/B错 | 942/stop/B错 |
| 111 | (B) | 984/stop/B对 | 1151/stop/B对 |
| 186 | (D) | 23938/stop/B错 | 6606/stop/D对 |
| 176 | (C) | 6777/stop/C对 | 1833/stop/C对 |
| 89 | (D) | 18448/stop/B错 | 5672/stop/B错 |
| 81 | (D) | 60000/length/None错 | 2738/stop/B错 |
| 69 | (D) | 25848/stop/B错 | 25189/stop/D对 |

本次固定8题：xhigh3/8=37.50%，medium5/8=62.50%；同轮paired gain仅186和69，paired loss=0。原正确4题两arm均3/4，原普通错4题xhigh0/4、medium2/4。本次刻意按原对错/学科/长度平衡且各arm一次，未见配对损失仅限这8题，不能外推全198、覆盖旧doc79已反序重现的medium退化、部署默认medium或签formal gate。两个gain都是非截断stop答错→stop答对，不是单靠补final计分。

截断单独看：xhigh仅doc81为60000length/reasoning-only/无thinkend/EOS/final，medium0length。doc81 medium2738stop/有final/thinkend+EOS但B错，goldD，属于截断缓解却未答对；原C32 xhigh58849stop/D对，本轮C1 xhigh也错，不能单归因medium。其余15响应均stop/非空final/完整thinkend+EOS。medium并非每题更短：96/106/111反而比xhigh长，其余5题更短。总输出xhigh137105、medium44986，仅token观察，不作性能收益结论。

全16完整request.http/body、解析response头及精确HTTP实体bytes（非TCP分帧）、prompt/output IDs/usage/reasoning/final/真实seq-doc-effort/严格regex最后匹配和gold均在D=G0/diagnostics/effort-heldout-c1-002；独立CPU audit/report与本次CPU只读回读均核固定8和组内4分母、None/length计错、不从reasoning补答、仅effort变量/16body匹配提案、历史xhigh prompt IDs相同及完整output首差。55冻结输入/322terminal成员/326audit成员大小SHA全部通过，未重复执行固定auditor/watch。源/runtime前后当前及原script一致，16raw合计prompt6708/output182091与服务计数差一致，prefixquery增6708、prefixhits仍32000；累计核账不是独立TCP或逐rank trace。

权威SHA：FINAL_SUMMARY 263886e3e720e063cc8a38b18d5af74c2b99930ff71339301facd0605fd0161e；FINISHED 37305ebc1b54ac9d8dd36b8d2898bb28e2fc005da07b14e6769da47a9a8c15fe；terminal-manifest 5ac6f23f8d21cc1faf5bf9631a652cd02b58e6ffa8c31f2d122a82c6b932c7f5（322）；frozen-inputs 387c83aa6971c165087e8ca26cb3f6410a9d48338dda582d6983bc64710d0d94（55）；audit/report 4811493481ea875b484825d44b6e708123a1521f1a7ca0c26c7e3fe7cc67a6c8；audit/manifest dbf63107f4647e9b70ef19d94639d6f212cb7bc676cc3d179fb60a263bba99d9（326）；audit/READBACK 444266613e53fc502456adef0c3f034e7470befb22cbd58c14895dcbbb1ca3a9；A/CPU_WATCH_COMPLETED 60fd96718d6aed03ceede9c53f4c0b41d8e56a034833c7a9eb4e121e453d1b44，CPU_AUDIT_EXIT=0。最终driver.log 4ffa8d1fde89b629284aeda3f1eeda437aa26dab0203b7ad5e254dc20b645a8e、cpu-audit.log 52fba5099b9e0b54c8b8cf826732cd78c4b6d6ae02724fe7c884df640100a348；本地补充terminal-review-20261101T2315.json SHAdec3945483beddcf91eab8b94acc9394ce6e5eab26f8d7b2d8725a9f2bdf6cad，原件在远端D/A，不依赖临时文件。

本次最终新窗口inode27006868286/start9686195/end9761528/75333bytes/SHA1b91d5429c9ba5c3777b4edb4da08743def4db7af8b41dec6e973d8db16f8cdb无fatal/RPC/Traceback，全部16每seq窗口无新设备/RPC/HTTP fatal。首CPU预备001字符串ID类型错误的0POST历史原件保留，不当生产故障。monitor本轮0新增POST/手动retry/生产源码配置cache修改/编译/服务动作/8035/提交推送，BF16和现有修复保持。正式GPQA174/198<88%、原C32唯一模型根因未确证及ERQA252/400保持；本小对照完成不代表整体修复闭环。下一步先基于已保存doc81的早期输出分叉及现有源码继续限定原因；下一批模型/配置/源码操作没有新增授权。整体按用户要求继续ACTIVE小时只读后续，不重复全量raw/manifest审计。

### 终态后小时核验与doc81既有产物定位（2026-11-02T00:20:41.348937+08:00；0新增请求）

2026-11-02T00:19:20.021730+08:00同API1336953/start607626732/argv/listener/source/runtime保持，health200、running/waiting/KV/preempt全0，generation5820486/prefixqueries322022/prefixhits32000未增；16/16与独立审计终态保持、原driver/watch已退出。7关键summary/manifest/审计/原script回执SHA一致；日志inode27006868286/start9761528/end9761693/165bytes/SHAedec5f760d65d49e763978c58670bb8bb1ab9681cdab77d2228e9a6aae681b22无新fatal/RPC/Traceback。快照heartbeat-combined-20261102T0019.jsonl SHA163de3529d6e4d9df8a43131cf1c65478b1785a69f096ee0ac4eaa1b9561bd5e。

本轮额外仅CPU读取已保存doc81三个SHA绑定响应（历史C32 xhigh、当前C1 xhigh/medium），未重复完整16审计。历史/当前xhigh prompt IDs均778且完全相同，输出首次分叉0-based112，原token4992→当前7995；prompt+已生成位置890，reasoning文本首差字符490。差异早于总长6400的首次边界，因此“仅在之后长解码跨边界时才第一次分叉”不能完整解释本题；但原C32可能部分prefill、align初始化/复制及采样数值路径仍不能排除，也不能将表面措辞分叉当机制证据。

当前C1 xhigh60000tokens/196254推理字符/length、0thinkend/0EOS/无final；全输出没有重复64token窗口（最大出现1次），尾部周期1–512均未连续重复3次。历史答对C32 xhigh58849tokens/188638字符/stop倒有59个重复64token窗口、最高4次，且也没有该范围周期性尾部。当前medium2738tokens/7082推理字符/stop/B错，亦无重复64token窗口或周期性尾部。仅这些事实不足以称当前为“字面token死循环”，也不以重复统计排除语义上反复推演。当前xhigh尾部仍在变化并继续推演，与60K预算耗尽一致，不是HTTP/RPC故障；medium结束较早却给错答案，不能把强行更早结束当正确性修复。

三原件SHA：历史doc81 e37fa23f2fde170aabddf0554e7dc2da57fbf38a9a5e19878217ab9b2b6057e3；当前seq13/xhigh 0d67a32b935b87c6f7b05d962670d4f746ff3c3db5befb3285a77f4e3b31d4bb；当前seq12/medium 17d0a1c4a40a9e5fefe7629d4774cac13f1be3e40eed47f3a9d7572b1c1ba9b9，均在D=effort-heldout-c1-002内，受原终态manifest绑定。CPU方法=逐token首差、全滑动64token窗口Counter、末尾period1..512×3重复、reasoning字符串首差；本地补充doc81-existing-readonly-20261102T0020.json SHA818d7cb9ad113178b78b18c8e95ec1c3e9626ead1e8c09574b62f052d64b7fea，结构化摘要写同state，无原题/推理全文进入仓库。

这只是已有产物的新局部定位，尚缺首差前logits/实际RNG状态/Mamba状态的匹配受控证据，不能确认唯一源码根因或声称已修复。无新模型验证/生产修复/服务动作；0新POST/重试/GPU/编译/源配置cache变更/8035/提交推送，BF16与现有修复保持。原正式GPQA174/198<88%、ERQA252/400及本8题X3/8/M5/8均保持；后续先在现有调用链上明确取得首差机制证据所需的最窄验证设计，不自动扩请求、调参或部署medium。用户小时ACTIVE继续。

2026-11-02T01:23:23.734769+08:00 终态后小时只读：本小时无新增定位结论、修复或模型验证。16/16及独立审计终态保持、driver/watch退出；精确API1336953/start607626732/argv/listener/source/runtime同，health200、running/waiting/KV/preempt全0，generation5820486/prefixqueries322022/prefixhits32000未增。7关键冻结回执及原script SHA同；service窗口inode27006868286/start9761693/end9761858/165bytes/SHAb42022d5b134cb5c9916be71dd47d5ae20cbf73aec09728df0d6219ae05606d6无新fatal/RPC/Traceback。快照heartbeat-combined-20261102T0123.jsonl SHAde985165a6011f92b370ef719c40b41f5a1afb559ec61764a7a004e389313bf6。未重读16raw/全326成员或重复doc81固定分析，0新POST/重试/生产源码配置cache变更/编译/服务动作/8035/提交推送；保留BF16/现有修复。仍缺首差前logits/实际RNG/Mamba状态匹配受控证据，无可确认源码修复点；下一步是收窄验证设计，不自动扩测或部署medium。原GPQA174/198<88%、ERQA252/400、本8题X3/8-M5/8和doc81局部事实保持，整体小时ACTIVE继续。

2026-11-02T02:26:03.104050+08:00 终态后小时只读：本小时无新增定位、修复或模型验证。16/16及独立审计终态保持、driver/watch退出；同API1336953/start607626732/argv/listener/source/runtime，health200、running/waiting/KV/preempt全0，generation5820486/prefixqueries322022/prefixhits32000未增。7关键冻结回执及原script SHA同；service窗口inode27006868286/start9761858/end9762023/165bytes/SHAf047449e7a0d562c178dd9c51ef99a9b2d5634c483e92ac46b86305437098b03无新fatal/RPC/Traceback。快照heartbeat-combined-20261102T0226.jsonl SHA2ac0f137e436f27848945911bc4543c0ab7995fe40de6831ccd62b11bdba85b2。未重复全raw/manifest或doc81固定分析，0新增POST/重试/GPU/编译/生产源码配置cache变更/服务动作/8035/提交推送，保留BF16及已有修复。首差前logits/实际RNG/Mamba状态受控证据缺口不变，原正式GPQA174/198<88%仍开放；下一步收窄机制验证设计，不自动扩测或部署medium，整体小时ACTIVE保持。

2026-11-02T03:23:08.047561+08:00 终态后小时只读：无新增定位结论、修复或模型验证；原16条/8pairs及CPU审计完整、driver/watch退出。同API1336953/start607626732/argv/listener/source/runtime，health200/running0/waiting0/KV0/preempt0，generation5820486/prefixqueries322022/prefixhits32000未增。7份关键冻结回执及原script SHA一致；新窗口inode27006868286/start9762023/end9762188/165bytes/SHA2ab28e47b0b7c408a1c318a98c58416926e9a3e41195b5dbbde227b8a54b106f无新fatal/RPC/Traceback。快照heartbeat-combined-20261102T0323.jsonl SHA53462275876dbd5cad2c7bfc1a2567748d05293c868b9e86d068a7a7c8ef0398。未重复全raw/manifest或doc81固定分析，0新POST/重试/GPU/编译/生产源码配置cache变更/服务动作/8035/提交推送，BF16和现有修复保持。仍缺首差机制的受控证据，无确认源码修复点，正式GPQA174/198<88%不变；下一步收窄验证设计，不自动扩测或部署medium，整体小时ACTIVE继续。

2026-11-02T04:30:13.505946+08:00 终态后小时只读：无新增定位、修复或模型验证。原16/16、8pairs及CPU审计终态保持、driver/watch退出；精确API1336953/start607626732/argv/listener/source/runtime同，health200/running0/waiting0/KV0/preempt0，generation5820486/prefixqueries322022/prefixhits32000未增。7关键冻结回执及原script SHA一致；新窗口inode27006868286/start9762188/end9762353/165bytes/SHA2422754460a711d2597814becadfaada8a2f011a88ab0346cfee7d28f04087d8无新fatal/RPC/Traceback。快照heartbeat-combined-20261102T0430.jsonl SHAa7996e914bd0db48825cb2f8c171b34f9a92ea8f6cb19290889b9569df3b33c0。未重复原raw/全manifest或doc81固定分析，0新增POST/重试/GPU/编译/生产源码配置cache变更/服务动作/8035/提交推送；保留BF16和现有修复。首差前logits/实际RNG/Mamba状态的受控证据缺口保持，正式GPQA174/198<88%仍未闭环；下一步收窄机制验证设计，不自动扩测或部署medium，整体小时ACTIVE继续。

2026-11-02T05:27:40.170512+08:00 终态后小时只读：本小时无新增定位、修复或模型验证。16/16、8pairs和CPU独立审计终态保持、driver/watch退出。同API1336953/start607626732/argv/listener/source/runtime，health200/running0/waiting0/KV0/preempt0，generation5820486/prefixqueries322022/prefixhits32000未增；7关键回执及原script SHA同。日志inode27006868286/start9762353/end9762518/165bytes/SHAbf7eca0c01b34d64240c66f9aeba3a060b04e15c0953fc9acc28d75dcfef20fb无新fatal/RPC/Traceback。快照heartbeat-combined-20261102T0528.jsonl SHA2857acf611bfb5b33d153ea4120ef30a0646c286602b15190be27e1d3922064f，实际工具时间05:27。未重读全部raw/manifest或重复doc81分析，0新增POST/重试/GPU/编译/生产源码配置cache变更/服务动作/8035/提交推送，BF16/已有修复保持。仍缺首差前logits/实际RNG/Mamba状态的匹配受控证据，暂无确认源码修复点；正式GPQA174/198<88%仍开放，下一步收窄机制验证设计，不自动扩测或部署medium，整体小时ACTIVE继续。

2026-11-02T06:29:35.098104+08:00 终态后小时只读：无新增定位结论、修复或模型验证。16/16、8pairs及CPU独立审计终态保持、driver/watch退出；精确API1336953/start607626732/argv/listener/source/runtime同，health200/running0/waiting0/KV0/preempt0，generation5820486/prefixqueries322022/prefixhits32000未增。7关键冻结回执及原script SHA一致；service新窗口inode27006868286/start9762518/end9762683/165bytes/SHA141671c85f370db20e54f9b281a36beb5756fa07b9938b6c23f10b04df05c197无新fatal/RPC/Traceback。快照heartbeat-combined-20261102T0630.jsonl SHA5834e6eaca1221c809a0e46b114bfe4d9918bcd3c302d4c1483dfcd7c17f1667，实际工具06:29。未重读全raw/manifest或重复固定doc81分析，0新增POST/重试/GPU/编译/生产源码配置cache变更/服务动作/8035/提交推送；BF16及现有修复保持。首差前logits/实际RNG/Mamba状态的受控证据缺口未变，正式GPQA174/198<88%仍未闭环；下一步收窄机制验证设计，16请求预算已消费完，不自动扩测或部署medium。整体小时ACTIVE继续。

2026-11-02T07:28:38.333184+08:00 终态后小时只读：无新增定位、修复或模型验证。16/16、8pairs及CPU审计终态保持，driver/watch退出；精确API1336953/start607626732/argv/listener/source/runtime同，health200/running0/waiting0/KV0/preempt0，generation5820486/prefixqueries322022/prefixhits32000未增。7关键冻结回执及原script SHA一致；新窗口inode27006868286/start9762683/end9762848/165bytes/SHAd4a3b9187b5851bc3fe22ed1fbb70eeeaf5efc5b8b080e8074ff2b411ea8a29b无新fatal/RPC/Traceback。快照heartbeat-combined-20261102T0729.jsonl SHAa95d0a4ab48eba52e22d0b8f37761171fc4964257827ad26cff913b758bc4537，以实际07:28工具时间记录。未重读全raw/manifest或重复doc81固定分析，0新增POST/重试/GPU/编译/生产源码配置cache变更/服务动作/8035/提交推送，BF16与已有修复保持。当前只有只读跟踪，无新修复在执行；首差前logits/实际RNG/Mamba状态受控证据缺口仍是定位阻塞，正式GPQA174/198<88%不变。下一步需有范围明确的机制验证设计及对应新授权，不自动扩已用完的16预算或部署medium；整体小时ACTIVE继续。

2026-11-02T09:12:41.547384+08:00 小时只读：本次首只读SSH因连接服务未响应退出255（不是模型HTTP/RPC/device故障），最初快照heartbeat-combined-20261102T0838.jsonl为0bytes，未把07:28历史健康冒充当前。首错记录FIRST_MONITOR_SSH_TIMEOUT-20261102T0912.json SHA998d0a912d0bdd8080914199094d23d63526043a0c0b51a990097a46d165bb67保留，09:12:04本地记录时间；未保存未返回的远端身份/health/source/log证据。随后指定PPU-07 connectivity-check只读通过（ok3/changed0/unreachable0/failed0），补完一次带连接超时保护的同范围只读核验；不重发模型请求或执行服务恢复。

补核实际2026-11-02T09:12:41.547384+08:00：同API1336953/start607626732/argv/listener/source/runtime，health200/running0/waiting0/KV0/preempt0，generation5820486/prefixqueries322022/prefixhits32000未增；16/16和独立审计终态保持、driver/watch退出。7关键回执及原script SHA一致；接续service窗口inode27006868286/start9762848/end9763178/330bytes/SHA1773617c7ed79bba5cdba499423c24c626459fe3ebb5e4197b5017f67df3e9ad无新fatal/RPC/Traceback。快照heartbeat-combined-20261102T0912.jsonl SHA12a7779fce2363ee3265d6f6d6a201cbe8078d53a643cd1c4ec6e43fc809e0f9，连接后续回执MONITOR_SSH_TIMEOUT_FOLLOWUP-20261102T0913.json SHA7c525412c486bfa7f5de20c2e6f0a2a6468acbfe7e76d82a9ce6970f710ecaae。初次只读连接失败后缺失项现已由补核完整取得，未发现模型服务异常；首连接超时原件不覆盖、不当未来新故障重复通知。

本小时无新增定位/修复/模型验证；仅连接只读重检，0模型POST/推理重试/GPU/编译/生产源码配置cache变更/服务动作/8035/提交推送，未重读全raw/manifest或重复doc81分析。BF16/现有修复保持，正式GPQA174/198<88%及首差机制受控证据缺口不变；下一步收窄验证设计，不自动扩已用完16预算或部署medium，整体小时ACTIVE继续。

### doc81首差前logits/RNG/Mamba最小取证方案（2026-11-02T09:32:59.683585+08:00；仅方案，未执行）

用户要求列清请求数、埋点与区分机制，先不执行；本轮仅读本地已冻结且SHA核同的源码副本和原产物摘要，0模型请求、0远端命令、0生产源码/配置/埋点修改、0服务操作。当前绑定身份最后实际核验仍09:12，不用本规划时间冒充新health检查。保留BF16/全部修复/原prefix策略，不重启、无8035/物理0–7、无提交推送。

**建议完整预算为3条短请求，当前授权执行数0。** 全部doc81/xhigh、C1、seed1234、原采样T1/p.95/k20/minp0/presence0/repetition1和原stop；R0 trace-off，R1 trace-on，R2 trace-on重复一次；body相同。新诊断契约将max_completion_tokens60000限为128，3条最大输出384，不跑60K、medium、额外smoke/C8/全量或自动扩测。必须先核三条prompt相同、输出0..127与原已保存C1长请求前128个ID一致，才把短请求当该轨迹的前缀取证；短cap可能影响调度，不预先假定等价。若提前stop或前缀不同，标not-reproduced/incomplete并停，不自动延长。原首差是输出0-based112（第113个）；采样它之前已消费prompt778+输出0..111共890tokens，标准文本position末位889，具体positions以实际metadata为准。

**完整方案需要worker内埋点；当前无已核实的安全免重启开启入口，因此当前不可直接执行。** 保存Python文件不能让既有worker函数对象/已捕获graph自动生效，禁止拿改文件、attach/热注入、重启、抢占物理8–15另起实例来绕过约束。先只读证明已有动态trace控制存在且绑定到这些worker；没有则保持本方案未执行，不把只加HTTP logprobs叫完整取证。若仅想HTTP初筛，替代预算2条128-token请求（原请求 vs logprobs/top_logprobs20），只能看有限概率/输出前缀，取不到完整原始logits、实际q/RNG状态和Mamba；这与3条完整版二选一、不相加，本轮都未执行。

**采集位置与内容**（通用request trace ID+步窗口过滤，不能把doc编号/答案或题面特化进生产逻辑）：

| 层次 | 实际调用链/位置 | 必取内容 |
|---|---|---|
| 请求/执行 | ModelRunnerFL `_prepare_inputs`→hidden_states[logits_indices]→`compute_logits`→`_sample` | trace/request→row/slot映射、真实input IDs/positions、computed/scheduled、discard mask、padded/真实shape、graph/replay签名及命中实现；比较前缀必须相同 |
| logits | `compute_logits`之后、grammar/processor之前；`Sampler.forward`及`TopKTopPSampler.forward_native`过滤之后 | 输出步0..112每步完整原始vocab logits、原始dtype，实际grammar/penalty/T/minp/topk/topp配置，实际保留token集合/概率、胜者与次优margin；保留阈值并列项，不能硬截正好20个；API logprobs受raw/processed模式影响，不能替代两阶段logits |
| RNG/选择 | `preserve_discarded_generator_offsets`外包裹；`random_sample`实际`q.exponential_`前后；`sample_with_exponential_noise`破坏性div/reciprocal之前 | 请求generator对象/设备/实际seed、完整get_state及SHA、get_offset（wrapper entry、draw前、draw后、finally后）、generators行key/实际分支、discarded/valid标记；保存实际q和实际probs，重算p/q胜者；只有实际使用global分支才取global状态，不能为观测再抽随机数，不假设一次消耗4 |
| Mamba管理 | grouped `mamba_buffers.preprocess_mamba`→native `collect_mamba_copy_meta`/`do_mamba_copy_block`；deferred corrections及accepted CPU→GPU resync | TP8全部rank、全部异构partition/layer的spec/shape/dtype/stride、逻辑block/slot、computed/scheduled、分组独立state_idx、accepted重置前/各分组/最终值、src/dst/size/bias；记录初始化与真实copy命中，零命中也需记录 |
| Mamba数值 | 初始化/prefill末尾、窗口内每次真实copy前后，以及decode110/111/112各层输入/conv状态/SSM状态/输出 | 仅目标请求活跃state切片，按原始BF16/FP32 state dtype无损保存；同逻辑位置比较，不以跨请求物理地址不同当错误。若实际首差更早而完整state窗未覆盖，机制证据仍incomplete，另设计更早窗口，不能补推因果 |

复制类不变量可直接用捕获的源state与实际copy_func的切片、bias、dst布局生成CPU字节reference：copy必须逐字节一致；数值更新必须用同输入、同原始dtype的匹配native/reference检查，不能因为state不同就直接判算子错。完整raw logits与q按113×实际vocab×dtype字节×实际采样rank数预算；Mamba按活跃spec大小×rank×checkpoint数预算，不dump全KV或其它请求。埋点需有界预分配缓冲、正确stream/event时序，采到probs/q被原地修改前的值；不得改计算、RNG、cache或graph签名/转eager。所有实际采样rank要覆盖，Mamba全8rank，不能只抓API rank0。

**判别表：**

| 在相同input IDs/positions和共享前缀下观察到 | 优先归属与必要证明 |
|---|---|
| raw及processed logits/probs相同，但实际generator生命周期/q不同且解释了token变化 | RNG/seed-row绑定/offset回退/随机核路径；核valid行应正常推进、discarded seeded行finally恢复entry offset，不假定固定减4 |
| raw logits相同、processed logits/保留集合不同 | logits processor、topk/topp或metadata，不归Mamba |
| probs与q都相同，返回token却不同 | argmax/tie、row scatter或输出bookkeeping，不归seed漂移 |
| draw前raw logits已不同，且Mamba初始化/copy目的state偏离源切片reference | 状态初始化/索引/copy管理路径，才有具体修复靶点 |
| 初态/copy结果/层输入相同，但Mamba更新或层输出不符合匹配reference | Mamba数值/算子路径嫌疑，需要另外授权的同输入算子重放确认 |
| Mamba状态及输出都相同，后续hidden/logits不同 | 继续查attention/MoE/GEMM/TP归约/LM head，不能硬归Mamba |
| q相同，只有小logits扰动改变近并列候选胜者 | 上游数值差异被T1随机采样放大，不自动等于采样bug或Mamba bug |
| 三条token前缀和R1/R2内部轨迹均一致 | 仅证明当前C1稳定且未观察到token级埋点扰动，仍未解释旧C32首差 |

**覆盖与停止边界：** C1的778token prompt+128输出可能根本不触发discarded-row回退或align跨blockcopy；必须报告实际命中次数，没命中不能宣称这两项修复已验证，prefixhits0也不能等同无Mamba路径。原C32正确运行没有首差前内部快照，不能拿本3条C1与历史答案单独证明C32因果；两边token一旦不同，之后state差异属于不同输入历史，除非另行授权固定公共prefix的teacher-forced/张量重放。条件性采样器克隆RNG重放、Mamba同输入reference或32-lane shape重放均不计入/不自动执行本3条，当前额外HTTP授权0、额外设备重放授权0；明确0POST不等于0GPU成本，不能暗做。

对应修复条件：若确证offset/row错误再改请求本地RNG bookkeeping；若确证copy字节/accepted或slot映射错误再修对应group状态管理；若仅数值扰动，先定位首差层及reference再决定修复，不降effort/温度或扩大预算掩盖。修复后需重新验证原正式范围，原174/198和本8题3/8对5/8不被本计划改写。

方案JSON本地/private/tmp/acc023-doc81-evidence-plan-20261102/plan.json SHA70731c5d258bf736966fd84385c234516a93109e63453d606ae93be599c1116d，结构化摘要写同state。源码依据为上次已绑定实际导入路径的冻结副本，已对6文件逐项SHA核同：runner5c78833043957e14032fc065b0c1545c50e1fd46f5e174854b09083075c223dd、sampling_rng d0ea4e18f0e56618ac216efbcea463bf09b1a51d35f44a43b32173109f4547da、mamba_buffers d9a05fef68331f425bf60f3683c7b9da7956d2f3f55fe621a69bdf096a07816c、native mamba_utils934e9d2a919d71badc3beb7e474b1508483f6298a171e67ed153b3bb3c0e4a49、sampler1a2f18ddc91c89f3744ab5a93624be056bf20b7a8b2e6e13d0236182718a2253、topk_topp35b9a1ffeb1e50b73b0ddd1ffc0f968910ee21cf9cc5455dd879fde547b6ddc1。它们不是今天新执行或新部署的探针。当前没有launcher/RUN_ATTEMPT或新请求排队。

### doc81免重启取证入口只读实核（2026-11-02T09:43:06.430608+08:00；0模型/控制POST、0埋点/服务变更）

用户本次只授权核实当前8010是否已有安全入口，未授权执行此前3×128方案。结论：**已找到现有通用I/O dumper和源码内RPC/profiler，但当前绑定graph服务没有可用的完整logits/RNG/Mamba安全免重启取证入口；这不是已部署新修复。**

运行证据：API1336953/start607626732/argvSHA c1b658b05137910a59f347c6fbb9048146d22f1274886b324b761803a9f30fbc保持；沿该API的children关系仅检查其EngineCore1344788及TP0..7 workers1349115..1349122，NSpid与原8010日志1983444/1983731..1983738对应，未查其它服务。启动日志该实例line47明确dtype=torch.bfloat16、enforce_eager=False、FULL_AND_PIECEWISE；现argv仍BF16/TP8/原graph配置、无--profiler-config。12个入口/修复/原生采样源码SHA全部匹配D/source-before冻结原件，原start-model.sh SHA875788ff3053946c6f25232f8699a24027184d80c4375af1fe0bde75fa7a3f4b保持。未attach或读取worker函数对象内存；代码归属证据来自绑定实例、启动日志和源文件SHA，不冒称直接取到worker内存对象。/proc environ只能观察初始/可见环境，不把其缺字段当运行时Python os.environ的独立充分证明。

| 候选 | 当前实际代码与运行证据 | 判定 |
|---|---|---|
| Plugin I/O dumper | `/opt/vllm-plugin-FL/vllm_fl/dispatch/io_dumper.py:752..764`，第758行`if _enabled or not eager: return`；`model_runner.py:5431`在load_model传enforce_eager。当前False；第866行确有`enable_io_dump()`进程内API，但静态调用扫描未发现把它接入服务控制的调用者或热读配置/信号控制入口 | 现有库函数不等于当前worker安全开启入口；在另一个docker exec Python进程调用，只影响新进程，不能启用现有worker。改env/YAML不能自动跨进程/追溯生效。不能为用现成dumper擅自转eager |
| profiler | `entrypoints/serve/profile/api_router.py:40`仅profiler_config.profiler非None才注册；WorkerFL `worker.py:1050`无配置直接RuntimeError。当前OpenAPI无/start_profile、/stop_profile，实际只读GET均404 | 未启用；即便启用，时序/shape等通用profile也不等于全raw logits、实际noise q、generator生命周期和Mamba state快照 |
| collective RPC | `entrypoints/openai/api_server.py:197`仅VLLM_SERVER_DEV_MODE时注册dev router；`entrypoints/serve/__init__.py:49..51`再注册/collective_rpc。初始API环境无该变量、默认0，当前OpenAPI无路由，实际GET /collective_rpc=404 | 当前外部入口不存在；没有向内部IPC投递命令、序列化callable或注入代码，不以内部RPC实现存在推断可安全使用 |
| 既有修复 | `sampling_rng.py:29..35`只在discarded seeded行保存/恢复entry offset；runner4723包裹sample，native topk_topp_sampler.py:437..468构造q并在div_/reciprocal_前后消费，未导出actual q/RNG。mamba_buffers分组修复也没有完整生命周期快照出口 | 行为修复与取证接口不同；HTTP logprobs拿不到这些机制证据 |

**完整取证最少需要放宽的边界：** 保持当前绑定实例且不使用未核实热注入方案时，需同时允许“新增有界worker埋点”与“仅8010 engine/workers一次受控重启以加载埋点”；只放宽请求限制或只改文件不够，只启用dev-mode/profiler也不够。实施采集还需另行授权此前3条短C1请求（trace-off/on/on，cap128；当前授权0），不是自动追加。埋点可优先在Plugin包装扩展点实现，保持BF16、现有修复、数学/RNG/cache语义及FULL_AND_PIECEWISE，预分配有界缓冲并在新worker生命周期中完成必要graph捕获。若扩展点确实覆盖不到才另行提出vLLM源码例外；本次不修改vLLM或任何生产代码。不需要放宽8035/物理0–7/提交推送禁令。若坚持现8010零重启且禁止注入，则完整方案保持不可执行；没有把另起实例、抢占8–15或改eager当作默认替代。

重启会产生新服务身份，需重新绑定，并核doc81相同prompt及前128输出ID匹配原冻结C1轨迹；不匹配则不能声称取到旧轨迹。旧C32没有保存内部logits/RNG/state，任何未来采集不能补回历史内部事实，也不能单凭3条C1确认原C32唯一因果。

最新计数generation5820486/prefixqueries322022/prefixhits32000均未增。新服务窗口inode27006868286/start9763178/end9763719/541bytes/SHA67b54eba686fd27c592c1825130464192f208132710fabdfc6cde33e16012ed5无新fatal/RPC/Traceback；此为附带核验而非定位/修复成果。本地控制面沙箱Ansible RPC/DNS限制已改用同一获准只读检查完成，PPU-07 connectivity ok3/changed0；不是新模型故障。没有模型/控制POST、GPU重放/编译、远端文件写入、埋点、服务动作或提交推送。

只读证据/private/tmp/acc023-doc81-hook-check-20261102：entry-check-02（活OpenAPI及源码）SHA94a2f725c5f1dd8fa11e8aefc50575235446e0575248b2fdeebc10a2b076e2d9；entry-check-03（关联worker/启动日志/来源）SHA5698706113794de71aa7d2c011d586784df1594e39d026acc8274c2d21b70fa9；entry-check-04（3候选路由GET404/源码核同/计数）SHAfeae11d6d0d521785f9193a446d4bc25468ab00ae232687667a60a9111c35e6e。汇总readonly-hook-report.json SHA64795bee4845de328e6256be657c750cfc98e235c2e6ae6a195bf61cade7e221；只读收集脚本也在同目录，未安装到目标环境，不是运行中埋点或模型launcher。后续monitor不重复本次静态扫描，不因本报告推定执行授权。

