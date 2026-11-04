# acc-008: User new service8010 C64 full GPQA and ERQA

acc-008 全量精度已完成并独立验收：当前8010用户服务、GPQA/ERQA均64并发、模型默认t1/p.95/k20、无额外request seed、输出预算30000、prefix-on。GPQA **162/198（81.82%）** 达155/198阈值；ERQA **244/400（61.00%）**，400完整计分、零拒答剔除，无指定ERQA阈值。原生队列于2026-10-27 19:59:53 CST完成，20:20独立复核通过；59次原生超时重试保留，最终400题全部返回。半小时监控qwen27b-8010-c64已删除；用户服务未停止/重启/修改，性能仍暂停。

User requests fullGPQA/ERQA with64 concurrency on their newly launched service. Capability e2e/accuracy, explicit mode formal-gate; skill bundle SHA1ed06a57f1f6e1ef39fb7fd872f579122b098a18f0255ade0a1160d6432c2b66.

Observed current service: mx-104, retainedB containerqwen36-27b-regression-b-20261022, API626708/startticks1140143723, actualport8010 (not historical9998), modelqwen36-27b-black-list, /data/Qwen3.6-27B/, TP2/BF16/physicalGPU2,3. Ready health/models200. Plugin release/0.2@1bc0c77, localyaml retained. Blacklist9/prefix caching ON and user legacy env variable present are preserved. User stdout is service.log. Startup confirms11/11FULL decode graph captures, maxcapture64; actual new replay not trace-attested, no performance promotion. No service restart/change/profiler/source optimization authorized or performed.

Freeze before requests: GPQA198 unique originaltaskgpqa_diamond_generative_cot (limit0), strict metric threshold155/198; ERQA400 originalnative tasks/evaluator, no user threshold, report native score/denominator and all400 score with rejection review. SerialGPQA thenERQA; eachC64. Sampling same previous user-default protocol and current generation config/log:t1/top_p.95/top_k20/no extra requestseed. Explicit output budget30000 is separate from sampling defaults. GPQA CPUper-job adapter only removes native fixedseed, native sourceguard/payload proof required; other model native seed unchanged. No model/data/scoring/installed client edits. New response cache, no prior response reuse.

New CPU evaluators qwen36-27b-acc008-gpqa-20261027 (required flageval-llmeval:v1 image1396e5d...) andqwen36-27b-acc008-erqa-20261027 (frozennative image997570...), CPU4/mem12G/noGPU/hostnetwork/casebind only. They replace previously user-deleted evaluators for this newly authorized run. Original required runner andtools-v3 reused, no custom evaluator/scorer. Image/task/data/source/payload/manifest preflight before firstquestion.

Monitor qwen27b-8010-c64 ACTIVE every30minutes, preserves prior user cadence. Terminal complete/cancel/needs-user stops monitor. First automation attempts withVEVENT wrappers rejected as no future runs; bare nativeRRULE succeeded, no duplicate created.

Historical initial preparation: no new model requests at that time, historicalGPQA163/198 ERQA239/400 are not this run. If validGPQA below155, preserve/no gate/diagnosis and still complete independently requestedERQA on unchanged healthy service; no optimization or threshold changes.

Evidence at /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression; jobsacc008-bootstrap/acc008-preparation/acc008-full-accuracy; accuracyacc008-*; newserviceuser-c64-02. Never overwrite/relaunch if these exist.

Commands registered before execution:

- `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc008-bootstrap.py` SHA256 `083656f9b760406eb231c5ddb2b8fb5161cbedd23e20a220b8eb285b003e4ebd`
- `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc008-prepare.py` SHA256 `0795fbf979a0b1f8e5e453da814e0efad1fa25cd1124bab8ab9257bfa87d9261`
- `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc008-gather-user-service.py` SHA256 `9d78160f04903e561f9a300fdc22a3005f97980b110007b5e0a47304421bff26`
- `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc008-full-suite.py` SHA256 `a37c41845ce1ab9a6943b5afc41e4f05858306d96fdcd6eb5f717003c9450109`
- `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc008-verify-gpqa.py` SHA256 `106a35796cd08d8257a6a32ea703d7b2da42e6a66a62b44d45ac52fdaed926f5`
- `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc008-review-full-results.py` SHA256 `50ff91bcac22373e6a0c1cce0ea3fe4556d080917ac5173db5a2b8cbe4c74019`
- `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc008-client-adapter/sitecustomize.py` SHA256 `1ecf64552c21a80c5ba2f54d6f734ab3366c362f2bb69a4243c254332b5e1158`

