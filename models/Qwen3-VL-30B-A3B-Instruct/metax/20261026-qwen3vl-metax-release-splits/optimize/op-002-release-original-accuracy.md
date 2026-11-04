# op-002：原始发布镜像split0完整GPQA/ERQA

最终状态：两个完整数据集各运行一次，评测已结束，原服务已恢复，监控已删除。发布镜像原始推理源码保持不变/default split0，prefix cache始终开启。

| 数据集 | 正确/总数 | 分数 | 阈值 | 结论 |
|---|---:|---:|---:|---|
| GPQA strict-match | 126/198 | 63.6364% | 64% | 有效失败，无gate |
| ERQA native accuracy | 163/400 | 40.75% | 40% | 通过，0拒答 |

整体仍未满足GPQA阈值，不能晋级正式性能优化。ERQA的native与全部400计错口径相同。原始发布镜像与旧修改镜像split0的198条完整GPQA响应/逐题分数均一致，证明低分现象在原镜像也出现；不是单变量根因或vendor bug证明。

06:56:59UTC已恢复 `qwen3vl-pr943-split1-mx104-20261023:1132797:1130835253`：原split1/prefixON/源码及34个冻结环境键、argv均现场核验一致，唯一模型参数差异为人类批准的 `/data/models/Qwen3-VL-30B-A3B-Instruct/`。当前两rank原native1/MoE/graph16/C8、HTTP200和GPU4/5归属均passed；候选服务停止、控制器退出。恢复服务没有继承或新签GPQA gate。

终审只读回执 `results/accuracy-final-audit.json` SHA481e394a301832fe73c78ae5d91afeb50bbeb9e9572a65126644367903942606；审计脚本SHAe36f57b86ba7ab815af4352229fd971f3278cd3f2d463f5e872a75a835e16b51。完整ERQA结果SHAed063a9b9d31322c65aa76565a791f1720bd7d25ca3720b54cdba61f29284c7b，完整总终态SHA8309b6e521e04cf09ba56f4732327a315bd5e63959a49a9a73e60a1b2ed3ea7d，恢复回执SHA8544635801fb5f5716cf730ad22a4fb17190108c0eb20351694cf6f30c8580f2。原始产物均位于本case远端，后续为过程记录，旧pending/工具incident不代表当前状态。


用户明确要求在新容器保持镜像原始代码/default split0、prefix cache开启，按此前相同配置完整评测GPQA198（64分）和ERQA400（40分），结束后恢复原服务。沿用本地inference-accuracy-evaluation的minimal-regression与formal-gate模式。此授权覆盖本实验，不自动开启性能优化或其他分片。

范围：mx-104，`qwen3vl-release-splits-mx104-20261026`，TP2/GPU4,5/18977。暂时停止的唯一源服务为`qwen3vl-pr943-split1-mx104-20261023`，结束/异常时单finally恢复精确原source1/argv/env/prefixON并核验当前graph/C8/source。其他服务不动。

所有镜像内原始推理文件保持不变，以同镜像无模型只读参考容器的内容指纹核验；保持Plugin省略num_splits→native默认0，不应用旧固定1/旧FVoverlay/兼容补丁。语义启动参数与原配置一致，实际导入用镜像自身/workspace/FlagGems-vllm/src。运行时观察仅通过case外部PYTHONPATH中的元数据工具，观察原函数/原CUDAGraph调用完成，不替换数学调用、参数、模型forward或RNG；完成graph/native/MoE证明后移除观察器再正式流量。

GPQA官方v1评测容器、原始SHA runner、198唯一题/strict-match、C32/taskseed42/requestseed1234/T.7/P.8/K20/max18000；ERQA沿用原flagevalmm、400题630图、C8/T.7/max18000/服务P.8/K20/responsecacheOFF。先做独立来源核验和preflight。两数据集各完整一次，合法低分不取消另一项；缺失/错误证据先恢复并定位，不改阈值。ERQA采集同时兼容有拒答和零拒答分支，报告native分母及全部400计错口径，不重犯无reject_info的采集错误。

已有24项算子参考/graph结果是同镜像组件证据，不能代替新模型服务graph/C8或正式分数。原始数据和所有脚本留在本case远端，执行前归档命令/SHA。当前准备中。

