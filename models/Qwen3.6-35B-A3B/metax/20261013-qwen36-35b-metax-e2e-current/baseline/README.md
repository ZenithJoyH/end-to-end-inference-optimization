# 20261013-qwen36-35b-metax-e2e-current / baseline

当前事实以optimize/state review034为准：原P1K baseline/prof003已完成；当前resident acc007完整159/198达标。采样候选未部署，AA003为CPU启动器失败0GPU，observer路线停止；新契约001仅CPU草案，无新性能结果/模型ABR，19FG保持。以下原始baseline证据保留，不按旧PID/旧下一步重放。

<!-- e2e:summary:start -->

- 案例：20261013-qwen36-35b-metax-e2e-current
- 当前状态：002/003 全轮保留且稳态不通过；已证 attention 编译停顿，候选未部署
- 当前候选：gdn-current-2093c683-1c6c64a9
- 下一步：见 optimize review018；op005精度170/198通过，D128候选稳态局部通过，完整D1024 P1K复现预热后编译/停顿，稳定性incomplete。原GDN旧不稳轮保持，不计算精确收益。

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|

<!-- e2e:summary:end -->

2026-10-15当前：API975866恢复原源码，12252文件无改动/C1/C8通过；历史GPQA164/198属于API952702，当前binding pending。后文按日期保留旧实例测量，不能作为当前实例gate或稳态性能。私有attention编译键修复、Event与新增编译5→0证据见[op005](../optimize/op-005-attention-compile-key-normalization.md)。


当前没有通过稳态准入的正式性能数据。P1K/D128/C64/N128 milestone预热如下，全部保留，因波动70.42%>5%停止；不能将其中快轮单独当作基线。

| 预热轮 | duration(s) | output(tok/s) | meanTTFT(ms) | medianITL(ms) |
|---|---:|---:|---:|---:|
| 1 | 20.9060 | 783.7000 | 2061.69 | 50.2948 |
| 2 | 24.5560 | 667.2088 | 2886.69 | 50.2373 |
| 3 | 52.1988 | 313.8770 | 12361.78 | 50.3215 |

GPQA65536基线完整164/198=82.8283%，阈值0.8，原生证据验证及服务绑定gate已通过。旧辅助进度regex漏计已定位，正式task/filter未变；直接调用原生filter核验的临时结果不作gate。

精度历史：30000上限旧轮149/198=75.2525%，来源和全部样本验证通过但低于80%，未签发gate；30题length、25题缺最终answer。用户只批准提高上限后，65536全量复测164/198=82.8283%，198唯一题/全部filter/config/provenance及服务源码连续性均通过，gate已issue/check。其他采样、198题和80%门槛不变。不能把随机复测的全部15题净增加都归因于预算。旧失败完整保留。

原服务四repo12249文件、模型清单、镜像/规范化挂载、启动和FlagGems配置保持一致。采样候选没有部署；实际部署后必须新full GPQA65536 gate。30分钟后台跟进仍开启。

新P1K baseline003仍不稳：三轮20.12/29.99/20.36s，output814.28/546.28/804.72tok/s，spread33.30%>5%，无admitted测量。慢轮106个ITL>1s（最长4.64s），另外两轮0；继续定位，不能报收益。原服务继续运行。独占graph验证的10–15分钟服务中断方案已准备但未授权/未执行；自动审批拒绝了未来停止服务的自动化扩展，现后台仅继续不停止服务的工作。


阶段探针（2026-10-14，Skill baseline；只作当前P1K父场景诊断）：Prefill P1024/D1/C64/N128三轮均128成功、0失败，输入131072/输出128 token。波动10.59%>冻结5%，0 admitted测量轮，保持incomplete。

| Prefill预热轮 | duration (s) | total-token throughput (tok/s) | p99 TTFT (ms) |
|---|---:|---:|---:|
| 1 | 7.9460 | 16511.46 | 4232.05 |
| 2 | 7.1048 | 18466.30 | 3680.65 |
| 3 | 7.1064 | 18462.34 | 3677.05 |

D1的total-token吞吐接近输入吞吐代理，仍含队列/网络/调度/首次采样；不能当纯设备Prefill时间。Decode P1024/D512/C64/N64已结束并完成终态核验，三轮均64成功、0失败，输入65536/输出32768token；warmspread79.31%>5%，0admitted测量轮。原始证据在remote results/phase-prefill-terminal-validation-20261014.json和results/performance/anchor-p1k-{prefill,decode}-001。

