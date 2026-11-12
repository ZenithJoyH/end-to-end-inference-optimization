# 20261104-qwen36-mx59-main-config-001 / acceptance

<!-- e2e:summary:start -->

- 案例：20261104-qwen36-mx59-main-config-001
- 当前状态：accuracy-only GPQA 通过；最新默认采样单轮ERQA400已独立核验完成，236/400（59.00%），无组合E2E验收。
- 当前服务：qwen36-35b-opt6，GPU4/5/TP2/0.9/prefix-on，源码/参数未改。
- GPQA：本次冻结规则168/198（84.8485%）；同批回答历史strict离线160/198（80.8081%），均超过75%。Gate仅绑定本次规则/实例。
- ERQA最新：默认temperature1/top_p.95/top_k20、thinkingTrue/max65536/C64，单轮400次HTTP全部200，236正确（59.00%），0请求失败/超时；3条长度截断无最终答案，按原规则计错。旧贪心三阶段210/400（52.50%）及原始单轮未完成证据分别保留。
- 下一步：保留各阶段原始证据；终态监控已删除。无自动服务修复、重新评测或性能测试。

<!-- e2e:summary:end -->


2026-11-05 current opt6 accuracy-only update: GPQA full198/396 independently verified; current pre-frozen native strict168/198 (84.8485%) >=75%. Identical raw answers under historical strict regex score160/198 (80.8081%); eight extraction-rule flips. Gate7997b357 binds current service/current frozen evaluator only, never historical regex or a future service restart. ERQA400 C64/thinking/max65536 still pending via existing pipeline004. No four-scenario E2E performance acceptance or automatic benchmark. Evidence: current experiment in optimize, ROOT/gpqa/independent-verification-004/verification.json SHA9139f804217cb7afd897b5bcef073c128df0f3cd946aa45d64d5a035a7cf50bc.

2026-11-05T10:22Z followup: ERQA official400/thinking65536/C64 has actually started; snapshot156completed/0failed, no full400 score yet. Mainpipeline004 still owns independent verification, monitor retained. GPQA results above unchanged; no performance/E2E final acceptance.

Final terminal-review001 SHAeb23ddad39d8602ebe13519800dcd3365d3176b64cd5c9dd0525ee3ddb0a230d and partial-independent001 SHA1dcf537b07debf5204d0b8f75a729968e8d170a02ebae1e95e94d304c4b4a73f verified. ERPQA400 full入口未执行；原客户端及safetyobserver已原生退出、未干预，当前队列观察0running/0waiting。保留已完成GPQA gate，ERQA无gate/全量分数，未宣布OOM原因或容量边界。

User-authorized seven-only supplement completed: doc393..399 allreturned,4correct/7; old29timeouts not retried. Combined205correct over371successful responses=55.2561%, or diagnostic205/400=51.25% when29timeouts countzero. This is an explicitly labeled two-phase aggregate, not a new native full400 accuracy/gate. Originalpartial andGPQAgate preserved. See optimize/erqa-unsubmitted7-20261105-001.md and SUB/summary.json SHA3c3f8d304f707d894bb54d66fe06f39358fd849330a3770713a018ce3c07f3de.

Final defaultsampling ERQA400 single-run:236/400=59.00%,400uniqueHTTP200,0requestfailures/timeouts,64clientpeak,397stop+3length65536/no-final countedwrong. Same currentservice/source/launch unchanged through terminalfresh. Versus oldgreedy three-phase210/40052.5%, observed+26correct/+6.5pp and length50->3; not a replicated causal or performance claim. Independent f54bdd59d7d9d54fd75ffe21459a4dc7fb9a2820df0fad86338cad24253a7335; terminalreview f6ef5f89dd04e584a038f33d7ecbed2a0034594664ff3d08e9760615d2ba3692; summary17cce7f189723c888960d4ecfe8aa7d92e40215e2fc98b0abfa48c618071666b. Monitor qwen35-mx59-erqa-default-c64 deleted after terminal audit; no further automatic traffic. See [current experiment](../optimize/erqa-default-sampling-c64-20261106-001.md).