执行前归档prepare_release_accuracy.py SHA1a174f2860541394c65f2dedfd94ffada095e17357e57b88e85c7035f4e6849c，外部sys.setprofile观察器SHA3690594d47b2935814dec17f445bf75e85be0c9b692e42c7b3382d236b28563e；CPU假profile计数/移除测试通过，仅证明工具状态机，不能替代硬件验证。原始runner SHA82cf6e8304cb6f9eb8ca48fe4055f6bbb2054a7b6a90d56de3d6b7a08e90c61e及当前维护工具已部署到本case tools。准备阶段仍不临停源服务。

准备时发现外部环境漂移：原服务argv仍指向/public-flash/models/Qwen3-VL-30B-A3B-Instruct，但该目录在Host/source/release容器均已不存在。原服务仍在运行，未执行任何停服或模型请求。发现/data/models同名副本以及容器/models路径，正只读核验，并已向用户异步确认是否迁移、能否在评测和源服务恢复时使用新路径；回答前所有依赖的GPU/停启工作保持待定。

原prepare脚本在只读采集旧权重路径处退出，0GPU模型启动/0评测请求，未改镜像代码。归档CPU-only prepare_v2（SHA f49eaa7ba18a1b1d34dfb63745a3d06667dcaa5205b55cecf7b167e0dd278103），仅继续评测器/数据来源/原镜像源码参考核验；外部观察器v2仅新增成功返回过滤，SHA0f537115a8fb06f8c5cf9deeb4a311e01784e67db56d4a8dca714a7c6a6c798d；旧脚本保留不覆盖。

用户已确认权重迁移，明确允许本次评测及原服务恢复使用 `/data/models/Qwen3-VL-30B-A3B-Instruct`；其余配置不变。CPU来源准备已完成：GPQA198与历史数据/任务指纹一致，ERQA400/630图/评分源码一致，发布容器四仓库推理源码与同镜像全新只读参考完全一致。新权重路径单独记录身份，不冒充历史分片完整字节SHA已核验，不重绑定旧精度gate。

执行前归档：`commands/accuracy_controller.py` SHA c5ced5af98c89606dd99c72008c8613b317dddfec6d2c25d27b9fa87b9496da0；`commands/prepare_final_accuracy.py` SHA d024b08aa25162fafb4fff7aecf3706e86e9f8a8a532904d166ef337eeb9b741。准备脚本仅核验真实safetensors头/index/文件边界、冻结已确认路径的candidate/restore配置、CPU测试外部元数据观察器及执行契约，不发模型请求。控制器预检当前精确服务身份/空闲/GPU4,5归属/挂载/原镜像源码后才临停；最小验证通过才启动正式评测；合法GPQA低分仍完成ERQA；单finally恢复原source1，唯一授权启动差异为用户确认的新权重路径。推理源码与模型权重不改。

最终CPU准备已passed，已确认13分片全部真实safetensors头/index/tensor边界完整，外部观察器v2 CPU测试通过。监控新建ID `qwen3-vl`，30分钟，仅关键变化通知。启动脚本先保存 `commands/start_accuracy.py`，保护manifest排他创建且校验控制器SHA，只启动此唯一串行控制器；正式运行实例信息以远端manifest为准。

启动阶段发现外部观察器v2在API/Engine及两个worker均安装profile，只有worker会满足移除条件；这属于取证工具作用域问题，不是镜像数值失败。尚无正式GPQA/ERQA请求。归档 `commands/interrupt_observer_scope.py`，精确绑定1804613/startticks1130178528，确认formal未开始后仅发送一次SIGINT，让原控制器自己的finally完成候选停止及source恢复；不得再中断finally/并发恢复。后续修正只在外部观察器中依据原始multiproc_executor的 `VllmWorker-{rank}` 进程名安装，保留所有旧证据，不修改镜像推理源码。

精确一次SIGINT已送达，控制器进入自己的finally；无正式评测请求，启动日志与中断回执保留。外部观察器v3 SHA3fd0869ce613a0b6aa22a4959ce22cbc95a6fa95231ac769e1876ca3b6453b8c，仅原始 `multiprocessing.current_process().name.startswith('VllmWorker-')` 时安装；API/Engine仅写skip回执且不装profile。v2控制器SHA0004cc6801cab747584930a1f22b904d0c6f62d786e580145c31cb2ab0bdd4a4、prepare_accuracy_v2.py SHA11f74e434a5d35dfa6bfec3eb471d111d97e0726c597c2856544ba5785d1d7e8，使用全新目录/配置/日志保留旧现场；准备硬门禁为上一控制器已退出、原服务当前graph/C8恢复passed、旧formal请求0。此修正未改镜像推理代码或数学调用，未改变正式数据/阈值/参数。