Mixed慢轮时间线：三簇集中client间隔位于0.682–1.861s（8请求）、11.262–15.904s（42请求）、19.097–23.695s（56请求）；同簇起止误差仅数毫秒。已按真实native client timing源码核验重建，不等于服务/设备根因。CPU-only产物results/p1k-baseline-003-gap-overlap-20261014.json；下一次trace应覆盖后半段而不是重复首24步。


| Decode预热轮 | duration (s) | output (tok/s) | mean TTFT (ms) | median ITL (ms) | max ITL (s) |
|---|---:|---:|---:|---:|---:|
| 1 | 30.4701 | 1075.42 | 2240.56 | 52.73 | 0.4715 |
| 2 | 56.6803 | 578.12 | 22408.47 | 52.46 | 9.0929 |
| 3 | 52.2610 | 627.01 | 18857.93 | 52.59 | 9.3810 |

慢轮2集中间隔覆盖初始0.693–27.801s，21请求/43interval；慢轮3覆盖0.427–18.810s，以及21.122–25.700s的57请求共同暂停。区间并集不是单个kernel时长。客户端全部9轮stdout/stderr与服务日志256KiB末段未命中队列超时/OOM/异常，不能因此联系私有Stream队列失败；客户端初始化干扰仍为待证明假设。source12249文件、模型/启动/FG/profile-off在阶段终态复核通过。

后续为prof-002有界capture，P1024/D512/C64/N64、1warm+2capture、各24engine iterations、TP0/1，专注初始填充停顿。已在源/配置/精度gate再次核验后启动，服务未中断；其耗时不属于无profiler性能。

prof-002已结束：两轮TP0/1共4新trace SHA及phase验证通过，各24step=1Prefill/8Mixed/15Decode、15graph launch，设备窗口4.66–4.72s没有重现原4–9s停顿。profile-stop/export造成约28.5s客户端暂停，只属profiling扰动。终态服务/source12249文件/模型/env未变，profiler OFF、API无请求。后续改变观测窗口或做完整时间线低开销主机/driver观测，不重复首24step、不归咎MoE、不报收益。


2026-10-14当前恢复事实：一次已授权中断285.98s后原服务恢复，当前namespacePID905636/birth489464369，source/args/env/FG白名单与workspace复用均保持；C1/C8 health、两rank各64graph launch通过。原正式164/198=82.83%已原生rebind/check新实例（evaluation_reused=true），不是新分数。gate accuracy/restored-anchor-accuracy-gate-20261014.json SHA161d7ffa...；旧gate仅是历史实例证据。私有采样20数值+8graph replay通过，资源条件为本服务停止时GPU6，尚无post-fix standardbenchmark或E2E，也未部署。后续CPU工程兼容及完整时间线观测按review-004，不重放已执行停止/评测脚本。

review019当前：完整P1K006的三测量1133.4/991.2/1146.2tok/s，波动13.68%>10%而incomplete；第二测量轮有自有TP attention/MoE编译和13请求共同8.90s停顿。源/gate保持、APIidle、FG全启用，停止重复测量及预热加码，先按op005文档核残余SplitKV参数与MoE输出界限专化。D128稳定不推广为完整场景通过；仍无ABR收益或最终验收结论。

Latest script-scope resume: approved restart completed, newAPI1008868; exact19scope, TP0/1 each22actualgraphlaunch, C1/C8 all9pass, profilerOFF. New full198/65536/.8 GPQA started13:44UTC, uniquecontroller1347505; no P1K untilnew nativegate. See op013/acc006 and currentstate; earlier no-restart/pause/oldgate text is historical.

13:47UTC precision terminal FAILED: UUID93378df7056a4feda30b619dec00112a strict0/198, flexible2/198. Bothfilters198 unique doc each (396rows); native resultSHA5600429275d8b34a6b47480577016fb65050044aaae56d948c1f4b47214e2422, samplesSHAf81e448b09ff1011b5334f48332b4ccaadf3c6ec92967af8e4918c4fa0c6feb8. Terminalvalidator executed once:12355source/model/env/instance/mount/config continuity passed then deliberately refusedbelow.8; no run-record/passinggate. P1K/performance stopped beforestart, no source optimization stacked. Accuracydiagnosis Skill invoked; root cause notconfirmed. New/oldMetaX MoE backendSHA75f34372... identical, Plugin call/import and otherpaths stillneed isolation. ServiceAPI1008868 remainsrunning/idle, no extra interruption.

