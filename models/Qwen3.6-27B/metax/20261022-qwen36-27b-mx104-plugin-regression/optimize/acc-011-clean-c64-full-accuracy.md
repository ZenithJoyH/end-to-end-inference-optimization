# acc-011：新 clean 容器 C64 全量 GPQA / ERQA

本轮 acc-011 全量精度已完成并通过原生及独立复核：**GPQA163/198（82.32%）** 达155/198阈值；**ERQA246/400（61.50%）**，全400计分、零拒答剔除，无指定ERQA阈值。目标为当前 `qwen36-27b-clean-20261028` 用户8010服务，两套均C64、模型默认t1/p.95/k20/无额外request seed、30k输出预算、prefix-on。原生队列完成于2026-10-28 18:19:56 CST，独立复核实际时间22:02:58 CST；触发时间18:31不冒充实际执行时刻。68条原生超时重试保留，最终400题均非空返回。用户服务未暂停/停止/重启或改配置/源码，性能暂停；半小时监控 `qwen27b-clean-c64` 已删除。

状态：**全量完成并独立验收：GPQA163/198，ERQA246/400**。用户授权对新启动的 Qwen3.6-27B 服务进行 GPQA / ERQA 精度测试，均并发64。本轮仅精度，不恢复性能回归，不修改模型、源码或用户服务。

使用本地 inference-accuracy-evaluation，能力 e2e/accuracy，显式模式 formal-gate，完整 bundle SHA `1ed06a57f1f6e1ef39fb7fd872f579122b098a18f0255ade0a1160d6432c2b66`。沿用当前案例与用户此前指定的模型默认采样及30分钟通知偏好；monitor `qwen27b-clean-c64` ACTIVE。首次创建缺 destination 被拒，补 destination=thread 后成功，无重复监控。

## 当前运行事实与冻结范围

唯一新目标为 mx-104 的 `qwen36-27b-clean-20261028`，容器ID `0425b53d4f77e23c3913fb78c8fde91d128982cc6826ba6369785d6a317aaf3f`，镜像为 env-010 的 `f001fd92fbc7`。用户 API 容器PID13812/startticks1148292268（Host2010668），端口8010，served name `qwen36-27b-black-list`，权重 `/data/Qwen3.6-27B/`，BF16 / TP2 / 物理GPU2,3。当前 health/models 200；graph配置 FULL_DECODE_ONLY / maxcapture64，prefix缓存开启。默认生成配置 temperature1 / top_p0.95 / top_k20。当前进程无 VLLM_USE_FLAGGEMS 和旧 contiguous prefill 环境变量；USE_FLAGGEMS1及黑名单9保留。

正式 GPQA 固定原生 gpqa_diamond_generative_cot，完整198唯一题、strict-match exact_match、阈值155/198，limit0。随后串行原生ERQA全400题，两者C64。ERQA不设得分阈值，报告原生分数、计分分母及拒答排除情况。输出上限30000是沿用的评测预算，不改模型采样默认分布，不额外设置请求seed。保留当前prefix缓存；此为用户服务精度测试，不作正式性能准入或单变量性能结论。

复用已核实仅sleep、闲置的CPU评测容器 `qwen36-27b-acc008-gpqa-20261027`（规定flageval镜像1396e5d...）和 `qwen36-27b-acc008-erqa-20261027`（原生ERQA镜像997570...）。使用全新acc011输入、结果、日志、响应缓存和任务目录；不复用旧答案或分数。原始runner、tools-v3 wrapper和ERQA任务/评分器不改。仅本轮sitecustomize在客户端payload中移除规定模型被lm-eval原生固定的request seed1234，源SHA守卫及离线payload proof必须通过；其他模型行为保留。

新镜像/容器谱系从 env-010 原生回执和当前inspect实测，核验RootFS、Config和原挂载Source/Destination/RW/Propagation；当前容器namespace现场采集，不沿用旧B的clone gate或实例。组件实际导入及源码含本地修改重新取指纹，模型共用挂载及原始全字节清单加当前stat/非权重重哈希验证。新服务日志只证明实际捕获记录，未采trace不宣称两次模型replay。

