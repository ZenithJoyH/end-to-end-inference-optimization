# acc-001：opt12 / C64 / 模型默认采样完整精度

- 状态：已完成；GPQA129/198=65.1515通过64，ERQA168/398=42.21通过40，2条原生超时拒答保留且全部400计错42.00也通过40。CPU恢复采集问题已解决，无重跑，原用户服务保留。
- 方法：本地 inference-accuracy-evaluation / formal-gate，覆盖当前用户启动的 PR638 + decode split1 + gems-opt/MoE 组合。
- 用户授权：新模型服务，GPQA与ERQA均64并发，采样用模型默认；每半小时报告进度。沿用GPQA64分、ERQA40分阈值，各完整一次，按顺序执行，合法低GPQA仍完成ERQA。
- 实例范围：mx-104，现有独立优化容器 `qwen3vl-pr943-split1-mx104-20261023`，用户服务 `qwen3vl-opt12`/9999/TP2/CUDA0,1/prefixON。设备/服务与旧case不同，新建当前案例，不拼接旧分数或gate。

## 优化方向与瓶颈依据

这是用户指定的精度评测，不是新性能优化。保持运行服务，不改源码/安装/参数，不重启模型；无新性能测量。上一轮PR638只完成CPU/mock，本轮不伪称已有GPU数值/graph回归。

## 配置与适用边界

模型 `/data/models/Qwen3-VL-30B-A3B-Instruct`，generation_config及本实例启动日志均表明 temperature0.7、top_p0.8、top_k20、repetition_penalty1.0。GPQA客户端原生factory会主动填temperature和seed1234，单纯不传gen_kwargs会变成客户端贪心，不能冒充模型默认。

保留官方原始runner与原ERQA评分源码，通过仅监听loopback19964的独立HTTP传输适配器转发至9999：移除客户端 temperature/top_p/top_k/min_p/typical_p/repetition_penalty/presence_penalty/frequency_penalty/seed/do_sample，让服务原生解析默认；原messages/图片/任务stop及18000输出上限保留，非stream，响应字节原样返回。只接受model opt12，最多64个并行转发，按阶段记录请求SHA/去除字段/上游字段名/状态/usage，不修改推理栈或评测器。独立CPU测试及实际两个native factory inert-client验证通过后才能发请求。GPQA task seed42只控制题目构造，不传至模型采样seed；新契约与历史固定seed/C32不直接作单变量对照。

GPQA完整gpqa_diamond_generative_cot，198 unique/strict-match阈值64，通过official v1 evaluator中的项目formal_accuracy.py包装SHA核验原始llmrun.py。独立UUID响应缓存。ERQA原生flagevalmm400题630图、C64、response cache OFF；核验原生filter_rejected分母并补充全部400计错口径。各一次，不挑分、不因GPQA低分跳过ERQA。

## 正确性与路径命中

执行前采集当前API PID/startticks、argv/环境白名单、图捕获启动日志、模型/tokenizer manifest、四仓库内容SHA/revision/dirty和实际默认安装路径；两次GPQA provenance一致且题目内容与旧冻结198题一致；ERQA400/630图/评分源码重验。原始权重manifest不是完整分片字节SHA，不声称全字节一致。

运行前普通smoke/C8沿模型默认采样；服务已启用FULL_AND_PIECEWISE并有原生capture日志。当前正常用户服务无侵入观测器，实际graph replay次数没有直接计数证据，不编造、不中断模型安装profile。保留这一验证范围限制；得分仅在当前源/实例/请求适配证据有效时报告，不把旧gate转给本实例。

## 性能效果

未测量、不评价吞吐；GPQA/ERQA耗时不作性能收益。

## 决定、风险与回退

保持用户服务与当前cache状态，不清cache、不重启、不恢复旧服务。评测端与loopback适配器由单控制器启动/结束，finally只结束自己的适配器，不停止模型。单次低分冻结证据并记录精度定位，不叠加优化、不自动重跑。如源或服务身份改变，标记证据无效，不复写旧SHA或门禁。

