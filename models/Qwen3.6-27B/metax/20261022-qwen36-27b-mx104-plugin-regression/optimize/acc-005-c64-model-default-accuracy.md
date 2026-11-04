# acc-005 新服务C64模型默认采样全量精度

当前结果：GPQA163/198（82.32%）达155/198阈值；ERQA239/400（59.75%），全400计分、零剔除，无指定ERQA阈值。两套C64/模型默认采样的完整原生产物与独立后检已核验，30分钟监控已删除，用户服务保留，性能仍暂停。

用户明确请求：使用其已新启动的服务，GPQA198和ERQA400均并发64、模型默认采样，每30分钟报告；仅精度，性能仍暂停。

只读确认B新API499980/startticks1133379219，端口9998，served qwen36-27b-black-list，GPU2/3、TP2/BF16、blacklist9、FULL_DECODE_ONLY maxcapture64；当前用户脚本SHAfe5b74ca3c05afe77fd339fd4afcd4dfa5936f49142468ac660411281f055c53，新服务已开启prefix caching。保留当前服务/配置，不替换、重启或修改源码。

模型generation_config和实际服务日志均确认temperature1.0/top_p0.95/top_k20；尚在核验原生客户端如何继承这些参数、取消其默认request seed1234。评测输出上限先单列沿用30000，属于评测预算而非默认采样分布声明；不把旧temperature0/GPQAC32/ERQAC8分数冒充当前结果。完整新契约/默认参数请求proof/当前服务manifest必须在发正式题目之前冻结。GPQA预冻结155/198门槛，ERQA未指定门槛只报告分数。

当前not_started，后续既有规定GPQA CPU evaluator和原生FlagEvalMM串行运行，不能重叠流量。正式性能不恢复，原verify不动。

默认参数操作约束：原生GPQA _create_payload固定seed1234；seed=None/null在其CLI parser中被解析成字符串，不可用。将使用仅本次CPU评测进程启用的sitecustomize参数适配，调用原生payload构造后仅移除seed，temperature1/top_p0.95/top_k20显式等于服务模型默认；原数据/任务/runner/评分和已安装客户端源码不改。此适配是遵循用户默认采样要求的参数层修正，需离线零网络proof并冻结SHA。ERQA原生t1、top_p/top_k/seed均不显式覆盖、64线程。新服务已ready，启动日志确认FULL decode graph capture11/11；未配置profiler，不伪造当前实例两次replay证明，不作性能晋级。prefix-on按用户当前服务保留。30分钟监控qwen27b-c64已启用。
执行前登记 /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc005-gather-user-service.py SHAace9528d462a8684904dff00e5847bb2bf42112f961879977bb9b6211a2668a7。
执行前登记 /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc005-client-adapter/sitecustomize.py SHAa72d3e676e09888180b68a4e1faef64f42e9b2cb1cad982ac7e713d52ad400d7。
执行前登记 /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc005-prepare.py SHA0b3f753505f602ef6058f7554e4584150d2dfce6287ee97a3a219c8c1267c2ad。

准备预检 acc005-container-inspect-equality：首次准备作业在当前B inspect与旧inspect的直接字典相等断言处停止，尚未运行fingerprint、模型请求或正式评测。保留原作业，先逐字段核对是否身份变更还是挂载数组顺序/表示不同；不绕过门禁。

预检差异已确认只是Docker Mounts数组顺序：/data与/public-flash顺序交换；ContainerId/Image/创建时间及每个挂载全字段相同。按规范改为完整字段规范排序比较，不减弱门禁；旧失败与3份inspect保留，新v2先重验当前三个容器身份再继续，inputs仍为空、未发模型题目。续作 /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc005-prepare-v2.py SHAa45e1e5c8d03079576dd5a5b2c56fac0622a21615db7d99abf85a367056b40ea 已登记。
正式评测前保存控制 /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc005-verify-gpqa.py SHA4723dd5006bd48e5c655de36ddcb50e77cbbced390fc502875ce86e0e7fed4f5，不覆盖旧脚本或产物。
正式评测前保存控制 /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc005-full-suite.py SHA101f6e661bd6b738bd6d306727990b90173c5e661d0c1722275f1304a8a38be8，不覆盖旧脚本或产物。

主Agent正式发题前审阅完成：v2准备exit0 SHAef0f07fd0a0a67eb4a751b1e7af4bbbac339c72f8d4e857298a6e7d877eb8889；service user-c64-01 SHAa8a58fb3eaee23c9ba5e195378eebd364341fe136e9841298ee1814892f134a3、instance48735de01cabcb1882a9a9ccf4a1660d937b1d8b1f6f5643dc48b70f0fbf3fc7。8个输入/服务SHA全部匹配，双GPQA provenance相同；GPQA实际请求proof t1/p.95/k20/max_completion30000/no seed，ERQA原生t1/max30000、继承服务p/k且无seed、线程64。四套代码实测内容与旧版相同，本轮仅服务/采样/缓存/算子选择等配置不同，不能直接作单变量回退归因。新启动控制 /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc005-launch.sh SHAaf9dbbc98a5cdb0b3cec0a9c1589722b240b66c718b9e8b6a1743cf729c29c2c 已登记，下一步单次启动持久串行队列。

