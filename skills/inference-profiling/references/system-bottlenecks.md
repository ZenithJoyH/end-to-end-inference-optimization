# 推理系统瓶颈诊断

在已有低开销证据无法区分根因时，按本轮问题选择分支。CPU、通信和负载不均衡可能是同一条等待链的不同表象：先找延迟从哪里产生，再选择实现或配置实验。本引用属于现有 `capture/analyze/reprofile`，不增加 runner、采集包装器、模式、schema 或门禁。

需要实际执行时，按入口信号自动选择[工具步骤](system-diagnosis-tools.md)的相关配方：CPU区间/栈、等待与配额、同组通信/链路、rank来源对照表或服务/KV/graph/资源快照。已有证据足够直接分析；工具选择、失败替代、窗口/预算与返回排序按配方执行，不把每个分支串成全量采集任务。

## 覆盖与路由

下表是诊断入口，不要求每轮全量采集。先复用当前服务、场景和阶段绑定一致的证据；缺什么且会改变决策才补什么。

| 类别 | 触发信号 | 最小证据与首个分流 |
|---|---|---|
| 请求接入与返回 | 服务内部快、客户端 TTFT/ITL 慢 | 关联请求 ID 的客户端发送/接收、服务接入/首 token/输出时间和连接/流式缓冲；分开客户端、代理、服务与慢客户端背压。跨时钟时间不直接相减 |
| 排队与准入 | Waiting 增长、尾延迟放大 | 到达/准入/完成速率、排队时间、失败和队列趋势；区分服务容量不足、并发限制和长请求阻塞，不把等待记为 Prefill kernel 时间 |
| 调度与批处理 | 小 batch 吃不满或大 batch 延迟陡增 | 每 iteration 的实际 running sequences/batched tokens、调度时长、batch/shape 分布；区分调度 CPU 开销、工作点和资源不足 |
| Prefill/Decode 干扰 | 长输入到来时 Decode ITL 抖动 | phase/iteration 边界、Prefill chunk、Decode 等待、KV/抢占和 Mixed 时间线；分阶段专项只用于证伪，回到父 Mixed 场景验证 |
| CPU 热点 | 设备空隙、某线程满核、请求处理跟不上 | 本文 CPU 分支：进程角色、线程 CPU 增量、调用栈与阶段关联，区分做事与等待 |
| CPU/主机资源 | 周期停顿、线程多但吞吐低 | CPU quota/cpuset/affinity、调度等待、上下文切换、NUMA/内存/缺页；同窗口采样，区分限流、抢占、内存与线程竞争 |
| 通信 | 卡数增加收益小、collective 长 | 本文通信分支：同 group/iteration/collective、消息量、参与者就绪与设备完成；先排除晚到，不凭 kernel 名称判链路慢 |
| rank/副本负载不均衡 | 少数 rank 忙、其余等待 | 本文负载分支：TP/PP/EP/DP 分组和同逻辑工作量；区分分工差异、路由倾斜和慢硬件/主机 |
| KV/显存容量 | 并发受限、长输入骤慢、重算增多 | 有效 KV 预算与 blocks、驻留长度、prefix 命中、抢占/重算、graph/workspace/临时张量分账；容量分析可交 Roofline 引用，不用空闲显存单点代替证据 |
| 带宽/搬运 | copy 多、计算单元不满 | HBM 读写或明确估算、H2D/D2H、clone/cast/layout 完整路径；先证明实际字节和冗余，再按 SOP C5 交 Roofline，不能只看利用率 |
| 执行组织/同步 | 小 kernel 多、launch 间空隙 | host 调用到设备执行的关联、stream/event 依赖、分配/同步栈；区分 CPU 提交慢、设备队列积压与必要依赖，不能相加重叠活动 |
| graph/编译/执行路径 | 动态 shape 抖动、配置无收益 | 实际 graph replay/捕获覆盖、编译事件和 shape、backend/impl_id/fallback 命中；区分稳态反复编译与首次预热，默认不转向冷启动优化 |
| 算子效率 | 特定 shape 慢、算力带宽都低 | 阶段/shape/频次、完整调用和实际实现；转关键算子 Skill，判断计算、带宽、并行度和 padding，包含量化/反量化与 merge 成本 |
| 系统干扰/运行状态 | 结果漂移、长尾或持续降速 | 同窗口频率/功耗/温度、设备/CPU/内存/网络竞争、链路错误、日志/profiler 扰动；记录共享使用者，不擅自清场。冷启动仅在用户指定目标时另立契约 |

