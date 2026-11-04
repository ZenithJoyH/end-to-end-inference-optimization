# 20261018-prefill-quantum-41 固定MBT的长Prefill请求配额

- 当前状态（2026-10-18 23:18）：逐step/16rank取证完成，确认前端时序→异步成批/接纳窗口→含Prefill step碎片化的放大链，尚未孤立为某个算子缺陷。原参数服务恢复并通过终态审计，源码/脚本未改、无新优化安装。此前Mixed原生比较passed（吞吐+5.3491%）、Decode守护incomplete保持；不追认整体晋级或正式验收，监控暂停。分类`framework`；父场景`p32768-d1024-c64-n128`。

Prefill三臂完成后曾晋级Mixed/Decode。首轮continuation因回退Decode预热不稳定停止并恢复。用户随后授权增加预热重测全部三臂，已独立完成：确认P32768/D128/C64/N64缩减Mixed增量收益约5.35%，Decode尾延迟波动与回退漂移仍妨碍守护通过。原参数已恢复，交付脚本未改，监控`glm-performance-20261018`已暂停；没有新的正式四场景或精度gate。

## Decode波动诊断（2026-10-18 22:24，离线完成）

仅分析`mixed-decode-02-w8-r3`既有33轮Decode（包括全部9轮measured）的逐请求原生结果、客户端计时源码和既有服务日志。命令先保存到`commands/analyze-decode-variance-v1.py`，另存`decode-variance-20261018-01/analysis-v1.json`；不发模型请求，不改服务/源码，不覆盖原始证据，不把原guard改成passed。

事前固定诊断定义：客户端首token相邻间隔>80ms分组（只是可见返回批次，不证明GPU batch）；>200ms为长ITL；共同已接纳窗口为最后一个首token+100ms至最早结束请求-100ms，同时计算0/500ms边界敏感性。对比填充时间、此窗口内ITL和结束尾段，核验原生SHA、512输出/511间隔及TPOT公式。所有指标仅是客户端诊断代理，不冒充设备时间或新增正式门禁。现有线索：请求发送跨度很小，但首token分批返回，早期请求ITL夹有数秒停顿；待量化后再判断服务稳定性边界。

主分析命令SHA `7c495fd3af17258671feda36b3fd6be72b7e5a2c931405172a27a6bd7d7501e8`；补充命令`commands/analyze-decode-variance-context-v1.py` SHA `f831eb81f1ae9760acc2fe4b0d1a2f5347821d2b3379c9fe4a97a14e68defaab`，执行前保存，补充核对启动前后日志、冻结客户端源码身份和全部阈值引用，输出`decode-variance-20261018-01/context-v1.json`，不覆盖主分析或原门禁。

### 诊断结果与原因

33轮原生raw/validation/output SHA全部有效，共2112请求成功、0失败（其中9轮measured、576请求）。全部请求1024输入/512输出，每请求511个可见响应间隔。按当前原生源码重建P99 TPOT，最大误差仅`0.000002282ms`，不支持“计时公式算错”解释；计时源码与三个冻结客户端的SHA一致。

| measured三轮中位数（客户端代理） | baseline | candidate | revert |
| --- | ---: | ---: | ---: |
| 完整批次时长 s | 23.637498 | 23.347452 | 22.942196 |
| 从首个请求开始到最后一个首token s | 5.816413 | 5.634834 | 5.130791 |
| 批次时长减上述填充代理 s | 17.817127 | 17.725506 | 17.811406 |
| 共同已接纳窗口平均ITL ms | 34.921101 | 34.760731 | 34.935963 |
| 同窗口P99 ITL ms | 35.874558 | 35.543820 | 35.644253 |
| 同窗口平均ITL轮间极差 | 0.69265% | 0.74459% | 1.24527% |

基线→回退完整批次缩短0.695302s，填充代理缩短0.685623s；共同已接纳窗口平均ITL仅增加0.04256%。这是不同轮中位数差的描述性对照，不是严格因果分解；不能把它重新签发成原guard通过。边界改为0/500ms结果方向不变，不能据此倒改原测量范围。

关键证据：

1. 各轮64请求客户端计时起点只跨13.623–15.873ms，但首token分3–5组到达。基线measured第9轮为`1/31/32`，约0.355/2.734/5.015s；第10轮为`1/7/6/31/19`，约0.283/0.914/1.467/3.838/5.816s。起点不是服务端到达/入队时间，返回组也不是已证明的GPU batch，但已明确波动落在批次填充而非持续生成段。
2. 33轮合计2073个>200ms间隔，全部始于最后一个请求拿到首token之前；共同已接纳窗口没有此类长停顿。基线第9轮首个请求ITL夹有2.366s和2.281s停顿，其他多数间隔约35ms；后续Prefill/接纳对先开始生成请求的阻塞，是源码与时间线支持的解释，具体前端/调度/设备成本仍待trace区分。
3. 原生`TPOT=(请求结束时间−TTFT)/(输出数−1)`，会把上述停顿计入早期请求；64请求的线性P99实际为最大值的37%+次大值的63%，恰由早接纳、被后续填充阻塞的请求主导。2073个长间隔只占全部间隔约0.19%，因此全体interval的P99 ITL约35–36ms并不矛盾。TTFT P99则主要跟最后一组Prefill/排队走。
4. 总批次时长与填充代理相关系数：33轮0.97791、9轮measured 0.96503。共同已接纳窗口平均ITL在全部33轮为34.560–35.400ms；本次样本没有持续生成阶段的大幅失稳信号。不能外推为长期稳定性或纯GPU kernel验证。
5. 调度源码阈值只在单请求待处理token数大于16384时截断，1024输入与逐token生成均不触发；检查当前scheduler/config及Plugin全部阈值引用，没有发现该短输入场景的其他Plugin分支。因此不能把Decode A/B中位数变化归因为该阈值的直接加速。
6. 三个服务日志均无preemption/recompute/OOM/Traceback记录，ready后无ERROR、compile/capture日志，前缀命中均0。每角色确有1168条相同`fa_utils.py:177` FA2能力导入ERROR，但全部发生在ready前；不能把它们说成“日志零错误”，也没有它们在测量期导致漂移的证据。

结论：**主要是阶段隔离不足：finite-batch Decode专项仍反复包含真实的批次填充/Prefill与接纳波动，不能将其TTFT/TPOT/总吞吐漂移当作稳态Decode算子不稳定。原生计时本身没有发现错误。** 这不是“全是虚假噪声”：突发请求的端到端延迟确实变化，若业务关心此模式，仍应作为框架接纳/调度问题优化。当前仅定位到阶段；没有服务端逐请求到达、每step shape/时长、历史CPU/卡频/后台负载证据，不能进一步断言是客户端发送、前端tokenize、调度成批还是特定Prefill shape成本。