## 执行与停止条件

先bootstrap只读绑定并复用CPU evaluator，再持久化preparation采集新服务/组件、双provenance、payload proof和native preflight。主Agent审阅准备回执SHA后，才单次启动full-suite。控制作业保存在 `jobs/acc011-*`，已有文件时检查状态，禁止重复启动或覆盖。源服务始终不重启/停止/暂停，无性能或profiler流量。GPQA低于155时冻结证据、不签gate、按精度定位方法审阅；可在未改健康服务上完成独立授权ERQA，不修改阈值。

完成后原生verify/issue/check与独立动态结果复验，逐题检查198/400完整性、原生分数、SHA、拒答分母、源码与服务连续性。历史162/198、244/400等均不属于本轮；不预设最终得分。终态删除监控。

## 外部证据及执行前命令登记

远端根目录 `R=/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression`。证据位于 `manifests/acc011-*`、`services/user-c64-03-clean*`、`accuracy/acc011-*` 和 `jobs/acc011-*`。

命令均已语法检查，登记SHA后部署；只改变外部编排和新产物目录，不改公共runner/scorer。

- `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc011-bootstrap.py` SHA256 `68f4c729016aa1081955aaf4abd96b65e49dda5e09a5222f113a95fbd218432e`。
- `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc011-review-full-results-v2.py` SHA256 `cfd6e55953dc424187b7458a754293642414ab854fef54cd4f1d631e5f820ac8`。
- `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc011-full-suite.py` SHA256 `a2fe64378c647d5897ddf3d9ee63ad149a1cbd4ac0f15d754dbd8144258f7f5f`。
- `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc011-client-adapter/sitecustomize.py` SHA256 `e36a5471dcb814eea51452c1df1ae168b618617f383c9da5b0219860d8470cc3`。
- `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc011-prepare.py` SHA256 `88fa9c31c34e29146ac1a89dc9c62c4306c1adc197d18b5ad1109ebe74c49406`。
- `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc011-verify-gpqa.py` SHA256 `0d1a3b3d1a86b324abf0ddb055c0b215b5a72bf902c46b3414c63450285941c8`。
- `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc011-gather-user-service.py` SHA256 `d02eaecee68cc2ce33ad617cbb3bfb11198001b5f2b3c24ccc0a8fabd6ff0ba1`。

Bootstrap v1在首个CPU评测进程检查处停止：当前Docker top要求包含PID列，单comm列被拒；尚无模型请求、evaluator修改或inspect输出。保留原jobs/acc011-bootstrap/command.json，V2只允许该唯一已知初始目录状态，并改为pid,comm核验全部进程仅sleep，其他断言不变。新命令 `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc011-bootstrap-v2.py` SHA `1c3c1356fbda87ded7f8618f50832b5de292a48ceb36be9cd1a865a2bb7fcfe1`，执行前登记并语法通过，不重做任何已完成评测。

原preparation完成新launch与四组件实际指纹，但gather在container-ID检查处停止：新lineage结构是clones.b.id，旧读取方式期望clones.b直接为字符串。记录实际失败并保留exit/证据，尚无模型请求。修正读取到id，保留全部当前容器/namespace/镜像/进程/源码/挂载和端口检查。新preparation-v2只接续同一不可变launch/fingerprints，原始preparation失败不覆盖，输入目录仍空。full-suite-v2消费新的准备回执，独立review-v3核对真实v2控制器；均不预设最终分数。四组件SHA与env-010相同，新fingerprint SHA dae9ffb7acbbbfd1d79e7cecaa2dd9ed1a0deea0c4c536b27c2ccd1e4a88b7ca。

