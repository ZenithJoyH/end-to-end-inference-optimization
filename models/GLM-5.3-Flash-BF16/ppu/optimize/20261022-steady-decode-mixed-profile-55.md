# 20261022-steady-decode-mixed-profile-55 稳态 Decode/Mixed 归因

2026-10-23 00:31：修复轮两段采集均通过。Mixed为128/128，16rank各252 graph launch、3个new-request marker，API/EngineCore分别41945/50770栈样本；结果SHA `7039832afe55d2802bd3148b6ff9911be5490d3e3fdcf58e189be002e0fd4c1d`。原服务已恢复启动且健康，但旧helper误读不存在的freeze.json，原restore-failure保留。保存`capture-repair-02/commands/finish-restore-v1.py` SHA `1d72812ab9fb2384e78294725102a4fe0ad20e8f8a6cee03d5b7337c9c8e58d7`，仅核验并接续原API3512273/540201965未执行的完整回归，不重启、不重采。之后零生成`current-audit-v2.py` SHA `c44ec288414e8a05ba5a01b394b1c355a54092bfd4c2fb6d3290ad245e0c24c3`；离线`repair-analysis-v3.py` SHA `15b89e9e74e5456d49d4b1560c4503e2fa91b8ad9832d80412f8cd5e0b544399`，5项CPU归属测试通过，只在恢复及审计终态后执行；原始采样、阈值和失败均不改。

- 状态：用户已授权修复日志/前端CPU采集并补齐Decode/Mixed；新接续目录`capture-repair-02`先做零模型请求CPU因果诊断，再冻结新采集命令。旧轮保持incomplete及原始证据，用户源码和推理参数保持。
- 最新终态：修复轮两段16rank及主机采样完整、原服务完整模型/FULL/C64回归和当前审计通过；下文旧轮失败及缺口按时点保留，不覆盖原始产物。
- 分类：framework/diagnostic；实际算子或框架候选待 trace 证据确定。
- 目标：PPU-13 / glm5.3-flash-opt-20260911 / 8011；父场景 `p1024-d1024-c64-n128`。
- 依赖：[点54当前用户版本基线](20261022-user-plugin-production-rebaseline-54.md)。

## 优化方向与瓶颈依据

2026-10-23 00:37恢复闭环：原服务3512273/540201965完整minimal、11答案、C64和FULL回归通过，当前只读身份/唯一安装/镜像挂载/源及index审计通过，全部采样器已退出。`completion-recovered-v1.json` SHA `56d5024a7e713b04f9405785e381c61c38cdea95f30f60fae7c1cb8e255db779`；模型最终审计SHA `4122012899ed8b1f76a3e15aa3fc791df281f7f51e94df822f078555bbcd06f5`。恢复命令未再次重启或重采，原路径错误失败不删除。正常DB写入与新实例的严格绑定缺口如实保留，原173/198达标分数未变，不伪造当前gate。已唯一启动两段既有trace离线分析，不使用GPU或发模型请求。

用户授权继续稳态 Decode 和 Mixed profiling，并针对实际热点优化，MBT 和启动参数不变。点54已完成三阶段各8轮预热+3轮测量；Decode/Mixed输出吞吐中位数1157.787722/1148.850004 token/s，测量spread为1.5042%/1.3646%。这只能证明当前基线稳定，尚不能区分主机、设备算子和通信的关键路径占比。

本轮使用本地 `inference-profiling` 的 capture→analyze；保留用户的 Plugin 修改与 index，不按历史 kernel 数字选择候选。计划沿用 Decode P1024/D1024/C64/N64 与 Mixed P1024/D1024/C64/N128；采集窗口需核对原生实现并在采样前冻结。若需缩短诊断 workload，另记差异和自身稳态准入，不冒充完整目标。

## 优化内容与适用边界

