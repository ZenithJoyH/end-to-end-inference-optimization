# acc-020：op068原始权重布局修复后全量GPQA

## 终态：有效正式精度通过（2026-10-23）

收尾：产品已确认 `qwen3-8-ppu07-op068` 为 **PAUSED**，原prompt／周期／目标线程保持。003审计4个manifest成员回读SHA均一致。定向YAML重复键／schema、acc020/op068链接及终态数值检查、git diff --check通过；全仓check-project-records仍报告其他案例缺字段／链接与历史过程材料问题，未修复无关文件，不虚称全仓通过。

本轮17:17:43开始、18:48:24自然结束，strict **176/198＝88.8889%≥88%**；原维护acceptance签发本轮gate，19:52:49独立CPU审计及原生gate check通过，结论 `passed`。198唯一doc0..197、396双filter行、每(doc,filter)恰一次，同题原始doc/arguments/resps/usage等完全一致；正式分母保留全部198题，不使用helper排除None后的子集高分。

完整解析198份API返回并用原始全prompt唯一映射到198题；服务新日志窗口恰198个HTTP200，未见真实HTTP失败／7200秒超时事件、NaN／非法访存或服务执行错误。187份非空final均finish=stop、含thinkend248069且末EOS248046，其中176正确、11错答。另11题（71、76、79、88、115、127、130、145、147、164、185）均生成60000 token后finish=length，reasoning非空、content=None、没有thinkend／末EOS；evaluator将其保存为 `<TIMEOUT>`，**这些是60K截断与空final，不是网络超时**，均计错保留。首次为18:33:02的doc71。198份prompt/completion/total usage与完整token数组一致，共2318370 completion token；未见提前EOS。这些输出健康问题不改变有效score≥threshold结论，但不能声称所有输出异常已解决。

原controller／wrapper／lm_eval／helper均退出，无CLIENT_ERROR、FREEZE_ERROR或summary.freeze_error。70个原终态manifest成员、49冻结输入、26份同实例minimal引用及3份完整日志prefix均核验；source-before＝source-after＝当前CPU源快照，三库HEAD/index、engine、bootstrap、模型元数据／tokenizer及权重stat、eval源码树与helper SHA不漂移。权重stat不是全量权重字节验证。当前API仍本轮READY绑定的2114316/start546089295，8010 listener/argv/选定环境严格一致，health200、running/waiting/KV/preemption均0，保持BF16及现有修复；本heartbeat无新推理／GPU／源码或服务操作。

证据根仍为下文CASE。原生结果目录为 `CASE/results/Qwen3.8-Flash-Next-ppu07-acc020-c64-full-moe/cde2e30d6f474ea6ab746ba5a8d1c60f/`，内含 `run-record.json` 及 `gpqa_diamond_generative_cot/Qwen3.8-Flash-Next/results_2026-10-23T10-48-12.852683.json`、`samples_gpqa_diamond_generative_cot_2026-10-23T10-48-12.852683.jsonl`。gate为 `CASE/evaluation/accuracy-gate.json`。终态完整日志在 `CASE/diagnostics/terminal-evidence-001/`，独立审计在 `CASE/diagnostics/terminal-cpu-audit-003/`。

关键SHA：gate `443b9f10b5360b6338a7ab6711f1cb92f3f5378a289866bad1c5870cb7d1df38`；原manifest `ac0e192cfe950e7fd37ecb503b114459005b2558bde32b59d5c09d48d908577f`；CPU report `d0f9ddb28d1bdb1de8dadcaa3901007f6f0673543e6c6038633a9762015a2452`；CPU manifest `ae1e3ebbf93fb76b23a6c19b33a138054c4819fe848b0ee34f6f07052f095925`。results/samples/run-record/summary/FINISHED等完整SHA在同一state终态条目。审计001／002工具格式／日志匹配错误及执行日志保留，003按原生解析规则修正，不覆盖旧证据，不是模型重试。

