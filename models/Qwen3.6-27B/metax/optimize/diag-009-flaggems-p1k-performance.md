# diag-009: Resume FlagGems P1K performance diagnosis

当前状态：FG路径已恢复、C8与两rankgraph命中通过，三阶段单实例稳态入口基线和双rank trace分析完成。没有候选/回退端到端增量结果；正式50000精度未解除。

User2026-10-13 requested continued optimization on the enabled FlagGems Flash Attention version. This explicitly resumes a bounded diagnostic performance cycle despite the retained native50000 formal failure; no formal scene close, newaccuracygate or final acceptance is implied. Existing clone/source isolation and OP001 source remain.

Restore whitelist with attention_backend, disable its complement blacklist, use the original private FG compilation cache. No model/Plugin/vLLM/FlagGems source change in this baseline. Source8002 stays protected. Stop only the exact task model82515/create1791815908.86 after idle and source verification. Newservice/log/manifests use fg-resume-01 names. Current mounts already match; reverify with maintained mount tool.

Currentcode hashes match candidate04. Old manifest runtime3.7.1.5 was hardcoded by service-manifest.py; actual current /opt/maca -> /opt/maca-3.7.0, .version.txt3.7.0.38. This is a historical identity gap, not proof of a newruntime upgrade. Build fresh factual identity; do not change oldmanifest or silentlyrebind oldgate.

Performance mode baseline: scenario-entry from retainedOP001, not originalanchor. Parenttarget P1024/D1024/C64/N128. Three plans: Prefill P1024/D1/C64/N128; Decode P1024/D512/C64/N64; Mixed milestone P1024/D256/C64/N128. Each3warmup+3measured rounds, last2warmup spread<=10%,600s perround, temperature0/ignoreEOS, randomrange0 and seed42. All admittedrounds retained. TTFT andTPOT/ITL are clientproxies with network, queueing andscheduler residuals; not puredevice times. Stage gains require parentMixed guard. Formalfourtargets remain unmeasured.

Accuracy mode baseline-sanity: freshgraph service, current imports/FGhit, capture+2replays andproject10GPQA-class questions C8. These scoped checks do not replace198fullGPQA. Anyrequired failure stops promotion. Subsequent narrowoperator direction is selected only after phase/profiler evidence, then minimumcorrectness andsame-config measurements; no unsupported claimfromkernelmicro alone.

Planning rev003: E2E cumulative effect unknown. OP001 complete-call graph operator speedups3.715/4.780/5.187x are historical localizedevidence; not E2E. C1 threequestion repetitions stable does not settle C32 numerical cause. Priority1 restore/measurethreeviews; priority2 onecurrentFlashAttention optimization ifftracehot; priority3 frozen50000 formal onfinalFG beforeformalperformance.

Prepared command/plan/tool identities before execution:

- `diag009-evaluation-tools.tar.gz`, SHA256 `2f2c842258d2917ee2cd70749fda19d7e2b0b384147b820cf70cdc8ddd84efbd`.

- `diag009-verify-mounts.py`, SHA256 `32adacf39859e88ad6e2dad04ada248a00b636c795fed67d34328f5264bec3e3`.

- `diag009-prepare-host.py`, SHA256 `c9f41bbf6ad41e2b3f510fde5a7d19e04dde9a6702c94781c4dfa19c30467690`.

- `diag009-stop-native.py`, SHA256 `b11afd364399a0fdfed2aaeebb7c20b9bbe41ac9afbd994dd8e6c8d172efbbe0`.

- `diag009-bind-fg.py`, SHA256 `9447f64d2e197f10e44d749a7592bed8303f0ffd04e122208953397c47169a71`.

- `diag009-execute-host.py`, SHA256 `a3f0b8958b5f6d14e6ab6a57c43db6e9b5a0b52ee1e89c1ea4ca0788a57eeb57`.

- `diag009-prefill-plan.json`, SHA256 `5a91e41f83fee047fffba166efee255d8de01300e8f1fb5e7a27e27490cef1ce`.