下一最小证伪方案（只记录、未执行）：在原配置采一轮相同突发请求的client send→server enqueue/tokenize→scheduler每step prefill/decode token数与batch shape→worker设备执行时间，按Profiling Skill独立冻结capture与rank/阶段覆盖；profiler-on不计收益。先解释为何返回分组改变，再决定是否需要新的无profiler A/B/R。正式finite-batch测量仍保留整个填充/排空成本；共同已接纳窗口只作为新增诊断视图，不能事后删慢轮、截短正式计时、放宽守护或把旧incomplete改passed。继续增加warmup不能消除每个新burst都重现的填充过程。

证据主报告`decode-variance-20261018-01/analysis-v1.json` SHA `79daa23347088af5b7229973e3019d52d2b3f62f6eb7eb9da682fa2dd727f0e1`；逐请求摘要SHA `692306dd97d57585763601f07ebad6274bfc61a2cd8ba9d005cbb159656fe4a8`；补充报告SHA `f4b3db8729e9f307b5a30b58c034c826b62e8b8eff74a631f503d7dcb32d94f6`。目录位于本文末远端父根，不复制原始JSON到本地模型目录。

本次没有新推理请求/服务重启/源码或启动脚本改动，没有新精度gate或性能通过回执。当前原配置实例`PPU-13:glm5.3-flash-opt-20260911:2485876:504687553`health通过，argv/环境/源码/权重/tokenizer/DB/thead与原配置一致；监控仍暂停。Mixed原生+5.3491%结论保持，Decode守护仍incomplete，候选仍未部署。

## 优化方向与瓶颈依据

### 用户追加逐step取证（准备，尚未派发）

沿用点41，在远端新增唯一`step-evidence-20261018-01`。Profiling Skill显式`capture→analyze`，最小回归Skill显式`minimal-regression`；不新建优化点、不修改已有guard。目标原参数threshold0/MBT32768/maxseq64/TP16/BF16/FULL_DECODE_ONLY/关闭前缀缓存不变，仍为P1024/D512/C64/N64有限突发。统一temperature0、ignore_eos、seed42（runner派生每轮seed），计划2轮预热+3轮非torch-profiler诊断+1轮torch profiler；均保留，单轮180s、总预算2400s，不无限重试。

现有trace入口缺少HTTP接纳→scheduler step的shape关联，需临时runtime hook，采取外部`sitecustomize`按精确模块/方法惰性安装：HTTP开始/首body、render/tokenize、AsyncLLM.add_request、InputProcessor、Scheduler.add_request/schedule、WorkerFL.execute_model/sample_tokens。只记录请求ID、CPU时间和shape元数据，不改变参数/返回值/数值，不保存prompt。worker使用异步CUDA Event对，全部请求结束/服务空闲后query，不注入synchronize；事件跨度包含host launch gaps，不冒充kernel self time。native torch profiler仅前12step、shape开启、stack关闭、ignore_frontend=true，要求16/16 worker及Prefill/Decode覆盖。

所有临时代码保存在本案例`commands/step-probe-v1/`，只在诊断服务追加PYTHONPATH和GLM_STEP_PROBE_ROOT及profiler-config；不改vLLM/Plugin/FlagGems/FlagGems-vllm文件，不安装新依赖，不改交付脚本。无hook时原路径不变、hook幂等；这是外置诊断补丁，`pr_readiness=experimental/not_for_PR`。执行前重新核对精确实例空闲、源码内容及image/mount一致；启动与恢复均做C1/C8、边界与graph replay最小回归；任何异常保留证据，finally恢复用户原配置并核验身份/health。源码/环境仅临时观测差异，不签发GPQA或正式性能gate。

判别规则：若HTTP→frontend/scheduler接纳已明显分散且决定首批shape，则前端/传输接纳优先；若请求已齐但多次不同排程且等待/空隙主导，则调度优先；若相同调度shape设备跨度可重复、而分组改变产生额外Prefill步骤或非线性成本，则shape为放大机制。必须把触发原因与放大机制分开；profiler-on数字不与旧无profiler结果计算收益，缺rank/阶段/关联链则保持incomplete。

执行前保存控制`commands/control-step-v2.py` SHA `30b1c17ab887127748d719499b48c3c87ad882f492d5212088d918365e6555ae`（v1未执行，v2补充总预算准入及允许非worker进程导入worker模块，实际rank仍须16/16执行证明）；probe SHA `4f6f2dfce689eba30cc9f70343af81a0b6f25edc873a08cd707cad522b5b4801`，bootstrap SHA `c8518cb8745d568491d19c8114a534127a04465d2804c96843f8987a77f654a2`。维护版工具原样复制为`commands/step-tools-v1/{vllm_profile,vllm_perf,trace_to_summary}.py`，分别SHA `3fe01b54994189330fa359aba9ac0eaca5bde509177099fe8ccc02bc1c591494` / `d7bac00f99827943cf63eac9cd557c1730bd5e9dcae74dfd1c9c31463a3a2187` / `8197f6a6a6b41516b40f7fc2fc2f9e5d3f47559bf6c0baca5ae6ccc89ac472f4`。先prepare只读核验与新目录准备，再freeze dry-run，最后唯一派发evaluate；新服务变更前将完整launch落盘，异常也进入恢复流程。

本地hook静态契约测试通过：返回值不变、协程转发、重复wrap幂等、schedule前元数据正确；stub不代替PPU验证。完整Skill bundle分别为profiling `c65d7be2635d0850cf7830113f88b0840c5d5b9b5b02ae30328474a34c0fea46`、accuracy `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`。Profiling包缺interface.json，机器selector校验返回incomplete；已明确按完整本地SKILL中的capture/analyze方法和维护版工具执行，不声称接口元数据验证通过。唯一派发命令`commands/dispatch-step-v1.py` SHA `89df5a537933490238c42d8c162db3e954c1f2a812371f4ef4fc897420a3b164`，执行前保存。

22:41首次prepare/freeze与唯一dispatch通过，freeze SHA `c721cd08a64566422ba7170fbe6478b0d8ce5e0a558c9dc7e8b45e918c79f883`、launch SHA `55648242c62fd58ae9f1f9f4f7b199d79e15998d6827de761ea4b7e95f86a52f`。但22:45诊断服务ready后，控制器把预先声明的临时PYTHONPATH差异误判为环境漂移，**在minimal与原生采样之前停止**；旧目录全部保留为incomplete，控制器正在恢复原配置，不伪造trace或自动重发流量。