## 外部证据

远端 `/public-flash/jinghao/qwen3-VL/20261026-qwen3vl-opt12-c64-default-accuracy`；主机目录归档commands/configs/manifests/logs/results，原始样本留远端。

- `commands/prepare_accuracy.py` SHA `3ee1ea6d41e7f0e6f4133cc97bcad62e0ac2b90d2a8cb66fac0c4f3b19e4ac16`。
- `commands/default_sampling_proxy.py` SHA `90b1e89fcee8d9103c2a6ac4dc39f11d26a3202038210b8c3312ae04202d5f67`。
- `commands/proxy_cpu_test.py` SHA `eb0c57e57c50dc1c70e01c5ed428803066586ac9b4fed4ddb9ec8dfafe070f76`。
- `commands/collect_current.py` SHA `49a754acc46eac8a644c2a548ea561e0c7691fd2b997bbeb8e076233eb3897dd`。
- 原始正式runner SHA `82cf6e8304cb6f9eb8ca48fe4055f6bbb2054a7b6a90d56de3d6b7a08e90c61e`；Skill完整bundle冻结在configs/skill-bundle.json。
- 监控 `qwen3-vl-opt12-c64`，30分钟，用户明确要求周期进度；终态后停用。

准备v1在CPU factory测试处发现现有GPQA evaluator只bind旧release案例，无法导入新任务路径；0生成请求、0服务变更，旧失败/日志保留。v2 `commands/prepare_accuracy_v2.py` SHA `51452c05b015d8b36c08876c7208b202a754b91b2155c7913defdc3e9a0da7a7` 修正为将新案例只读执行资产复制到两个现有空闲evaluator的私有同绝对路径，不改其挂载或评测源码；输出后通过docker cp校验回收至Host同路径，CPU provenance回收后才冻结contract。旧准备产物如存在必须内容相同，拒绝覆盖冲突；新日志用v2文件名。后续正式运行前再次同步冻结配置和service manifest，原生结果仅保留一轮，不重跑模型。

v2在任何CPU factory/模型请求前被完整Docker inspect的易变ExecIDs字段比较挡住，非服务或精度失败。v3保存独立fresh inspect，只比较Id/Image/Config/HostConfig/Mounts/Created这些稳定身份；不覆盖旧inspect。evaluator已有私有任务目录须核验适配器SHA且无native GPQA结果后才同步准备资产，无推理源码/挂载改变。`prepare_accuracy_v3.py` SHA `f45c58adfae296342d23db32b78db62102e2f7cc725914cd583d05063374a662`；唯一正式控制器 `accuracy_controller.py` SHA `56a005a857f663987ed36a582bf56dc78179dae27e2ca0b6cd3dd88d0c54d67c`。新的执行契约在两次CPU provenance等全部检查通过后冻结全部commands SHA；启动采用排他manifests/controller.json，不重复启动。原生结果随后从evaluator私有目录回收到Host同绝对路径，验证全部SHA/原生来源；每阶段请求审计单独冻结，避免引用会继续增长的跨阶段日志SHA。

v3仍在0生成请求时识别Docker Mounts列表顺序不同，现场差异仅`/data`与`/public-flash`返回次序，所有Source/Destination/Mode/RW/Propagation逐项相同。最终v4按Destination排序后比较完整挂载对象，其他稳定身份仍严格相等；不是放宽挂载门禁。`prepare_accuracy_v4.py` SHA `89e007b27cafff9931fe90b244931d5f0ab068a1aab337ffcfe122318f040d3e`；最终待启动唯一控制器改为 `accuracy_controller_v4.py` SHA `d2f24a65e4081b760738f2a8ffa6eef73df9e031ea7228af8739bcc5b98f412a`，排他启动 `start_controller_v4.py` SHA `f05b0259aecd26eb37964fc34bf5c593fb9b8c5d328f0020e9cec7b36f2ee902`。前述controller从未运行，旧CPU准备失败不作模型失败、不占正式评测轮次；不执行旧preparer/controller。