- `diag009-decode-plan.json`, SHA256 `96590647515d141bd91961818d8855ed9a17cb069a22e6be5d9a085625990dd9`.

- `diag009-mixed-plan.json`, SHA256 `cfe6dd8a15239a5dce959f1e630f79afd88b6ca1796b49b6a2c36ff8862df2b8`.

- `diag009-c8-config.json`, SHA256 `898637defb7488e8b0c0bc2574e97125dd77d34fe11d3c99ee615e87e2ed4886`.

Current mount parity recheck passed. Generatedstart `commands/start-fg-resume-01.sh`, SHA256 `3d5fbe3c17c706494c59e7f240e424a4414e8f5568c193332fe0093145047938`; onlyrole/log/receipt name andexplicitunsetblacklist differ from savedFG candidate04 script. OriginalFGcache andall servearguments retained. Currentweight/tokenizer22file verification is running before modelrestart.

Hostcontroller started PID3117282/create1791871292.99. Exactreceipt SHA256 `4281f72defb354a43ce48e5d4f057bb896ccaf5271acdcc78dc70a06eb9f8166`; v2worker SHA256 `0860cf54bf1fdccb411f4886dc9e3302fa898b1489aebc6562ee2607193fa929`. Originalv1 launcher failed before mutation duehostmissingpsutil; correctedonlyhostcontroluses/proc, no dependency installed. Fresh22weight/tokenizer file hashes match, receipt `manifests/diag009-current-weight-verification.json`, SHA256 `17c35dc10abd4acdec7066e2de6569da2064194998c700ca699d4890171f9e96`.

FG restored as `qwen36-fa-opt:92016:1791871328.92`, manifestSHA `ba5038ff6d431e982fc0a1868b6d9491991ed0a64a889d7602d35e6c3a0a4b57`. Bothrank190graph launches/960partial/960merge observed; actualdefault.flagos attentiondispatch, profilerstopped. C8runner rejected expected_samples10 against198rawdataset before modelrequests. Fix rawcount198 while limit10 remains; v2outputs/cache/UUID unique, no dataset/model change or service restart. Oldfailedcontroller/progress retained.

- Prepared `diag009-c8-v2-config.json`, SHA256 `9b5fbb6a89e8f8a44b99789c6ffee162dd17110d69201c3d4efd3eff24c6bc5f`.

- Prepared `diag009-continue-phases-host.py`, SHA256 `529a5502b4ce84899796d4f87ab9eb2b8c066f21c4dea602397d60dbf72e8986`.

- Prepared `diag009-launch-continuation.py`, SHA256 `9fa93a25195e8e83f7347860c3d576bbff5f0f5ba7e73aa06d453a879ed42fff`.

BoundedC8/phase continuation hostPID3127265/create1791871798.09, processreceipt SHA `dfc987a47f63e96da62b341e186672e8431cc5a6fdd0da09826a039ac8b6f952`; existingFGinstance reverified, norestart. C8v2config SHA `9b5fbb6a89e8f8a44b99789c6ffee162dd17110d69201c3d4efd3eff24c6bc5f`; firstinvalidC8 datasetpreflight sent0 modelrequests.

Prepared conditionalcurrentprofile: `commands/diag009-profile-current.py`, SHA256 `279af926218d7d5694c6f4581df5a42fc790941be53a4c63e548784fc2941cc8`. Modecapture, P1024/D128/C64/N64,2rounds/1warmup/1profiled,600s perround. Executeonlyafter3phase baselinescomplete, actualsameFGinstance, C8pass; expectrank0/1. Allprofiler timings are attributiononly; no claimsfromcategorysums as criticalpath.

C8v2native runnercompleted10requests andexit0; host JSONlineparser failed because str.splitlines() also splits Unicode line separators insidevalidJSONscience strings. Correct LFfile iteration consumes existingC8results; no repeatedmodelrequests. Preservefailedcontinuationevidence, separatephasecontroller follows.