实际评测已启动：2026-10-26 22:20:29 CST，原生GPQA generate_until已提交198题、并发64、响应缓存命中0；run b5fd3bdf8a9340f7aa3fb25fc3afcbb1。实际gen_kwargs t1/p.95/k20/do_sampleTrue/max_gen_toks30000，CPU进程限定adapter移除request seed；harness seed42仅用于数据/框架可复现，不作为模型请求seed。Native客户端显示max_length2047但tokenized_requests关闭，未据此截断HTTP请求；服务模型maxlen262144，输出预算30000另列。identity-before确认同API/启动时间、四源码包内容、generation_config和health200，原生preflight exit0。持久jobs/acc005-full-accuracy、Host控制PID2805682/startticks1133515275；随后自动串行ERQA400/C64，无精度流量重叠。尚无本轮最终分数，旧acc004结果不混用。监控qwen27b-c64已每30分钟启用，完成/取消/需用户处理阻塞后删除。

2026-10-26 22:40:07 CST 半小时检查：原生GPQA请求进度149/198（约75%），尚无最终results/gate或全量分数；ERQA仍在队列未启动。22:39:02核验同一API499980/startticks1133379219、health200，同一Host controller2805682启动时间一致；11个冻结输入/客户端adapter/原生工具引用SHA均未变。早前22:33只读错误模式计数0（Traceback/API error/timeout/request-failed/HTTP500）。另复核当前原生API客户端：get_batched_requests使用semaphore64，amodel_call在每次请求/重试先deepcopy gen_kwargs再构造payload，因此日志显示参数pop后的字典不代表后续请求回退temperature0；没有修改客户端或额外发题。仅报告实际进度，不将辅助部分计分当最终分数。继续既有串行队列，半小时监控ACTIVE、性能暂停。

2026-10-26 23:04 CST 半小时验收：本轮GPQA完整198已于22:58:34结束，strict **163/198=0.8232323232323232（82.32%）** 达冻结155/198。原生full/verify/issue/check全部exit0；主Agent复核8个run-record引用SHA，396行/198唯一题、strict/flexible各198，strict163，与原生聚合一致。run-record SHA9698776fda82edbabb7b4eb61eb8912f9c76941690a03cd5cffa7eb1ebabd8e3；gate SHA321fd8ad387d720da9cb23b6612e3704e3798d391166c59600aa978d0965da56；native verified-result SHAc34a8923157a45797ce41d8a0df687ab754345f26fe4ce6f276d53f595176882。11项冻结配置/适配/原生工具SHA均不变，identity-after-gpqa同API/启动时间、四包内容、generation_config和health均通过。

ERQA已于22:58:53串行接续，仍是用户9998服务、64线程/单endpoint、默认采样t1/p.95/k20、无额外请求seed、输出预算30000、prefix-on。23:04:33已有70个可解析原生items，70唯一question_id均属冻结400且answer非空；23:03:34日志已开始119题、无匹配Traceback/ConnectionError/timeout/HTTP500/OOM。既有controller启动时间一致、仍运行，尚无ERQA最终分数，不计算部分分数。继续原生评分/拒答分母及源码/数据/图片/身份后检，无重复启动/额外推理；30分钟监控ACTIVE，性能暂停。当前结果不作与旧白名单/贪心C32的单变量收益归因。

2026-10-26 23:33:31 CST 半小时检查：ERQA246/400个原生items均可解析、question_id唯一且属于冻结400题、answer非空；日志已开始310题。完整raw/evaluated/result尚未生成，不计算部分分数。23:34:54复核16条BaseApiModel._single_infer/tenacity before_sleep的APITimeoutError原生重试提示（23:33早先普通timed-out匹配13，随运行新增）；不是16题最终失败，不做失败数量推断。其他Traceback/ConnectionError/HTTP500/OOM模式在23:33检查为0。既有controller启动时间一致、同API499980启动时间一致且health200，11个冻结输入/适配/原生工具SHA未变。未手动重试/改超时/采样/服务/源码，继续原生队列并等待最终400题评分及拒答分母后验；GPQA163/198通过保持，监控ACTIVE30min、性能暂停。

2026-10-27 00:03:41 CST 半小时检查：ERQA364/400个原生items均可解析、question_id唯一且属冻结400题、answer非空；全部400题已开始，剩36待返回。完整raw/evaluated/result仍未生成，不报告部分分数。原生tenacity APITimeoutError重试提示累计38条，其他Traceback/ConnectionError/HTTP500/OOM模式0，不把38次提示当成38题最终失败。00:05:16同controller启动时间/运行态、同API499980启动时间及health200、11个冻结引用SHA均核验通过。