已保存仅编排修复`commands/control-step-v3.py` SHA `42eb2ea9cda75225d89a7cd7ce919c86c42c72c211ec5d904f265c74ac8b009d`：环境比较只允许PYTHONPATH恰好等于既有probe目录，并额外核验GLM_STEP_PROBE_ROOT恰好指向新唯一`step-evidence-20261018-02`；其他argv/环境/源码等全部严格不变，先保存runtime再断言。须待首次控制器完成原配置恢复及最小回归，才允许v3 prepare/freeze与新派发。复用同一不可变probe/工具，不改数值、workload、轮数或阈值；第一次并无native capture，不拼接失败数据。新dispatcher `commands/dispatch-step-v2.py` SHA `d9b28e653f298b9fb2542ad709d9732a2ca75470770e95890244eefd5504b78e`，分析`commands/analyze-step-v1.py` SHA `a16ffa93931fe5e9fd1d3ef181919aa18a0ff5acbe904133e45d802e2c5922a5`，均执行前保存。

首次控制器22:48:58已确认原配置实例`2499832/505051719`恢复、minimal通过、health通过。随后v3 prepare/freeze通过，freeze SHA `528ca2215f1e622f30206f29a74bb3210a32b37056f601f2066768159fc34362`、新launch SHA `f829e78e59dec3571681c529188ac6d41687a50960ac8e8134289f6c26225787`；22:50:10唯一派发宿主控制器1246967，不重复旧控制器。设备trace离线分析另保存`commands/analyze-step-traces-v1.py` SHA `2d7147d659b07b1f555b9c00402d3894a601eea7767ea5ddf5d32c0091aff6aa`，仅消费新采样，通过rank文件名、逐step标记、CPU runtime correlation到GPU kernel确认阶段，kernel累计时间不作关键路径或收益。

22:53第二次准备仍在minimal/采样前终止：`freeze.json`通过统一写入函数sort_keys重排profiler JSON对象，argv末参数与重新序列化预期字符串键顺序不同；已保存runtime证明所有基础argv/环境/源码及profiler配置内容相同。旧02目录完整保留，自动恢复原配置；这两次均没有native capture，也不是模型运行失败。

先保存v4 `commands/control-step-v4.py` SHA `9954d3d7410216b7cead6a3043f41ab676cc3103a102340ede205332223497a2`，以`check-saved-identity`只读重放02的runtime/冻结契约：仅profiler JSON按对象等值比较，基础argv、精确诊断环境和源码仍严格比较，并加基础参数/额外环境/profiler值/源码四类反例。通过该离线检查、02恢复完成后才使用新03目录prepare/freeze/唯一dispatch；不盲目重复服务测量。新dispatcher v3 SHA `8ea0443b730d9f7a9571a7a3b458d207004e176bfee8f201cef14d30788edd35`；CPU分析v2 SHA `66e1eefabc6684a2794b65700bc3fa9fe529d23dba29ad8a9fc9222fe5de3361`；trace分析v2 SHA `34af4039b62e27fc9a156a11728c4551746946494dabd38945966b1f70c3a198`，均先保存到同一commands目录，模型源码和测试契约不变。

离线正例通过、4类反例全部拒绝。02于22:57:37恢复实例`2512344/505103636`并通过minimal/health。03目录prepare/freeze已通过，freeze SHA `9392e214f30a610a553c7915f940dba83adc3cbab3e3c97fe3c07a5c7b3b5381`、launch SHA `b4973a75f049a2365a7f8448573b9b05b64bc2bc4b8656f7c7656075c910b483`；继续原采样契约，无新的性能或原因结论。

03已于22:59:33唯一派发控制器1447672。23:03:19诊断实例`2519239/505138754`ready，23:03:29 minimal通过，23:03:31确认16worker/1frontend/1scheduler hook active；没有hook控制错误。原生6轮采样开始，尚无逐step归因或收益判定，结束仍恢复原配置。

03六轮原生均完成、384请求成功0失败，23:07:47原生返回0；CPU/CUDA Event缓冲18文件完整落盘，无控制错误。CPU关联报告`step-analysis-v1.json` SHA `1e75fce1a3a24772ed88fea70c27e616ddda62b7d5ffaa2f5b7f63b22a9958de`；trace报告`trace-analysis-v1.json` SHA `b17b7ca993a53cdce7cb0198339fc985f096a25a6d7061def99d9a39bea379d1`，16/16 rank、Prefill/Mixed/Decode三阶段覆盖有效，每rank35441个GPU kernel，其中35405个通过CPU runtime correlation关联step。进一步以trace真实矩阵Input Dims核对逻辑token shape，并按关键算子分析Skill的完整调用边界解释，不把累计算子时间作端到端关键路径或收益。

终态汇总/恢复审计命令执行前保存`commands/finalize-step-evidence-v1.py` SHA `45057ba85581588c015d9e0b99ec28128cf13423284d014a974ab849e13bce76`，只读取既有证据，保存`causal-summary-v1.json`与`terminal-audit-v1.json`；不新增推理请求，不覆盖原completion/guard。

### 逐step最终结论（23:18）

**不是三选一：前端应用接纳/render完成时序是触发因素，异步batch queue的提前排定和step边界接纳把差异放大，不同shape与额外整网执行把差异落实为真实延迟。没有证据表明某个FlagGems算子或持续Decode循环随机失速。** 这里的ASGI入口不是TCP socket实际到达，render时间也包含异步分词/排队/处理等待，不能把它直接归因为tokenizer计算变慢。

| 事前声明的低开销诊断轮（非torch profiler） | round3 | round4 | round5 |
| --- | ---: | ---: | ---: |
| 请求数/输入/输出 | 64 / 1024 / 512 | 相同 | 相同 |
| 含Prefill的step数 | 5 | 3 | 4 |
| 这些step的调度token shape | 1024,3073,4100,32768,24623 | 1024,32768,31777 | 1024,32768,29729,2110 |
| P99 TTFT ms | 6380.672 | 4932.309 | 6030.044 |
| 完整批次时长 s | 24.204642 | 22.677064 | 23.694752 |
| 含Prefill step的max-rank stream跨度合计 ms | 6318.204 | 4872.609 | 5988.212 |
| 后续Decode step的max-rank stream跨度中位数 ms | 34.774361 | 34.736401 | 34.594521 |

三轮prompt总量均为65536 token，没有减少工作负载。stream跨度是异步CUDA Event测得的完整执行跨度，包含host launch gaps及同step的Decode/通信，不是纯Prefill算子self time；max-rank合计也不是严密的全局关键路径。上述是不同派生seed轮次的描述性对照，不是固定prompt干预、因果占比分解或新的性能收益。

证据链：