21:39只读预检确认：连接到指定 PPU-13；容器内当前 PID3318148/start_ticks537692913 与点54一致，原 argv 不含 profiler 配置，相关环境变量为空，health200，OpenAPI中没有 profile 或 RPC 路由。

当前已安装 Plugin 的 `vllm_fl/worker/worker.py:1057–1063` 与 vLLM 的 `v1/worker/gpu_worker.py:929–937` 都在 profiler未启用时直接抛错，要求 `--profiler-config`；原生 `config/profiler.py:37` 默认值为 None。维护版 `evaluation/performance/vllm_profile.py` 仅调用原生客户端 `--profile`，不会替服务启用 profiler。

因此未盲发 `/start_profile` 或 benchmark。用户现已明确批准临时仅增加 profiler 诊断配置；新诊断脚本由原启动脚本仅追加 `--profiler-config` 生成并做逆变换字节校验，原脚本不改。MBT、全部推理参数、源码/index、生产DB URL不变，结束恢复原启动方式。

冻结方案：原生 torch profiler CPU/CUDA、record_shapes=true、stack/memory/flops=false、gzip，`delay_iterations=900/max_iterations=256`；Decode P1024/D1024/C64/N64、Mixed P1024/D1024/C64/N128各8轮无profiler预热+1轮准入probe，末3预热输出吞吐spread≤5%，再各采1轮，不重试、不删慢轮。单轮1800秒、readiness3600秒、规划预算14400秒。正式基线仍引用点54各8+3，本轮probe/trace不构成收益。

当前Plugin实际标记为 `execute_new_N_cached_M`，N/M是请求数，并不是原生vLLM的context/generation token标记。阶段归因必须结合FULL_DECODE_ONLY的实际graph launch、shape和correlation；cached非graph部分无其他证据时保留unknown。每个trace逐一核对容器CPU PID/start_ticks对应的TP rank与文件名、设备kernel、至少两次graph launch、请求marker，Mixed还须观察新请求接纳；缺覆盖停止后续采集并恢复。前端用原生CPU profiler；EngineCore无原生完整CPU trace且未安装py-spy/perf，仅外部100ms `/proc`运行/排队计数，不冒充Python self-time或完整主机关键路径。

独立复核发现并修正恢复标志设置过晚、仅按文件数判rank覆盖、计划未纳入SHA冻结三点。精确停止前登记恢复责任；启动期间API一出现即登记PID/ticks/argv，不能只依赖日志路径清理。控制器、observer、计划与工具全体内容冻结，prepare/dry-run零生成。

22:09本地21项AST/mock单测全部通过（复测0.228秒），覆盖PID归属拒绝、partial-stop恢复、冻结计划/工具变更、16rank成功与缺失/CPU-only/错rank/缺前端/不足两次graph/Mixed无接纳等失败路径。测试SHA `23e59dc39f85120547a05b204342509ba4b9f781940c2c0e9b5a515e23895269`；不执行控制器顶层import、零远端/GPU/模型，仅工具测试。

## 正确性与路径命中

准备阶段零生成；22:19后已按授权重启为临时profiler实例并开始回归请求，源码/index、推理参数、原launcher与DB URL不改。点54原生173/198（87.3737%≥86%）及原正式回执保留，不制造新 gate。诊断实例及恢复实例均执行原smoke C1/C8、三16K边界、11明确答案、C64与FULL捕获/多token回放核验；不能把旧实例gate直接改绑。恢复后只在全部稳定身份（包括DB字节）一致时签显式rebind；若正常调参改变DB则保存差异待专门绑定核验，不重置DB或伪造一致。

采集需证明16worker CPU/设备trace、真实阶段标记和graph replay，主机接入/Engine证据不足则明确缺口。累计kernel时间、通信重叠、CPU自耗时/等待与无覆盖间隙分别报告；不相加16rank时间，不把trace累计时间当端到端关键路径。

## 性能效果

### 修复轮最终归因（2026-10-23）

