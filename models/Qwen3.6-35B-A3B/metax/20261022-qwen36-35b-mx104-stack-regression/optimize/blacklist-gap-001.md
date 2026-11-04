# opt1 to opt2 performance gap diagnosis

User requests finding gap between native benchmark_results/qwen36-35b-opt1 and qwen36-35b-opt2, specifically whitelist to blacklist. Same dedicated B mx-104 GPU4/5; user-owned benchmark still running. Initial phase read-only/CPU only; no service stop/restart, model request, kernel benchmark, profiler or source change. Original formal gates do not bind updated sampler/compiler/Gems/currentlaunch; do not claim formal performance or select best rounds. Planning review capability used to reconcile multiple retained changes and prefill/decode/mixed evidence. Keep all raw user rounds including cold/unstable; historical SUMMARY is only runner's original Run2/3 average, not independently accepted steady-state result.

Initial observations: opt1 five workloads all128success/131072outputtokens, original three rounds each; opt2 P1K/P4K/P16K complete, P32K still running at firstcutoff. P4K SUMMARY output1275.30->1082.01 (-15.16%), TPOT45.55->54.58ms (+19.82%), meanTTFT4560.76->4476.96ms (-1.84%); medianITL37.12->45.91ms (+23.68%). Stronger generation-cycle signal than first-token delay. P1K new599.70/948.70/1329.47 vs old1525.81/1567.46/1603.25 shows unverifiedwarmup; never drop extra rounds afterseeing results. NewP4K first303.69s vs later120.79/121.49 and P16 first383.98 vs227.99/224.01 preserve as transitioneffect, not steady claim.

Archived pre-cleanup inspect contains actual inherited32-op whitelist, USE_FLAGTUNE=0, FLAGGEMS_ATEN_SHAPE_AWARE=0; currentAPI113715/start1140171929 has onlyblacklist6, USE_FLAGTUNE andshapeaware absent. Service log shows real FlagTune costmodel loading/AUTO fallback due missing optionalxgboost at startup. LatestGems5.5dev@a456722a/FlagTree0.7@fe1d24f6 and FGV sampler also differ across history; historicalopt1 CSV lacks exact launch/source manifest. Do not claim allgap is whitelist or benchmarkcoldstart purelyFlagTune.

Primary falsifiable candidates: newly permitted linear (mm/mm_out exclusion does not cover atenlinear), newly enabled normalization/reductions/shape operations; sampler integration/compilerversion/changedtuningmode as competing causes. ActualvLLM defaultunquantized_gemm callsF.linear; model40layers. But compiledgraph may lower differently; staticreachability is not currentGPUtime proof. Existingonceoplist contains operationnames but not timing/counts and may omitvendorlognamespace; do not infer absentpath is unexecuted.

Before execution commands/perf-gap-registry-001.py SHAc68f6bc61f727de9203eecd16061096b90a15fa4d5b2de0c466796b41320c3bd: freshprocess currentGems only_enable(oldexactwhitelist) vs enable(currentblacklist), recordFalse, no kernels/model. commands/perf-gap-readonly-001.py SHA65610de4715b10f44f5f1d16fcad868d2c62948374e0e216a0fba8b28dd776a6 snapshotsallCSV/rawrounds+hashes/currentenv/log, registrykeys/functions and compiledgraph ASTcalls. Unique remote performance-diagnosis/blacklist-gap-001/read-only-001. CPU is registration/path evidence only, no hardware performance assertion. Currentuserbenchmark/service/launcher remain untouched.

User explicitly authorizes stop current benchmark immediately and prioritize gap diagnosis, accepting proposed B/A/B shorttargeted+two-rank traces. commands/perf-gap-stop-client-001.py SHA5179985a5ff073a0c492b7f1c0e8d1e9fbfbbb81a2d5a8e54194d33fc0c24c51 verifies exactparent17183/cwd/Bmembership and direct nativebench child/model8020 binding, SIGTERM only, preservesallpartialCSV/log. No service stop in this step. Next performance Skill mode targeted/diagnostic-only; profiler capture+analyze authorized. No formal/currentgate claim.