1. **前端差异跨过调度边界。** 客户端发送起点跨度约15–16ms；ASGI入口跨度round3/4/5为232.479/136.191/135.166ms，前端提交完成跨度418.178/253.559/261.629ms。round3在279.259ms排第3个step时，64题均已进入ASGI，但只有4题完成前端提交，安排的是3072 Prefill+1 Decode token；round4在276.127ms对应step已提交60题，直接安排32767 Prefill+1 Decode token。是可观测的ready集合不同，不是scheduler从同样已就绪的64题中随机选择小batch。
2. **提前成批与接纳窗口放大。** round5在288.919ms已排定62题的29729-token后续batch，而余下2题约290ms才完成前端提交；它们到约2640ms才进入scheduler，提交→接纳最大2349.455ms。之后额外产生2110-token（2048 Prefill+62 Decode）整网step，max-rank stream跨度816.156ms。调度选择本身中位耗时约1.65ms，不能把数秒的已排定GPU工作/排队等待说成`schedule()` CPU执行慢。
3. **当前源码与事件顺序一致。** `vllm/v1/engine/core.py:519` 的`step_with_batch_queue`优先填充执行队列，已排定batch不等待随后到达的请求；`:589`以后在队列满时`future.result()`等待输出。主循环`:1269`的`_process_input_queue`只在step之间处理输入。这解释了微小的提交时序差为何会冻结不同的后续shape，并让晚到请求跨过一个大Prefill等待。没有给IPC socket接收线程额外打点，因此不声称已逐纳秒拆出IPC传输、线程唤醒与主循环等待各占多少。
4. **shape是真实执行差异。** 新trace实际记录`aten::mm`输入`[M,4096]×[4096,512]`，M为1024/32768/31777等，另有`[M,16384]×[16384,24]`。rank0在32768/31777两含Prefill step分别有3266/3276个GPU kernel，kernel区间并集2294.268/2232.982ms，stream跨度2373.907/2295.036ms。大step主要有真实设备工作；碎片化则增加全模型调用、launch、通信与混合shape成本。此处未把累计kernel时间相加宣称端到端收益。
5. **没有发现持续Decode失稳。** 诊断三轮后段的step中位数34.595–34.774ms；round3相对round4仅+0.1093%。round3/4 TTFT差1448.363ms，含Prefill step跨度差1445.595ms，方向高度吻合，但不据此声称严格的99.x%因果份额。相同小shape首次与后续调用仍有差异：例如3073-token step在warmup round2为829ms、round3为376ms，可能混有首次shape/JIT或其他host成本；本次只在最后一轮采kernel trace，不能进一步锁定为某个算子算法问题。

**采样器自身的边界已识别：** 第6轮带torch profiler，max_iterations=12后，第13个step发生约11.736s的stop/export跨度，完整批次为35.747s。这一轮完整保留，只作为instrumentation/export干扰，不与前5轮混算，也不能把它当成生产Decode卡顿。前2轮预热同样完整保留，不进入三轮诊断代表值；没有事后挑轮。

下一步仅建议、尚未实现：优先在Plugin扩展点验证有界ready-Prefill合批/晚到请求接纳策略，关注异步lookahead已经排定小batch的窗口；不固定等待64题、不改变MBT、不修改vLLM源码，必须守护C1/C8、TTFT和Decode。若仍需细分算子成本，再做固定prompt、固定小Mixed shape复放，区分首次JIT/host gap和稳定kernel成本。当前证据不足以直接给某个FlagGems算子加黑名单或改kernel。

终态审计通过：原配置实例`PPU-13:glm5.3-flash-opt-20260911:2536898:505188227`健康空闲，argv/环境/三仓库及vLLM源码/权重/tokenizer/DB/thead与实验前一致，graph capture+多次回放与minimal通过；profiler和临时PYTHONPATH已从活动服务移除。`start-model-opt.sh`仍为SHA `5b1d0a52b129ada50cf38f2ba35194cb43d67a41901d2876e1150e4e7eef31ca`，没有源码改动、提交或推送。旧01/02准备失败证据完整保留，均无native capture。原Decode guard仍incomplete、Mixed缩减+5.3491%仍只属于原契约，不产生新精度gate或四场景验收。

最终因果摘要`step-evidence-20261018-03/causal-summary-v1.json` SHA `1e9d4943b7c33f2b70276adcf607e8e660e8ae176084aa325860533b4023d600`；终态审计`terminal-audit-v1.json` SHA `bac98b49f2dd1cf2dd100120800dbcc683446969db85a557e79849cce4f021db`。本次新增的是当前环境的框架机制证据，不是新的算子算法结论；不据单个诊断改写通用算子知识/SOP。

### 原Prefill配额优化依据

当前调度源码对running/waiting请求都将`num_new_tokens`限制到`long_prefill_token_threshold`，同时保持整个step的MBT预算。默认0长请求占满32768预算；候选16384允许两个半段请求组织到同预算中。MQA是池压缩后的密集矩阵，再按每行有效范围Top-K；提前分块可能减少早期query对尚不可见KV的密集计算。单请求理想矩阵量从32768×8192变为16384×4096+16384×8192，约减少25%；实际跨请求分块、512MiB logits上限、MoE/KDA与KV gather开销会改变净收益，不能把此比例当成服务加速。

此前点37阈值8192在2轮warmup内波动11.223%，没有measured结果。本轮是16384单变量，事前统一4轮warmup、末2轮≤5%稳态准入，所有baseline/candidate/revert同规则；并非事后丢弃慢measured轮。

## 优化内容与适用边界

MBT32768/maxseq64/TP16/BF16/FULL_DECODE_ONLY/prefix cache disabled保持。仅通过已有启动参数改变单请求配额，不改vLLM或Plugin源码、不改交付脚本。三个角色显式阈值0/16384/0，独立服务实例。原用户服务结束后用其原始参数恢复。

先冻结`P32768/D2/C16/N16` Prefill-focused probe，4warmup+2measured、单轮1800s，主指标output throughput≥3%（固定输出量时等价批次完成速度），P99 TTFT/TPOT/ITL退化≤5%，两轮spread≤5%，回退吞吐漂移≤3%。每角色1个独立服务只支持targeted结论，不能作为formal。

## 正确性与路径命中

精度Skill `minimal-regression`：每角色C1/C8；16383/16384/16385个明确token ID输入，生成8token，核对实际token计数并与baseline输出逐项一致，覆盖阈值分块边界。纯Decode每请求token=1不受阈值限制；若Prefill候选有收益，仍需Decode测量守护与父Mixed同配置A/B/R，之后才考虑保留。当前精度按用户认可的补充173/198，任何新数值异常停止晋级。

## 性能效果

三个角色均4warmup+2measured完整有效，稳态准入通过；全部原始measured轮保留。各角色输出吞吐两轮分别为：baseline 0.5820343704/0.5823560445，candidate 0.6077807560/0.6080626982，revert 0.5819672752/0.5822911799 token/s。