v4的真实GPQA/ERQA native factory CPU测试和规范化身份检查已通过；末尾provenance发现新fresh inspect在Host生成后尚未同步到evaluator，0生成请求。只补未完成步骤的 `finish_prepare.py` SHA `1baba7afbf76e55cdbede11899447e97d59d92e3afff1b176a238d0d0f7a412d` 先同步冻结的configs/manifests/tool/commands，再采集两份新provenance并回收Host，拒绝覆盖已有provenance。不重跑已通过的原生factory测试、不发模型请求、不改任何推理源码。此前CPU准备工具incident全部保留，正式控制器仍从未启动。

上述准备已完成：prepared SHA `79e081b54786d5bf5b234c29701ac5ba00cf36ee99a1c8ee0600b0b3210d0ed6`，execution-contract SHA `8b99955a20effc691364443868817061149e273a2e621a5f6edc268c26754f18`。唯一controller2924802/startticks1133720501，源服务1188871/startticks1133556479，14:54:25UTC adapter-ready，14:54:41普通smoke/C8/source通过，14:54:49正式GPQA开始。14:56原生进度53/198，无最终分数，ERQA尚未开始。原始runner偶发SCORE日志matched0不当精度0分。模型未重启、prefixON保留。

GPQA/ERQA运行时native输出位于两个evaluator私有的同绝对路径，Host gpqa/erqa目录在单数据集结束前可能为空。每半小时读取Host events/native stdout与request-audit按stage/unique messageSHA计数，必要时docker exec读私有native进度；不要把空Host目录误当未启动。切勿tail完整长响应，仅读进度、汇总和状态。单次正式低分继续ERQA，完成后按原生分数/唯一题目/源码前后和实际upstream采样字段审计验证，不自动重跑。

2026-10-26 23:05（Asia/Shanghai）半小时跟进：唯一controller2924802/startticks1133720501仍活跃，events停留正常GPQA阶段，未出现终态失败。request-audit按stage与unique messages_sha256核验GPQA198题均已发出，166题HTTP200响应已完成，0proxy error事件；这是响应进度，不是已完成判分或精度分数。ERQA尚未开始，按原顺序待GPQA结束后运行，未启动重复控制器或干预服务。按用户要求发送周期进度通知，监控继续。

2026-10-26 23:35（Asia/Shanghai）半小时跟进：GPQA已23:27:28完整完成，原生strict-match **129/198=65.151515分>=64，通过**，198unique/perdocsum/原生分数和来源、source前后均由控制器核验；另独立调用原acceptance.check_gate复验通过。采样审计198条请求/198条响应/198unique，实际upstream无采样字段或seed覆盖。结果SHA73665c96419ca54c50f80e84aaba863735fe8e748854eb8609493cd00c82eca7；sampling-audit SHAd661c7ed5b2952521d39ad49346d331bbd1fb9090353334dbf4f4281b96604a3；gate SHA868159a853355d76cbcd515c2eff94d856bbd48da1f2e1b1735a943438052e72。gate只绑定本轮实际服务与传输，不能转旧case/未来重启；无性能结论，graph直接replay计数的范围限制保留。

ERQA已同一23:27:28按原计划自动启动C64完整400，当前347unique已发、284uniqueHTTP200完成、0proxyerror，无最终分数。控制器仍同PID/ticks活跃，无重复启动、无重跑，用户模型未停。按用户要求通知GPQA关键通过及ERQA进度，监控继续；ERQA终态及用户服务final审计通过后才停用。

