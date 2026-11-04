# accdiag-024：C64首Prefill实际设备输入、逐层输出与logits

2026-10-18用户明确授权：仅8010补埋点并重载一次，C64受控复现总请求不超过128；保留i64，首次异常保存原始输入/映射/逐层输出/logits/回复/token/完整可读日志，不影响8035，不跑全量GPQA。采用inference-accuracy-diagnosis及inference-accuracy-evaluation `minimal-regression`，覆盖accdiag023缩窄的首Prefill执行边界；旧正式acc015164/198 failed-score/no gate不改写，不叠加性能优化。

## 冻结对象与门禁

PPU-07、模型容器qwen3.8-flash-opt-ppu07-20261015、8010物理8–15；旧API2623908/start494912777/argvSHA5744d99971adc1f0e9c1885acb61cd9910ccc7fd7adb84f33a11d009702c007e。8035物理0–7其他任务，保护4161238/start487889425/argvSHA91849d0b77b52d602a9ffc0ce9dbb608667ce127ce61cc8a0474883e334ffc0c，禁止任何操作。连接校验仅PPU-07，sandbox的本地RPC失败后提权实际inventory验证passed；inventory误附--list与默认--graph冲突，只读工具参数错误，已用无参数inventory确认ppu组。

只读预检：双health200、8010 running/waiting0、无在途accdiag客户端；CASE规范路径owner0/mode0700、空闲约7258GiB、主机可用内存约1.77TiB。重载前再精确核身份、idle、源码/镜像与原mount parity；有漂移或其他负载则不操作。只向当前精确8010 API发一次SIGTERM、等待原树退出，无自动KILL/重启重试，不停止容器。8035全程只读绑定守护。

CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018；D=CASE/diagnostics/accdiag-024-c64-first-Prefill-20261018；R=D/runtime-001。私有目录/opt/qwen38-accdiag024-c64-inputs-20261018，Plugin从当前021-v2真实复制且全部字节相同，仅新观察器。017 Gems index15ddfe41/index_putd8422ca2、QSA M16 3bb3d083、HC/PLE覆盖禁用、模型权重/tokenizer/采样/CLI/设备/黑名单均不变；无vLLM/Gems/共享安装改动。新私有编译缓存与CPU同步/opaque taps会改变编译及时序，不声称等同原正式负载或性能结果。

## 取证设计与预算

复用已核SHA的021-v2观察器（f7c50b23）/017 legacy（e9c633c7）及既有Plugin custom-op taps，不改模型数学。所有冻结opaque request-prefix都捕获第一次computed0 Prefill：actual device input_ids/positions/query_start_loc/logits_indices、实际ngram kwargs、CPU请求行/预期API prompt IDs/请求slot映射；48层的input/post-ple/attention-branch/output完整选中token行，36层GDN before/after与物理状态行、12层QSA operands/选择/有效KV页，首32步及EOS真实logits/prob/noise/RNG。首步若chunked，只与冻结prompt的scheduled前缀比较，不把合法部分Prefill误报为输入错位。保留全部已返回raw HTTP bytes/token与真实采样前缀。

所有捕获按request/step/rank排他落盘，每rank tensor预算256GiB（8rank总2TiB），不复制一份全量focus PT制造额外TB；终态manifest绑定原始PT，另冻完整日志/已有first-state。若超预算或缺输入边界，按观察器异常停补位并记录缺失，不能称完整。既有有效KV mask保留，未写padding NaN不作模型事故。共享pool last-writer与初始状态快照限制明确保留，逐层输出不是全池历史。所有rank实际输入/层/logits各自保留，API原始回复未返回时不补造。

## 唯一请求计划

共128条/并发最高64/零重试：2条C1 doc2 → 8条C8（0/1/2/3/4/5/6/178） → 118条C64持续更替（背景doc0–115共116，doc178早晚2次）。目标seq73在63条真实Decode后投入；seq119晚期保留8个背景供准入，提交前ADMISSION不能替代模型实际绑定。全部prompt精确来自acc015原native samples/保存的API prompt IDs；原temperature1/top_p.95/top_k20/min_p0/presence0/repetition1/seed1234/stop/max60000、return_token_ids/prompt_text不变。图capture两类7/7且2C1实际replay>=2才进入后续。

普通背景答案与gold不同只记录，不改负载；输出空final/提前EOS/60Klength/格式不合法/HTTP失败、目标错答、实际输入或索引/状态/有效KV/采样异常、埋点/保护错误时，唯一现有客户端停补位，在途自然取证，绝不自动恢复/追加/重试。预算未复现则not-reproduced，未实际Mixed或未覆盖大索引如实not-covered，不增加范围。首异常先通知，再补齐冻结；不因冻结需时而迟报事实。