按accuracy技能，本轮只清除绑定op068候选的正式精度阻塞；并非逐项数值等价或单变量因果证明。正式INFO是解析API对象、不是wire；8rank入口／capture／replay证据来自同实例启动和minimal，不是本198题逐rank kernel trace，无逐层QK/logits/state现场。历史分数不能直接归因单项修复。P1K Prefill/Decode/Mixed稳态性能及四场景验收仍未完成，不报告端到端倍数。写回后暂停monitor，保持当前BF168010并等待用户方向；新性能执行前需新鲜gate-check，本heartbeat不启动性能。以下为历史运行记录。

## 目标、授权与依赖

用户2026-10-23要求基于当前版本继续性能优化。本轮为op068修复后的必要正式精度验证：此前acc019有效174/198=.8787879<.88，不能用算子验证或旧acc018分数清除阻塞。只消费op068本次单次启动的新8010，不再启动／停止／重启模型服务，不访问8035或物理0–7，不改源码、采样、选参、黑名单或缓存策略，不提交推送。

固定PPU-07／容器qwen3.8-flash-opt-ppu07-20261015／8010／TP8物理8–15，canonical三库、BF16 model d458a1ce、完整thead fused_experts_impl入口、vendor cac5b989和原PLE/QSA/alignment/index/index_put/randn修复保留。唯一代码变量是用户已验证的op068去自动转置策略；没有新性能优化叠加。

R为 `/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/operators/op-068-thead-moe-weight-layout-fix-20261023/model-regression-001`。先等待原minimal controller退出／僵尸、FINISHED通过，且没有DRIVER_ERROR／FIRST_ANOMALY／FREEZE_ERROR。仅CPU审计完整10HTTP、token/usage/stop/thinkend/EOS、2C1一致、native C8/FULL、8rank真实入口和全部manifest/source前后当前一致；任一失败不启动正式请求。已有审计只读，不重复执行。

## 冻结正式契约

模式accuracy/formal-gate，覆盖op068；原维护formal_accuracy调用SHA验证原llmrun。单服务gpqa_diamond_generative_cot，198唯一doc0..197、limit0、C64，exact_match,strict-match阈值.88。温度1/top_p.95/top_k20/min_p0/presence0/repetition1/max60000，evaluatorseed42、原API默认seed及stop，完整tokenIDs/prompt；API最多3次总尝试、eval重试0、timeout7200。198逻辑题不等于HTTP尝试数，None/TIMEOUT占位不等于真实网络超时。

新eval容器 `qwen38-eval-ppu07-acc020-c64-full-moe-20261023`，规定flageval镜像，独立UUID／SQLite响应缓存。只复制既有不可变数据集缓存，不复用旧答案。两次新provenance逐字一致、原dataset revision相同后冻结契约并原生preflight；过程中不发送额外smoke／隐藏预热。模型prefix cache仍关闭。正式INFO保存完整解析API对象／token，不是wire bytes；本轮不新增wire或逐层QK/logits/state埋点。

## 控制与证据