2026-10-27 00:05（Asia/Shanghai）半小时跟进：GPQA分数不变；ERQA仍运行，原生evaluator私有`erqa/native-output/erqa/items`已386份结果，proxy386个uniqueHTTP200完成，399个unique messagepayload已发。部分长请求触发原客户端APITimeoutError并走未修改的原生重试；代理42条BrokenPipeError均在取得upstream HTTP200后回写已断开的客户端时出现，不是模型服务崩溃证明。模型modelsHTTP200为opt12，唯一控制器同PID/ticks活跃。尚无ERQA400原生聚合/最终分数，未更改并发、超时、采样或模型，不补跑。

最终需以400唯一question_id/原生结果/原生filter_rejected规则计分；proxy unique messageSHA不等于question_id，重试/相同payload/原生拒答也不能当额外精度门槛。当前控制器transport audit按400unique/HTTP200作了较强假设，若仅此采集检查失败应保留失败并以已完成原生结果CPU复核与独立审计解决，不重发模型请求、修改原分数、丢弃拒答或提高gate要求。先等待现有原生评测自然终态，禁止为修复采集器改动在跑的冻结控制器/请求链路。

2026-10-27 00:35（Asia/Shanghai）半小时跟进：ERQA原生items已394/400，较上次新增8份，未出现erqa_result聚合或根终态；proxy记录393uniqueHTTP200payload、399uniquepayloadstarted及70条超时/客户端断开关联错误。原生题目文件数与消息payload去重数不同，进一步说明不能拿payloadSHA唯一数强制替代question_id完整性。6个原生结果尚未落盘，继续原客户端重试和既有控制器，未改变参数或补跑。controller仍同PID/ticks，模型modelsHTTP200返回opt12，GPQA65.1515通过不变。按用户要求发送周期进度，监控继续。

2026-10-27 01:05（Asia/Shanghai）半小时跟进：ERQA原生items仍394/400，过去30分钟无新增，剩余6题仍在原客户端重试；proxy error累计110事件（不是110个失败题），唯一payload已发399、成功393，无原生聚合或终态。只读核对原BaseApiModel仍`stop_after_attempt(5)`且num_infers1仅调用一次_single_infer（其内SDK可自行重试），未修改任何重试/timeout。服务modelsHTTP200，metrics19running/0waiting、KV占用约0.3342，说明仍有在途服务请求，不等于服务已挂；不把HTTP健康当精度通过。唯一controller同PID/ticks活跃，继续原冻结流程，向用户明确剩余6题超时且进度停滞，不增加调用或重跑。

2026-10-27 01:35（Asia/Shanghai）半小时跟进：ERQA原生items396/400，较上次新增2份，仍只有task_info.json，无原生聚合分数或控制器终态。proxy395uniqueHTTP200、399uniquepayloadstarted、130error事件；不当失败题数。唯一控制器同PID/ticks活跃，modelsHTTP200仍opt12。剩余4题沿原生重试等待，没有调整并发/采样/超时或重复启动，继续监控并按用户要求通知进度。

2026-10-27 02:05（Asia/Shanghai）发现原生ERQA已01:59:42以rc0完成，private evaluator保存完整400raw/evaluated和native result42.21、2条原生超时拒答（ERQA_105/ERQA_50，RetryError/APITimeoutError）。原控制器在native结束后先等待代理drain300秒，被客户端重试留下的在途HTTP请求触发assert，02:04:42退出，尚未harvest/计分复核；这与native score失败不同，原failure SHA2824c42a1142432824b08eed46faab23da64f776757d841a8e14fdbcf702dfe9保留。finally已只停自有adapter并02:04:43验证原用户模型source不变/models200，final SHA0486db5864e2dc475908c37225ad3b471c4b575e1f64d18977e8f4783c79a29f。

调用本地inference-accuracy-diagnosis，issue `accdiag-opt12-c64-erqa-collector-drain`，分类measurement-invalid/collector lifecycle；暂不把初步分数当最终验证。本地Skill缺machine interface，显式选择检查返回incomplete，已完整手动读取方法并冻结全部内容（入口SH Adae96b45b710eece923608299f41d09bc893883afedbab527af32f7b95183e54；内容bundle文件SHA640f928fecc687f0e05c645f9e066d9db22bbb6800ea4b4b6db0f9984c6a92a0），不伪称机器模式选择成功。