Read-only utility initially parsedJSONL withstr.splitlines and broke Unicode separators, then usedliteral newline to verifycomplete396rows. This wasutilityfailure, notinvalidmodel dataset and notscorefix. Prior tinyhealth/graph qualifiedexecution only; no claim of semantic pass. Rawrequests/answers remainremote; currentfailure notrewritten/retried.

14:38UTC authorized cache-isolation lifecycle running: host1426324/birth501432585; candidateAPI1025146/birth501435120, C1/C8health passed, native graph/KVrole check in progress. Sole envdelta VLLM_CACHE_ROOT under current case, no source/19scope/cache deletion. Plan2ca14820..., lifecyclee27deeed..., monitor57dc52b4.... First0/198 remains failed; review023 ranks existing lifecycle then newfullGPQA ifqualified, P1K blocked. PrivateMoE4shape exact does not exclude graph/model. Actual vendorcacheblock32 corrects earlier1056 guess; unsupported1056 probe retained, not rootcause. OldFXartifact/cachebinding suspected, not confirmed.

14:42UTC cache-isolation window completed346.56s (14:32:48→14:38:34), one authorization consumed, no future restart permission. CurrentAPI1025146/birth501435120; GPU6host1428564/ns1025947 andGPU7host1428565/ns1025948 bothbirth501445784. Source12355/argv/19scope/model/image/mount unchanged, soleenvdeltaVLLM_CACHE_ROOT. Two ranks each22actualmcGraphLaunch and20cachewritecalls show K/Vboth[tokens,1,256], oldtraceVheads8 mismatch removed. C1/C8ninepassed, profilerOFF. Newservice52590ffc33cfb35e0877546c4b2611ac7bbea76f8b557955d9fba0cb8469bef4, runtime3ea0ea0895f3459d2b6921f2c7c08713b0c70dc73e07e00dd013851aac13e828, undermanifests/acc006-isolated-cache-{service,runtime}-20261015.json.

Oldcompileartifact24bc62e8... unchanged. NewrankFX d12605b2.../710ddf40... and correctKVshape are single-variable counterfactual evidence supporting stalecache input-binding hypothesis; formal semantic resolution notyetclaimed. CPUevidence accuracy/acc006-cache-counterfactual-evidence-20261015.json SHAc67dd01740541a644013e912b8d99760136cc6ef1d53c645bfef43f82ca16e33; creator55fb02e9... completed.

NewformalGPQA UUIDd7e72aff3e6a4a7c8809d3ae7113be32, hostcontroller1446999/birth501481765 started14:40:59UTC, eval_modelqwen36-35b-script19-isolated-cache-full-graph-c32-g64k; original198/65536/temp1/.95/k20/seed42/C32/strict>=.8 unchanged. Source/env-bound newservice; provenance2equal/preflight0. Config269a8003fea443f07bafea501f528f63567905c73d095a16a99c405fd62785c6, contract219a5d447c52e0ab459740ac562e8495fd32e0e95994da760981d059f8b33e5a. Launch3941ca83... executedonce. Monitor10573a53539cd44e93727a158f6f1e7ed869a00758e76c02032fcd91ca620894 saved; terminalvalidatora447e4f70a25e85ba9408384fe518f1da9c260d15366aeb1ce2d9ee678d589b0 savednotexecuted. 14:42snapshot0complete/0timeout/32active; notformal score. P1K blocked until native terminalgate, no concurrentGPUprobe/profile/benchmark/sourcechange. Firststrict0/198 remainsfrozen; no oldgate rebind. Heartbeat updated ACTIVE30min/quietunchanged for thisUUID.

2026-10-15 16:23UTC最新：隔离缓存后的正式GPQA已完成，UUID d7e72aff3e6a4a7c8809d3ae7113be32 strict164/198=82.8283%>=80，0timeout；全198/65536/temp1/top_p.95/top_k20/seed42/C32不变，全部filter/原生来源/config/12355源码/当前service/env/model/tokenizer/镜像挂载连续性通过。CPU收尾15:56:07完成，nativeissue/check成功：gate accuracy/acc006-isolated-cache-g64k-accuracy-gate-20261015.json SHA9fdcc14eec68a6203a3c46cbf7e45c46fdcea5474ba4def838119fedaf98a642；terminalcontinuity06b0a111d267331fd8525ed33c6be9b66add1385f36273844fd7c725683b8fb7，terminalvalidation4f6834150a253a745c977c3254a54fd3ba48a6ee734669d5f8e3d30c9e6940d8。未重复GPQA或issue/validator。当前API1025146及GPU6/7workers保持，旧cache/source未动，原19FG范围不变。

