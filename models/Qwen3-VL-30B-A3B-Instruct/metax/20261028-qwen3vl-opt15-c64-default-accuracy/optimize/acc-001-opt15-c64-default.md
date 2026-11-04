# acc-001-opt15-c64-default

状态：准备。用户明确要求对重新启动的服务C64全量GPQA及ERQA；本次新授权支持新轮次，不复用旧分数或gate。模式formal-gate，已读取本地inference-accuracy-evaluation及项目映射/实验/产物契约。

## 当前身份和范围

mx-104，qwen3vl-pr943-split1-mx104-20261023内qwen3vl-opt15/8030，API1718819/ticks1149208177，GPU0/1、TP2、BF16、batch8192、seq64、mem.91、FULL_AND_PIECEWISE/64、prefixON。模型/data/models/Qwen3-VL-30B-A3B-Instruct。当前模型空闲，models200；日志显示当前默认T.7/P.8/K20/repetition1及graph capture完成。源码新增sampler文件与注册改动，按当前完整指纹冻结，不宣称与旧版本相同。Attention磁盘f81fa552…原paged/default0。本轮不改源码/配置/采样、不重启/停止/清cache、不做性能或新诊断。

## 方法与停止条件

正式GPQA198 strict-match64/C64；ERQA400 native40/C64，各完整一次顺序执行。采用原官方runner/数据/评分。loopback19964只去掉客户端sampling和seed覆盖，保留messages/images/stops及18000输出cap，实际上游审计。两次task/data provenance一致、原ERQA400题630图/评分SHA、CPU真实factory默认参数和普通smoke/C8通过后开始。无直接graph replay计数，不编造证明。有效GPQA低分仍完成ERQA；失败冻结证据，不挑分/补跑。ERQA报告native拒答过滤及全部400计错。controller finally仅停自身adapter，保留当前用户服务并核验身份/source/models200。

## 外部证据与执行前记录

用户远程根/public-flash/jinghao/qwen3-VL；解析同路径root权限755、约9TB空闲，新case不存在。新case为20261028-qwen3vl-opt15-c64-default-accuracy，CPU评测器opt15-gpqa/erqa独立命名，直接bind本case，无GPU。bootstrap.py SHA a24c4aeaa349a225a408ee9c98f03ddbae96b22abeed50583df83c4518dec8c8，复制已验证旧C64脚本到新路径、绑定新服务身份，源模型不变。脚本归档后才执行；生成prepare/controller/launcher的SHA继续记录。原始数据远端保存。每半小时通知实际进度，完成终态核验后停监控。

## 性能效果

未测性能，无性能结论。正式结果尚未产生。

bootstrap完成，两个新CPU evaluator已创建，0模型请求。执行前脚本SHA：prepare_accuracy.py 72e909a32235729bdb9550191a23653b1a8b9694fd069c9995ebd19751814792；accuracy_controller.py 2db85b1a8f30c982d4b071a2a065aa46facd4405c60557e9afec8eec365be7f1；start_controller.py 9cfcc32765735b5cb598e129c8d3540da178c2ce0e30140d72614eff66fe2f6a；collect_current.py 9c6e4d35d5f8a9fb8895fa3f9118bc927ffcbb6d68cd4b19c96fea47b128350d；proxy29f4db33保持已验证实现。准备阶段再次核验实际服务与两次来源，不执行旧控制器。


CPU准备通过，两次provenance相同、同198题，真实factory去sampling/seed保留messages/stops/cap。prepared SHA2ed17a0a9ba16d8638682e55b3299abffcbcf03339a1d5d65088eed9c4a1486a；contract SHA86d5cd7b5978092a6f0b56a4526094fb0d8a428a7880338e7df886196875ed38。唯一控制器2523492/ticks1150704791已启动，排他锁manifests/controller.json；不得重复启动。监控qwen3-vl-opt15-c64 ACTIVE，每30分钟通知。正式结果尚待产生。

14:05:21UTC普通smoke/C8/source通过，ERQA400题630图/评分源码预检通过。14:05:29UTC完整GPQA198/C64已实际开始，初始64attempt/0completed，暂无分数。ERQA顺序待跑。全仓记录检查有既有跨案例格式/过程产物错误，本新case未出现在错误列表；未改无关记录。


## 2026-10-28 22:35 BJT跟进