执行前登记修正版命令（语法通过）：
- `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc011-gather-user-service-v2.py` SHA `0222da5341caa9c8db15a7ae51c3d5898e1764ca11a7fc741d324f9c2a317332`。
- `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc011-prepare-v2.py` SHA `2162f6576728936440c6bf6df2cd0a67e1a6ce15fff48cf343b47c95b2d1cff7`。
- `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc011-full-suite-v2.py` SHA `c24d0230108ba21b186d35ca8a5817567b7937faa4b4586195ab8f9bd3362ceb`。
- `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression/commands/acc011-review-full-results-v3.py` SHA `ff83d86708ba2ab0edc68a00fa33cad61b3c4616706a77b105f40ae517bca0df`。

## 正式发题前审阅通过

按精度定位Skill将准备阶段失败归为measurement-invalid（控制面记录结构），并非模型精度回退。修正显式读取lineage.clones.b.id后，新preparation-v2、服务collector和原生preflight全部通过；没有在失败阶段发送模型请求，旧失败产物保留。

preparation-v2 exit SHA `7ea68fe9b9659c2086ebf81b500bde5147b92e7786e86f853901dbfad3e6d965`，当前service SHA `46aa416343f2372387704c161da25fb57281fd0926cbc4b35f08b1415bb17ccd`，实例 `04dac0a157881c6bd3ba493e1c0ae538365c7f564df10006d717f78147d5cf3b`。主Agent独立重新计算7个输入及service SHA，双provenance一致 ae5050bae5011730255f44df855d19d87328328a644f015e6fb7b40878bdd47d，核验完整题集/任务/155阈值/C64/默认payload无额外seed/30k预算及当前容器、用户prefix配置。ERQA400唯一题/630图、num_workers64与原生离线payload通过；旧fulljob不存在。

已登记单次正式启动：`python3 R/commands/acc011-full-suite-v2.py --reviewed-preparation-sha 7ea68fe9b9659c2086ebf81b500bde5147b92e7786e86f853901dbfad3e6d965`。持久作业 `jobs/acc011-full-accuracy`，GPQA198后自动原生验收并串行ERQA400；同实例/source/input连续性检查前中后执行，无自动整轮重跑。完成后只用独立动态 `acc011-review-full-results-v3.py`，不用旧v2（绑定旧控制器路径），更不用任何历史已知分数作断言。

## 实际正式启动

2026-10-28 **15:39:00 CST**，GPQA原生runner真实进入generate_until，198题缓存命中0、待请求198、concurrency64、每请求timeout7200，payload t1/p.95/k20/30k与冻结proof一致；当前尚无最终分数。新run为 `accuracy/acc011-gpqa-runs/Qwen3.6-27B-user-C64-8010-defaults/bf560b4d05e849a7a7d0bfbc3b5aec91`。持久Host控制PID2045815/startticks1148386221，job `jobs/acc011-full-accuracy`；服务连续性/source/default配置与health200再次通过，原生preflight exit0。GPQA完成后原生verify/issue/check并自动串行启动ERQA400/C64，不重复发起整轮任务。

半小时monitor `qwen27b-clean-c64` 已更新为新的v2准备/正式控制器和独立review-v3路径。原identity collector前置失败经精度定位Skill分类measurement-invalid并修复复验，未改变服务/模型/runner/scorer/阈值。新整体状态仍incomplete，等待两套完整原生结果；性能暂停。下次从本轮原生job和现有产物接续，禁止重新启动。

2026-10-28 15:59 CST 半小时检查：GPQA原生客户端最新辅助请求进度 **162/198（约82%）**，尚无完整results/run-record或最终分数；ERQA尚未启动，继续在同一控制器串行排队。当前Host控制PID2045815/startticks1148386221未变；当前API13812/startticks1148292268、四组件源码哈希、默认采样配置、环境和health200均通过，11个冻结引用重算SHA一致。原生日志APITimeoutError、Traceback、ConnectionError、HTTP500和out-of-memory匹配均0。只读核验没有额外推理、重启、重复启动、参数/源码变更或性能测试。保留monitor qwen27b-clean-c64 ACTIVE30min，按用户周期偏好通知实际请求进度，不能将162/198当正确题数。