| Prefill指标（每角色measured中位数） | baseline 0 | candidate 16384 | revert 0 | 候选变化 |
| --- | ---: | ---: | ---: | ---: |
| 输出吞吐 token/s | 0.582195 | 0.607922 | 0.582129 | +4.4189% |
| 批次时长 s | 54.964387 | 52.638358 | 54.970616 | -4.2319% |
| P99 TTFT ms | 54923.661 | 52353.492 | 54928.910 | -4.6795% |
| P99 TPOT ms | 3428.705 | 3445.128 | 3423.722 | +0.4790% |
| P99 ITL ms | 3428.705 | 3445.129 | 3423.722 | +0.4790% |

原生比较因缺少cache preparation描述为incomplete，未覆盖。补充既有运行证据后的独立恢复报告为passed、无issues；只支持Prefill晋级，不是原始原生passed回执，也不是正式验收或Mixed收益。各实例graph capture、C1/C8与边界检查通过；candidate/revert边界输出与baseline相同。恢复实例`PPU-13:glm5.3-flash-opt-20260911:2310422:502491552`与原服务argv、环境白名单、源码内容一致，交付脚本SHA `5b1d0a52b129ada50cf38f2ba35194cb43d67a41901d2876e1150e4e7eef31ca`。

### Mixed晋级冻结（测量前）

在同一实验下新建远端`mixed-decode-01/`：Mixed `P32768/D128/C64/N64`（父正式场景输出1024→128，请求128→64）；Decode守护`P1024/D512/C64/N64`（短prompt与排队残余仍在）。各角色独立实例，顺序baseline0/candidate16384/revert0，每角色先Decode再Mixed，各4warmup+2measured，末2warmup输出吞吐极差≤5%、单轮timeout1800s；本轮预算10800s，非冷启动目标。

Mixed继续用维护版性能runner和原生比较器，输出吞吐≥3%、P99 TTFT/TPOT/ITL退化≤5%、measured各指标极差≤5%、baseline/revert漂移≤3%。Decode是守护而非要求加速的独立候选：同一批服务实例、原生逐轮校验和SHA核验后，输出吞吐及P99 TTFT/TPOT/ITL退化≤5%，轮间极差≤5%，回退漂移≤3%；单独保存guard回执，不冒充原生独立收益比较。任一不稳定/缺证据保持incomplete；任何数值边界失败停止晋级。三角色全完后恢复用户原配置，不自动写交付脚本。

控制命令`commands/control-mixed-v1.py` SHA `a3488b7de7d8689841449fa8631f3fecd25ce32cf2a0b5ef00ead3a8a04462fc`；prepare冻结配置、不发模型请求，之后dry-run核验再执行。冻结时Mixed/Decode尚未运行，不能引用Prefill表为端到端完成。

prepare已冻结：Mixed plan SHA `1c4b0f1bd7ff094550408e83eb2f0eb10bc4ce41635d3d3821b6c32c035a56b6`，Decode plan `d912aadb9071932b34597cb931c613b8642e4516196e116c800a8e27c72efe50`，Mixed comparison `33dd57195a62c7720d3015ab61fcdecb61c92d13ae0b3e8492fd54b3f227a412`，Decode guard `aa829539dd403730723df26e4985b899d5508f3b5a2af6bb717e0c9bdc107b38`。调度入口`commands/dispatch-mixed-v1.py preflight`核对当前实例、权重/tokenizer/源码/DB与冻结输入并生成两份原生dry-run，不发模型请求；核对后仅一次`launch`后台启动。初次copy传输尚未完成时prepare报文件不存在，无服务变更；已等待文件到位后prepare成功，未重复测量。

两份dry-run各6轮与种子/长度/EOS已核对；调度命令SHA `88879351037f92f05158350e72886fcec63b9d4773ee4ae49486e32514e15759`。continuation已启动，宿主控制器PID1216797；新的`mixed-decode-01/controller.log`、`operations.jsonl`、各角色原生结果持续落盘，monitor已改为跟进此子目录，不重复旧Prefill实验。

16:23跟进：baseline Decode原生6轮完成、逐轮raw/validation/output SHA有效，128/128 measured请求成功；吞吐两轮1328.171929/1366.412423 token/s，中位数1347.292176，P99 TTFT中位数6278.375612ms，TPOT45.640095ms、ITL36.391913ms。warmup输出吞吐极差0.1320%通过，但measured P99 TTFT为6579.806125/5976.945098ms，极差约9.60%，已超过冻结5%守护稳定性条件；保留两轮，不挑选、不重跑或改门槛。即使后续Mixed有收益，也不能将本次Decode完整守护签为passed。当前继续已启动的Mixed取证与最终原配置恢复，不叠加新实验。

baseline Mixed已完成3轮warmup（各64成功、0失败），尚无measured及candidate/revert结果；当前实例`PPU-13:glm5.3-flash-opt-20260911:2323596:502628539`健康且最小回归通过。尚无新的Mixed端到端收益结论。

### Mixed/Decode终态（18:42核验）

baseline/candidate的两个阶段均完成各4warmup+2measured，measured各128请求成功、0失败，raw/validation/output SHA已核对。以下为每角色全部measured轮的中位数，P99不是跨轮合并后的总体分位数。

| 阶段/指标 | baseline 0 | candidate 16384 | A/B变化 |
| --- | ---: | ---: | ---: |
| Mixed 输出吞吐 token/s | 35.991754 | 37.924562 | +5.3701% |
| Mixed 批次时长 s | 227.607693 | 216.007767 | -5.0965% |
| Mixed P99 TTFT ms | 222775.478 | 210301.923 | -5.5992% |
| Mixed P99 TPOT ms | 1713.191 | 1623.555 | -5.2321% |
| Mixed P99 ITL ms | 3502.691 | 3478.973 | -0.6771% |
| Decode 输出吞吐 token/s | 1347.292176 | 1435.592308 | +6.5539% |
| Decode P99 TTFT ms | 6278.376 | 4938.275 | -21.3447% |
| Decode P99 TPOT ms | 45.640 | 41.075 | -10.0033% |
| Decode P99 ITL ms | 36.392 | 36.188 | -0.5613% |

Mixed两轮吞吐baseline为35.995020/35.988488，candidate为37.921622/37.927503 token/s；Decode candidate为1433.854716/1437.329900 token/s。A/B观察存在改善方向，但并非完整可归因收益。

revert服务17:12通过最小回归；其Decode第3/4轮warmup吞吐1341.426761/1445.909434 token/s，极差7.49696%超过预冻结5%，原生runner在measured前按规则失败。控制器未执行revert Mixed，随后恢复原配置。这是实际稳态准入失败，不是工具元数据错误；不得靠补证据、修改门槛或把warmup当measured修复。baseline Decode原有P99 TTFT 9.60218%波动缺口也保持。