GPQA于14:22:43UTC完整结束：125/198=63.13131313131313分<64，有效失败、无gate。独立只读核验198unique strict样本/perdocsum125、原生结果与样本SHA、两次provenance、config及源码/参数前后完全一致；198上游转发均无sampling或seed覆盖。result SHA b73cb9824a225c6904c1a9e48794d60d49373e431f0c2118337b5e113b5a64cd；native20507644f73094f8744b85719ac08ff8bcba5ba613fc6b3d370964904875ef64；samples94203d3c0771fd00bd36fba09f710cf3849c180a4528c1245f1d1cda6c26e53a；sampling audit b5b7a5a895743db0b015a231bef01a0d5f183bf400c331f2d4189cd49d1339eb。

调用本地inference-accuracy-diagnosis，冻结accdiag-opt15-c64-gpqa-001：正式阈值失败、证据有效、原因unconfirmed。历史opt12通过与本轮源码/实例/无requestseed轨迹不同，不能据单轮分数归因新sampler或库；未执行新复现/修复/重跑，不叠性能优化。原始失败证据保留，不挑分。

ERQA于14:22:43UTC按计划开始C64完整400；当前原生items持续增加，尚无最终分数。唯一控制器2523492/ticks1150704791仍运行，用户API1718819/ticks1149208177未变、8030models200。继续现有任务和原生重试，不改并发/超时/分母，不补跑。

本次最终进度读取：ERQA原生368/400条、368unique question_id；尚无erqa-completed/completed/failure。每半小时监控保持。

## 答案提取审计（用户追加请求）

用户要求核查125/198是否存在实际答对但提取错误。仅离线CPU审计同一原生198响应，不调用模型、不重跑正式评测或修改正式分数。归档commands/audit_gpqa_extraction.py，执行前SHA789d2f3d1b64a87515392cfbd16a5504907c60ebb146d2090449d2158bd6d946。在本轮official evaluator中重放原RegexFilter/MultiChoiceRegexFilter，逐题核验原回执、最终答案行、18kcap及宽松增计的4条上下文；证据写新的results/gpqa-extraction-audit.json，不覆盖原结果。


离线复核完成：原strict/flexible提取器在全部198响应上逐题重放与回执完全一致。73个strict错误中，62题最终明确选错，提取值与末尾最终答案一致；11题全部completion_tokens=18000且无明确最终答案。未发现明确最终回答正确但strict提取错误的样本（confirmed=0）。

原flexible在doc_id68/74/79/98上计对而strict未提取，但68/98只是Perhaps D/A后仍继续且被截断；74重复序列、79反复列举数值选项，原宽松fallback命中选项文本，不构成明确最终正确答案。flexible整体只100/198，不能择其加分项拼接为正式成绩。未独立重标数据集科学标准答案，不把部分推理正确等同最终答对。正式仍125/198=63.131313%，没有修改分数/门槛/输出长度或发新模型请求。

审计回执results/gpqa-extraction-audit.json SHA44f63593b890a38c28336df3e6a820f9182f123470bb97317c10b7f0e7e411d3；原评测器extraction.py SHAd62d2d6f03fff4c9d6a3141b3cdd1c2398ddf0c12e7d2e90998101b4e17d103c。全部逐题审计含responseSHA留远端，不改ERQA既有运行。


## 全量终态：2026-10-28 23:05 BJT

GPQA125/198=63.131313<64有效失败，无gate；ERQA182/400=45.50>=40通过。ERQA400unique，全部有bool correct，0拒答，native与全部400计错均45.50。独立CPU核验400题/630图/原评分源码SHA、原filter_rejected无拒答分支、182correct及原native分数一致。475次原生转发与475响应/399唯一消息体仅传输统计，不充当题数；默认采样无override/seed审计passed。父controller2523492退出，finally仅停自有adapter，before/afterERQA/final四仓/配置/模型/源码/服务完全一致，API1718819/ticks1149208177/models200保留。

回执SHA：erqa-completed a721cbfdd2e89178576e6d668aa9dd637acefe9d94e50be5281669c2160031b5；erqa-sampling-audit bd4de7ad8e7e9a17a1a8575a35a7c7026c41b0b4631e18853be0e8302db5b8db；completed a93651e112964745c52b18e5223868cc1b3b68f7b5c7e046ab30a2ad60e8c6f8；user-service-final 28b60cc041bd30f25d6745ce1777bb2bf545713736b56b9669e206415c15cf15。

原全量两项完成，整体accuracy failed，未测性能。用户追加11题65536补测已按依赖启动，单列diag002，不覆盖原正式成绩。保留唯一监控至补测终态。