- Prepared `diag009-validate-and-run-phases-host.py`, SHA256 `4e4b620eedf45db592a6a8d18792ea4b4556a4a8d4dd21540e8b1ea4b3c94934`.

- Prepared `diag009-launch-phases.py`, SHA256 `2a71d7bf31658918bdb66dae4c900dc0f0c4d4f9c18050dbe2ae5df403227e26`.

- Prepared `diag009-profile-current-v2.py`, SHA256 `1ebd17556706c0ea358b6784775de629341112d5450d0b63ff9d4c1b7a2bf5ea`.

NativeCLIpreflight version/help eachtimedout30s withdefaultplugins,0benchmarkrequests; disablingallplugins onfullCLI gave Failedtoinferdevice type while constructingunrelatedserveparser. Prepared privateclient-onlyconsoleentry directly forwards installed unchanged `vllm.benchmarks.serve.add_cli_args/main`, withnativeFlexibleArgumentParser. No newbenchmark mathematics/evaluator; maintainedvllm_perf still bindsrealentrySHA+nativebenchmarksource+version/flags+rawresults. ServerCLI, model, Plugin andvLLMsource unmodified. ClientVLLM_PLUGINSempty appliesonlytoentrychildprocess; privatePATHprefix usedconsistentlyfornewmeasurement identities. Failedrun-record with0rounds retained.

Privatecliententry validated: version0.122s/help13.434s, both0,0modelrequests; validationSHA `63928581a02f85ed960284fa97640c611ef66d456020fdaa6ef3e768b56eb320`. EntrySHA `b60947c477daea008b8738351ba030efd62d6fd82b65fa6d50613c44a3fc7164`, installednativebenchmarkSHA `dfeb9bf42b587ffae5cc8ef959e066df5c4a89d078f663c554f6d3973c3d54f3` unchanged. NewclientPATH/emptyplugins is frozenforallnewthreephase runs, original0-roundfailedrun preserved. C8reuse only, no repeatedaccuracyrequests or modelrestart.

- Prepared `diag009-run-phases-v2-host.py`, SHA256 `8bb8454618fd5b8e9c81917da0d03acd2de3d94f4bda7e3538e39c8ecaca46a8`.

- Prepared `diag009-launch-phases-v2.py`, SHA256 `4e201b1562b849ce7b0ef1a5293b4a05322841c18c21877bc62b999d39a38c08`.

- Prepared `diag009-profile-current-v3.py`, SHA256 `d4a09b749d0f04de51d5ccf485e4a93119df3531b703fc3c1cee53fd019c1e69`.

C8baseline-sanity passed fromexistingnative10doc/20filterrows, sampleSHA `c07a62bc330fd3d82fa001cd49daaee82b161ed1900879e14d0aad61a4ed5fc6`. Activephasecontroller PID3141026/create1791873842.9, receiptSHA `dbb935a64fb9d4d0b6732c92751fffaf83cc95f39cf270f5c09435e173a2d82f`, workerSHA `8bb8454618fd5b8e9c81917da0d03acd2de3d94f4bda7e3538e39c8ecaca46a8`. Rolebaseline-02 usesfrozenprivateconsole entry/nativebenchmark code; oldpreflightfailed0rounds retained. Conditionalprofile isnowv3 fornewphaseprogress andsamecliententry.

First two phase baselines complete (3warmup+3measured each, allnativecount/token/finite metrics checks). PrefillP1024D1C64N128: medianbatch21.432s,input6115.692tok/s,meanTTFT8.3659s,p99TTFTroundmedian10.9141s; warmupspread0.923%. DecodeP1024D512C64N64: medianbatch35.208s,output930.705tok/s,meanTTFT6.3957s,meanTPOT56.138ms,p99TPOTroundmedian66.113ms,p99ITL50.496ms; warmupspread0.0159%. Decode isonefinitewave, stillinitialPrefill/residualscheduler cost, notpuredevice. All3measuredrounds retained; roundmedianP99 isnot pooledpopulationP99. Mixedpending. No comparableanchor orcandidate yet, so cumulativeE2Egain unknown.