## 执行前命令与SHA

本地/tmp脚本只作为执行副本，复制到CASE/commands同名后远端核SHA。controller显式加载原accdiag022-control.py（f848326c…）的HTTP/取证/保护helpers，未修改原件。四脚本本地py_compile通过；CPU metadata正例/负例/MRoPE三轴检查7项通过，只是mock，不冒充PPU通过。

| 文件 | SHA256 |
|---|---|
| accdiag024-control.py | 673c82f1f41f79a8968c3679b2aa61d7718066f43bc5644f9c53ba992b291923 |
| accdiag024-probe.py | df0dd1050b99bf0d757819270075608a471cbce845401d61f1be3e4d82ae4a46 |
| accdiag024-deploy.py | e3c1c2ce0c81ba80da441bb0c7a4f3ae73a5671157f22ee479651fcf80cb6659 |
| accdiag024-cpu-test.py | 575dc4c2efeb70fe62f1d63dd77e728ef73c118665bc72f983dab8ec67b983b1 |

执行顺序：`python3 CASE/commands/accdiag024-cpu-test.py CASE/commands/accdiag024-probe.py`（CPU-only）→ controller `--case CASE --mode prepare`（私有复制/配置/计划，0请求0重载）→核PREPARED/实际launch/source/diff→同controller `--mode restart`仅一次→`--mode launch`仅一次后台唯一`--mode run`，自动只wait/2C1/C8/C64/freeze，无restart/prepare/重试功能。新请求前写READY/CLIENT_PID/RUN_STARTED/requests SHA，已有任一marker则拒绝重复。终态自然写CLIENT_FINISHED/FINISHED/FINAL_EVIDENCE，无formal gate。复用旧heartbeat ID，仅监控当前run实质变化/首次异常/完成，终态暂停。

当前准备期：尚未修改活动服务、未重载/发请求；下一步按上述冻结命令执行。回退需要另行仅8010重载授权，不自动回退。pr_readiness=experimental-private-diagnostic，不提交/推送。

远端prepare已成功：PREPARED SHA `158ce426d6fbcfbe44c0a0d59da79ffdcba87b88eeb8bc128539fecaf5f6f272`，requests `d54d265fb6d7dcc0278100684eb27a9eb962481356ff94b40e9e24e181145f7f`，probe-config `de030ccc6362ce16c2763151c3404706cf8e0a000307167c86a759f0b0f0ac44`，DEPLOYED `07f9dfd083494683c2d71bff7485042eef094ff07ce43a1ac71e8970bf4a2323`，launch `fca84cf8e11748b9cdaa463a530daa3eb494fff641dcaf1911983675a7fc1cab`。model仍eb9f096d、runner仍c3537353，Plugin真实字节相同，旧017双i64及M16/三仓/engine源码核验passed。实际launch最终PYTHONPATH为新私有024+旧017 Gems，原脚本前部无效旧export被后部明确覆盖（不以旧无效行推断导入）。ppu-smi只见原任务TP8在8–15、受保护TP8在0–7，无额外占用。0新请求/0重载，此后仅执行已冻结restart一次和launch一次。

## 已执行唯一重载与接续

14:57:01+08只对精确旧8010/API2623908发一次SIGTERM，14:57:05原树完全退出，additional_signals=0；同刻启动新私有024服务，未再发重载/KILL信号。14:57:28唯一后台driver/client Host1940573/start502247549已启动，controller SHA同上，14:57:29进入wait，不具备自动restart/重试路径。READY/新API身份、8worker实际probe和graph仍待确认，此时新模型请求0，不提前称复现已运行或通过。

精度minimal-regression完整bundle SHA `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`已inspect/verify核对；首次verify缺receipt、随后inspect仅输出而未生成文件，均为本地工具调用错误，显式保存相同receipt后verify通过，不是模型或远端异常。旧日志的vendor native extension缺失警告为既有fallback环境，当前Plugin字节与原路径相同，不据单条warning声称目标算子命中/失效。

原heartbeat `qwen3-8-ppu07-gpqa-c64`已产品确认更新ACTIVE、30min，名称“Qwen3.8 PPU07 accdiag024 C64首Prefill取证”，只读跟踪唯一run/当前R；禁止prepare/restart/launch/run或额外推理，首次异常/阶段/实质结果/完成通知，无变化安静，终态暂停。尚未READY时仅监控编译/graph，不重复启动器。后续取证与进展继续写同一记录。

## 15:01 READY / 初始护栏进展