All controller source syntax checked. Adapted previous external orchestration only: unique namespace/evaluators/newPID/startticks/port8010/log path/currentscript reference; no runner/scorer changes.

Pre-execution review correction: the initial copied acc008-review-full-results.py retained historical final-result constants, caught by primary review before any execution or result. It is not an executable acceptance method for this run and must NOT be used. Superseding independent verifier `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc008-review-full-results-v2.py` SHA256 `e5e2e9a89bc4d06c191e349be969366de204ed45a9084505fc77a83fa106b213` derives actual score from native full-run verification/receipt references, preserves rejection denominator and reports no frozen expected score. Only threshold155/198 is fixed; no known final score is assumed. Old copied controller remains external evidence, never executed. New source syntax passed.

Primary pre-request review PASS: prep exit0 SHA`666ac32a582103530068d8bae041424d42d6c9c7983cf0de7a935a7cace7728a`; serviceuser-c64-02 SHAe01261a9eb0bd7c2639f4744389be27d7b15b31eb88fbd90fe82170cd4699b76, instance19f061a806dea94cf3298f69bd4ed88f8411d4d0c253c4bd04dfbf8c39859d50, observedAPI626708/startticks1140143723/8010.8 frozen input refs rehashed, GPQA doubleprovenance identical, full198/strict/155threshold andC64/defaultpayload/no seed/30k confirmed. ERQA400unique/630images/datasetSHA/source/config/C64 and offline nativepayload confirmed; preflightpassed with no model request. Prefix-on and all actual user env bound (legacycontiguousenv1 retained).

Launch script `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc008-launch.sh` SHA256 `2186498bfc2a7c5a63ad089fdcb592305a965fc4bfd4cb054822934eafdfb955`; execute once after reviewed preparation; existing-job guard prevents duplicate. Queue GPQA198 then nativeERQA400; monitorqwen27b-8010-c64 ACTIVE30min.

## Started actual native evaluation

acc-008: new user8010 service full accuracy RUNNING. GPQA198 entered native generate_until at2026-10-27 16:58:15 CST, C64/cache0/newrun86f261cd7fcd48f8a3bed83ca59e416c; native preflight exit0, durable controller5777/startticks1140221643. ERQA400/C64 queued serially afterGPQA. Actual model-defaultt1/p.95/k20/no request seed/outputbudget30000/prefix-on preserved; no current final score. Monitorqwen27b-8010-c64 ACTIVE30min. No service/source changes or performance run.

Native logs show all198 contexts built; generate_until response cache0,198remaining, API semaphore64/timeout7200. Request payload proof max_completion30000 and exactdefault distribution; task/harness seed42 does not enter model request seed. Context length2047 log is auxiliary API-client limit, tokenizer requests disabled and no truncation check applied. No new run-record/results yet.

Followup: read existing queue, then complete native verify/issue/check for GPQA and native ERQA full/rejection/source/data postchecks; use only superseding dynamic independent review commands/acc008-review-full-results-v2.py SHAe5e2e9a89bc4d06c191e349be969366de204ed45a9084505fc77a83fa106b213. Never run deprecated copied reviewv1.

2026-10-27 17:24 CST 半小时检查：既有GPQA任务仍在运行，最新原生辅助请求进度170/198；相邻API进度行为169/198，属持续返回中的异步观察。未生成本轮最终results/run-record/gate，不报告部分分数。ERQA400/C64仍排队等待GPQA完成。Host控制进程5777/startticks1140221643、API626708/startticks1140143723均一致，四包源码SHA及模型默认配置连续性通过，8010 health200，11个冻结引用SHA未变。原生日志匹配Traceback/APIError/ConnectionError/timeout/HTTP500/OOM均0。继续当前串行队列，未重复启动或发额外推理，未改服务/采样/源码/超时，性能保持暂停；监控qwen27b-8010-c64 ACTIVE30min。

acc-008 2026-10-27T17:55 CST：本轮GPQA完整198题得分162/198（81.82%）达到冻结155/198，原生full/verify/issue/check与主Agent独立复核通过，396行/198唯一题，8个run-record引用SHA均核验。run-record SHA89ea77e920b37bdce7d1f4c2c80130aa28733cf2464b5af4ad3ec2d22f1b0e39；gate SHAe80544c4fcc2d32e2b8c1b1ba804b79803865f76a3574389b074369fd8278b7c；verified-result SHA2e6d012b91a55c1386a7d679b291f5bd41c7215b44588bf49358df4c791313db。GPQA在17:38:55结束，ERQA400/C64于17:39:15串行开始，当前144条原生items均唯一、属于冻结400题且answer非空，无partialJSON或最终分数。17:53原生日志APITimeoutError/Traceback/ConnectionError/HTTP500/OOM匹配均0。当前同controller/API启动时间、四包源码、默认采样、health200和11冻结引用均通过；复核零额外推理，没有重跑GPQA、修改服务或恢复性能。监控qwen27b-8010-c64 ACTIVE30min，继续既有ERQA任务。