Exact userbenchmarkparent17183/nativechild219131 SIGTERM completed, stopreceiptSHAe52d4bc05f6abdcc864fd2aa3addb62fc2fe9419d11a18dec1440ff1fd49e386. Native benchmarktemperature defaultNone -> omits payloadtemperature, serverdefault0.6; diagnosisexplicit0.6 preserves sampling (notgreedy). FrozenmatrixP1K/D128/C64/N64, threewarmup/twomeasured perarm plusone profile64iterationwindow/rank; currentlatestGems/FlagTree/FGVconstant, onlywhitelist vsblacklist changes. Profilerconfiguniformallarms; unprofiledroundsbeforeactivation. Scope is targeteddiagnostic userexception, notformalperformance/currentgate. Rawroundsallretained; warm/measuredspread andBreturn drift>8% meansincomplete, no best-of. Finallyoriginalfullenv/argv/cwd restored, secret/fullenvkeptonlymemory, sourceshashprotected, oldlauncherunchanged.

Plan commands/perf-gap-bab-001-plan.json SHAde84db94af6c87459dcb91e6e8a508ba2c3d02a2917a126b4fcd4da85e054ed3; controllerSHAc9ac29ba3b3b5e6f759d8c0177c00d2d621bb4f6e043e05362da4832a0138f07; exec helperSHAb5a58e2b0f788d4d8271ccfcbe3eea37fd7317971ca84d364312515ddcfdcf68; starterSHAface2f0673b7d378ac3bee9445b79ca0745eef5dc5a3a6a2105e3cefc85b8586. CPU AST reviewed only, not hardware through evidence.

Controller001 failed before signal: Python Enum str(SIGTERM) serialized as Signals.SIGTERM in container snippet lacking Signals binding; original API unchanged/0diag. Finalizer then lacked original instance/log fields, old summary retained/no nativefinalreceipt. New002 fixes onlyint(sig) serialization andoriginalbindingmetadata, no benchmark/profiler/sourcecontractchange; newrootbab002/native-launch002. Do not replay001.
perf-gap-preflight-failure-audit-001.py SHAb77e17b08f44f747347de41b8bdd161eaeb8052315b263f29a69d4a6b27174e1
perf-gap-bab-002.py SHAe42dc7555414a991af97c136e599a563d608a7ef7bdaec77b55dbaa487474a0c
perf-gap-bab-002-plan.json SHA68ef765ae6eec8cde1ddafdb323ddc8378e3aab2a4c0ceca7701b108c1f6408a
perf-gap-start-bab-002.py SHA3e764abc221f290f233a50ad72e60f29fc4ac75ae51b02e3b92d1e36817a3619

BAB002 completedexit0, restored originalblacklist/no profiler/fullenv+argv+cwd parity,9667sourcefilesunchanged. Live restoredAPI370006/start1140894280. ShortunprofiledB1meanTPOT52.816ms/A52.031/B253.342; throughput920.388/933.426/911.519. Policy effect~1-2%, nothistorical15%. All6tracefiles two-rank validatednativecapture;64 cached64 iterations, softmax[64,248320], per-rank _guarded_sweep ~501.5ms/64=7.84ms eachstep inallroles. Oldsamplerarchive shortlist64 vsnewFGVfullvocabularyradix; candidateprimary root algorithmmigration, notpureglobalpolicy. Key-operator-analysis skill applied now to targeted samplingfilter.