15:01:27+08 READY SHA `ace6f3a8e61bb5ba849bbb735e1990741d3ceac3bca4bc28862356edabc3357f`，新8010 API Host1932757/start502245175，argv SHA仍5744d999…；8rank actual runner024 probe SHA及私有Plugin来源确认，两类graph各7/7。RUN_STARTED SHA `a03a304d12ce0af1c3a4a06ab2974dbf35c4510c780b7bf35077eba5c55f2626`，READY时prompt/generation/running/waiting均0，唯一driver1940573同原identity，未另起客户端。

15:02:57快照2派发/1完成/1在途/errors0，仍C1-smoke，不冒充C64已覆盖。seq0 doc2 HTTP200/正常stop/final B，487tokens、think-end位置246、最后248046；raw SHA `b03ad68ac67c2c988a105d9012b0a5f21d5aca5ade9188586172d5e14e5801e5`。两份C1首Prefill8rank均actual-device input/positions/query/logits-row审计issues=[]、48个完整decoder output tap，当前每rank645份PT（部分第二请求sampler尚在追加）；每rank真实FULL replay>=737，IndexFunction/IndexPutFunction verified_i64_load_before_multiply均True。无新FIRST_ANOMALY/CLIENT_ERROR。487与旧021的535不同，仅为不同诊断同步/编译缓存下的观察，不能当同条件数值修复或性能收益；当前只比较本轮两C1的实际tokens。

8035仍原保护实例health200。已有逐层PT需继续按manifest核SHA与对应请求绑定，不能只凭文件数称所有数值都正确；后续C64与目标seq73/119尚待执行，不估ETA。

15:04:01只读快照：两C1均正常B/487tokens、完整token逐一相等，第二份raw SHA `3d86940525d45461e743f9a80cd563638f5f900efdf30ee5b720b7d8a5f18603`。GRAPH_REPLAY_CHECK于15:03:16确认8rank FULL实际replay至少2次，唯一driver已按计划派发全部8条C8护栏；10派发/2完成/8在途/errors0，C64尚pending，不追加或重发。无FIRST_ANOMALY/CLIENT_ERROR，8035原health200。当前logits_indices快照来自prepare返回GPU张量的CPU读取，实际raw logits/prob/noise来自真实采样边界；不声称额外捕获了hidden gather执行瞬间的独立索引读数。后续仅监控现有进程，C8自然排空且无首异常后自动进入既定118条C64。

## 15:30首次故障通知与终态冻结（只读取证，不恢复）

heartbeat首次核查即向用户报告8010故障、8035健康、两C64目标尚未派发，再只读追查原始日志。服务首fatal15:20:17为`TimeoutError: RPC call to sample_tokens timed out.`，安装vLLM的multiproc_executor.py:319–327采用VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS，envs.py:1591–1595默认300；本轮原launch显式unset该变量。EngineCore等待worker共享内存响应超时→EngineDeadError→API给63条请求HTTP500→退出。客户端`KeyError: choices`是解析500 JSON（只有error无choices）的次生错误，不是首个worker错误或模型精度证据。第一排他客户端marker15:20:17.837584、seq40/doc30、请求耗时300.145秒，原件不改写。

此前2C1+8C8共10个实际回复全部正常且gold匹配，10份raw SHA/完整tokens与usage核验通过；C8 doc178最终A/2695tokens，think-end2470/末248046。15:15:17起派发C64初始63条背景，总派发73/全部请求结束73，其中**仅10个成功模型回复、63个真实HTTP500**；不能把progress completed73称为73个完成问题。seq73/119两个C64 doc178目标均未派发，63Decode+455Prefill实际C64不覆盖，无本轮模型提前EOS/reasoning-only结论。

worker在fatal前仍有取证/算子日志推进：8rank最后step8741，actual batch42req/8192tokens/graphNONE，15:20:14仍有layer5 GDN scatter mismatchFalse；PT至15:20:17写到layer6输入。同步CPU拷贝、序列化/哈希和NFS落盘约366GiB，与RPC时限冲突是强嫌疑；直接退出机制RPC超时已证实，但没有单变量去埋点对照，不把原精度异常归为此原因，也不称为新非法访存复现。

8rank均已有52条首输入审计（seq0..51）、issues空，31条prefill-finished（seq0..30）；每rank约10121/10122份PT、45.694–45.704GiB tensor。其余逐层/采样捕获被服务退出中断，缺失必须列明。generic gather/scatter最大3190、stride102400、offset326656000、i64/i32相同、字节[1306631680,1307024896)在27751628800内；20972未覆盖。现有operator mismatch/observer异常0，无runtime/FIRST_ANOMALY或8rank first-state（HTTP故障后worker已退出，不能补造GPU冻结）。