观察器v3 CPU作用域测试已通过：MainProcess不安装profile，VllmWorker-0安装，原始native/MoE/graph计数和移除一次均通过；这是工具CPU证明，不代替模型硬件gate。v2排他启动器归档到 `commands/start_accuracy_v2.py`，必须先收到CPU准备passed与上一控制器完整恢复/退出证明。正式两个数据集仍各一次，旧中断阶段计0正式请求。

第一次恢复于2026-10-26T05:12:54.889297UTC passed，源实例1116298:1130210239，source1/prefixON/新权重路径/原源码及graph16/C8均已核验；对应回执 `results/source-restored-accuracy.json`。该实例随后供新控制器串行临停，不能作未来恢复证明。v2准备passed，旧控制器退出且旧formal请求0，v3的CPU作用域测试也在远端passed。当前唯一v2控制器1827843/startticks1130239517，05:14:08.618022UTC启动；`manifests/accuracy-v2-controller.json`，当前事件 `logs/accuracy-v2-events.jsonl`。监控 `qwen3-vl` 已切换到v2当前终态，保留旧工具incident不当作现状。

v2新服务实例 `qwen3vl-release-splits-mx104-20261026:13908:1130242847` 于05:14:41.927082UTC启动，原服务串行临停。运行证据确认VllmWorker-0/1（14337/14338）安装v3，MainProcess13908/EngineCore14127跳过profile。非worker各出现一次重复写 `probe-skipped` 的FileExists诊断回执（外层嵌套import返回再次尝试skip），错误只被工具捕获，无profile安装/无数学改动/无异常传入模型；两worker无此错误。保留原回执，不将它当模型精度失败，也不为此重复服务。原始镜像FV实际import路径 `/workspace/FlagGems-vllm/src`，prefixON和全部指定启动参数在当前模型日志确认。13分片权重已正常加载，等待graph及最小检查，正式分数尚未产生。

v2实际服务已完成原生graphcapture并正常响应smoke/C8，两rank原native0及原FV MoE返回也已取得。工具未收到pybind11 C扩展的 `c_return` 事件，导致graph replay计数/观察器移除证据缺失；这属于取证证据incomplete，不是模型kernel或正式精度失败；控制器将按原契约自动finally恢复，不另发中断，不重跑任何正式数据。以原始Torch `/torch/cuda/graphs.py` 包装方法成功Python返回（并检查RETURN_VALUE/RETURN_CONST指令，排除异常退出）计数，是不替换数学函数的最窄修正。

执行前归档v4观察器SHA72c0b5489f8ff3fcb4e95c05214872a5c5311fc47fb531d5f9c569feef3bc0fc、真实CPython CPU事件测试SHA c2a6106fc4272bb89c943798548204211287da7ba033dca63b7218202a5df3b0、v3控制器SHA0fb924df9f130146126e069d177a4118fb21bb9a14386cd327e5ae895e7239a3、prepare_accuracy_v3.py SHA cbcca70c6c0e99fdff524e1dc9c700af28ca11e7d7de45a61738b9ba54b66a1c、排他启动器SHA9f5b8f1bfa3971217636de9e55f12660ed7c2bec12771f0149c294e6bfc32ba3。CPU测试通过真实sys.setprofile调用stand-in图方法，验证capture1/replay16/成功RETURN指令/worker限定/非worker幂等skip/自动移除；没有Torch/CUDA/RNG调用。下一次仅在上一源服务恢复passed并控制器退出后启动；每个正式数据集总次数仍为1，不修改数据、阈值或镜像代码。

v2自动finally已于05:26:34.291625UTC恢复source1实例1124611:1130292206，原源码/已授权新路径/graph16/C8passed，控制器已退出。旧v2失败仅缺取证回放事件，0正式请求；没有模型错误或分数。本次v3准备已passed，保持所有原始推理源码，使用Torch原始方法成功Python返回作为实际graph事件；旧工具回执完整保留。当前事件路径改为 `logs/accuracy-v3-events.jsonl`，模型目录 `model/release-original-split0-v3`，正式两个数据集仍各一次；当前恢复终态只看 `results/source-restored-accuracy-v3.json`，不复用旧恢复。

