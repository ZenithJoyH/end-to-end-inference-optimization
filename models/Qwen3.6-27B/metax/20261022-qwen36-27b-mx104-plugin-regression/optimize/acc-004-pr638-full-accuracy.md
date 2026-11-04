# acc-004: PR638 后全量 GPQA / ERQA

当前结果：GPQA159/198通过阈值155/198；ERQA235/400=58.75%，零拒答剔除、无指定阈值。全量精度已完成并独立验收，小时监控已删除，性能仍暂停。

2026-10-26 用户明确要求应用PR后全量精度。仅恢复本次精度工作，性能仍暂停。B独立容器，物理GPU2/3；verify原容器及其他服务保持不动。PR源码SHAf49f4a5b...；当前FG/FGV及用户白名单27作为被测组合，不将分数差全部归因此PR。

GPQA formal-gate：完整198题，原生gpqa_diamond_generative_cot，limit0，阈值155/198=0.7828282828282829，沿用t0/top_p1/seed42/max30000/C32。ERQA用户明确扩展：原生400题/630图，t1/max30000/C8/单次推理/无响应缓存，无指定阈值，仅报告分数及原生拒答与全部400题分母的差异。ERQA参数在模型请求前冻结，保持原生评分，不改runner。

新candidate-03保留当前手工FULL_DECODE_ONLY/maxcapture64/maxlen262144/whitelist27/prefixcacheoff；使用原独立18027endpoint和native profiler，USE_FLAGTUNE0避免maca调参检查，独立编译cache不删除旧产物。先当前实例graph capture、每rank两次真实replay和固定最小回归，再两套全量串行，原生证据验证后报告。新命令先保存commands并登记SHA。当前尚未启动评测，详见state.accuracy_pr638。

预检问题 acc004-collector-editable-root：首个pr638-preflight在组件采集处失败，固定默认FGV site-packages路径已不存在；实际editable导入/opt/FlagGems-vllm/src/flaggems_vllm已只读核实。按精度定位Skill判为measurement-invalid取证问题，非模型数值失败。利用原工具既有--expect-fgv-root参数修正，不修改采集原件/模型/评测契约。保留失败作业，两份已通过GPQA provenance复用；新preflight-v2从组件采集继续，不重启服务，无重复数据集请求。

Graph前置已由主Agent显式审阅：candidate03 instance bde51c9ea4413ef7e8d45e4c97a8006a43255112e7970957719a802398a8e0aa，workers331258/331259、startticks1130952356。四个新trace每份15次重复大模型graph，C1每次1169 kernels、C8每次1217 kernels；mcGraphLaunch与完成GPU kernels/ac2g双端关联核实，每rank保守至少2次真实replay。C1/C8 profile轮9请求全成功，profiler已停止。mtime比内部export晚钟落后217.06..217.71s，保留机械检查并用本次独立empty-before/current SHA/内部epoch/liveworkers/request和stop记录解释，不沿用旧例外。此证据只证明P64/D16 graph，不等于所有shape或完整精度通过。GPQA两份provenance完全相同、datasetrevision与既有198数据一致；ERQA400/630图/源码及离线请求t1/max30000已冻结。

编排问题 acc004-dryrun-mixed-stream：原生sanity预览exit0且model_requests_sent0，但外层合并stderr诊断后从首字符JSON解析失败，未启动12条精度请求。已按measurement-invalid保留原日志，新v2队列仅提取末尾唯一完整原生plan并校验serviceSHA/12请求/zero-sent，复用预览而不重跑。模型和评测器未改，完整GPQA/ERQA尚未发送。

当前持久队列 jobs/pr638-full-accuracy-v2（Host PID2280819）已完成源码/服务连续性核验，进入原生固定sanity的smoke-doc0。尚无完整GPQA/ERQA新分数。两套全量随后串行；GPQA原生issue/check及ERQA400唯一ID/原生拒答分母/数据图片源码后检已编排。小时监控qwen27b-pr638启用，终态停用；性能仍暂停。Skill全bundle三文件SHA已外部保存并登记；原生远端tools-v3另有冻结指纹，不冒充最新本地工具版本。

最新实际进度 2026-10-26 15:39:15 Asia/Shanghai：固定最小回归9/12完成，c8-doc6/7/8仍在执行；尚无本轮完整分数。持久队列健康，GPQA198和ERQA400按已冻结参数后续串行。

2026-10-26 小时复核：15:50:14 CST最小12条全部完成，GPQA10=8/10、算术2、无fatal/warnings，低于既有9/10参考；原v2队列已停止，未发完整198/400。主Agent核验14个原生引用SHA，失败receipt SHA b991ffe44018629a3fd6a4c20aac2120da297a363f9b72ca351c720812178ff2。调用精度定位Skill，记acc004-minimal-gpqa10-score；这是当前组合与旧参考的回答差异，尚不能归因PR，旧参考早于Gems/配置更新。保留失败，既不重试最小以取最好分，也不降低契约。用户明确要求的全量GPQA/ERQA继续作为完整精度诊断；不视作最小通过或性能晋级。新控制 /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/pr638-full-diagnostic.py SHA e06bdf21654e27a18a4c7482fb0fea35d11a8d0939b1376aa803b3f900661b9e 已保存登记，冻结155/198和原ERQA配置不变。
执行前命令审阅：sequence/terminal明确标注minimal未解决，最终控制SHA 17b9b1cb6448505acfb319eda14f3ae2b907f798c57c6c58e84c0f98357cea64（替代上方未执行草稿SHA）。