原生比较器对已有Mixed A/B重新核验证据后返回`incomplete`，原因`revert: insufficient independent process runs`。Decode完整guard同样不能通过。最终判定：**候选不保留，尚无本轮已确认的端到端收益**；保留Mixed +5.37%的缩减workload观察，不等同于正式P32768/D1024/C64/N128或四场景验收。

当前恢复实例`PPU-13:glm5.3-flash-opt-20260911:2390706:503072235`。argv、环境白名单、源码内容、DB/thead、权重/tokenizer指纹均与本轮原配置相同；health和已保存最小回归通过，交付脚本SHA仍为`5b1d0a52b129ada50cf38f2ba35194cb43d67a41901d2876e1150e4e7eef31ca`。没有提交/推送，也没有修改vLLM源码。

### 下一轮规划（仅记录，未启动）

1. 先解决测量稳定性：在新契约对全部A/B/R统一预冻结更充分的预热/重复，保留本轮所有失败；将阶段结果独立归档，避免Decode守护失败掩盖Mixed回退缺口。仍用性能Skill targeted、同workload，Mixed≥3%、守护≤5%，不从历史基线拼接精确收益；不能靠只补一轮revert签发本轮passed。若仍不稳定或收益低于3%则停止晋级，服务恢复原配置。
2. 算子候选KPool gather/compress融合：仅静态方向，先用关键算子Skill冻结数值/stride/graph契约，测完整交易而非核心kernel；至少1.25×且可消除关键路径足以支持约3%目标才进入服务，数值/graph失败立即停止。融合属高风险，保留前需要正式精度。
3. 点40 CPU元数据候选仍暂存未安装：仅当累计关键路径证据表明19.514µs/次可形成实质收益才继续，避免用孤立micro倍数排序。

当前Prefill +4.42%与Mixed +5.37%并不相加；Decode TTFT包含prompt/排队，不能据其A/B变化宣称纯Decode kernel更快。当前无新trace，MQA计算量假设尚未完成机制归因。本轮诊断已闭环，monitor暂停，下一轮尚未执行。

## 决定、风险与回退

最新8+3三臂测量已完整结束，Mixed收益按原生比较确认，Decode守护仍incomplete，故整体未晋级部署16384。原配置已恢复且健康、graph/最小回归通过，监控已暂停。保留旧不完整轮及新完整轮全部产物，不补造guard通过、不修改采样或阈值。只操作目标容器内精确API后代，不碰源适配容器；无vLLM源码修改或推送，交付脚本不变。

## 外部证据

新8+3轮的终态只读审计命令（执行前保存）：`commands/final-audit-w8-v1.py`，SHA `b380bd0186c9bc8cd0f1a4a95cb6479ee445083928e3c9b7a0daa6b3059f8a68`。它在控制器完成恢复后重验六个原生run-record、全部逐轮SHA和Mixed原生比较，核对Decode回执与原采样字段、当前恢复实例和原配置一致、graph/最小回归及health；不重跑测量、不改原始值/门槛。单独保存`mixed-decode-02-w8-r3/terminal-audit-v1.json`，原comparison/guard/completion全部保留。

21:50终态审计已通过：审计SHA `2f82c96e689a2bdb5cc4ae45b3e59fce21dae6594ae88709832933489283db35`；completion SHA `2ffeafdd2c98c2bf218a8accdb2c429312dd3cae3dbe7913473a446ff316b94e`（status=incomplete，error=null，original_service_configuration_restored=true）。Mixed原生比较重新计算与已保存回执逐字段相同，六组全部warmup/measured文件均保留且SHA有效。恢复实例`PPU-13:glm5.3-flash-opt-20260911:2485876:504687553`，argv、环境白名单、源码、DB/thead、权重/tokenizer与新轮original-runtime一致，health与C1/C8/graph capture及多步replay覆盖通过。交付脚本SHA仍为`5b1d0a52b129ada50cf38f2ba35194cb43d67a41901d2876e1150e4e7eef31ca`。监控已暂停，不自动继续实验或部署。

### 用户授权的新测量轮：8warmup/3measured（执行前冻结）

用户在本轮incomplete后明确要求增加预热并重新跑齐Mixed/Decode三臂。继续同一优化点，新远端子目录`mixed-decode-02-w8-r3/`；旧`mixed-decode-01/`全部保留。性能Skill模式`targeted/performance_only`、正确性`minimal-regression`；不是正式四场景或D1024/N128验收。

- 三臂仍为threshold 0/16384/0，各独立服务实例；MBT32768/maxseq64/TP16/BF16/FULL_DECODE_ONLY/关闭前缀缓存、生成seed42/temperature0/ignore_eos与原workload保持。
- 每角色每阶段统一8warmup+3measured（此前4+2），末3warmup吞吐极差≤5%才进入measured；全部measured保留。Mixed P32768/D128/C64/N64主指标≥3%，P99 TTFT/TPOT/ITL退化≤5%、measured极差≤5%、baseline/revert漂移≤3%；Decode P1024/D512/C64/N64仅守护，吞吐和P99 TTFT/TPOT/ITL退化≤5%、极差≤5%、回退漂移≤3%，不要求Decode加速。三个角色使用同样规则。
- 每角色先Mixed再Decode。仅原生warmup不稳定且服务健康空闲时，保留该阶段failed/incomplete并继续另一个事前声明阶段和后续角色，以免漏掉Mixed回退；不强行产生失败阶段的measured，不自动重试。最小正确性、服务健康、原生有效性或其他失败则立即停止并恢复。
- 每角色graph capture、两次replay覆盖、C1/C8及16383/16384/16385-token边界等价检查；源码/权重/tokenizer/DB保持，交付脚本不变。结束或失败后恢复原参数并验证健康。
- 单轮timeout1800s，规划预算14400s，超预算不再开始新阶段/角色；不做宽泛进程终止或目录清理。用新契约重测全部A/B/R，不拼接旧轮次、不降低既有门槛、不提交推送。

当前只读预检：恢复实例2390706/503072235健康空闲，argv/环境/源码/DB/权重/tokenizer与上一轮恢复身份相同；远端案例目录规范路径已核验，owner=root且当前操作可访问，NFS可用约6.7T，新子目录尚不存在。继续使用既有已隔离优化容器，prepare会重新核对源/优化容器image与Mounts一致；不新建挂载、不碰源服务。

准备执行`commands/control-w8-v1.py prepare/evaluate`，SHA `df4c9b080f021b226a5b27a0df011769f5a8cdbafd8c57556d3510f901ee7c51`。原生runner复用点39已部署工具，prepare逐文件核对当前本地工具SHA，不一致则在任何服务变更前停止。Skill完整bundle：performance `872b65dd0e7a4e8c5b342c37b1c34729f14154d1e68be01ed60938d5b22dc8d1`，accuracy `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`；证据`commands/w8-skill-and-tool-binding-v1.json`。