| rank0采样活动，毫秒 | Decode | Mixed |
|---|---:|---:|
| 窗口 | 6489.893 | 18852.726 |
| 记录设备活动并集 | 6401.144 | 17662.037 |
| MoE GEMM累计 | 2462.616 | 6444.896 |
| BMM累计 | 864.972 | 1904.885 |
| Sparse MLA累计 | 562.097 | 1502.749 |
| align stage2累计 | 277.698 | 553.305 |
| 显式PCCL并集 | 371.358 | 1128.144 |
| 未记录活动间隙 | 88.749 | 1190.689 |

Decode全16rank的通信并集348.681–401.552ms；Mixed1128.144–1886.008ms，包含各rank等待/同步及实际collective活动，不能相加或称作可消除的通信关键路径。图关联kernel的rank0并集分别6316.101/12448.882ms；Mixed含新Prefill请求的step为4942.099ms，可能同时有Decode，不称纯Prefill。其余cached非graph与无阶段归属分别47.595+6.078/196.467+12.117ms，保留unknown。

基于trace epoch的内侧CPU计数窗口为6.3988/18.7034秒（100ms采样）：API user/system分别0.32/2.71、0.88/7.90秒；EngineCore为4.24/1.25、10.63/3.46秒。CPU进程多线程时间与设备重叠，不能相加求总时间或当纯调度开销。API/Engine主线程runqueue仅约0.006/0.362ms、0.012/2.031ms；统计栈主要为select/wait、shm等待及sched_yield，故无证据先把CPU排队认作主瓶颈；也不能据此宣称主机开销为零。py-spy包含idle与诊断扰动，不提供精确Python self-time。

完整离线报告：`capture-repair-02/decode-analysis-v3.json` SHA `b5d5fd8be8e2ef5f01a01c91954453ba54a23f09c634163798cbf7409c6320c9`；Mixed SHA `526f033dc3c3d6fdb8c344f5a673b56950437b61f764d545f8e7d14fea749022`。它们不是无profiler性能收益。旧轮rank0数字不混入新轮。

planning55-repair复盘：当前累计收益仍未知，点54基线为当前同代码无profile锚点，点55无源码改动。下一优先级为：(1) 点56实际FlagGems align非二次幂计数的精确整数向量化，低风险/高命中但净收益上限较小，先完整链micro证伪；(2) MoE GEMM2的K128单K-tile流水配置，先证明实际config后做单变量micro；(3) BMM布局及Mixed index_put/通信等待的依赖关联，现有trace不能证明关键路径，不先改通用调度。任何候选均须最小模型/graph回归和同配置无profile三臂，原MBT与推理参数保持。

本轮没有新端到端收益或候选。Decode的8预热+1无profiler probe准入通过，末3预热输出吞吐1146.018/1169.290/1144.933 token/s，spread2.1254%≤5%。profile轮64/64成功、输入/输出各65536 token；它不是点54无profiler三轮基线的新测量，不用profile时间计算收益或退化。Mixed未运行。

既有Decode trace逐文件SHA/CPU PID/start/rank核验后，16个worker各有326675个正时长kernel事件、128次graph launch、128个cached-only请求marker。每rank设备事件观测区间约6.519秒，设备活动区间并集6.427–6.467秒，未记录活动间隙51.4–92.0毫秒；这些间隙不是已经证明的硬件空闲或主机阻塞。以下仅列rank0采样窗口内的kernel累计时间，不能相加16rank、不能直接当端到端关键路径或可实现收益：

| 实际trace符号 | 调用次数 | 累计时间(ms) |
|---|---:|---:|
| `fused_moe_kernel` | 10752 | 2503.299 |
| `bmm_kernel` | 14336 | 864.831 |
| `triton_flash_mla_sparse_fwd` | 1408 | 562.017 |
| `mm_kernel_ppu` | 44032 | 391.873 |
| `pcclKernel_twoShotAllReduceKernel` | 11648 | 336.717 |
| `mhc_pre_fused_kernel_hc_mult_4` | 11520 | 299.603 |
| `linear_kernel` | 16256 | 292.242 |
| `moe_align_block_size_stage2` | 5376 | 277.721 |