16:18:52 CST 全量原生GPQA已启动，run53b1ad26174845a2a076e6e7da486512，C32/seed42/t0/top_p1/30k/198契约不变。当前持久作业 /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/jobs/pr638-full-accuracy-diagnostic（Host PID2321693/startticks1131346237）；identity-before确认四套源码内容指纹、同API进程/启动时间和health200，preflight exit0。最小失败作为diagnostic-context保留，不改为通过；原v2停止记录不覆盖。当前尚无全量分数，ERQA400随后串行。控制命令最终SHA17b9b1cb6448505acfb319eda14f3ae2b907f798c57c6c58e84c0f98357cea64。
只读逐题核验：唯一正确性损失为doc7（旧A正确→新B错误）；doc8两版均错误、答案不同。10题全部HTTP200/finish_reason=stop/无health观察且生成均少于30k；不是本轮超时、空输出或截断造成8/10。具体数值/执行原因仍未证实，禁止归因PR。16:18:59 CST已真实进入generate_until，198题/C32/缓存命中0；该0/198仅起始进度，无最终分数。

2026-10-26 17:15 CST 小时验收：GPQA full198已于17:00完成，strict **159/198=0.803030303030303**，达到冻结155/198，正式精度passed；原生issue及check均PASS。gate SHA b37ba36d738a28fdb08cdac3e9a39618ad0df2f7c0e346c955c792cc5260db40；run-record SHA e1d8463967106b4fe7220280c0d8c584d2ce24f292130c698af6ab5823e0e140。原生结果目录为 accuracy/pr638-gpqa-runs/Qwen3.6-27B-PR638-current-stack/53b1ad26174845a2a076e6e7da486512/（远端案例根下）。主Agent额外复核全部8个run-record引用SHA；部署原生iter_sample_records读取396行、198唯一题、双filter各198，strict159、flexible133，与原生聚合一致。samples SHA76e43a877b9ce3491f37e2feecade117a4a894ec8b59671e8ebdf3dda77078c2。辅助只读摘要曾误用str.splitlines导致合法Unicode分隔符被当作换行；改用已有原生迭代器（SHA9799f2df22b1f9bf08331b6ae7e0fdfc345e2dcadc0f81202265f59b38ffcd11）复核通过，没有修改评测、样本或重新生成回答。原生progress末0/0为辅助显示，不能替代聚合和样本结果。

GPQA结束后自动连续性检查确认API330455/startticks1130941540和四套包内容SHA均不变。ERQA已于17:00:36 CST串行启动；17:15:44观察到29个可解析原生items JSON/29唯一文件ID，日志已开始36题，无匹配到traceback/timeout/connectionerror/HTTP500/OOM。这是响应落盘进度，不是最终评分；完整400及原生拒答分母、源码/630图/配置后检尚待完成。没有重复启动，队列无exit.json、仍在erqa-full400。小时跟进继续，完成后停用。小样本8/10差异照实保留，不能据此否定已验证全量score>=threshold，也不能将当前组合得分单独归因PR638。性能继续按用户要求暂停。

2026-10-26 19:07:49 CST 小时检查：同一pr638-full-accuracy-diagnostic作业仍处erqa-full400，未生成exit或最终raw/evaluated/result，仅task_info和260个原生items。260份JSON均可解析、question_id唯一且全部属于冻结400题、answer均非空，日志已开始268题；不计算或报告部分分数。原生日志三条APITimeoutError出自tenacity before_sleep，SDK与native重试记录保留；这是既有runner的内置重试，不视作3题最终失败，也没有人工启动重试。其他Traceback/ConnectionError/HTTP500/OOM模式计数0。19:08:47核验Host控制进程2321693启动时间一致、运行态S；ERQA评测容器及B均running，同API330455启动时间一致且health200。未重启/重复启动/改源码/发额外模型请求。GPQA159/198原生验收结论保持，继续等待ERQA完整400及原生评分、拒答分母和provenance/身份后检；性能仍暂停，小时监控继续ACTIVE。

2026-10-26 19:31:52 CST：同一ERQA原生作业已落盘300/400响应，300唯一question_id全部属于冻结400、answer非空；日志已开始308题，三条native超时警告未增加，其他错误模式仍0。尚无最终raw/evaluated/result/退出回执，不报告部分分数、不另发请求。保持原生队列继续完成及后验核验；GPQA159/198通过、性能暂停，小时跟进仍ACTIVE。