只读运行问题观察：在同ERQA镜像、相同原生GPT构造参数下离线读取provider client.timeout为connect5/read600/write600/pool600秒；ModelAdapter的allowed model-config keys没有timeout，CLI的7200秒没有作为provider HTTP timeout转发。这确认了原生HTTP重试所使用的超时策略，不能据此归因具体设备/算子性能。未向模型发额外请求，也未改运行中超时、采样、服务或源码，保留既有native重试/完整契约继续收尾。GPQA163/198通过不变，监控ACTIVE30min，性能暂停。

2026-10-27 00:33:31 CST 半小时检查：ERQA393/400个items JSON可解析、question_id唯一/属冻结400、answer非空；7个尚未落盘ID为144/163/169/266/367/49/81（ERQA前缀），未生成最终raw/evaluated/result。累计53条native APITimeoutError before_sleep重试提示，其余Traceback/ConnectionError/HTTP500/OOM模式0，不将次数当成最终失败题数。00:35:09核验同controller/API启动时间及运行态、health200，11冻结引用SHA均未变；同9998服务Prometheus聚合7个running、0waiting。这是服务聚合观察，不冒充逐请求/rank trace对应关系。继续既有原生队列收尾，不追加请求/重试、改配置/超时/源码或恢复性能；GPQA163/198通过不变，监控ACTIVE30min。

原生队列已完成exit0：本轮GPQA163/198（82.32%）、ERQA239/400（59.75%），原生400全部计分、无拒答剔除；56条原生超时重试提示保留，不当作最终失败。final-result SHA50adb1e400309c3ad9b4a006a9c4897186d608e993edb23b1623246244a39f7a。独立零推理验收控制 /public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc005-review-full-results.py SHA10ff14de2ad02758f542218b9ae630a3c942abf572fd7e7213f3da6dd25f714e 已保存登记，将再验所有native引用、当前同实例/四包/环境/模型默认、C64/no request seed/30k/prefix-on及原生拒答口径，重验冻结400题/630图/原生评测源码/配置。

本轮完整精度于2026-10-27 **01:00:47 CST**完成，主Agent独立离线复核通过：

| 数据集 | 正确/完整题数 | 得分 | 判定 |
|---|---:|---:|---|
| GPQA | 163/198 | 82.32323232323232% | 达冻结155/198，原生issue/check及复验PASS |
| ERQA | 239/400 | 59.75% | 全400题计分、零拒答剔除；无用户阈值，只报告分数 |

两套均64并发上限，当前用户9998黑名单9服务，默认temperature1.0/top_p0.95/top_k20、不额外请求seed，输出预算30000，prefix caching开启。原生最终56条APITimeoutError重试提示保留，最终400题均返回非空响应并计分，不能将重试次数当作失败题数。独立复核重验GPQA八个run-record引用、原生gate与分数、ERQA400唯一ID及原生拒答分母/239个correct，11项配置/adapter/原生工具SHA未变。另独立重验400题/630图/原生评测源码/配置与准备阶段一致，同API启动时间/环境、四套代码内容、generation_config和health200均通过，复核零额外模型请求。未把当前实例graph启动capture日志冒充trace证明的两次replay，本轮精度结果不替代性能最终验收。

最终证据（远端案例根下）：`accuracy/acc005-full-results.json` SHA50adb1e400309c3ad9b4a006a9c4897186d608e993edb23b1623246244a39f7a；`accuracy/acc005-full-primary-review.json` SHA0fe06d3bcd541e8b777798d64a16a7dc6d54f562f2e58293dd4f913a6488be6d；`manifests/acc005-erqa-primary-postcheck.json` SHA917ab8a9939fed85cd58523e8ea500fd12418bd215be774de537375513e55ff4，原生postcheck SHA56b28cdec8d830aaacca330182a044dd42643fb4da34f39b46ae419b7e1e9ac9。

ERQA raw/evaluated/result SHA依次59d039daca073a60aac6febd1581db0d243a046020bcbc0a4fc94a37b714a9df / 42907cc59c28673820bdaec6b4bcecf7633264f343e34cff45d59a573f5ca90f / ddea1c5a2313c09d5b69e8e0b892a20b5efcb40fa4b3d3b62f9e7538a56d0dff。全部原始回答/日志/图片留在远端，不复制入本地模型目录。

半小时跟进 **qwen27b-c64已删除**，app返回deleteStatus=deleted。用户模型服务保留，不停止/重启/改源码或参数，未恢复性能、提交或推送。当前结果属于C64/默认采样/黑名单9/prefix-on组合，不作与旧白名单/贪心C32或ERQAC8的单变量收益归因。

收尾记录检查：当前案例schema/实验文档链接无错误。全仓check-project-records另有372个本案例以外记录/过程产物问题及3条警告，未改动无关案例，不标全仓通过；本次模型精度的原生与独立验收已另行通过。