Run-record SHA: Prefill `27437d3e8d5ca49aff7c6dfcb1b2414c3a76eb097a2dd83d47de566fbc547092`; Decode `886d72202ff39023f7534ed9bac5c2639fc20e8b69b028f495ee65da7fd87035`.

Mixed03warmup didnotstabilize: last2output629.478/703.642tok/s,spread11.126%>10%,0measuredrounds; originalrun preservedincomplete, nooutlierremoved. NewMixedmeasurement contract uses6warmups, fixedlast3window<=10%,3measured, sameP1K/D256/C64/N128/source/client/instance. Thisfuturecontract appliesequallytoanyMixedbaseline/candidate/revert comparison; prefill/decode remainseparatevalidbaselinefacts. Oneboundedrecovery; ifunstableagain diagnoseinsteadof endlesswarming orrelaxingthreshold.

- Prepared `diag009-mixed-recovery-plan.json`, SHA256 `8ea697a387cb594cf887de18d4c0d7cd245a93e91025fd13e6d10f8223718fae`.

- Prepared `diag009-run-mixed-recovery.py`, SHA256 `09c960713f70f950cebcf1afbbeff484912cbe6c275244171f3cffc39d94d7b0`.

- Prepared `diag009-launch-mixed-recovery.py`, SHA256 `63aa77890c65db61206c0a7cb557a2db12d6376ef2622bfa819bf69439e53a72`.

- Prepared `diag009-profile-current-v4.py`, SHA256 `2d950eaa775301fb2857934a3d91625abbf59c07c68e84577249da636ea57ecc`.

## 三阶段入口基线结果

以下均为当前保留OP001的FlagGems服务，不是未优化anchor。每项保留全部3轮测量，表中是逐轮指标中位数。

| 阶段 | P/D/C/N | 输出吞吐 token/s | 平均TTFT ms | P99TTFT ms | 平均TPOT ms | P99TPOT ms | P99ITL ms |
|---|---|---:|---:|---:|---:|---:|---:|
|Prefill|1024/1/64/128|5.972（输入6115.692）|8365.883|10914.136|不适用|不适用|不适用|
|Decode侧|1024/512/64/64|930.705|6395.714|11183.898|56.138|66.113|50.496|
|Mixed里程碑|1024/256/64/128|706.477|5354.858|11178.853|69.605|87.025|1383.593|

Mixed原3轮预热未达稳态，已保留；新冻结6轮预热末3spread5.563%通过10%，随后3测量全部有效。Mixed原始请求、输入输出token计数、全部原生指标及来源校验通过，测量总384请求；batch耗时轮中位46.382s。记录SHA `8b340232d3d81b0029f65a6f6852ccb398221c90c5b55999272d41ac8f13fec2`。

TTFT/TPOT/ITL为客户端代理，含调度、网络和阶段干扰；单token Prefill没有TPOT。各行workload不同，不能按吞吐比例直接计算优化收益，P99轮中位不是合并总体P99。当前正式四场景仍未完成，没有candidate/revert或累计E2E增益。

当前P1024/D128/C64/N64 trace捕获通过：两rank各55mcGraphLaunch、880SplitKV/880merge，完整GPU/CPU分类存在。捕获回执SHA `11812f9cbca060539e130a2673b5ccfa1aa7a6ae319596d2b06cef13ac3a33a6`；profiled时长不是性能结果。下一步按可靠forward迭代标记、shape和Kernel语义分别归因。

阶段分析：GPU标记来源为当前 `vllm_fl/worker/worker.py:annotate_profile`，new/cached对应scheduler列表长度；本P1K no-new迭代同时有query1 Split-KV调用签名。Rank0 FA kernel活动占Prefill3.47%/Decode11.87%/Mixed4.00%，其余主要为GEMM、GDN及通信。该比例不等同关键路径时间。下一点为[OP002拆分策略](op-002-packed-decode-split-policy.md)，先微基准证伪再决定源码修改。