执行前归档CPU-only `commands/final_accuracy_audit.py` SHA24ad8ba482d950b9c0702503e3e38b8591839ab1d899fbe8d62699d63bf87237：只在原controller/proxy已退出且native rc0后，复用冻结原controller的ERQA原生校验代码（AST提取，不执行控制器），核验400unique/source/630图/filter_rejected/perdoc分数，逐文件SHA回收private原始输出，核验所有实际转发attempt无采样/seed覆盖（不要求400unique消息体/全HTTP成功），独立复核GPQA gate及原用户模型PID/source/defaults/models200。只产生恢复与后验回执，0新生成请求，原失败/原分数/原生拒答全部保留，不重跑、改阈值/分母或修改服务。

2026-10-27 02:11:39（Asia/Shanghai）最终CPU后验全部通过：原生raw/evaluated各400唯一question_id，630图/数据/原评分源码不变，原BaseEvaluator.filter_rejected确认ERQA_105/ERQA_50为APITimeoutError拒答；398条正常计分168正确，原生accuracy42.21>=40，全部400条将2超时计错168/400=42.00亦通过。403个原生文件从evaluator私有目录回收Host同绝对路径，逐文件SHA完全一致，没有补发任何生成请求。实际task_info为num_workers64/num_infers1/cacheOFF/temperatureNone/max_tokens18000/opt12/冻结19964 endpoint。全部544个ERQA转发attempt均无显式采样字段和seed；399unique消息体、398份成功回复、142次BrokenPipe/status200及4个未完成attempt是HTTP健康/重试观测，不等于400原生题目覆盖或额外精度门槛。

同时原acceptance.check_gate复核GPQA129/198=65.1515>=64，原模型PID1188871/startticks1133556479、四仓库/模型/tokenizer/defaults/argv/env白名单均精确等于run前与finally快照，prefixON、modelsHTTP200。原controller/proxy都已退出，自有adapter已关闭；用户模型未重启，0恢复生成请求。采集incident根因为native退出后的drain断言放在harvest之前，已CPU恢复为resolved；不是模型数值或正式分数失败。旧failure2824c42a仍原样保存。

| 产物（相对远端case根） | SHA256 |
|---|---|
| results/erqa-completed.json | ef1e508cf35e203ecb932d676147726077426c48abf30e453d55a8165ba06eb8 |
| results/erqa-sampling-audit-recovered.json | 997e55cefa4d451f0a875cd244bcadbb6b5ca6b6177c084ddc083e8c39c93c2f |
| manifests/erqa-native-recovered-files.json | ae19beb309995bbc3483d73f63d3324310fa17dd20e6f418a5dc40bf4ece6d03 |
| results/collector-recovery.json | 4c722b600409cc5231248a8c28522b746b2f3addbc139d5bece246643538acf0 |
| manifests/source-after-recovered-audit.json | 5a080c303819a949a6097c82274910266424f71c318f96f9ad1c7a2c0978d853 |
| results/completed-recovered.json | 5e337ce4156964f4956a969fa6b92be0a34de08fb38b6f31e7a44f98777a6504 |

最终决定为本轮两数据集完整精度通过，无待跑评测或自动重跑。GPQA gate绑定当时19964传输测量，adapter现在已停止，不转给直接9999服务或未来重启；source/设备/采样/C64等与旧C32不同，不能把分数差直接归因PR638，也没有本轮端到端性能结果。graph只有startup capture和正常图配置smoke/C8，未安装直接replay计数，范围限制不改写。监控在两项终态与用户服务核验后删除。

终态监控`qwen3-vl-opt12-c64`删除已由automation工具确认deleteStatus=deleted。本地optimize/acceptance双视图与平台摘要更新，代码未提交推送，用户服务未停止/重启。