prepare已通过：工具逐文件无漂移，源/优化image与mount一致，刷新证据SHA `cf42e5e48aaf3994862f4af4ef05f64ea92cdc5d37e79c540d1783274a683939`。Mixed plan SHA `5f1eb94f6d9af3eb275602870fd490edc02e136cd16a59627857154f6894f21f`、Decode plan `0c2d3013fa7fa850059f337fb4986571896f1f29ae3ec2983f4cbb7f8692780a`、Mixed comparison `4375a17d6aea779ff581530973d93eac5b829ae57f262cc056e06fe5381a86c4`、Decode guard `ffb19d5e0bd3af12921a932ff427f9a65fe7853340e64607b33a7053aba03a6d`。将先执行已保存`commands/dispatch-w8-v1.py preflight`核对两阶段各11轮原生dry-run，再以同脚本`launch`唯一派发；不启动旧控制器。

已执行preflight并逐项核对：两阶段各8warmup+3measured、长度/C/N/EOS和全部派生seed一致。dry-run SHA分别`295f5c479dbbe81e017204e57754d585062e4ab414ce188f076f0291107f4738`与`3cd6416729b6710de8c813ee7fcdc0dd884abd2fbb6136a863f3da953486c19a`。dispatch SHA `639666fe17cb197ceaafef553fb854f3e79002267f675a0fd96bf3d86b2522d7`，只派发一次，宿主控制器PID556254。新轮结果`incomplete/running`，无新性能判定；monitor已切到`mixed-decode-02-w8-r3/`，不再操作旧轮。

19:24只读跟进：baseline实例`PPU-13:glm5.3-flash-opt-20260911:2399095:503659177`已于18:56 ready、18:57通过最小回归，本次health通过。Mixed已完成6轮原生warmup，尚未完成8轮稳态准入或进入measured；candidate/revert尚未启动。控制器无错误，比较/guard/completion尚不存在，继续原冻结测试，不重复派发；预热轮不作为收益。

19:54只读跟进：新轮baseline两阶段各11轮完成、原生complete，全部measured请求各192成功、0失败；raw/validation/output及run artifacts SHA核对有效。

| 新8+3轮baseline阶段 | 输出吞吐中位数 token/s | P99 TTFT ms | P99 TPOT ms | P99 ITL ms | measured输出吞吐极差 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mixed P32768/D128/C64/N64 | 36.017673 | 222678.420 | 1712.141 | 3496.607 | 0.02783% |
| Decode P1024/D512/C64/N64 | 1386.271921 | 5806.235 | 44.761 | 36.339 | 4.09773% |

两阶段末3warmup吞吐极差分别0.01535%、0.81444%，通过准入。但Decode measured P99 TTFT三轮5007.381906/5806.234816/5810.463857ms（极差13.83137%），P99 TPOT为40.884152/44.861835/44.761082ms（极差8.88648%），仍超过冻结5%。这些轮次全部保留，不能因增加预热就忽略尾延迟波动，也不把TTFT/TPOT代理差异解释为纯设备速度差异。

baseline Mixed/Decode run-record SHA分别`bdaf5eb2c133bedce93133d7b8bd082cd264e74c501db377d1c7d0370461d77d`、`9e707a28d84749362f4628e2764e88dfccaec2ac71658c86c5694dbee9f1aa8d`。candidate实例`PPU-13:glm5.3-flash-opt-20260911:2430548:504006593`已于19:54 ready并通过最小回归，本次health通过，开始Mixed测量；revert尚未启动。继续完成预声明三臂，Mixed收益和Decode守护分别判定；本次尚无新A/B结论，Decode完整guard的稳定性缺口已记录。

21:00只读跟进：candidate两阶段各11轮均complete，measured各192成功、0失败，raw/validation/output及run artifacts SHA核对有效。Mixed输出吞吐三轮37.944278/37.950636/37.943677 token/s，中位数37.944278（相对本轮baseline为约+5.35%的A/B观察）；P99 TTFT/TPOT/ITL中位数210210.904758/1622.868157/3474.764833ms，吞吐及各尾延迟measured极差均<0.061%。Decode吞吐1403.493620/1402.719359/1423.758681，中位数1403.493620，P99 TTFT/TPOT/ITL中位数5622.023058/43.790012/35.642778ms；其TTFT极差8.21213%仍超冻结5%，其余指标极差不超5%。全部三轮保留，不变更规则。

candidate Mixed/Decode run-record SHA分别`a8f53015bd9a289d9a5319b498f9646aaa27ae54c831394a184bbfc779048ceb`、`c814e10273ea23417c8da3c38c09ddf9e0a69d513b8674f8fbfd99b3f4748b26`。revert实例`PPU-13:glm5.3-flash-opt-20260911:2462136:504340262`20:50 ready并通过最小回归，health通过，Mixed已完成2轮warmup；仍无最终comparison/guard/completion。继续原控制器完成回退及恢复，不将当前A/B观察提前宣称为完整三臂收益。

### 新8+3轮完整三臂结果

本轮六个原生run全部完成各8warmup+3measured；每阶段每角色measured 192成功、0失败，共1152条measured请求，无缺失回退。三个角色graph与C1/C8、分块边界最小回归均通过。唯一候选变量仍为`long_prefill_token_threshold=16384`，不是增加MBT，也没有本轮模型源码改动。

| Mixed P32768/D128/C64/N64（measured轮中位数） | baseline 0 | candidate 16384 | revert 0 | 候选相对baseline |
| --- | ---: | ---: | ---: | ---: |
| 输出吞吐 token/s | 36.017673 | 37.944278 | 36.014891 | +5.3491% |
| 批次时长 s | 227.443902 | 215.895531 | 227.461469 | -5.0775% |
| P99 TTFT ms | 222678.420 | 210210.905 | 222674.421 | -5.5989% |
| P99 TPOT ms | 1712.141 | 1622.868 | 1712.303 | -5.2141% |
| P99 ITL ms | 3496.607 | 3474.765 | 3498.979 | -0.6247% |

Mixed吞吐baseline/revert漂移仅-0.00772%；全部主/守护指标的轮间极差和回退漂移满足冻结条件。**原生比较器passed、无issues，确认该缩减Mixed场景的增量端到端收益约5.35%。** 这是当前保留组合→阈值候选，不是未优化anchor累计收益；每角色一个服务实例、3轮测量，不能推为长期容量或正式四场景验收。