CASE：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-020-full-gpqa-ppu07-c64-op068-layout-20261023`，排他新目录。命令在CASE/commands，当前项目工具链和完整Skill bundle在CASE/bundle及receipt，不运行硬编码acc019旧脚本。先本地stage.py --mode stage排他传送后唯一acc020.py --mode launch；其子进程 --mode wait-run最多等待50分钟minimal终态，通过CPU审计→prepare→provenance/preflight→单次formal。任何前置失败保存原错，不自动重试／恢复。无需heartbeat再次launch。

执行前SHA：controller `28cb9fc7c39b4fd8b4ec54b23e7ddbb7750837226fec58a1d559b60dd89f40fa`，source probe `588ce4d1d39b6d2e190da51de5e2545c1b9940ec3c05942276c113b5ff6488ea`，minimal CPU audit `5d805b7f8691b0c6f81c07442460e7236b39983c418fbf38147bf0b0d01a3a03`，stage `805077f6c03ce740ffeb9514750c76dbbdf73dd19950d31226147745ab185078`，payload `2ab7191a6f6687439423c46d43e51583c53ad3433ce52c0ab052654fc7fef977`；本地根 `/private/tmp/qwen38-acc020-20261023.tzgKyG`。新wrapper d345525c、acceptance99ea1301、原runner82cf6e83随manifest完整绑定。本地工具检查中模块名调用缺test_acceptance导入路径失败，随后按原discover入口9项failure/19项acceptance检查通过；不改工具，不把该调用错误当模型失败。

source CPUprobe覆盖三库内容／HEAD-index、engine内容、bootstrap、模型元数据与权重stat；不是全量权重字节hash。API身份用本轮READY＋listener/start/argv，不继承旧PID。记录服务日志新byte/inode边界，只把新窗口异常当本轮事故。原生results/samples/run-record/gate及source/runtime前后、日志prefix、manifest/FINAL_SUMMARY/FINISHED必须齐全；缺证或freeze_error仍incomplete，不能因存在gate而省略终态核验。

## 当前状态与停止条件

CPU审计002已逐题核完198个全prompt／token／usage，但全行错误关键词扫描误匹配INFO模型回答正文中的普通“error”，非客户端异常；002命令及execution.log保留。另存003 `CASE/commands/terminal-cpu-audit-003.py`，SHA `171fe52387927cb58a65a1062e200ff65742a2c5d5f55485cd82bd5611a3cfa4`，将完整API返回对象与非响应错误日志分开检查，其余条件不变，排他输出 `CASE/diagnostics/terminal-cpu-audit-003`。仅重做CPU证据分析，不重做模型测试或修改原始产物。

独立CPU审计001的首错保存在 `CASE/diagnostics/terminal-cpu-audit-001-execution.log`：额外反转义把doc136的LaTeX `\nu`误作换行，属于审计解析错误、不是模型异常。按实际evaluator `create_message` 的纯 `json.loads` 规则修正，且核实原占位文本为 `<TIMEOUT>`；不改评测原件。另存002脚本 `CASE/commands/terminal-cpu-audit-002.py`，SHA `bf7521ea4cd25883b73dd7ac5424d81fb04311558f698d40619e2949aeea0031`，排他输出 `CASE/diagnostics/terminal-cpu-audit-002`；旧命令及失败日志保留。仍仅CPU审计／原gate check，不执行任何新测试。

终态CPU核验执行前记录（2026-10-23）：原controller已生成176/198及passed gate，尚待独立终态核验。新增只读审计命令 `CASE/commands/terminal-cpu-audit-001.py`，SHA `05bd094c78ec7358fa17e9540b715a52fffdf6e31ae7c6db3ce2968e49ede295`，仅读取已有原生samples/results/API日志、manifest与来源，核当前精确8010绑定并调用原维护acceptance check；仅排他保存CPU审计到 `CASE/diagnostics/terminal-cpu-audit-001`，拒绝覆盖。不重新issue gate，不发推理/GPU请求，不启动／停止／重启服务，不执行性能测试。源探针仅stdlib文件／Git检查，不导入生产模型包。

2026-10-23 18:16+08只读监控：原controller、wrapper、lm_eval和helper身份仍匹配；8010保持同一READY实例、health200、running21/waiting0、KV47.78%、preemptions0，generation计数继续推进。没有CLIENT_ERROR、FREEZE_ERROR、原生samples/results、exit.code、FINAL_SUMMARY、FINISHED或新gate；正式新日志窗口未见运行错误。CPU复核当前source与source-before严格一致、49个冻结文件及eval/task-helper源码树SHA仍匹配。formal-run.log的11635830字节前缀SHA cde33a838d743dcf39b65c92bcae44d4b79d7cf68b25dca70e17fa00a6ac170d完整解析177个API返回对象：全部非空final、finish stop、thinkend248069和末EOS248046，prompt/completion/total usage均相符，长度89–37174，零None／length／解析错误，未见真实HTTP或网络超时日志。该177是返回对象数，不作为去重题数或正式分数；不使用helper子集高分。仍为running/incomplete，继续原监控且不启动性能，无额外推理或服务操作。

2026-10-23 17:50+08只读监控：原controller／wrapper／lm_eval／helper身份不变且存活，同一READY绑定的8010在17:46:02 health200、running64/waiting0、KV42.30%、preemptions0；新服务日志窗口未见执行错误，未见CLIENT_ERROR／FREEZE_ERROR／终态summary或FINISHED。再次CPU核验当前source严格等于source-before、49个冻结文件及eval/task-helper源码树SHA一致。现有formal-run.log的4502381字节前缀SHA为1c8c48091f5317b3ccb4e0071edb3095158feadae6f7159c96e79b8ab2f08689，完整解析125个API返回对象（零解析错误）：全部finish=stop、非空final、完整completion/prompt token与usage一致、包含thinkend248069并以EOS248046结束，completion长度89–16904；未见None、length或真实HTTP/网络超时错误。这是已有返回对象的健康审计，不是按doc去重的完成题数、正式分数或wire证据；不报告helper子集高分。全量评测仍running/incomplete、无新gate，继续原monitor，未新增请求、变更服务或启动性能测试。

2026-10-23 17:23+08：op068模型minimal已17:17:09完成，原driver退出，既有后继controller完成唯一CPU审计（report365252d6，10完整HTTP／8rank实际入口／C1一致／capture与replay／source／101原manifest均通过），自动于17:17:43启动本轮formal。PREPARED SHA5ed4cd83、FORMAL_STARTED SHA3c960791；原controller2462106身份不变，没有新启动或smoke。新API2114316/start546089295/argvSHA c146e2da精确匹配READY和8010 listener。

两次新provenance逐字一致SHA c39228d57fd391a9f723496f54fa2fb3f0d7aeb17810a2edf63559152dc63523，dataset content-sha256:167548b01bcfd7d38d0eb80bb01bd1e6dded4d3aa14b41a4bdba0beb5423dadc。本轮config85a85400、contracte5dd8211、source-before9a60f2f0，preflight通过；UUID cde2e30d6f474ea6ab746ba5a8d1c60f，原生初始化缓存命中0/198。服务日志边界inode24771028132／byte365889，边界SHA6c6333b3；只按此后窗口判断正式新错。

17:20:43 health200、running64/waiting0、KV9.28%、preemptions0；正式新窗口未见运行错误，现有三库／engine／模型元数据与权重stat／HEAD-index／bootstrap经CPU回读严格等于新source-before。49个frozen-inputs全部SHA一致；eval lm_eval源码树9ab74567及task helper源码树d7ee1693与新provenance一致。注意helper文件原始字节SHA为a43f7a6d，provenance使用文件名→字节SHA字典的canonical JSON摘要，两种哈希不能直接比较。本次只读检查最初按dict处理list型minimal manifest、以及混用这两个SHA口径，均在核验工具内报错；按原schema／原生source_tree口径重读通过，不是模型异常，未改任何产物或重跑审计／评测。

17:23:21原controller、formal wrapper3505434、lm_eval3509108和score helper3509109均存活；无CLIENT_ERROR／FREEZE_ERROR／FINAL_SUMMARY／FINISHED。目前没有原生samples/results终态，不把派发、health计数或helper子集分数当正式完成题数／分数。仅更新阶段记录，保持只读monitor；全量精度状态仍incomplete/running，无新gate，不启动性能测试。以下为启动前历史。

16:52:50+08已排他交付27文件／SHA回读通过，STAGED SHA9afee407010eb0507ec7161108861c07fa6534674d62289060e95708f9c7b7c7。唯一后继controller2462106/start546139717/argvSHA46844f513bdecca12a9d253ea035bb21ea9d624f7f16916f900e3ef2b29d5f51，WAIT_STARTED epoch1792745570.6854806，正在等待op068最小回归；尚无PREPARE_STARTED或FORMAL_STARTED，正式GPQA请求0。本地工具按正确discover入口累计43项通过（provenance11、verify4、failures9、acceptance19），不代表模型精度通过。

只有最终有效score>=.88才能签本轮gate并继续P1K阶段稳态性能；低分failed-score或无效证据转accuracy-diagnosis冻结，不自动重跑／FP32对照。普通错答、空final／length由既有评测继续收集，不擅自取消或删题。完整token缺失时明示，不能虚称完整GPU因果；历史分数差不直接证明单项修复的因果。

监控复用qwen3-8-ppu07-op068，每30分钟只报告实质结果、首次失败、明显停滞、完成或需处理；终态停用。保持本轮BF168010不停止。新gate后计划当前P1K的Prefill/Decode/Mixed稳态基线；这些性能契约尚未启动，不能声称已优化或达到四场景验收。
