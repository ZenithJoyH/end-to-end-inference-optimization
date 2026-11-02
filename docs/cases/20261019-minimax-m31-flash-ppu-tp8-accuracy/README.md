# MiniMax-M3.1 Flash1019 / PPU-07 三项精度

用户已在minimaxM3.1-opt-20261008启动`/mnt/cpfs/models/MiniMax-M3.1-Flash-W8A8-FlagOS-20261019`。本轮使用现有专用优化容器，只做用户指定的完整三数据集精度，不创建性能实验或更改服务。实际服务MiniMax-M3.1/8035/TP8/maxlen100000，保留用户prefix-cache。

采样temperature1.0/top_p0.95/top_k-1；GPQA198默认18000、Math500500默认28000，ERQA400/30000，并发32/32/16，串行单次执行。GPQA阈值81%，另两项只报告原生分数。preview历史与Flash新结果分开保存；当前尚无Flash分数。

源容器镜像身份和/mnt同映射与既有隔离案例一致并重新检查；权重/tokenizer建立新清单，源码与服务身份重新捕获。-01预检在ERQA私有payload证明里发现旧opt7名字断言，零推理请求，保留失败材料；-02按实际服务名修正，并将launch_config中的maxlen标量归一到实际100000，不改变运行服务。数据和评分器未变。

本地记录：[acc-001](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261019-flash-three-task-accuracy/optimize/acc-001.md)、[state](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261019-flash-three-task-accuracy/optimize/state.yml)。

外部案例：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261019-minimax-m31-flash-ppu-tp8-accuracy`；当前run为`accuracy/user-flash1019-t1-suite-20261019-02`。命令、原生输出和绑定留远端，本地仅保存摘要和SHA；monitor minimax-m3-1-acc-001按30分钟只读监控，整队终态暂停。

启动确认：本轮所有数据/payload与GPQA原生preflight通过；单次三项queue与GPQA原生评测器已启动，Math500、ERQA串行排队。身份与SHA见acc-001/state，尚无新分数。


## 本轮完整精度终态

三项单次全量原生评测及独立证据复核均完成，整队`all-three-native-runs-completed`，无整套重试，未修改服务/源码或运行性能。结果绑定10/19Flash权重、MiniMax-M3.1/8035/TP8/maxlen100000及冻结的当前源码组合；不是preview结果。

| 数据集 | 正确数/总数 | 原生分数 | 判定 |
|---|---:|---:|---|
| GPQA Diamond | 171/198 | 86.363636% | 通过81%阈值；原生gate/check通过 |
| Math500 | 461/500 | 92.20% | 原生分数，无指定阈值 |
| ERQA | 255/400 | 63.75% | 原生分数，无指定阈值 |

GPQA198唯一doc_id（两个filter、396物理行）与Math500500唯一doc_id完整，正确数与原生metric一致；Math500原生generation_kwargs与冻结task/payload proof一致，实际上限28000。ERQA400唯一item/evaluated question_id均匹配冻结集合，原生255正确与63.75%一致，复制产物SHA与原始结果一致。ERQA NUL-only0、原始空响应0、30000tokens触顶8；输出健康单列，不新增分数门槛。

采样temperature1.0/top_p0.95/top_k-1，GPQA/Math500任务默认18000/28000，ERQA30000，并发32/32/16，保留用户prefix-cache。当前模型实例绑定仍匹配、health200。整队终态后monitor `minimax-m3-1-acc-001` 已PAUSED。各native返回码0；不因本轮精度完成自动恢复性能。历史preview记录完全保留，不进行跨权重的软件收益归因。

原生产物根：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261019-minimax-m31-flash-ppu-tp8-accuracy/accuracy/user-flash1019-t1-suite-20261019-02`。整队`result.json` SHA `795197fbdfb697d96b12c6e67e5c0caf91c327e8c80f14a4f6b2a31ad1301efe`。