客户端15:20:18自然停止，driver仅冻结已有文件，15:32:54完成且已退出；FINISHED SHA `e8e4562b9b41d48d2eea326c32408574a3f2b8cd65aa72e36102d49b76a4c536`，CLIENT_FINISHED `644b4791836e29fb669f52b8b1e0dfaa9ccde773b0bdd35dd3e299fd2a3588fe`。FINAL_EVIDENCE SHA `342020d681f3c30c384b9e9f4518e4606b1a4af124e937882372fec007bb566d`，81347文件/393445194744字节（含日志副本），终态日志和原8rank文件大小一致，后续独立SHA审计仍需完成。8010已不监听；8035保护PID/start/argv不变且health200，无heartbeat发信号/恢复/补发/新推理。

追加一次CPU/Host只读取证脚本`CASE/commands/accdiag024-terminal-audit.py`，本地/tmp副本SHA `a33a99ce26a3643f88e01a3c7d4ece152ef36e6c00ee858bca5be7c28963f090`。先验证controller/FINAL SHA与driver已退出，排他创建R/post-controller-audit-001；两CPU线程分块重算全部81347文件SHA/大小、核8rank producer manifest及已提交PT、列未提交/可能截断PT与ZIP目录、完整日志尾部、10成功raw/token/真实采样前缀与63error-body。命令`python3 CASE/commands/accdiag024-terminal-audit.py --root R`，无torch/GPU导入/推理/服务操作；只写新的审计报告与进度，不改旧文件。已有目录则拒绝重复，失败不自动修正/重跑。完成后更新本记录并暂停heartbeat，等待用户决定后续取证方式/是否仅恢复8010，当前不得自动重载。

## 终态独立审计完成 / 暂停等待方向

CPU审计耗时329.53秒，全部81,347份文件、393,445,194,744字节SHA与大小零差异。`R/post-controller-audit-001/report.json` SHA `8fa5725a0c42793341df7a323c969917d5bd18817f45391da6937622a3625d62`；同目录`manifest.json` SHA `48ac4d205f05b2368278309d5f56e6845f6c071aaa150a2d7a563b2cc0b6f804`。8rank producer清单与FINAL逐份一致，完整live/frozen events日志相同；10成功API的完整token等于rank0真实non-discard采样前缀，其后的198为post-sampler/bookkeeping尾部，未作为已发API token。63错误原件均实际HTTP500/error JSON，无choices，不误记为正常空final或真实网络超时。

独立审计发现7份未提交PT，保留原件但不作为有效张量：rank0/1/2/3各1份ZIP目录不完整，rank4/5/7各1份有ZIP目录但未进入producer manifest。均在step8741/layer006-input，rank0/4/7为seq35，rank1/2/3/5为seq34。rank6无未提交PT。哈希一致仅说明保存字节未变，不证明这些中断张量完整；后续seq31..51逐层输出中断、seq52..72首输入尚未捕获，目标73/119完全未发。每rank31份完整48层输出只对应首Prefill**fragment**，seq30首采样discard=True，不能当全部prompt已处理或成功HTTP。seq10..29各仅1个实际non-discard采样token；其余缺失最终回复不能补造。

generic gather/scatter实际最大3190/stride102400/i64与反事实i32 offset均326656000、storage合法；packed decode实际device索引最大559。两者均未覆盖20972；最大实际model batch42，C1/C8的8732个FULL回放记录不能冒充目标C64回放。所有已记录input-audit issues和index/state/observer issues为空，但缺少原异常目标轨迹，不能宣布修复、排除原数值问题或推定本次HTTP故障等同旧reasoning-only。

直接故障机制是300秒sample_tokens RPC timeout（高置信）；“所有背景首Prefill大规模同步序列化/哈希/落盘约366GiB导致诊断干扰”有262秒首批取证与后续仍推进的强证据，但未做单变量对照，不宣称其为旧精度根因。精度minimal-regression整体为**execution-incomplete**，没有新formal gate或性能结论，历史acc015164/198 failed-score保持。完整错误链在`R/service-diag.log`，首HTTP标记与日志前缀在`R/first-anomaly-existing/`，原始回复在R各`req*response.raw*`，逐层与首输入原件由`R/FINAL_EVIDENCE.json`绑定；没有故障后8rank GPU first-state，不能称完整全池因果现场。

原driver/API已自然退出，未发额外信号、未恢复8010或追加推理，8035原保护身份与health保持。原heartbeat `qwen3-8-ppu07-gpqa-c64`已由产品确认**PAUSED**。后续建议先将背景初始Prefill缩为轻量元数据检查，仅在实际63Decode+1fresh目标边界捕获完整逐层/状态/logits，避免初始63条同步转储；这属于需再次授权的埋点变更/8010恢复/新受控请求，当前只记录建议、不执行，也不以放宽RPC超时替代原精度根因证明。
