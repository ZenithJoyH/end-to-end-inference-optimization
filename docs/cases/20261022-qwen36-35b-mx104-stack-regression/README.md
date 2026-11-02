# Qwen3.6-35B / mx-104 整理与迁移完整回归

**当前补充（2026-10-26）**：后续原生C64的PR638+FGV MoE组合曾独立通过160/198；最新用户请求GEMM1/2配置搜索已完成53组初筛、12项新进程复核和14项完整MoE。BF16目标M64两阶段确认1.35x/1.07x、M8192确认3.51x/1.13x；完整MoE收益依合成路由而异。候选随后已按用户要求写入当前B私有FGV算子文件（c4673a），新进程选参通过；GPU4/5当前手工服务保留未重启，新配置待重启加载，未测候选模型端到端或新GPQA。见[配置实验](../../../models/qwen3.6-35b-a3b/metax/20261022-qwen36-35b-mx104-stack-regression/optimize/fgv-moe-gemm-tune-001.md)。下文C32事故、旧监控/服务及早期状态作为历史记录保留，当前事实以结构化state和实际进程为准。


用户要求验证MoE源码归并、FlagGems-vllm editable安装、Plugin release/0.2迁移及采样导入修复未退化。完整GPQA已核验：基线160/198=80.81%，候选147/198=74.24%，低13题/6.5657个百分点，未达到冻结门槛，未签发gate。当前正式性能阻塞，按精度诊断Skill执行B/A/B同请求对照，根因未定。性能baseline-01因P4K预热spread18.26%超5%、P1K延迟波动而incomplete，11轮保留。

源容器qwen3.6-35B-verify保留；由其有效writable状态快照建立A/B私有回归容器，镜像来源、同挂载、四包5754文件起点一致通过。A按已保存原始字节恢复Plugin d1653d9和FGV普通安装，B保留整理结果。GPU0/1、TP2、模型权重/Tokenizer相同。

完整精度GPQA198；候选阈值已冻结为A1原生精确160/198，不放宽。性能覆盖P1K/P4K/P16K/P32K、D1K/C64/N128，每角色2个独立服务，每实例4预热+3正式，吞吐下降不超过5%、TTFT/TPOT/ITL上升不超过5%，回退漂移不超过5%。所有测量保留。