## 2026-10-28 16:29 CST：GPQA完整通过，ERQA运行中

本轮GPQA完整198题得分 **163/198 = 0.8232323232323232（82.32%）**，达到冻结155/198。原生full、verify、issue、check均exit0；主Agent再调用已登记的原生结果验证器和acceptance check独立复验，完整396行/198唯一题、多filter及结果来源一致，原生gate check PASS。没有重跑题目，没有使用旧163分结果。完成时间16:16:39 CST，ERQA400/C64于16:16:59 CST自动串行启动。

新run-record SHA `5a1c7b67c30c84724bfb7b7d842dc353b15f47dc2596b53f30b255a8b9f83f98`；`accuracy/acc011-gpqa.accuracy-gate.json` SHA `41df6a43b6b2037ffeb991bca38a0724a22b80a64b810816d70ef089d906654c`；`accuracy/acc011-gpqa-verified-result.json` SHA `f48b364dba4ff222196fa6ee1214d298c06a1e08e7c379fd1aa68c48f7b0b70f`。run/result/sample路径都在本轮bf560b4d05e849a7a7d0bfbc3b5aec91下，不替换旧回执。

ERQA当前 **131/400** 个原生items可解析、ID唯一且在冻结400题内、answer非空，partialJSON0，无完整评分或最终分数。当前Host controller与API启动时间、环境、四组件源码、默认生成配置和health200通过，11冻结引用重算SHA一致；两套原生日志APITimeoutError、Traceback、ConnectionError、HTTP500和out-of-memory匹配均0。独立复核额外模型请求0；没有重启、改源码/采样、重复启动或性能测试。继续现有ERQA，monitor qwen27b-clean-c64 ACTIVE30min，完成后使用review-v3动态核验全400分母/原生评分及同实例证据。

2026-10-28 16:59 CST 半小时检查（重试日志相邻检查至17:00）：ERQA **257/400** 个原生items已可解析、ID唯一且在冻结题集中、answer非空，partialJSON0，尚无完整raw/evaluated/result或suite最终exit，不报告部分分数。日志新增原生APITimeoutError提示，后续检查累计 **28条**，已逐条确认全部来自原生before_sleep.py的Retrying _single_infer（首条16:47:05、最近17:00:24 CST），不是28题最终失败；Traceback/ConnectionError/HTTP500/OOM匹配均0。任务持续返回，保留原生重试和所有日志，不手工重发题、调整timeout/采样或重启服务。

控制PID2045815/startticks1148386221及API13812/startticks1148292268未变，四组件源码、环境、默认generation配置与health200通过，11冻结引用SHA一致。复核零额外推理，无服务/源码变更或性能测试。GPQA本轮163/198（82.32%）原生与独立验收结论保持；继续当前ERQA和30分钟monitor，完成后独立review-v3检查全400及原生拒答分母。

2026-10-28 17:29 CST 半小时检查：ERQA **371/400（92.75%）** 条原生响应已落盘，均可解析、ID唯一且属于冻结400题、answer非空，partialJSON0；尚无完整评分文件或suite最终exit，不能当最终分数。原生APITimeoutError累计 **59条**，全部匹配before_sleep原生Retrying回调，最近17:29:14 CST；不等同59题失败。其余Traceback/ConnectionError/HTTP500/OOM匹配0。任务较上次257持续增长，保留原生重试和全部证据，不手工重发或改变配置。

当前控制PID2045815/startticks1148386221、API13812/startticks1148292268、环境、四包源码和generation_config连续性及health200均通过，11冻结SHA一致。零额外模型请求，未改服务/源码/采样/超时、未恢复性能；GPQA163/198（82.32%）已验收结论保持，监控ACTIVE30min，继续现有ERQA完成后原生和review-v3全量复验。