2026-10-26 20:29:06 CST：ERQA398/400份原生响应JSON可解析、question_id唯一且属于冻结400题、answer非空；日志已开始全部400题，剩余ERQA_389和ERQA_393分别自20:17:02/20:17:26开始，尚待原生返回。当前无完整raw/evaluated/result，禁止部分分数冒充最终结果。native超时重试warning累计4条，其他错误模式仍0；20:30:30核验既有controller启动时间及运行态一致、同API实例health200。另只读核对当前native BaseEvaluator.filter_rejected源码：保留字符串回答的既有拒答前缀策略，验收时使用原方法，不替换评分。未加请求/重试/更改超时或源码；GPQA159/198原生pass不变，性能继续暂停，hourly监控ACTIVE，等待最终验收后停用。

原生全量队列已终态：GPQA159/198、ERQA235/400=58.75%、零拒答剔除；400份响应/唯一ID完整。最终result SHA367a026ad20e52ed220a9543141ee45ee2eecd4a1bcc91af9e8a3389fc37673a。主Agent离线复核控制 /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/pr638-review-full-results.py SHA22532f661de1c9632dec29157f504f2a1d8d99eb5fa86d8d828096834e028473 已保存登记：重验所有native引用、原生gate、原生拒答口径、同服务/四包内容以及冻结400题/630图/评测源码/配置的后检；零额外模型请求。保留原最小8/10差异，不恢复性能。

本次用户要求的全量精度已完成，原生队列20:33:22 CST退出0，主Agent离线复核通过：GPQA **159/198（80.3030%）** 达冻结155/198，原生issue/check及最终再次check通过；ERQA **235/400（58.75%）**，400唯一题全部计入评分、原生拒答剔除0，native分母和全部400分母一致。ERQA无用户阈值，只报告得分。四条native超时重试警告保留，最终400份响应均非空，不把重试提示当作四题失败。数据400题、630图、评测源码、配置与原prepared完全一致，当前API启动时间/四包内容及health核验通过；复核零额外推理请求。原最小8/10相对旧9/10的差异仍保留，未定位单点原因，不因此否定达到正式阈值的全量结论，也不将组合得分单独归因PR638。

证据均位于远端案例根：`accuracy/pr638-full-results.json` SHA367a026ad20e52ed220a9543141ee45ee2eecd4a1bcc91af9e8a3389fc37673a；`accuracy/pr638-full-primary-review.json` SHA26af6fa77ea8a1f4a2e171de74590fcabcccc15fa4b9aba3f95fd7d700089dbd；`manifests/pr638-erqa-postcheck.json` SHA53c450d8e8e77160ba55a6bd71c70e25dd6f8abd8347c0b0d64750b699da378d。ERQA raw/evaluated/result三个文件SHA分别为27417f77486a67facd73bbc6f614314ef8cc4ebd5f582d58753e3b7b22e557b1 / bdaa789e11c50485249b8c7d016def4e53a11248cde04c4f740fa63dabd03e9f / 3b8b27235d36862c5b1f598105559413f1f0d4daedb0f61ada1e990927ab3de6。

小时监控qwen27b-pr638已通过app automation_update删除，deleteStatus=deleted。完成的是精度工作；性能回归按用户要求继续暂停，未提交/推送，也未修改原verify或其他服务。当前B服务保留，后续若重启/改源码或配置，按规则重新绑定或评测。

归档检查：本案例记录/实验链接检查无错误。全仓check-project-records存在372条本案例以外的记录/过程产物问题及3条警告，未修改无关案例；全仓检查不标为通过。这不涉及本次已完成的原生精度及独立证据复核。

用户追问启动脚本一致性（2026-10-26只读核验）：当前`/public-flash/jinghao/qwen3.6-27B/start-model-flagos.sh`主机/B内容相同，SHAc9e2d403ffa30846d5ecf32ab924c95ca4f4a15b8e9778115deec616fe1a5d47。与评测candidate03不一致：当前脚本启用blacklist9（exponential_,index_select,mm,max,mm_out,max_dim,linear,sort,sort_stable），白名单export已注释，但脚本也没有unset继承白名单；评测实例明确whitelist27且unset blacklist。不能根据注释推断启动shell中白名单一定不存在，也未把未运行的脚本当作已命中黑名单的服务。

共同显式参数为同模型/GPU2,3/TP2/BF16/8192 batched tokens/64seqs/0.9memory/prefix-off/FULL_DECODE_ONLY捕获64。其余差异：评测127.0.0.1:18027、migration名称、显式maxlen262144、USE_FLAGTUNE0/packed_decode1、独立vLLM/Triton缓存、禁用请求日志与profiler配置（正式评测已停）；当前脚本0.0.0.0:9998、black-list名称，不显式设置maxlen/上述调参与packed/cache，另export MACA_VISIBLE_DEVICES2,3、VLLM_USE_FLAGGEMS1、VLLM_FL_STRICT0。模型text_config最大位置262144，但不将静态默认推断冒充当前脚本运行证据。只读实际进程仍是candidate03的18027/白名单27，当前目标端口查询未见9998监听。

结论边界澄清：159/198和235/400仅覆盖已测白名单组合，不代表当前黑名单9项脚本已完整验收；原gate未被改写或否定。当前文件不能证明评测时其内容，未做时间归因。没有执行用户脚本或启动新精度/性能，定时任务仍已删除。