这些是Decode场景末段采样的热点线索。`execute_new_N_cached_M`是请求计数，cached也可能包含续Prefill；虽有FULL graph/相关ID，尚未独立核实全部异步kernel关联语义，设备token phase仍标unknown。rank15也以MoE/BMM/Sparse MLA居前，不能据此直接选择历史旧参数或认定某一实现就是当前库路径。

通信补分类已完成：每rank均11648次PCCL twoShot AllReduce及128次AllGather，共11776次；rank0通信区间并集354.510毫秒（其中AllReduce336.717、AllGather17.794），各rank并集335.810–383.989毫秒。与名称未匹配kernel的时间交集均为0，但未匹配项仍unclassified，不能据此给出通信关键路径/可消除等待或加速上限。原analysis-v1的17.794毫秒只是旧regex识别子集，不能作为总通信开销；补充报告保留旧产物、不改原trace/coverage。

主机侧：rank0主线程记录的event synchronize墙钟exclusive约4.387秒、graph launch约0.655秒；另一线程同步等待约6.317秒。阻塞等待不等于CPU工作，这些线程时间不能相加。frontend文件1142字节/55事件仅含metadata与Trace envelope，没有CPU活动；EngineCore Python self-time也缺失。因此尚不能给出完整主机/算子/通信关键路径比例，也不能把CPU等待判成调度瓶颈。

真正候选仍需单变量最小正确性/graph回归，再做无profiler同配置Mixed三臂及Prefill/Decode守护。沿用吞吐≥3%、P99退化≤5%、测量spread≤5%、回退漂移≤3%，不调整MBT或用冷启动调参作为稳态收益。

## 决定、风险与回退

完整归因未通过，不安装候选、不自动补跑Mixed或重采Decode。原失败和全部trace保留；profiling技能要求缺frontend覆盖时不能将17个文件数量视为完整通过。日志错误仅在新离线证据中澄清，未改原failure或冻结阈值。

原参数服务已恢复为3465683/539586647，health200空闲，完整C1/C8、三16K边界、11答案、C64 64/64与FULL捕获/多token回放通过。用户三库源码/index、原launcher、argv/env、权重/tokenizer、thead、镜像挂载和唯一安装未变。DB正常写入5f343e67…→6a7822d7…是稳定身份比较的唯一差异，原URL/策略不变，未清库/复制/回退；原生173/198≥86%仍有效为原评测事实，不是精度失败，但此次重启加DB写入尚无新实例绑定回执，不伪造新gate。

下一轮只提出以下顺序与首个证伪，不由本monitor自动执行：

1. 先修采集可观测性：只读核验原生frontend profiler的线程/lifecycle/step与delay900，确认空trace原因；日志显示`External init callback must run in same thread as registerClient`，目前仅为观察，不定根因。若必须补采或增加有界外部Python采样，先保存新契约和命令，不能通过放宽覆盖条件继续。恢复实例还须完成显式绑定核验，不重跑或篡改已有分数。
2. 首个算子候选为MoE阶段配置/完整链路：先确认当前函数来源、真实shape/路由、GEMM1/2最终配置及alignment，而非从kernel名称或旧单算子收益推断。仅在真实配置/shape成立后，比较一个阶段的单变量、完整MoE changed-input graph数值与微测；数值/graph失败或无净收益立即停止，再按原Mixed三臂/Decode守护验证。`key-operator-analysis`的配置迁移反例用于约束这一方案，未直接移植其他模型参数。
3. 次候选为BMM相邻数据搬运/布局：先用现有correlation与运行函数来源证明BMM用途、shape/stride和物化开销，再选已有实现替换或窄融合。当前来源/可减少字节尚unknown，不先新写kernel。通信先确认实际collective和重叠范围，不把同步墙钟或PCCL累计时长当可消除开销。