请求/队列/工作点判断交回协调者与性能 Skill；算子与 Roofline 按既有路由派发。证据足够时直接提出首个单变量实验，不为表格补满而采集。

若当前服务采用 Prefill/Decode 分离部署，额外关联同请求的 Prefill 完成、KV 传输/接收就绪、Decode 准入与首步；区分 KV 搬运、目标端排队和握手等待。没有该架构则记不适用，不为诊断新增部署。

## 证据绑定、工具选择与停止规则

1. 在当前实验记录写明问题、已知与竞争解释、输入证据、执行者、缺口、操作范围/预算、停止条件和预期产物。新采集/attach 才核当前目标环境及适用镜像/挂载门禁，不在源适配容器中采样或实验；纯 analyze 核既有报告原身份/范围与适用性，不要求源 PID 存活或重新访问目标。metrics/NIC-only 按各自服务/接口核身份，不增加无关 PID 前置。
2. 按证据类型绑定原报告服务、采集时段、命令/工具版本及适用的 PID/TID/角色、设备/rank/group；离线分析操作时间不冒充原采集时段。短期 PID 原文留外部，长期保留必要映射摘要、路径和 SHA。不要把其他服务或客户端线程误记为 worker；共享同一 capture 的分支复用原身份，只映射各自实际覆盖，不复制派发采集。
3. 选择能回答问题的最小证据：现有请求指标/日志、线程资源增量、采样栈、调度/阻塞报告、设备时间线、通信原生报告可以互补。`vllm_profile.py`、`sglang_profile.py`、`trace_to_summary.py`、`trace_analysis.py` 不自动提供通用 CPU/off-CPU 或通信链路诊断。
4. 新执行只核实际使用工具的环境、版本/帮助、输出语义、权限和开销；复用原报告仅核其能力/语义与覆盖，不重复工具发现或远端预检。Linux 的 `pidstat`、`perf`、`py-spy`、平台 profiler 按已装参数选用。工具/attach 权限不足就保留已有有效结果和缺口，不安装、修改安全设置、增加容器权限或加载全局探针。只采已派发范围，不用 system-wide 代替精确绑定。
5. CPU/系统报告分别验证来源、采集时段、非空可读、指标单位/累计或区间语义、采样数/丢样/截断/符号覆盖和角色覆盖；新采集需证明来自本次执行，复用有效报告不要求新时间戳。日志验证实际行为而非配置声明。counter/系统报告有效不等于 device trace 已通过；无需设备时间线的问题不强制重采 trace。报告有效性与回答当前问题所需覆盖分别判断，缺失 native 栈、off-CPU 或 peer 覆盖仅限制对应结论，标 `unknown/incomplete`，不要填零或为补满字段重复采集。
6. 对齐时记录时钟域、工具换算和误差。同 Host 也不假定 CPU 与设备原始时钟可直接比较；跨 Host 用请求/iteration/microbatch/collective 序号关联，并核实同步或校准精度。误差大于待解释 skew 时不计算精确晚到量，可比较本地持续时间、顺序和重复模式；不通过任意平移让时间线“看齐”。
7. 采样会漏掉短事件，attach、全栈、debug 日志、调度 tracing 和多 rank 采集也可能改变调度/路由。记录范围、采样率、停顿、丢样与负载差异；不把 profiled batch 变化当原服务事实。不支持、权限不足、同输入预算耗尽时返回缺口和重开条件，不无限升级采集强度。只控制本任务采集器，结束后核验其退出；不擅自重启服务。