缓存隔离执行边界得到反事实支持：相同源码/参数，旧cache启动Vheads8且0/198，新增VLLM_CACHE_ROOT后K/V均1head、两TP各22actualgraphreplay、C1/C8和新full164/198通过；可恢复性能工作，内部缓存key/二进制失效机制仍不作过度确定归因。原始0/198、C1无关输出及私有负面/utility失败全部保留，不改判为通过。该分数只绑定当前组合/环境，不能归因单个Plugin/MoE/library改动或冒充NV验证。原用户启动脚本尚未写入cacheRoot；下次reload须保持隔离策略，不授权未来停服。

P1K新scene-entry基线已16:21:45启动：run-idop013-p1k-full-001，modebaseline/rolebaseline，controller1531875/birth502086404，nativeclientns1032848/birth502086510。完整P1024/D1024/C64/N128/temp1/ignoreEOS/seed42/range0，4warm末3spread<=5%/3measuredspread<=10%/600sround/全轮保留/无profiler。当前仅新scope单实例基线，不能与旧20scope不稳轮算精确gain。新planSHAf0a5bac2...、comparison8bbbadbd...、v2identityb5be1a8c...、observer1dfbb147...、v2launch36841b6f...。Freshsource/gate/APIidle/资源/镜像挂载/timeNS/cgroup通过。首版dryrun因baseline不能传--accuracy-gate而拒绝，0benchmarkrequests/无run目录，原文件日志保留；v2仅修原生接口，外部nativecheck+gateSHA仍冻结在identity/launch，七轮dryrun通过，不放宽测量/精度标准。真实测量尚无结果。

CPU收尾器1533067/birth502096784已16:23:29启动，commands/wait-finalize-op013-p1k-full-001-20261015.py SHAde78eacd2efda4335ae607c3812398f241dca454fc922a37ada40ac5b149d4d3；launcher11b45361...已执行，不可重放。只等现有native退出后finishd14dd85a...与analyzef929f151...，不产生新GPU工作。监控monitor-op013-p1k-full-001-20261015.py SHA3ffd90624dde2d41c84fb96fbe3a88ef0cafdb9b1a5d4775e8ec20e8f5c911d4。终态核native全部轮+稳定性+observer开销+source/gate连续性+compiler/共同停顿时间线；未达稳态/incomplete保留，不丢慢轮/自动加warm。review024首优先本轮baseline，其后按实际当前owner/routing/compiler证据重排；不能切P4K/最终acceptance通过。所有旧creator均不重放，heartbeat继续ACTIVE。

16:26:56UTC同P1K controller1531875仍运行、64active；首轮warm原生valid，116.005s/output1129.879tok/s、meanTTFT2080.8ms、medianITL52.873ms、maxITL.637s、ITL>1s为0。仅捕获两TP各一次mxcc --version，均不是--fatbin编译事务；不把compiler_executable计数2当作新kernel编译。尚无正式measurement/稳态或预热后结论，不算收益。CPU收尾既有1533067继续等待，源码/服务/白名单不变。

2026-10-15 16:47UTC P1K终态已核：op013-p1k-full-001 全7轮原生有效，各128成功/0失败，input/output各131072；末3warmspread0.843836%<=5%，3measured输出1132.9415/1132.7759/1133.0204tok/s，median1132.9415，spread0.021576%<=10%。3measured meanTTFT1923.3/1987.4/1855.0ms、meanTPOT54.593/54.545/54.665ms、medianITL52.935/52.803/52.880ms、maxITL.489/.509/.504s；均客户端proxy而非puredevice。全部7轮无ITL>1s/共同停顿、0root--fatbin编译事务；两TP仅warm1各mxcc--version，不当kernelcompile。Observer .011729core/p99sample12.442ms/5859samples missed0/fatalnull准入。Source12355/实例/env/模型/挂载/gate继续通过，APIidle，native和CPU收尾均退出。Nativecheck_run通过且project稳定通过，但仅新scope单实例sceneentrybaseline，无匹配anchor/candidate/revert，不能计算旧20scope精确收益或关闭P1K/最终验收。