Finite operator-onlymicro003 on restoredidleGPU4, no modelrequests/sourcechanges. Exactoldarchivedshortlist moduleloaded onlyinprivatebenchmark; directcurrentFGV interface. Bothuse same latestGems oldprimitivewhitelist toholddependency/policyconstant. M64/V248320/FP32 fromBF16 logits /temp.6, k20/p.95,2fixedseeds; exactold/newmask+finitevaluesassert (no tolerance), stoponfailure. Eachnew/old/new group3warmup+10samples GPUeventspan/wallincludesCPUvaliditysync; resetcopyexcluded, oldsampleroutsideCUDAgraph so nofalsegraphclaim. Memorycap2.2% singleGPU; require0running/waiting andidle4/5.600sbudget, no oldfullmodel or benchmarkreplay.
perf-gap-sampling-micro-003.py SHAbe6be554bd8804dce74e970a819d6c3ad61bc8b903f2cf1c0466bb99de5d7ae3
perf-gap-run-sampling-micro-003.py SHAa1652b3ea18d497baef91b7ff3ba0753d78cbf8206cf268a49d6cd3d3f9e5412

Prepared independent file-only commands/perf-gap-analysis-004.py SHAced076012bd67fc0cb14973dffdd05a2f6a7f54219821ca671b96f69e6a2cc82: requireBAB002native0/errornull/restoreerrornull, all3x5unprofiled rounds/64success8192out65536in, sixtraceSHA/tworanksx64execute_new_0_cached_64 andsoftmax[64,248320], warm/measuredspread8% andBreturndrift8%, micro003exactold/newpassed. Recompute medians/policyrelativeeffect/perrankGPUactivities (notcritical-path shares), fresh restoredPID/start/envhash/argv/cwd/healthmodels and9667stacksourcehashes. Inactive untilmicro resultpresent/pass; uniqueoutputindependent-analysis-004. No newgeneration/sourcechanges orformalacceptance.

Independent004 passed SHAad414302a63462add2fa590f705ffa879ce8cdce6fe57b42f81a457e7d631d1e. Micro003 native0/exactmasksandvalues/2seeds/new-old-new confirms10.56-10.60ms vs2.30ms, +8.27/+8.29msperAPI. Sourcec467MoE/GDN/sampler/compiler/Gems unchanged9667files; fresh restoredAPI370006/start1140894280/envhash+argv+cwd/health+models verified. Closeout commands/perf-gap-closeout-005.py SHA88000695bda926f08403c0534f746ff5cb607ae3342abfd3293273cdcdad052c writesconclusion/CASphase/currentjobnull only, no source/service/modeloperation.


## 最终定位结果

主要 gap 是采样接口迁移后没有保留旧 shortlist64 快路径。历史 opt1 使用旧 Plugin 专项 shortlist，最新 FGV 公共接口对 V=248320 做完整排序；temperature=0.6 后，BF16 logits 转FP32再缩放，实际进入 general FP32 radix 路径。此归因由六份真实两rank trace和固定输入的算子 new/old/new 对照共同支持，不仅是静态推测。

| 同配置短程 P1K/D128/C64/N64 | 当前黑名单 B1 | 旧白名单 A | 重新启用黑名单 B2 |
|---|---:|---:|---:|
| 输出吞吐 token/s（两轮中位数） | 920.39 | 933.43 | 911.52 |
| mean TPOT ms | 52.816 | 52.031 | 53.342 |
| median ITL ms | 43.029 | 42.537 | 43.540 |
| mean TTFT ms | 2080.87 | 2059.02 | 2098.36 |

以B1/B2中位控制值为分母，白名单吞吐恢复 **1.91%**，TPOT降低1.97%；B返回漂移-0.964%。三个服务的预冻结末两轮预热spread分别1.62%/0.65%/0.76%，两轮测量spread0.54%/0.06%/0.86%，均低于8%守护。所有15个无profiler轮次保留，不删除冷预热首轮。当前依赖固定时，单独白黑名单变化仅解释小部分历史差距。