当前v3模型实例49667:1130327011，05:33:28UTC最小验证passed：两rank50091/50092原native0、原始镜像FV MoE返回、各550个成功capture调用和16次成功replay、sysprofile均已移除、API/Engine无profile，smoke/C8与原始四仓库源码/实际启动参数核验passed。minimal SHA13f0babaee7aa554e508dc31348a1a3bb5ef50d91e51dba35eca855f92c2396a，service SHAe0afb748be8d7d6a4fa42f75ffceff634d151df105f0ec15a4bef75f7045256c，runtime SHA9e2d82331182275a8a3efdd152a3e85482de2ccbb5cca9a27e38234343c84dcf。正式GPQA已05:33:36UTC启动，05:33:50原生确认响应缓存0命中、198请求、C32、原T.7/P.8/K20/max18000；无最终分数，随后仍须ERQA400及最后源恢复。冻结执行契约SHAe5700abeb26b375112264d2218f8fa748de245b52e3b9cb713e50fc5f3089014。

05:37UTC监控只读核验：mx-104连接passed，唯一v3控制器1878273/startticks1130323717仍一致存活；原生GPQA进度83/198，无当前v3失败/最终分数/恢复故障，ERQA待控制器串行启动。无重复启动或推理配置变动，正常进度不通知。

06:07UTC监控发现当前正式GPQA已于05:54:08UTC完成126/198=63.6363636364%，低于64分，无gate；合法失败且源码前后未变。控制器按人类要求于05:54:13UTC启动ERQA，不重跑GPQA、不叠加优化。已调用inference-accuracy-diagnosis，issue `accdiag-release-original-gpqa-001`，先归类用户选择的原始发布镜像继承精度阻塞；根因尚未确认，不能仅由此分数归因native/kernel或最新FV。执行前归档CPU/只读原生结果复核与描述对照脚本 `commands/analyze_release_gpqa_failure.py`，不发模型请求、不修改任何推理参数或代码、不干预运行中控制器。失败正式产物SHA ad9c05bd6456bfdc38f64611350fe45e6562f7537c629a466ad7a5cb9dbe1098。

CPU原生完整证据复核通过，audit SHA36ed16c7699b7de6027298f2996eca9196eb99fd5b53b90070833e977ad5eb7f，脚本SHAd39a3dfbca03239a7ff4bbdfe08df86d218bcabd8bff7bf3aee4e9b8e16ce7a3。126/198 strict-match与原生metric/全部唯一题/来源/身份一致，评测前后service/repositories/model/tokenizer完全相同，无gate。与旧修改镜像split0相比，198题doc/arguments/完整响应SHA/逐题分数全部一致（126两者对、72两者错）；与历史fixed1相比4全文相同、114两者对、55两者错、17仅fixed1对、12仅auto0对。该对照是描述统计，镜像/库revision不同、权重路径mtime不同且无历史分片完整字节SHA，不能宣称单变量根因已证或复用旧gate；但明确原始发布镜像本身也未达到64分，并非仅新环境才观察到这组低分。最小graph/C8通过不豁免正式失败。

当前按请求继续ERQA，控制器PID/ticks一致存活，native metrics running8/waiting0、generation_tokens857621、prompt_tokens145439，未见当前失败/最终ERQA结果。根因confidence unconfirmed；未执行额外模型请求/代码修复/GPQA重跑/性能测量。所有当前score/gate只属于此次测量实例；最终仍需source-restored-accuracy-v3当前恢复证明。

06:37UTC监控只读核验：唯一v3控制器PID1878273/startticks1130323717存活且一致，ERQA逐题文件308/400（308份均可解析，仅进度，不是最终计分/完整集验证）。native日志无Traceback/ERROR/TimeoutError标记；metrics running8/waiting0，prompt352631/generation1316374较前次增加，任务持续推进；无当前终态或恢复失败。不重复通知已报告GPQA失败，不改配置、不重复启动，继续现有ERQA→单finally恢复流程。

07:07UTC监控读取当前完整终态：ERQA于06:53:05UTC完成163/400=40.75%，0原生拒答，native及全部400计错口径一致，达到40分；GPQA仍126/198=63.6364%<64，整体正式精度失败，无GPQA gate。控制器已退出，06:56:59UTC源split1当前实例1132797:1130835253恢复回执passed，prefixON/已确认/data/models路径/原源码及graph16/C8声明成立，待终端现场复核。执行前归档 `commands/final_accuracy_audit.py`，仅CPU/只读重新核验ERQA400/来源、发布镜像原始代码前后一致、源当前精确PID/ticks/全部冻结env+argv/graph16+C8及HTTP200/GPU归属/候选停服，无新模型请求，不重跑任一数据集。