证据：runrecord results/performance/op013-p1k-full-001/run-record.json SHA335474b47664a87497bed051134e47ccca4cc5bf660e5310b669a659387d4e73；terminalc5821fb18832a5bd2d472fe018ac3589034b79eee68715ca66c8ffa676c89bad；analysis23b0c1ffe48887b8901e836d4b99e48fb404556680a8eb5d16bed12c32a50875；postcontinuitya1691d4dfc78d41b946b95aa0ebed6098a0c2780fe46c5895228878e58951269。无编译/停顿结论仅限本workload、7轮、主线程5Hz/后代发现1Hz，不能排除亚秒进程或未测shape。

review025重排：先当前source稳态phase profiling确认compute/host/comm热点，再从真实dispatch/shape选择单变量算子或Plugin优化；旧samplerM1负面、旧MoErandomtile和当前范围未选FGattention延后。新profile_idprof-003-script19-steady-p1k已16:57:12启动：host1542915/birth502299063，commands/run-prof003-script19-steady-20261015.py SHA4f45257ce658ea0947e83b04c3ed17527b8af64cfcaee4889008c00d9305e2f9，launcherd1ec345f...已执行不可重放。Plan04fc6d9d...，P1024/D1024/C64/N128两轮firstwarm/lastprofile、600sround/temp1/seed42/ignoreEOS，沿用现有24step native profiler，无重启/源修改/关闭FG。旧4trace库存48be84c0...保持，actualnative source dfeb9bf4...证明初始单请求probe早于start_profile，抓主批次。按实际new/cached marker、query/cache shape、graph验证phase；cached可能仍chunkedprefill，不盲判pureDecode。当前仅capture，phase/rank/热点结论待生成；profiler耗时/导出暂停不算性能收益。monitor29008f0b5b4285eec82265400be0d6d918e589f3c26262470d18669437bbcdf7，唯一status results/prof003-script19-status-20261015.json。现有完整19FG/无callerworkspace/服务及精度gate9fdcc14e...保持；不并发其他GPU实验。

2026-10-16 review027: current baseline/service/gate unchanged. PrivateMoEpair full42row nativebench failedpromotion andwasnotdeployed; newpostforward samplingevidence trackedunderop003. No baseline speedup or finalacceptance claimed.

2026-10-16：原baseline数据不变；02:20Z现有模型目录在host/容器均缺失，原API/TP活且idle，后续GPU工作因model绑定不可核验暂停。见optimize/state.yml identity-001及review028，不以历史精度/服务进程存在旁路当前连续性。

2026-10-16 review029：用户已原路径下载完成；35文件/26shards齐，配置/tokenizer/index SHA与size相同，mtime变更，原tensor内容SHA无记录，不能宣布新下载等价或已加载。服务/四进程/12355source/env保持，未重启/加载。新resident双绑定明确区分原已加载模型与磁盘恢复，仅资格当前实例，禁止future rebind。新完整GPQA acc007已于北京时间10:48:51启动，UUID198b58e3e9a3457094744f9c7f9f1f80、198/65536/temp1/.95/k20/seed42/C32/.8；初始0/198/32active，无gate，不并发性能。后台30minACTIVE安静监控。历史164与P1K数据不改，op003 private80numericpass但60行native续接等待新gate；生产未部署、无E2E收益。详见op013与state review029/acc007。

<!-- baseline-record-review:start -->
## 正式目标覆盖与历史测量

本节是记录审查：原测量状态与角色保持不变，不是新评测回执。`incomplete` 表示此表未闭合正式基线证据；历史、缩减或有观察器的结果须按原范围解释。

| 正式目标 | 正式基线证据状态 | 已记录指标数 | 边界 |
|---|---|---:|---|
| p1024-d1024-c64-n128 | incomplete | 5 | 已列出原始观测；是否满足正式基线契约仍以原回执和稳态/身份条件为准。 |
| p4096-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p16384-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p32768-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |

| 场景 / 角色 | 已记录性能数值（附单位） | 证据范围 / 原字段 |
|---|---|---|
| p1024-d1024-c64-n128 / baseline | output_throughput = 1132.9415090378832 token/s；mean_ttft_ms = 1923.3154966423172 ms；mean_tpot_ms = 54.59329339388323 ms；median_itl_ms = 52.880474366247654 ms；p99_itl_ms = 56.29328929819166 ms | single newsceneentry baseline; not formalABR or final4scenarioacceptance；仅 script19 候选的场景入口，非原 anchor/ABR/最终验收；`/op013_P1K_current` |
<!-- baseline-record-review:end -->