2026-10-27 19:46 CST实际检查：ERQA398/400原生items均可解析、唯一、属于冻结题集且answer非空；ERQA_309/ERQA_367尚未落盘，完整raw/evaluated/result与suite最终exit尚未生成，不能报告部分分数。原生APITimeoutError before_sleep重试提示累计59次（最后日志19:40:08），其余Traceback/ConnectionError/HTTP500/OOM匹配0。8010聚合2running/0waiting，仅作为服务聚合观察，不冒充逐题/worker映射。既有controller/API启动时间、四套源码、模型默认配置与health200、11冻结引用SHA核验均通过。继续原生任务；没有手动重试、改超时/参数/源码或恢复性能。已验收GPQA162/198（81.82%）保持；monitor qwen27b-8010-c64 ACTIVE30min。

2026-10-27 19:49 CST相邻心跳只读检查：ERQA仍398/400，待309/367，原生重试累计59，suite最终exit/results尚无。与刚才19:46实际检查及通知一致；距上一通知不足3分钟，本次不重复通知，保留30分钟跟进，不重发题或变更任何配置。

2026-10-27 20:19 CST：原生队列exit0/completed_full_scores_verified，full-result SHA2c241220970fcea86f10150b41508e8027a38a1f70ac683fe950897881aa8f51。GPQA162/198、ERQA244/400=61.00%，400全部计分、无拒答剔除；400items均唯一非空、59次原生超时重试保留，无其他匹配错误。先执行已登记SHAe5e2e9a89bc4d06c191e349be969366de204ed45a9084505fc77a83fa106b213的commands/acc008-review-full-results-v2.py独立零推理复验，不能运行deprecated v1；成功后归档及删除监控。

## Final verified result

| Dataset | Correct / complete | Score | Verdict |
|---|---:|---:|---|
| GPQA | 162/198 | 81.81818181818182% | Native and independent verification PASS, threshold155/198 |
| ERQA | 244/400 | 61.00% | Native score only;400 scored,0 excluded,no user threshold |

Final raw/evaluated/results, original-native rejection handling and all400 unique IDs agree. Native APITimeoutError retry warnings59 do not equal failed questions: all400 returned nonempty answers. Independent validation rechecks originalGPQA verifier and nativegate, frozen input refs, actual score/396rows/198unique, currentAPI626708/startticks1140143723, four package source hashes/defaultsampling config andhealth200. ERQA400questions/630images, native sources/config and payload proof are unchanged. Review sent zero additional model requests. No inference/performance test restart, parameter/source change, commit or push. Actual graph capture logged11/11; fresh perrank replay not trace-attested, no formal performance acceptance claim.

Final `accuracy/acc008-full-results.json` SHA256 `2c241220970fcea86f10150b41508e8027a38a1f70ac683fe950897881aa8f51`; independent `accuracy/acc008-full-primary-review.json` SHA256 `3904409cff93bd0d556fbfa8422b7ec382cde036362e9081500d39d7bdd9776e`; independent `manifests/acc008-erqa-primary-postcheck.json` SHA256 `bb72ff374a1f5b90a3af4207afb2fcb2ab4d69cef9ff5925637e08bbc6c24385`; native postcheck05a437e497617a711cd5e40346d4f89a5b0a91c49898602572ae90c2a4c1f677; job exitSHAee5993481fd903f6455e91ba351362796cc31eef0c22de7c3ec9085cb4f2c380. All paths relative to frozen remote case root.

ERQA raw/evaluated/result SHA respectively48ca1f3c4a450e7ae6d18eeca573739ce4a0eda92155b2c77a1463d9a47e047e /3157a16e2dcb42f71827dba14ea93535ab5a3b613f127820bb772a943bc5acc0 /79bf6ac07a121340d04a34bf38d970eea424472d6a7f2275ff1077220fcb4638. Original answers/logs/datasets remain remote. GPQA record/gate hashes are recorded above; no old163/239 orPR638 white-list scores are substituted. Stochastic default sampling and service configuration differ across historicalruns; no single-change accuracy/performance attribution.

Monitor cleanup: automation_update(mode=delete,id=qwen27b-8010-c64) returned deleteStatus=deleted. Keep user service and evaluator containers intact, no further requests; performance remains paused, await user direction. Current user-requested full precision scope is complete; project-wide performance acceptance remains incomplete.