三臂两rank各采集64个 `execute_new_0_cached_64`，每rank64次softmax输入均[64,248320]，证明为实际C64 Decode窗口。各trace的 `_guarded_sweep` 均512次，即每步8轮，约 **7.84ms/step/rank**，对白黑名单不敏感。当前黑名单下 `linear_kernel` 10304次/64步，约2.54ms/步；白名单改由更多MCBLAS调用，显示linear确有路径变化，但其净收益较小。上述为各rank设备活动累计，不相加两个rank、不冒充关键路径百分比；正式无profiler结果和profiler时间分开。

旧 shortlist 与当前 FGV 在同一Gems/primitive白名单、M64/V248320/FP32、k20/p0.95/temp0.6条件下：

| 固定输入 | 当前FGV B1 ms | 旧shortlist A ms | 当前FGV B2 ms | 新增ms/步 |
|---|---:|---:|---:|---:|
| seed20261028 | 10.556 | 2.304 | 10.596 | 8.272 |
| seed20261029 | 10.600 | 2.299 | 10.572 | 8.287 |

每组3次预热+10次计时，GPUevent和wall均保存；输入reset不计时，旧版CPU validity同步计入。两组过滤掩码差异均0、保留值差异0、旧实现fallback0。当前FGV过滤比旧路径多约 **8.28ms**，与历史中位ITL增加约8.7ms相符。此数值回归只覆盖所测输入，不证明完整GPQA或所有tie/fallback/graph语义。

## 结论边界与后续方向

- **已经完成：** 原始历史结果核对、同当前依赖的B/A/B政策隔离、两rank真实Decode路径证明、完整过滤API的固定输入new/old/new数值/耗时复现、原配置恢复和源码独立核验。
- **历史比较边界：** opt1/opt2之间还有编译器/库版本、采样器和环境变化，历史CSV缺精确launch manifest；不能声称每一个历史百分比均已完成独立归因。P1K/P4K/P16K初轮及P1K第二轮尚在明显过渡态，原用户SUMMARY不是本项目新稳态验收。
- **当前服务：** 已恢复原完整argv/env/cwd、黑名单、GPU4/5、8020/opt2，无profiler，GET health/models200；9667源码文件字节不变，FGV MoE调优/GDN/采样器代码本次均未改。原用户压测已按授权停止，部分结果保留，没有自动重跑。
- **下一优先项：** 保留 `flaggems_vllm.apply_top_k_top_p` 接口，在库内恢复有保护的shortlist算法，分别核验实际top-k backend、tie/top-k边界、原生fallback、RNG不变和graph。旧代码含CPU `bool(valid.all())` 同步，不宜直接无条件复制进当前库；当前黑名单还会使普通 `torch.topk` 进入Gems，须证明最终backend。修复须另建单变量实验并同原workload复测/新正式GPQA，不能把当前微测比例当端到端恢复。
- **次优先项：** 仅针对linear做选择性回退，不一次扩充全黑名单；当前政策对照已显示收益约2%，预期低于采样算法修复。USE_FLAGTUNE缺省/AUTO回退只作为预热与模式控制线索，尚无独立E2E因果量，不据此改配置或安装xgboost。

知识差量 refined：API迁移时保留了语义接口，不等于保留了专项算法复杂度；温度缩放后实际值域决定BF16/radix分支。下一次先核对原快路径、实际dtype/value分支和固定开销，再做白黑名单/依赖单变量隔离，避免把混合环境迁移归因于一个开关。

独立核验 `performance-diagnosis/blacklist-gap-001/independent-analysis-004/verification.json` SHA **ad414302a63462add2fa590f705ffa879ce8cdce6fe57b42f81a457e7d631d1e**。本次没有新完整GPQA、正式性能gate或已保留生产修复。

Closeout005 completed: conclusion SHA062c5aa886e550a7a80f8571388bc3dfe6614c68b0f614f115123ac8fff0b309，continuation SHAec34374a725dd1677d2933648b829df367f554a215dbe23684a888d8d79908ff，phase perf_gap_diagnosed_sampling_algorithm_service_restored/current_job=null。原用户测试未自动重启，生产修复未应用；本次诊断任务结束。