| Decode P1024/D512/C64/N64（measured轮中位数） | baseline 0 | candidate 16384 | revert 0 |
| --- | ---: | ---: | ---: |
| 输出吞吐 token/s | 1386.271921 | 1403.493620 | 1428.285235 |
| P99 TTFT ms | 5806.235 | 5622.023 | 5121.462 |
| P99 TPOT ms | 44.761 | 43.790 | 41.147 |
| P99 ITL ms | 36.339 | 35.643 | 35.826 |

Decode候选相对baseline吞吐+1.2423%，未观察到中位数守护退化，但**不能确认纯Decode收益或完整守护通过**：baseline/candidate TTFT轮间极差13.8314%/8.2121%，baseline/revert TPOT极差8.8865%/7.1517%；baseline/revert吞吐、TTFT、TPOT漂移分别+3.0307%、-11.7938%、-8.0747%，超冻结3%。guard按原契约为`incomplete`，不是数值错误或已证实候选负优化。8轮预热仍未消除该噪声，禁止继续盲目增加轮数、删首轮或放宽阈值。

整体`Mixed passed + Decode incomplete`，全局晋级仍为incomplete、候选不自动部署。TTFT/TPOT含prompt与队列/调度成本，不能根据上述变化推断具体Decode kernel速度；MQA减少无效计算的机制仍属源码支持假设，没有本轮trace证明。旧轮缺回退不完整结论保持不变，新轮独立确认Mixed，不拼接旧轮。

证据位于`mixed-decode-02-w8-r3/`：`comparison-result.json` SHA `04837cbc83788f5de652a5eaaf8ce679b77a9a2aa7516a8b464b718a8771aaee`；`decode-guard-result.json` SHA `22b9b6a4623d9244aaf2cf947b549264653e53468bb7eb90aeca1db95dd20df7`。revert Mixed/Decode run-record SHA分别`fe0ff7100daeb0508bb6a0fda87b089e490519480c914c96bc81593bdabdab52`、`594934811125e4c19b74eb01b79a2761d229ce32851d866074d7a27091afb705`。21:44控制器已开始恢复原配置，终态恢复审计另记，不提前宣称ready。

### 本轮规划复盘

当前已证明Mixed增益，未证明Decode守护；没有同身份anchor→最终组合的四场景累计验收，不相加Prefill/Mixed/micro收益。下一轮仅记录以下方向、尚未启动：

1. 优先利用本轮原生逐请求证据只读定位Decode波动，区分首token入队/Prefill残余、客户端发送与设备token循环；不假定是冷启动，不再盲目增加warmup。先不发模型请求；若离线证据仍不足，单独冻结profiling capture并核验rank与阶段覆盖，再根据归因建立新的targeted同配置验证，继续沿用原守护门槛。必要正确性范围为minimal-regression；若行为/数值变化则停止并诊断。
2. KPool gather/compress融合仍为算子静态候选；先通过完整交易micro（目标≥1.25×）、数值与graph，并证明关键路径可消除成本达到有意义规模，再晋级Mixed服务测试。融合高风险，保留前执行正式精度；无净收益或语义/graph失败立即停止。
3. 点40 CPU元数据消除同步仍仅暂存；19.514µs/次不足以直接立项服务切换，需先证明累计关键路径成本。当前服务不包含该候选。

下一复盘触发：Decode波动完成归因，或出现新算子完整交易证据。当前只收尾本次三臂测量，不执行上述新实验，不改交付脚本或推送代码。

终态核验命令（执行前保存）：`commands/finalize-readonly-v1.py` SHA `de97d25ad0b86649356e627f03b32b2835a5e43bfdcc285b89eccdf3b39f79ca`。只读取完整/失败的原生结果并校验SHA，用未修改的原生比较器核对已有Mixed A/B和缺失revert，记录incomplete；核对当前恢复实例的argv、环境、权重/tokenizer、源码、DB与health。另存`mixed-decode-01/terminal-summary-v1.json`，不覆盖completion或采样，不发模型请求、不重启服务。

已执行，终态摘要SHA `2e658ee31d3a6a66b47a8f0448e69e99d60bad1a0bdd734b2f1ccfbc9e145139`；原`completion.json`仍为incomplete。Mixed baseline/candidate run-record SHA分别`67ce808d3759af3955ff9f15d8adfd6d9ed8aeec00e4edd7415817819eb1b0af`、`1665c9b74de0f9f3392d75a2eb27d20a28c9b55754668bcc948b456f619af660`；Decode candidate `e7f74db91925efa8d747c9a9f173776b2908f5a2c3e0933d86c8b82dd926eff6`，失败revert `92b2646a3ad5df01e7a9a683f4a8b956ecfdb50e33301604848c71c649c2d02a`。

2026-10-18补充：三臂及原配置恢复均完成，原生比较因service manifest缺少`performance_context.cache_preparation`返回incomplete，原回执不覆盖。准备执行`commands/recover-evidence-v1.py`（SHA `1ddbfdab883ed423a97fc8798913a1850c02eca51e4ec86662292df2f1fd1f7c`）：只读核对既有argv关闭前缀缓存、同实例日志0%命中与原生结果，在内存补充此描述后调用未修改的维护版比较器；单独保存有明确事后补充标记的回执。不得修改原manifest/run-record/采样字段/阈值，不发模型请求。只有核验通过才晋级Mixed。

恢复已执行：`comparison-evidence-recovered-v1.json` SHA `917a1267cf6398030f565517a3659c2018d5ef599a585470433405e598393d44`。原始三个run-record SHA依次`ef272f227dc52d41ca647d0b9ca190733eb75b53aac16ed41a1dcd227afbdefb`、`b65f5a5f840d20464e77b7ddefd616cf489c535c9d2616b83e80084a23be6017`、`1ca63c191aa52b89abfd48c745a9b6cc88253a24869cefcff5a9d15155a6ee3c`，保持未改。

远端：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261018-point41-prefill-quantum`。
执行控制`commands/control.py` SHA `a7d347740b9ccc31ae6828a8c14e821100b11edb1b0ea738d108c3f7c2f0e2a3`；冻结`plan.json`/`comparison.json`，各角色目录保存launch/runtime/minimal/performance原件，`operations.jsonl`记录服务操作；终态`completion.json`和`comparison-result.json`。

准备阶段首版在点39仍有请求时因空闲断言停止，未进行服务变更。v2将只读冻结与执行前空闲检查分开；v3额外等待点39的postrun manifest生成后才做设备探针。当前实际控制`commands/control-v3.py` SHA `2c212e5e3dc34a8efcd18e47beda79680742c71bf063b6097d0284e1c64b294a`。计划SHA `19758104fe83f24653661a3b5308edb96fa0f68836e975fda79af988d20597cb`、比较契约SHA `888fefc9ff016d164964c44e1ff025b7d10334f3bf7110a680270afdc42a3525`；原生dry-run通过并核对6轮、实际生成参数、阈值和JSON pointer，未发送请求。