2026-10-28 17:59 CST 半小时检查：ERQA **395/400（98.75%）** 个原生响应已可解析、ID唯一且在冻结题集、answer非空，partialJSON0。尚缺ERQA_163/240/266/367/49五题；完整raw/evaluated/result及suite最终exit尚未生成，不报告部分分数。原生APITimeoutError累计 **67条**，全部为原生before_sleep Retry回调，最近17:56:13 CST；其余Traceback/ConnectionError/HTTP500/OOM匹配0。进度较上次371继续增长，沿用原生等待/重试，不重发整轮、不调整超时/配置、不提前评分。

同Host控制PID2045815/startticks1148386221与API13812/startticks1148292268存活一致，四包源码、环境、默认generation配置、health200及11冻结引用SHA通过。只读检查额外模型请求0，无服务/源码/采样变更或性能测试。GPQA163/198（82.32%）已验收保持；监控qwen27b-clean-c64继续ACTIVE30min，齐400且原生评分完成后执行登记review-v3并删除监控。

## 最终完整结果与独立验收

| 数据集 | 正确 / 完整计分题数 | 得分 | 判定 |
|---|---:|---:|---|
| GPQA | 163/198 | 82.32323232323232% | 达冻结155/198，原生及独立复验通过 |
| ERQA | 246/400 | 61.50% | 全400计分、零拒答剔除；无指定阈值，仅报告分数 |

原生job exit0/status completed_full_scores_verified；独立运行已登记且SHA一致的review-v3，完整复验GPQA原生结果/396行198唯一题、正式gate check、ERQA原生400唯一题/原生拒答策略/分母400/评分246、630图及数据/源码/配置/离线payload、冻结11引用与当前服务连续性。独立复核额外模型请求0，当前API13812/startticks1148292268、四包内容和默认generation/环境及health200保持。没有重跑GPQA/ERQA、改阈值/参数、改源码、重启模型或恢复性能。原生ERQA累计68条APITimeoutError重试日志，全部原样保留；最终400题全非空，不是68题最终失败。其余Traceback/ConnectionError/HTTP500/OOM匹配0。

原生完成时间UTC10:19:56.872137（CST18:19:56），本次heartbeat触发UTC10:31:23.419，实际独立review回执UTC14:02:58.179623（CST22:02:58）。这些时间分别来自调度及原生回执，不将触发时间当作实际复核时间，也不推断延迟原因。复核初始化的mantis未安装提示是未使用的视频评测器可选依赖提示，ERQA原生完整计分与来源检查均通过。

关键产物（均在远端R内）：

- `accuracy/acc011-full-results.json` SHA `2f9c3fa42f374dec6f78e8415b9dbcc215e21b7cbdf20d0464cc7ca7e1a1a0f7`。
- `accuracy/acc011-full-primary-review.json` SHA `f6f7235ef018d1de04412bdcacc2aec664b209a5565f37037aaade99af6b3014`。
- `manifests/acc011-erqa-primary-postcheck.json` SHA `bb72ff374a1f5b90a3af4207afb2fcb2ab4d69cef9ff5925637e08bbc6c24385`。
- `jobs/acc011-full-accuracy/exit.json` SHA `0500c4d65b938399dce2341e68606dc88e293d6d9f17e78fe9932de298c4839a`。
- ERQA raw/evaluated/result SHA依次 `38ad366bed50090421b6399e60aeba148435fbecc2b9ea7c3544a50986e94cd8` / `eab47f2813b2ac7aefa16c5dca00bc833d734eb69bd0156506cd357e0cc75283` / `514f36b6dfffd86bd0f5232e532ccd5fccd243704c50ca89b06772c938aed5e5`。GPQA run-record/gate SHA见上节及state。

监控清理：automation_update(mode=delete,id=qwen27b-clean-c64) 返回deleteStatus=deleted，半小时跟进已结束。保留用户模型和CPU evaluator容器、模型、数据、源码及全部原生产物。不继续发题，不恢复性能，等待用户下一步指令。本轮仅证明所绑定服务和完整精度契约；随机默认采样和历史实例/配置不同，不把分数变化归因为环境变量清理或单个PR，整体性能验收仍incomplete。