旧规划以H4 Sparse MLA/索引为条件候选；本次将MoE/BMM提升为优先核查对象，但主机缺口与Mixed缺测使该排序仅为partial-trace observation。无PR代码、提交推送、跨平台验证或四正式场景验收。

## 外部证据

- 新授权接续：当前服务3465683/539586647、用户三库内容SHA及原argv、health/idle已重新核验。原生`AsyncLLM.start_profile/stop_profile`通过`asyncio.to_thread`启停CPU profiler，前端with_stack=false且没有通用Python采样。保存CPU-only三臂诊断`capture-repair-02/commands/frontend-cpu-probe-v1.py`，SHA `20eeef4aa56b0e82f59bb078a42fdb118174ba13f65e52addfafe2075e5458e6`；仅独立torch CPU进程，验证线程池/同线程/同线程Python stack，不发模型请求或改服务。CPU证据确定后再选择最窄诊断修复，不修改vLLM源码。
- CPU三臂均返回0、torch2.10.0：线程池启停没有5个已执行marker或CPU算子事件，仅Trace envelope；同事件循环线程捕获55个CPU op及5个marker；同线程Python stack捕获100175个Python函数事件并覆盖5次纯Python工作函数。由此复现线程归属缺口，也证明只移动启停不能自动测到Python self-time。采集修复选择原生worker trace保留900/256窗口，配置ignore_frontend=true，API/EngineCore改用外部有界CPU栈采样并结合/proc CPU ticks，不改推理代码。保存`capture-repair-02/commands/host-tools-v1.py` SHA `61ace018568e7acc848c7051edc75cef127879d494285b9d3b9df4ce36305194`，仅安装固定py-spy0.4.1到该任务私有cpu-tools目录、no-deps，不更新容器推理依赖；采集前核验二进制SHA及精确PID/ticks归属与attach能力。
- 新采集控制器`capture-repair-02/commands/control-v1.py` SHA `7d3ef471969a2ace7ba2041682d2d0db5da03c92af85fec99bc241ce2b000b1a`已保存待prepare：原预热/请求/设备窗口保持，每阶段独立检查服务日志新增区间的start/stop HTTP200、客户端原生结果与64/128成功计数；不再要求客户端打印服务端短语。CPU sampler `commands/host-sampler-v1.py` SHA `8b066c734eaf947827018b8107c9df32ab60ec6a23dc144cae089e49672e3473`以49Hz采API/EngineCore全部Python线程，绑定PID/ticks、时钟及二进制SHA，停止只发给精确自有sampler。固定二进制SHA `e7c2de2dc54449ec88c086f1859555b4e34e63ccdcf3f8804496f9306cd44de6`，真实API只读dump已成功，未发模型请求。统计栈样本不冒充精确Python self-time；CPU总开销用/proc累计调度时间，设备/通信按逐rank区间分析。全部采集终态后恢复原服务并做完整模型/FULL/C64回归。
- 23:36:33 prepare零生成/两条native dry-run通过，新freeze SHA `4aa78e4453222bcb735a2e00e4c4d3e47d8133ca00ac93082714fbf94ccc2d33`。4项独立CPU coverage fixture通过（缺worker、缺host、Mixed无新接纳均拒绝），测试SHA `6918983020c6741cf569fc1667b3e2834666d190cf8a898590e6768c0ac870e5`。旧轮缺前端证据不放宽：新契约明确更换host观测机制，worker内容/预热/长度/请求数和门槛保持，逐份新证据验证。
- 23:38:25新控制器唯一派发，宿主PID1390730/start539931506；以本子目录dispatched.json核对，旧父目录failure/completion仅为历史，不重复启动旧控制器。采集完成前不安装候选或额外发请求。
- 23:46只读确认新诊断实例3480444/539932326的minimal、semantic、C64及final-audit均passed；原完整范围和FULL检查通过，Decode稳态准入正在进行。新只读heartbeat `glm-decode-mixed` 已创建，30分钟、仅实质变化通知，不重复派发或自行安装候选；首次创建因缺destination在工具参数校验前失败，补destination=thread后唯一创建成功，无重复monitor。
- 23:56:37 Decode采集覆盖通过：原生64/64，16worker各128次graph launch，API/EngineCore采样均return0，分别20395/25055样本、127/133 frame；末3无profiler预热1143.981/1158.508/1135.921 token/s、spread1.9744%。新host证据已真实补齐，非空文件数量并非唯一判断。capture/coverage/host-result SHA依次`84d19eb33666732158f94bcf6291b46830c6c258443473f7cf6a37a9e7250a3d`/`5dc95c6b19701ef6bd1f705a283211a07836d73c2e346ad11fcf0388bce3105d`/`7d3e4c55a31626313e74f8f8e6ef8cc4ba108a8c10c6d53a01d18ad5562fa8a3`。2026-10-23 00:00 Mixed准入已有1轮原生validation；仍由唯一控制器继续，全部采集和恢复结束后再做离线归因。
- 00:16:26 Mixed的8预热+1probe均完成，末3吞吐1147.613/1156.501/1152.704 token/s、spread0.7710%，原生record SHA `c0adf7afde38f0f3a25858c0ca6c46a09a920c2d433222142f454675408d70e8`，已开始原声明的单次采集。保存终态只读审计命令`commands/current-audit-v1.py` SHA `58617044844e6ba8c8e33142a155a9acc9ad51f1fb6559bc6aef8a474b8e2df7`，仅在控制器结束后执行，验证当前恢复实例/身份/health、sampler均退出、16worker无hook；不发生成请求。
- 实际MoE库来源补证：当前API、EngineCore及rank0 worker均未设置`VLLM_FL_USE_FLAGGEMS_VLLM`，Plugin lazy getter默认0；PPU不满足NVIDIA完整API guard，分步CachedOp→FlagGems adapter因此调用`flag_gems`。当前通用alignment来自`FlagGems/src/flag_gems/fused/moe_align_block_size.py`，E288走标量stage2；不能把FGV已安装当作MoE实际来源，也不能据此推断GLM专有算子不使用FGV。后续候选须以实际命中库为边界，保留用户当前开关和Plugin源码。
- 新离线分析器`capture-repair-02/commands/repair-analysis-v1.py` SHA `2dd3728994b33b18d108d4d32b86a99e6077ea84f3c8a75e666b68d0a099edf0`已准备，5项CPU相关性fixture通过（SHA `4829d6621e6b2e75cb910d6aa995e2d7456beb33b4530d36ed07c7932918256f`）。仅在采集及恢复终态后执行，避免干扰预热；结合唯一runtime correlation、实际FULL_DECODE_ONLY graph与同trace时钟分组，含new Prefill的step保留可能混合Decode，非graph cached仍unknown，不凭marker数量分配token阶段。host栈样本与/proc CPU秒分开报告，设备/通信逐rank并集，不跨rank相加。
- 分析器补为`commands/repair-analysis-v2.py` SHA `9e967a7815ebad561a6f33f3950cc3e6163d8c59617caae40f7c53a64c49773f`，仅增加利用trace的baseTimeNanoseconds与event ts构造rank0设备观测epoch窗口，选取该窗口内/proc采样端点统计CPU秒，避免拿整段客户端CPU计数和末段设备窗口混算。没有重采或改原字段，端点约100ms分辨率、CPU tick量化和重叠限制保留。5项phase fixture复测通过，测试SHA `dccc58ecdd562d290d1f692b74fbad7605ff7dd33c7db90fad71c3cf00b7a2a7`；v1未执行、保留。
- 现有已核验基线与最终身份：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261022-point54-user-plugin/steady-p1k-01/final-readonly-audit-v1.json`，SHA `7f906a972b3bced4d7e191fd5d766edf2e42ea3053d07e230828a468e1f51028`。
- 当前Plugin源码根：`/workspace/e2e-opt/glm53-20260911/vllm-plugin-FL-review-20261020-p45-v4`；原生vLLM源码根：`/usr/local/lib/python3.12/site-packages/vllm`。本次只读源片段、进程、环境白名单和GET health/OpenAPI取证，没有全树新审计或采样产物。
- 远端唯一根（已创建）：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261022-point55-steady-profile`。本地不创建history或过程脚本目录。
- 待保存命令 `commands/control-v1.py`，SHA `2b0de47cc137a625489a198ddd2d95777575e11e632dc1b4294df6932c621fd1`；`commands/host-observer-v1.py`，SHA `c47c53a37637d1fc21494eede4fedbf95a51b12fb93cd27393607df520f56c6d`。AST通过，执行前再冻结零生成检查与完整输入SHA。
- 旧工具包不含profiling Skill，额外打包当前完整Skill两文件到 `commands/profiling-skill-v1.tgz`，SHA `9f1b69d9290853d3aaa9dc628c8481abd3a2a024ed277ca2941da50994890103`，bundle SHA `c65d7be2635d0850cf7830113f88b0840c5d5b9b5b02ae30328474a34c0fea46`；仅补方法归档，不修改既有runner。
- 22:11:38 prepare零生成通过，冻结60份输入，`freeze.json` SHA `e3ad688c286b714b878a3b86c5bddc7f447f56351d2854f77e587505283db287`。两条native profile dry-run通过，派生客户端seed74283（base42），temperature0、ignore_eos、finite batch；旧点54基线控制器已退出。下一动作是上述保存控制器的唯一dispatch，才会停止精确旧API并临时开启profiling。
- v1 dispatch在派发前身份检查遇到 `KeyError: containers`：轻量`m.live()`不返回容器清单，完整`g.capture()`才有。只读核验确认没有dispatch-started/restoration-armed/diagnostic，旧API3318148/537692913及health保持不变，零模型请求、零停止。原v1命令和freeze保留。已保存v2编排修复 `commands/control-v2.py`，SHA `208cf706ac8a9a1795f42f4125c7d0da3e94586b08a92aceff57fca4895b4cf4`：仅在缺字段时只读inspect原冻结精确容器名；新freeze-v2引用原freeze，所有采集/预热/阈值/恢复规则不变，不修改用户源码或旧证据。
- 22:18:02 v2零生成恢复prepare通过，`freeze-v2.json` SHA `ca8974bef33794d53b4a318c9934df0b8ae50d44c7408191c1d24b8160da0f99`。27项本地工具单测通过（原21项+6项容器读取/漂移/原freeze不可变），测试SHA `ec58560c58f597137b04feaea10ffe4241771cd5dde42f869cc0a8e34c5a220d`；不是模型测试。
- 22:19:03唯一dispatch宿主PID3884371/start539455289；22:21:33只读见新诊断API3377600/start539456108、argv仅多profiler配置、FULL捕获11/11和Application startup。完整回归/两段采集/最终恢复仍待控制器完成，未见终态错误文件。旧原服务停止的恢复责任已22:19:07登记，未改交付脚本或用户源码。
- 22:23:19只读检查：diagnostic minimal与semantic均passed，C64/路径最终审计待落盘，未见failure/restore-failure/completion，尚无profile结果。
- 22:26:21只读检查：C64仍无终态结果，最近服务日志显示64 running/0 waiting，health200；不据此宣布C64通过或性能稳定，仍由唯一控制器按原预算继续，未追加请求或干预。
- 离线分析脚本 `commands/trace-analysis-v1.py` SHA `f63e6a415a5558dce6d9c720ba366b36b915e2fb1a5c40aca73a9009a4eb753e`，11项mock测试通过（SHA `8896cd66c5e1ea8d5782e5e5fcc1719525ad4db4335f037bf291a2020cc9e2fc`）。采集和恢复终态后已执行，输出`decode-trace-analysis-v1.json` SHA `b35791a020483aaf01d0da256dfc4527ef466cd04b7212fff49678eb0503da33`：16 worker可做局部分析，原frontend缺口使总体仍incomplete。逐rank区间并集/重叠、同tid已记录墙钟exclusive、相关metadata分别保存；不把墙钟exclusive当CPU排程时间、不把无记录间隙当硬件idle，设备阶段缺乏关联仍unknown。
- 离线补充计划：原通信regex漏掉实际`pcclKernel_twoShotAllReduceKernel`符号，保存`commands/trace-comm-analysis-v1.py` SHA `cdc2f54177f3f3af5be5bbc05efa50e89f6ebef96920cae4de6e6157b3fdc770`后，仅对既有SHA绑定trace补充显式PCCL collective符号分类，逐rank/device计算并集/重叠；11项本地fixture通过，测试SHA `328f54fa8d47d099259ed0dd0176178dd636750af96abc8ca1ba441f9057a6fb`。不发模型请求、不修改旧产物、不能升级原coverage或推导通信关键路径。
- 本地`validate-local --records`整体未通过，报告既有其他模型状态/链接和过程产物问题；未清理或改动无关用户文件。本点过程脚本均临时/远端保存，不放入models目录。
- 22:56只读确认控制器已终态：22:40的断言错误是在客户端日志中查找服务端`Profiler started/stopped`词句；原生Decode diagnostic为complete、64/64成功，服务端两个profiling接口均HTTP200，已有17份trace，尚未验证内容覆盖。22:44原启动方式及完整minimal/FULL/C64恢复通过；新实例3465683/539586647，DB正常写入SHA变为6a7822d7…，严格rebind未签发，原173/198不改。Mixed未运行。保存零生成恢复命令`commands/evidence-recovery-v1.py`，SHA `f01d603a67f643a00c621956fd324b586d6f438b8daff3ac0c87b9d9907a5a60`，仅复用已有原生证据、原覆盖校验及当前只读恢复审计；不改原失败/分数/阈值，不重启或重采。
- 22:59证据恢复完成：`evidence-recovery-v1.json` SHA `1249fd93ec2ef730fb767be7a9430c1e0a523470371104761cfe4d951e210578`；`decode-trace-coverage.json` SHA `d06805728bd10324ab8aad1dc9987f190277b5ca8f829570a7700b74dbf91b53`，16 worker通过、frontend缺CPU活动，因此总体incomplete。`heartbeat-terminal-audit-v1.json` SHA `410250a542407e94b33309540e9641b8e39f0196567baac8acd28ad36c4dddd6`确认当前恢复身份/健康；它不是精度gate。
- 原`failure.json` SHA `1dbad081d52b9c1cc34004e746b3ae2338879adb73241916da8ecaf66f351628`、`completion.json` SHA `96cc49f628dc678e8f18da997e58cb0056f8a5bd77a587701e2de23c46d688af`和`restored/final-audit.json` SHA `922e0f9045f9b49dbc917c9e726ecd2950ae79e6bfddb3da18925997c95b766d`均保留。旧日志断言失败不等于C64失败。
- 通信补充已执行、11项本地fixture复测通过：`decode-communication-supplement-v1.json` SHA `a02826de63bfd5d2af89fe9f1d7acdc9689545f5b33e2acd9bf7b3fe77054cbc`，逐16rank SHA绑定完成；只有worker分类成功，不将输入coverage改成passed。原始大trace留远端，本地仅索引/摘要。
- 23:12工具确认删除`glm-decode-mixed-profiling`。本轮终态恢复与partial归因闭环；未启动补采、新候选、额外模型请求或修改推理源码/参数。当前待主聊天处理可观测性与恢复绑定缺口，再按上述优先级推进。