原始栈/调度报告/通信日志与汇总保存在批准的外部 case 目录。交回原协调者，复用当前优化点的 evidence/hypothesis/next-action；不建立 profiling 历史目录或第二套验收记录。

## CPU 热点与等待

### 触发与最小取证

当设备时间线有空隙、enqueue 间隔大、tokenizer/API/调度吞吐不足、某 rank 经常晚到或尾延迟周期抖动时：

1. 分清客户端、API/网关、tokenizer/detokenizer、scheduler、model worker、通信 proxy 及其线程。记录同一代表性窗口的每线程 user/system CPU 增量、可运行/阻塞状态、上下文切换、请求或 iteration 进度。说明 CPU 百分比采用单核还是全机口径；全机平均低不能排除一个关键线程满核。
2. 核对实际可用核心、cpuset/affinity、CPU quota 和父级约束、线程池规模及 NUMA 放置；读取同窗口 cgroup 限流计数增量而非开机累计值。cgroup v1/v2 文件与单位按当前系统核实，不能混读；v2 可参考 `cpu.max`、`cpu.stat`，但具体统计范围取决于当前内核，父级约束不可忽略。[Linux cgroup v2 文档](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html)
3. 只对疑似关键角色补一段有界 Python/native 栈；记录采样是否包括睡眠线程、是否只看 GIL 持有者、是否能展开 native/内核栈、Python 构建与工具兼容性。`py-spy` 的 native/GIL 选项是可选采样视角，不是完整的调度或 off-CPU 等待时间证明。[py-spy 官方说明](https://github.com/benfred/py-spy)
4. 对主要空隙关联 host 提交、设备启动/完成和同步调用。host API 持续时间可以包含等待设备，PyTorch `self_cpu_time` 只排除被记录的子调用，不自动等于 OS 的 on-CPU 时间，也不覆盖全部 Python/native/内核活动。[PyTorch Profiler 文档](https://docs.pytorch.org/tutorials/recipes/recipes/profiler_recipe)

### 分流与首个实验

| 已支持的机制 | 需要区分的反例 | 首个单变量实验与拒绝条件 |
|---|---|---|
| 关键线程 on-CPU 工作多：Python 调度循环、元数据、tokenize、序列化、采样或 native 处理 | 栈中出现函数不等于它耗时；inclusive 栈不能重复求和；高 CPU 也可能是轮询 | 针对已定位的重复工作、批量处理或既有线程池参数只改一项；预期该角色 CPU 工作和设备空隙同时下降，否则拒绝该因果解释 |
| runnable 但得不到 CPU，或被 cgroup 限流 | 进程睡眠/等待设备与 CPU 争抢不同；全机还有空闲核心不排除 cpuset/quota | 在已授权的任务资源范围内，仅调整线程数或亲和性等一个变量；quota 修改若超出现有授权只提交方案。限流/调度等待未改善或只是转移争抢则不保留 |
| off-CPU 阻塞：锁/futex、IPC/队列、网络/I/O、页缺失 | 等待上游无工作、设备同步属于不同依赖；锁栈不自动证明 GIL | 由调度/阻塞证据定位等待对象与生产者，单改相应批量/队列/数据路径；等待减少但上游供给与端到端不变时重新归因 |
| 线程竞争、GIL 或 native 线程池过量 | Python 线程多不证明 GIL；只有 GIL 持有者样本不能证明其他线程等它 | 核实 Python 构建及 GIL/锁证据，只在已确认机制下调整一个线程池或并行组织；上下文切换下降但目标吞吐/尾延迟不改善则停止 |
| NUMA/主机内存导致提交或通信 proxy 慢 | 同时更换 CPU/内存/设备掩盖变量；远端分配量不等于关键路径成本 | 关联核心/内存与设备/NIC 放置、缺页和本地持续时间，仅在专属资源上做一项放置实验；固定 workload 并核验实际放置，未命中不算证伪 |
| host 在等设备、通信或必要同步 | CPU 火焰图中的驱动/synchronize 热点可能是下游慢的结果 | 沿关联设备/collective 依赖路由后续诊断；不先改 CPU 计算，不删除正确性所需同步 |

示例：全机 CPU 只有 15%，关键 scheduler 的设备提交却周期停顿。若目标 cgroup 的限流增量与停顿对应，支持资源约束假设；若线程持续 on-CPU 且 metadata 栈占主导，支持主机处理假设。二者需要不同实验，不能从“CPU 低”直接排除主机瓶颈。

## 通信、同步与等待

### 触发与证据

当 collective/点对点活动长、扩卡收益差、跨机明显变慢或通信阶段抖动时，先确认实际通信库与路径。NCCL 只是 NVIDIA 示例；其他平台按其已安装库与原生工具核实，不套用 NCCL 环境变量。

1. 绑定实际 TP/PP/EP/DP 及子通信 group、成员、设备/Host/NIC、通信库版本与实际 transport。保留 collective 类型、序号/iteration/microbatch、dtype、shape、各 rank 发送/接收量、调用次数、stream 和 group size；all-to-all 不假定每 rank 消息量相同。
2. 对同一逻辑通信，关联上游计算完成/输入就绪、host enqueue、设备开始/完成、下游依赖开始。host 返回可能异步，kernel 开始也可能仍在等 peer，不能任选其中一个当所有 rank 已就绪。缺少这些事件时不强拆精确阶段时间。
3. 至少覆盖被怀疑的晚到者和等待者，说明其他成员缺失的结论边界。先用已有轻量 per-rank 证据筛选，再补代表性成对/分组时间线；不机械要求所有机器、所有 rank 同时重采。若未覆盖全部相关成员，不排除未采 rank 是真正慢源。

### 按机制分流

| 机制 | 可区分的证据 | 下一项实验 |
|---|---|---|
| 参与者晚到/输入未就绪 | 同 collective 的到达差异与某 rank 前序 CPU/计算/copy 长尾重复相关 | 转 CPU 或负载分支，单改晚到源；通信等待缩短不等于链路带宽提高 |
| 小消息启动/同步成本、调用过碎 | 同阶段大量小消息，消息尺寸和频次支持延迟主导，尚未证明带宽不足 | 通过现有框架扩展点合并/减少一类通信或调整一个批处理变量；计入新增缓冲、等待和计算 shape 变化 |
| 传输/算法/拓扑限制 | 排除明显晚到后仍有稳定通信服务成本，实际链路/transport、消息尺寸与计数器支持 | 在隔离资源和已有授权内单改一个通信组织/算法候选；若需通信 microbenchmark，使用同拓扑/组/消息范围，不以独立峰值代替服务收益 |
| 重叠不足或重叠争抢 | 下游确实等待通信，或并发通信与计算争抢设备/HBM/NIC，关联依赖和资源证据可见 | 只调整一项排程/stream/通信组织，核验合法依赖和完整 iteration；两条 stream 同时活动本身不证明开销隐藏 |
| 共享链路/主机 proxy/异常重传 | 同窗口 NIC/链路错误与拥塞增量、proxy CPU、其他已知使用者对应抖动 | 先提交资源协调或限定本任务的实验；不关闭共享任务、不修改全局网卡/驱动/系统设置 |

通信 kernel 总时长可能含 peer 等待、自身计算、协议与搬运，不能当成纯网络传输时间；多 stream/rank 时长不能相加作为端到端成本。即使能界定“最后参与者就绪到完成”的窗口，它仍可能包含同步、协议和设备调度，未有原生传输证据时只称通信服务窗口。逻辑 payload/时间与物理线速、bus bandwidth 的口径分别记录。

拓扑/transport 以运行证据验证，不由“设置了开关”推定；先排查系统健康再调通信参数。NVIDIA 可参考 [NCCL 官方性能排查](https://github.com/NVIDIA/nccl/blob/master/docs/userguide/source/troubleshooting/performance_and_tuning.rst) 的拓扑、GPU/NIC/CPU/NUMA 定位方法。调参也执行既有最小正确性、适用 graph 和无 profiler 验证；归约次序变化可能影响数值，不以“只改通信参数”豁免回归。

示例：rank 0 的 collective 比 rank 1 长，但 rank 1 前一段 GEMM 更晚完成，通信结束接近。若边界与时钟支持，这首先支持 arrival skew；若各 rank 输入早已就绪而设备通信仍长，再查消息量、实际链路与争抢。仅有两个 kernel 时长不够区分二者。

## rank、专家与副本负载不均衡

先分清“不均衡的工作量”和“相同工作量执行更慢”。把慢 rank 的前序 CPU、计算、KV、copy、通信和等待串起来，不能用设备利用率平均值找根因。

1. **确定可比单位。** 绑定当前 phase、逻辑 iteration/token/microbatch、请求集合、实际并行 group 与角色。在同一单位记录每 rank 的有效/填充 token、query/KV 长度、local shape、专家分布、计算与通信时长及等待。不同 rank 的异步 DP iteration、不同 PP stage 不能直接逐行相减。
2. **按并行方式解释。**

   | 并行方式 | 比较依据 | 容易误判的情况 |
   |---|---|---|
   | TP | 同 group 同 iteration 的 local shard/head/shape、计算量、输入就绪与通信参与 | 维度不可整分、不同分片或 padding 造成结构性差异；卡忙不等于有效算力高 |
   | PP | 同 microbatch 的各 stage 实际层/算子工作、发送接收等待、bubble、首尾 stage 特殊工作 | 各 stage 本来不同时开工；填充/排空与稳态分开，不能要求同绝对时刻利用率相同 |
   | EP/MoE | 每 rank/专家接收与实际执行 token、padding/capacity、专家 GEMM shape、dispatch/combine、跨机流量 | token 数相同仍可能因小专家 batch、分布或容量 padding 耗时不同；总 token 平均掩盖热点专家 |
   | DP/服务副本 | 同到达窗口的排队、有效输入/输出 token、缓存状态、完成与失败、资源配额 | 请求数相等不等于工作量相等；长短请求、prefix 命中和路由造成差异，不是模型并行 rank 的逐步 barrier |

3. **判断持续还是偶发。** 保留代表性多 iteration 的最慢者身份、工作量及 max/median 等离散度和样本数，不设通用通过阈值。慢者随 token/专家路由变动，优先查工作量分配；相近工作量下固定设备/Host 更慢，转 CPU、拓扑、频率/错误或共享竞争检查；PP 还须先排除设计性 stage 失衡与 bubble。
4. **做一个有边界的实验。** 按已支持机制只改一个路由/批处理/专家组织/并行分组或 stage 分配候选，保持语义与资源范围；改变卡数/拓扑须另立可比基线。单改 shape 或负载策略可能增加 padding、通信、KV 与排队，必须包含这些成本，不通过丢请求、丢 token 或改变专家语义“平衡”。
5. **停止与回验。** 如果差异落在时钟误差/样本波动内、缺少关键成员或工作量不可比，返回具体缺口；如果离散度下降但关键 iteration/Mixed 主指标未改善，不能保留为端到端收益。通过既有最小回归、适用 graph 和无 profiler targeted/checkpoint 验证，并守护另一阶段和尾延迟；只降低平均利用率差异不算成功。

示例：EP 中两个 rank 的接收 token 相近，但一个 rank 分到许多小专家 batch，另一个集中在少数大 batch。先核对有效/填充 token 与每专家 GEMM shape，不能把前者慢直接判成坏卡。PP 中某 stage 等待多，也可能是上游 stage 长或 pipeline bubble，应按同 microbatch 的生产与消费依赖定位。