GPQA原生gate：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261019-minimax-m31-flash-ppu-tp8-accuracy/accuracy/user-flash1019-t1-suite-20261019-02/gpqa/accuracy-gate.json`，SHA `a8f2b84e1e215f5de1b0001924981b76eba4d591476ae8fd19b20ac35fbb9007`。

ERQA原生结果：上述根目录`erqa/native-output/erqa/erqa_result.json`，SHA `5e56d061764d51a075299a45c3fdbd077825369ce4469e7e9f0c9763112756cf`。完整原生result/sample/evaluated与审计SHA见state.yml中acc-001.results；大体积及敏感材料仅留远端。


## diag-001 三数据集错题离线分析

基于这轮Flash原生响应与评分结果，未重新推理、未改评分、服务或源码。此诊断不阻塞已通过81%阈值的GPQA gate，原生分数保持86.36% / 92.20% / 63.75%，监控PAUSED，未恢复性能。

| 数据集 | 错题 | 已核验的主要分布 | 结论边界 |
|---|---:|---|---|
| GPQA | 27 | 16触顶18000：10未提取有效答案、6提取到错误选项；另11未触顶但选错 | 长推理预算/最终答案形成是优先验证点，不能据此保证加长后答对 |
| Math500 | 39 | 仅1触顶28000；39均提取到boxed表达式；5个独立符号等价候选，其中2题检测到指定形式要求 | 不是以长度为主的问题；5候选不能直接认定误判或加回分数 |
| ERQA | 145 | 5触顶且无最终Answer行；140未触顶且最终明确选错；0最终明确正确却判错的观察 | 主要失分不是NUL/空输出或已证实的解析丢分；视觉/推理/数值路径尚未区分 |

GPQA总计22题触顶，其中6正确；10个无效提取项加末尾换行后0恢复，忽略大小写也0恢复到正确答案。化学14/93错（有机化学12/72错、其中10触顶）、生物8/19错、物理5/86错。不能把超长思考当作必然错误，增加生成预算是否恢复正确性需同请求单变量对照。样本未保存finish_reason，不能冒充已观测原始length终止标志。

Math500的原生evaluate先提取boxed，再归一化并比较字符串，并非完整代数符号等价判断。离线重放原生规则复现500/500判分；独立严格LaTeX解析与符号化发现5个等价候选（3个无自由符号），其中2题有表达形式约束，18次解析失败，需逐题核对，未改461/500。错误集中中级代数13题、预备微积分11题，Level4/5共28题；不能全部解释为长度不足，也不能把全部剩余错误都归于模型推理。

ERQA共392题有近末尾Answer行，0个明确正确最终选项被原生规则判错；仅1次最终行与原生提取选项不同，但两者均非标准答案。8题触顶，其中5错、3对；0 NUL/空输出。多视角16/37=43.24%、空间53/84=63.10%，相较Pointing27/34=79.41%、Task Reasoning30/38=78.95%更弱。这只是失分分布，未用同请求可信参考路径对照，不能直接认定模型固有能力、量化或FlagGems算子为原因。ERQA评分器会覆盖raw_answer字段，分析使用真实items.answer；原生parser存在合成字符串优先级隐患，但本轮未证明其造成正确最终答案丢分。

三项日志已检查的traceback/HTTP4xx5xx/连接错误标记均0。API/输出健康正常不等于证明不存在细微数值误差；尚无新的首差异tensor或参考实现证据，不归因编译器/算子。

后续优先级：①GPQA触顶错题保持prompt/采样/服务不变，仅对照生成预算；②人工审查Math五个等价候选及题目形式约束；③选ERQA多视角/空间错题，以同图片、同prompt比较可信参考路径，区分视觉理解、推理与数值偏差。这些是待执行验证，本轮未启动。

最终报告：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261019-minimax-m31-flash-ppu-tp8-accuracy/accuracy/user-flash1019-t1-suite-20261019-02/offline-diagnosis-20261020-03.json`，SHA `c8debbddcdbd11a46b8762ae9f3ca0ed19e8e6bb72c7ac57fdda17963f38c65a`；完整统计与私有样本ID见同目录-02报告，SHA `81f3841440b65baed9958d54558d728fd835a13a07168c537bfc2371b0e484e7`。初版-01只作过程留存，Math filtered_resps含完整回答，不能把其中单词invalid当提取失败；-02已用原生boxed抽取重放修正这一辅助统计，原始评分不变。

2026-10-20请求健康排查见 [reqdiag-001](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261019-flash-three-task-accuracy/optimize/reqdiag-001.md)：根service.log的11处str.get异常来自原容器8035/nameMiniMax-M3.1-new的请求校验，顶层请求对象为字符串触发vLLM第870行无类型保护。真实schema的dict/单JSON/合法salt通过，字符串/双重JSON精准复现；外部真实body未取得，客户端重复编码仅为可复现的可能来源。健康接口200，无源码/服务/模型请求变更，不修改历史三项分数/gate。