用户[飞书参考](https://chitu-ai.feishu.cn/wiki/ElUGwY9zsiBCwrk5pWfcE5Q0nue)已读取：TP2/BF16/C64/FULL_DECODE_ONLY及MetaX优化环境。统一context69632容纳最长2891 prompt+65536生成预算；统一MBT8192，prefix cache关闭。

- [结构化状态](../../../models/qwen3.6-35b-a3b/metax/20261022-qwen36-35b-mx104-stack-regression/optimize/state.yml)
- [完整实验](../../../models/qwen3.6-35b-a3b/metax/20261022-qwen36-35b-mx104-stack-regression/optimize/regression-001.md)

远端证据根：/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression。

按用户要求，heartbeat `qwen35b` 每小时检查并接续回归，完成后停用。当前基线FGV未加载，实际MoE走Plugin→FlagGems通用实现；安装一致性与内核运行覆盖分别记录。

性能基线的11轮全部请求成功，但P4K预热不稳、P1K部分延迟波动超限；原始数据全保留，不能据此归因迁移退化。详见完整实验及结构化状态。

精度事故accuracy-regression-001已冻结原生results/samples/身份/SHA；两组198题doc/prompt/target/生成参数完全一致，26题对变错、13题错变对。候选单请求同seed三次输出相同，有限B/A/B作业accuracy-repro-bab-001在原A及重新启用B上继续三次同请求。C1诊断不能替代C32完整gate；未修改优化逻辑或vLLM。详见完整实验。

05:04更新：C1 B/A/B已全部完成，九次全文一致；只证明C1未复现，未解除完整精度失败。已冻结并启动固定8题、每臂3次的C8 B/A/B有限作业accuracy-repro-c8-bab-001，保持原生prompt/采样/生成预算，逐组核验实际8请求并发，保留全部结果；若仍无差异再进入预声明C32。状态以远端continuation实际phase/current_job为准。

06:06更新：C8三臂72响应全部核验；每题在每臂三次全文均不同，原环境自身也波动。按原生strict过滤器离线重现原全量160/147后，固定8题三轮答对数为B[7,8,6]、A[6,7,6]、重启B[7,6,6]。这不是完整198题分数，也尚不能解释少13题。已转同题同seed的C1/C7/C8各三组诊断，保持服务/参数/源码不变；正式精度门禁仍失败、性能阻塞。

06:20更新：同题矩阵48响应完成，C1全文稳定，C7/C8分别11/19种全文。空闲期CPU/GPU0原生指数RNG及均匀概率采样组件对照可重复，未复现基础RNG问题，但未覆盖真实服务generator状态。已启动同题C7三组的原生logprobs观测作业accuracy-repro-logprobs-001，用于定位首处分歧；未修改采样参数、源码或完整门槛。

后续更新：C7相同源码/服务/请求字节的“自由→排队→自由”63响应已完整核验，全文分别8/1/14种；排队21次全文和完整报告概率均相同，撤销准入控制后差异返回。准入相关重复性现象已复现，但完整少13题根因未定。当前唯一作业accuracy-admission-parity-001按同一受控准入比较原A/候选B/重新启用B的C7/C8，仍为单题诊断；完整147/198门禁未恢复，正式性能阻塞。


最新进展（2026-10-23T03:12:17.161836+00:00）：受控同题C7/C8的原A、候选B、重启B全文与完整报告概率序列全部一致，独立核验135响应、90组管理命令回执。该结果未推广到异题：固定doc0..31的三轮C32共96响应全部有效，原生strict答对26/25/24，仅2/32题全文可重复。完整候选147/198仍低于160/198；根因未定，正式性能继续阻塞。

用户已明确授权临时仅增加原生profiler配置并恢复。有限作业accuracy-execution-profile-001已启动：candidate-01-r4按精确绑定停止，candidate-01-r5正加载；两轮固定C32各采前128 worker steps，结束或失败后finally恢复candidate-01-r6原冻结参数并重验graph/C8/源码与真实路径。当前无trace通过声明，不改任何优化源码、模型、采样参数或门槛，源verify及GPU2/3保留。原生工具未覆盖；独立profiler脚本、授权、配置和执行清单全部先归档并核验SHA。


临时观测实际启动核验（2026-10-23T03:16:05.317017+00:00）：candidate-01-r5已通过graph两次replay、C8和完整manifest核验，manifest SHA7ee808dbab8ececaf6a9334e386eb321e30b2a807a90b1f4ba69f56fa556fc93，qualification SHAb3d0bbd50870d22f9b3949f27131ba1fe9e75aba040e2ecc5a1a5fd4b4a9cd3e。控制器PID/starttime匹配，原生start_profile返回200、pause/resume恢复回执通过，当前未暂停，真实running32/waiting0。首轮已出现两个rank命名trace文件，但64请求尚未完成、完整trace有效性/第二轮/原配置恢复仍待有限控制器完成；不得据文件存在宣称采集或回归通过。小时监控保持ACTIVE并更新为此唯一作业。


最新状态（2026-10-23T03:55:38.580896+00:00）：首轮32响应与两rank各128步已由plugin-phase-verification-v2.json独立核验（SHA95e7aeec077b89350bd9338fe7cf5d44b2bc3119ae3340dde067ca573dcaab50），每rank shortlist准备/散射各128、graph126、GDN chunk60/packed-decode3780，实际采样优化命中仅属于此观测窗口。共享盘mtime与Host有约214.8秒时钟偏差，已用新文件/原生export、trace base+CPU ts、正确rank/PID和每轮管理回执校准交叉验证，未改任何文件时间或阈值。原001时钟失败、followup守护退出、002错启动器0请求均保留；r6和r8原配置恢复/graph/C8/源码路径验证已通过。

唯一活动作业accuracy-execution-profile-003已启动，真实首次创建r7且控制器身份匹配，目前服务加载/资格核验中；它只采剩余第二轮32，finally恢复r9原冻结配置，累计授权上限64不扩大，首轮不重跑。当前尚无第二轮/最终r9恢复通过声明。完整候选147/198仍低于160/198，无gate，正式性能继续阻塞，小时监控ACTIVE已切003；不重放旧失败或启动额外客户端。


## 两轮取证/恢复最终核验与规划复盘 regression-planning-001

证据截止2026-10-23T06:00:21.307938+00:00。综合报告`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/accuracy-diagnosis/accuracy-regression-001/profile-comparison-001/comparison.json` SHA4763b4ce64797265b702f1eb3bb35f899cea5d968a63d6a9a2fb474ab0e48734：两轮64响应、4份rank trace、全部管理命令/恢复回执、原HTTP字节和源文件校验通过；同32题仅4题全文相同、28题不同，原生strict分别24/32和26/32（仅诊断，原完整160/147逐题再次重现）。两个rank各128步都执行shortlist准备/散射各128次；后126步各有graph replay、packedGDN。实际新请求分组24/8→23/9，采样topk输入首batch24→23，embedding8192+2980→8192+2979，表明现准入控制没有固定执行分组；new/cached不是纯阶段token计数，具体doc归属/完整少13题根因未定。

最终服务candidate-01-r9恢复原launch v2，profiler=None，fresh RPC无hooks/proxy；与原r4除instance/runtime证据外全部manifest字段相同。fresh runtime SHA8a217f4baef2921b29c3a85df2e153871075704062e16dbc04298d57f79eb7a5，native offline scoring SHAbfe54ca2709629b5b7bbd6e84ebb8a2f2de0772147e12e1e92bb156fec1d143f，最终restoration SHAc4c0c2a659717671db2067c955873aba0640816afbcab358db86bc0eb1fefe03。没有重跑首轮或超出64请求，旧001时钟/阶段接口失败、followup守护失败、002启动引用0请求失败均保留。FGV两rank仍未加载，editable安装一致性不代表其内核覆盖。

复盘结论：保留原整理/editable/release0.2/采样生命周期组合，未在回归中叠加优化逻辑；完整147/198<160/198，门禁失败与正式性能阻塞不变；四正式场景均无有效累计A/B收益。首要下一步是只读核对原生入队确认和实际请求状态推进，准备可审核的确定准入/完整198方案；现R9日志未见Added/Received，不能臆造队列回执。第二方向只读对比A/B实际加载函数/dispatch及partial-prefill/cache/generator边界；不能用RNG单独解释此前RNG前raw概率差异。无稳定A/B区分不归因迁移，不改采样数值实现；任何必要正式workload/并发/契约或新启动观测参数变化必须明确方案并获相应授权，不能默改C1或挑最好完整重跑。两轮profiler授权已完成，不自动追加第三轮。小时监控继续后续只读诊断与方案准备，状态不变安静。

最新后续（2026-10-23T06:35:53.229150+00:00）：用户授权仅临时原生日志flag的有序准入取证；唯一有限job accuracy-ordered-admission-001正启动r10，按原first32两轮64并finally恢复r11原配置。原profiler授权已结束，不追加采集。新源码审计证明Added仅发送完成、五个A/B状态/采样方法AST一致，但不是队列/设备/13题根因证明。详见当前[实验记录](../../../models/qwen3.6-35b-a3b/metax/20261022-qwen36-35b-mx104-stack-regression/optimize/regression-001.md)，完整147/198<160/198、性能未验收不变。

2026-10-23T06:46:10.160553+00:00更新：原生日志001在0诊断输入时因EngineCore前缀解析守护退出，r11原参数/graph/C8/manifest恢复通过；旧结果保留。修正并在实际日志CPU核验后新002接管，当前r12加载→原first32两轮64→finally r13恢复。已授权64未扩大，正式147<160及性能未验收不变。

最新核验（2026-10-23T07:32:55.982416+00:00）：002两轮64响应/64原生发送与utility回执/真实C32/两rank/源码/strict和r13原参数恢复全部独立通过；两轮32题全文完全一致，strict25/32各一次，原198评分160/147再次逐题重现。报告SHA cba51202c395edc8e54fcc0e8dc7225962b2c0dc6235a9833e55b26a7d2b2275；这只证明固定B32有限重复性，完整147<160与性能incomplete不变。授权64已完、current_job=null，仅继续CPU原生198 transport及launch/gate生命周期草案，不自动新增A/B/完整挑分/profile。

CPU方案推进（2026-10-23）：真实原生客户端的198题payload序列化、parse/cache/usage/回填映射，在fake HTTP原生rolling与32×6+6 transport原型之间完全一致，缺发送回执/屏障失败停止守护通过，0模型请求。报告SHA3710f807b1af3e6cb7b3dbc531677df3b2fcbd36371a73c4c60192659a4130e3。实际context是JsonChatStr单字段NamedTuple，len均1，本任务保持doc输入次序；已纠正此前按通用注释推断的prompt字符降序。live driver、原生CLI/provenance与失败sidecar尚未接入；日志与无日志launch的gate不能静默转移，冻结工具也不接受未记录的新backend。继续准备可审阅方案，不启动新诊断或正式评测，原147<160与正式性能阻塞保持。

### 新授权有序B/A/B定位进行中

用户允许相同有序准入比较base与当前候选，并在稳定差异后单变量回退。唯一accuracy-ordered-bab-001已启动：B-r14→A-r4→B-r15，每臂两轮原32题，共192，最终恢复B-r16原启动配置。当前仅第一B加载，无新结果；既有完整147/198低于160/198门槛仍有效。临时日志在新授权内，vLLM/模型/门槛保持；完整记录见模型案例optimize/regression-001.md。

### 有序对照中断已处理，接续剩余A/B

旧BAB001在B64后因清单采集器默认目录的同名namespace遮蔽而中断，A诊断0；只修观察层Python -P后原r16恢复和源码一致性全部通过，未改vLLM。B64独立原生strict25/32两轮，32篇全文重复。新remaining001仅接续A/B128、引用旧B64，总192不变；目前A-r5清单/graph/C8过并进入首轮，最后自动恢复r18。仍无稳定A/B差异，单变量回退待结果，147/198<160/198门禁不变。

### 有序B/A/B192独立完成，固定32未复现迁移差异

32题在B、base、重新启用B各两轮六份全文均一致，原生strict六轮25/32。192响应/Added/有序屏障/两rank与恢复已独立通过；r18恢复原参数，无日志/profiler/hooks。报告SHA96d4db976123c3ef06228466cf3afb13ba4f64188edfaef465e07f00903c86d2。原160/147完整结果有效，尚无门禁或根因结论；单变量代码回退未开始。下一组按持续授权覆盖原26失分题并加入6逆向题，以同有序C32进行预声明B/A/B192诊断，详情见optimize/regression-001.md。

### 原26失分题有序B/A/B完成：未复现稳定迁移差异

预声明32题（原26失分+6逆向controls）三臂各两轮192响应已独立核验，六份全文逐题一致，native strict每轮24/32。原26失分题每臂19对7错，稳定A/B差异0，故未触发代码单变量回退。r21恢复原启动配置/graph/C8/加载指纹/no profiler hooks/unpaused通过，FGV两rank未加载。verification SHA9a9658a4acbfc88d05808d0cb79f68e9dd0f4eb79c3830b3590a1bb548d2ec43，原完整160/147逐题再次重现且门槛保持。

两组有序cohort共有10题在同body和稳定源码/launch身份下，换cohort后全文10题变化、strict3题翻转；每组内A/B仍相同，支持执行上下文敏感性而非稳定迁移差异，但原少13题的具体原因未证实。当前无活动job，继续只读/CPU形成完整198可审阅方案；四场景正式性能没有有效累计结论，不能宣称整体验收通过。

### 2026-10-26 PR638应用及单轮正式C64结果

用户要求应用PR638后64并发全量正式评测。精确head3e04e696单文件替换，新r31 graph/C8/长C1通过，原native GPQA198滚动C64独立strict154/198(77.78%)<原160/198，396filter/5756源码/当前r31身份与恢复观察均通过，证据有效但无质量gate。之前原C32160/147及应用前C64161保留；一次比较22对转错/15错转对不足以确立PR因果，未盲回退/新请求/挑分重跑，当前保留PR。独立verification SHA c9752ab3778ff11557867230eb344c2dd5014dddc66a13d8af1d9799652cd033，新issue accuracy-pr638-001；见模型案例optimize/pr638-001.md。任务和独立审核完成，监控已删除，正式性能继续阻塞。

2026-10-26用户更新PR验收依据：NV原生参考77.53%，本轮77.78%获明确接受，PR638已正式Ready for review。旧160门槛判定/原生回执不追溯覆盖，未重跑或新签gate，详见optimize/pr638-001.md。

### 2026-10-26 按用户要求切换MetaX MoE到FlagGems-vllm

当前专用B/r39已在`TritonExpertsFL.apply`非LoRA分支将`nvidia`扩为`(nvidia, metax)`并调用`flaggems_vllm.fused_experts_impl`。实际callee为私有MetaX backend，两rank各32条PID绑定原生日志、graph两次replay/rank、C8 8/8和长C1=42均通过；真实GPU15数值/数值graph两次replay通过并复用。其余5755源码、PR638、模型与vLLM保留。此前观察脚本因日志抑制/缓冲误拒绝并安全恢复的全部失败记录保留；最新启动仅显式增加`PYTHONUNBUFFERED=1`使库输出可在线核验，推理argv和其他env不变，新gate须绑定准确新launch。

唯一followup003已提交原生滚动C64/full198，threshold0.7753在新流量前按用户NV77.53参考冻结，分数尚待完成和独立核验，不复用旧分数。不会自动跑性能或推送代码。当前状态及完整命令/SHA见[当前MoE实验](../../../models/qwen3.6-35b-a3b/metax/20261022-qwen36-35b-mx104-stack-regression/optimize/fgv-moe-001.md)。

2026-10-26 MoE切换完成：当前B/r39原生滚动C64/full198 strict160/198（80.81%）独立通过，达到预冻结NV77.53%参考且等于原160绝对门槛；新准确启动身份gate验证通过。198unique/396filter、全部5756源码/当前r39两rankFGV函数与原生路径、graph/C8/长C1、nohooks/unpaused均通过。verification SHA2bec056ec4dd667f3e501fbee106ba079bd874de612890d424a8daa19c3c12a8，gateSHA4f23550de1ae0d062dca376adfdd049f307f9813f7b280dfdc91113632bcf42f。只运行一轮，原160/147/161/PR154保留，未解释原C32差异或宣称性能收益。当前已保留新MoE路径/PR638/显式无缓冲启动身份，监控已删除，不自动性能或推送。

Plugin维护更新：当前B的release/0.2已从7cb5599更新至1bc0c77（已合入PR638），517工作区文件字节不变，保留所有本地修改和FGV GEMM配置；399源码语法和真实Conda+MACA导入通过，未重启/新评测。详见[plugin-update-001](../../../models/qwen3.6-35b-a3b/metax/20261022-qwen36-35b-mx104-stack-regression/optimize/plugin-update-001.md)。

当前B冗余修改清理完成：回退未消费env声明、旧Plugin MoE GEMM2/activation fallback改动，旧配置表归档；保留当前FGV完整调用分支AST、FGV GEMM/GDN、sampler和PR638。399语法及真实import通过，无服务重启/新模型请求；18135检查未运行。详见[plugin-cleanup-001](../../../models/qwen3.6-35b-a3b/metax/20261022-qwen36-35b-mx104-stack-regression/optimize/plugin-cleanup-001.md)。

Sampler interface migration: current B now uses Plugin registration -> FGV apply_top_k_top_p, retaining native sampler/RNG and all GDN/tuned MoE source hashes.44 numerical/6 lifecycle, actual-wrapper/RNG/fallback and3 same-graph classification replays passed. Top-p-only remains explicit native fallback after a threshold-rounding mismatch. No model service/full GPQA/newgate or E2E result. See [sampler-fgv-001](../../../models/qwen3.6-35b-a3b/metax/20261022-qwen36-35b-mx104-stack-regression/optimize/sampler-fgv-001.md).

2026-10-27 容器环境清理完成：同名B已替换为保留全部私有源码的独立快照，13项Docker预设和5项bashrc SDK导出移除，必要12项变量集中到原启动脚本。5878源码指纹、挂载和全部推理参数一致；GPU4/5、8020、opt2保持。旧容器停止并以`qwen36-35b-regression-b-20261022-env-backup-20261027-001`保留，当前未启动模型。独立回执SHA aa7e8de02db1835d9a0cfc608761cf039e13cbe85f26ffe8556e6a7ba7d94026；新容器/环境不能复用旧精度gate。详见[env-cleanup-001](../../../models/qwen3.6-35b-a3b/metax/20261022-qwen36-35b-mx104-stack-regression/optimize/env-cleanup-001.md)。

2026-10-27 按用户指定MetaX文档完成当前B的FlagTree源码安装：官方main@fe1d24f6，FlagTree0.7.0+metax.gitfe1d24f6/Triton3.6.0。原运行包备份保留，5878推理源码/启动脚本不变；GPU4向量3dtype、BF16dot与旧版逐位对齐、graph2及栈导入通过。严格数学参考探针发现新旧均有相同9.54e-7误差，所有失败/回退/三方矩阵保留，不是新增回归。独立306个RECORD哈希及wheel来源核验通过，verification SHA60a4fd65ac9e90cdcbe160ae9be480c3af94eb6bf6442edc15f0fdcd804a91eb。模型未启动/未跑GPQA/无新gate；详见[flagtree-source-install-001](../../../models/qwen3.6-35b-a3b/metax/20261022-qwen36-35b-mx104-stack-regression/optimize/flagtree-source-install-001.md)。

2026-10-27 用户启动服务失败已定位：共享专家gate的ATen linear进入Gems linear_kernel，BF16 tile128x1x64在MetaX MMA layout/pass中失败。黑名单mm/mm_out不覆盖独立linear。原始TTIR新/旧/新纯编译均失败（新版MACAPipeline断言，旧版LLVM lowering），不能简单归因升级；尚未改黑名单/回退/重启。当前服务已退出，完整服务与新gate仍阻塞，详见同一FlagTree安装实验的启动诊断。


2026-10-27 按用户要求升级当前B的FlagGems至官方master a456722a（5.5.0.dev0+ga456722a1），旧源码/安装备份保留。原N1 linear编译错误由上游MetaX小维度AABS保护解决；M8192/64/1数值及限定graph2通过。完整服务在GPU4/5、8020/opt2启动成功，11/11 graph capture、health/models200。新版另有CPU RNG clone兼容问题，B/A/B定位后只在原脚本黑名单追加clone，模型argv不变，5878保护源码/FGV MoE调优/GDN/采样器保留。独立verification SHAadad81d581c1abfa3bc52302624502d0a9c8aac247bab3afc146c8e2006ee7ec；无新版GPQA/性能/gate，历史失败保留。详见[flaggems-update-001](../../../models/qwen3.6-35b-a3b/metax/20261022-qwen36-35b-mx104-stack-regression/optimize/flaggems-update-001.md)。


2026-10-27 opt1→opt2性能gap已限域定位到采样算法迁移：同当前依赖的黑/白/黑P1K/D128/C64/N64短程输出920.39/933.43/911.52tok/s，白名单仅恢复1.91%，回退漂移-0.964%。六份两rank实际C64 Decode trace的全词表radix每步约7.84ms；固定M64/V248320/k20/p.95/temp.6的新/旧shortlist/new完整API微测10.58/2.30/10.58ms，掩码与保留值两组输入均相同，新增约8.28ms吻合历史ITL增长。尚未改生产代码或完成修复后原workload复测；9667源码字节不变、原黑名单服务/完整env/argv/cwd恢复且健康。独立SHAad414302a63462add2fa590f705ffa879ce8cdce6fe57b42f81a457e7d631d1e；全部预热/计时/失败和用户partial保留，详见[blacklist-gap-001](../../../models/qwen3.6-35b-a3b/metax/20261022-qwen36-35b-mx104-stack-regression/optimize/blacklist-gap-001.md)。

2026-10-28：按用户要求保持0.9恢复服务并做有限内存取证，64文本+96图文+1快照请求全部完成，未复现OOM。实际graph后物理占用94.807%、图文最少空闲约56MiB；KV常驻20.8GiB，预算计非Torch增量，分配器inactive split峰值1.276GiB。原MoE256MiB OOM直接触发点保留，唯一历史根因未隔离。取证钩子已移除，原参数服务恢复并两C8通过，6850生产源字节未改，不跑新全量/性能。详细证据在本案例optimize/erqa-oom-probe-001.md与远端同CASE/operator/erqa-oom-probe-001/followup-001。


2026-10-29 显存修复短程：保持0.9，KV预算计入初始non-Torch占用；仅预算修正版保留，原C32窗口32图与35,112 rawpatch原生视觉边界零OOM，独立报告SHA9d88ecf7d18840dfa4705131b294176e79b505e8c5cac017f4c2197726e7b5b6。图像拆批因冻结数值门槛失败已回退，未全部完成；MoE/GDN/采样保留，无全量重跑/性能/gate。详见当前模型optimize/erqa-memory-fix-001.md。
