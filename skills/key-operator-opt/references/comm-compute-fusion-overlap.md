# 通算融合与 overlap 候选方法

用于 [SOP C3.1](../../../docs/performance-optimization-sop.md#c31-通算融合与-overlap-候选)匹配的候选。消费已有阶段、真实 shape、通信组、执行路径和时序/资源证据，按 [D0](../../../docs/performance-optimization-sop.md#d0-并行探索局部筛选与批次集成)先局部筛选，再批次集成。本文不声明任何目标平台已经支持某种原语，不新增采集器、模式、schema 或门禁。

## 1. 触发与机制分类

若通信长或跨 rank 等待可能由 CPU 提交迟、quota/NUMA、rank 工作量偏斜或上游 producer 慢造成，先用已有证据区分 arrival skew；collective 长不等于传输慢。只有未解决且会改变候选的该类问题，才由协调者复用 Profiling [CPU/通信/rank 分支](../../inference-profiling/references/system-bottlenecks.md)，而不是先加 stream 或融合。kernel 内预取等无关分支或已有足够排除证据时不新增 CPU/rank 诊断。缺少精确关键路径时保留假设和上界，可提出小证伪实验，不能编造收益。

| 机制 | 匹配信号与改善机制 | 分类与首个单变量实验 |
|---|---|---|
| 通信与计算融合（comm-compute fusion） | 算子与通信相邻，整张量落显存或 host/launch/barrier 成本可消除；目标实现允许按合法 tile 就绪交接或在同一公开调用内融合计算/通信 | 接入更优现有实现为 `operator/replace`；新数值融合/特化为 `operator/improve`。先在同组/shape 比较一个受支持融合路径与当前完整调用，不把普通异步 API 排程称为已融合 |
| stream/chunk/microbatch overlap | 存在已就绪分块与独立工作，可把部分通信放到计算之后的暴露等待之前；拓扑和执行资源允许进展 | 组织现有操作/依赖为 `framework`；新融合 kernel 贡献单列。仅改一个 chunk 粒度或一个已证明独立的排程依赖，包含 pipeline fill/drain 与小 GEMM 退化 |
| copy-compute overlap | H2D/D2H、pack/layout/设备搬运与其他块计算可独立，实际 copy 路径、内存条件和资源支持并发 | 重排/缓冲组织为 `framework`；接入已有算子为 `replace`，新 copy+compute 数值融合为 `improve`。仅改一个数据交接/双缓冲策略，计入主机 staging、额外拷贝和容量成本；不同 stream 不保证独立 copy engine 或带宽 |
| kernel 内预取/流水 | 当前 kernel 存在访存/数据依赖等待，实际编译器支持适用的异步搬运、布局或流水原语，可缩短等待 | 属 `operator/improve`。固定算法/输入，仅改变一项预取/流水安排；确认生成代码/原语实际命中，比较寄存器/shared-memory 增量与 occupancy/吞吐，不把增大 stage 默认视为更快 |

按主要收益机制分类，不按文件目录。跨层方案拆为有关联、可回退的实验，记录依赖与实际组合效果，不重复计算同一等待的节省。先评估已有公开实现是否适配，再决定新实现投入，能力未知时只安排能改变决策的最小核验。

新增 vLLM 专用通信/计算数值融合遵循算子规范，落在 FlagGems-vllm 并通过公开 API 接入；通用 ATen 实现只在既有 schema 完整语义范围内落 FlagGems。Plugin 承担排程/metadata/分发等框架组织，不接收新增数值 kernel。厂商已有通信 runtime 保持原职责边界，不要求将所有通信实现搬进算子库；私有编译器改动、共享系统和 vLLM 源码权限仍按 AGENTS。

## 2. 实际能力与依赖核验

在当前优化点记录下列决策相关事实，复用已匹配证据，不机械补齐所有项。通信组/peer/远端可见性只适用于实际含跨 rank 通信的候选；单设备 copy 或 kernel 内流水按其真实参与范围核验，不为使用本引用新增多 rank harness。

1. **绑定真实执行。** phase、query/KV/token 与 per-rank shape/dtype/layout、TP/PP/EP/DP 或子组、peer/count、设备/NIC/Host 拓扑、库与源码 revision、实际 backend/导入路径、当前 graph 模式。不能以总卡数或 NCCL 示例替代目标平台的组与传输。
2. **核实能力。** 当前 runtime/通信库/后端/编译器的实际版本与构建是否支持所需异步、分块、stream/event、设备侧同步/通信、buffer 注册或 graph 行为；编译器预取、TLE、布局和流水接口逐原语核对，不能因支持一种特性推定全部可用。源码或参数存在不等于运行路径命中。
3. **画出最窄依赖。** 每块的 producer 完成/输入就绪→通信提交与实际进展→接收可见→consumer 完成；解释哪些块可独立、哪些 reduction/非线性必须等待完整输入。host API 返回不等于设备完成，kernel 启动不等于数据已到达；合法同步不能为了 overlap 删除。
4. **协调组与执行顺序。** 同一逻辑 collective 的参与者、序号、count/dtype/分片和条件选择满足实际 API 契约；P2P 的 peer/发送接收量正确配对。多 communicator/stream 的顺序依实际库约束建立，避免循环等待；不要求无关组无条件全局串行。shape/capability guard 与 fallback 必须在通信开始前形成组内兼容决策，避免部分 rank 进入新 collective、部分走不匹配旧路径。
5. **验证可见性和生命周期。** 跨 stream/设备的 release/acquire、event/barrier 或等价原语须有当前平台语义依据；局部 event 不能自动证明远端可见。buffer 地址、所有权、别名、容量、workspace/ready flags 的初始化与复用覆盖生产、传输和最后消费；不能在异步消费前重用/释放。graph replay 不能读上轮 flags/数据。
6. **核实进展与资源。** 通信/自旋/常驻 kernel 是否可能占满执行资源，使 producer/consumer 或 peer 无法调度；确认实际 occupancy、进度保证与等待边界。没有进展保证、顺序不明、循环等待或超预算时停止该候选，不靠扩大超时或删除同步使其“通过”。

未经数学等价与原数值契约证明，不把 activation、normalization、quantization 越过 collective 归约，不提前改变全局统计的就绪条件；分块 consumer 仅消费真正已就绪的数据。归约次序或累加路径变化单列数值风险，仍按原标准和集成精度流程验证。

通信或状态写入一旦启动，异步错误/超时向上报告，不能 catch 后切 fallback 重试同一操作。只有尚未开始且无副作用时按现有策略选同契约路径。错误处理仍由任务生命周期与原通信库规则约束，不能自动重启共享服务或重建无关组。

NVIDIA 的 [NCCL stream 语义](https://docs.nvidia.com/deeplearning/nccl/archives/nccl_2307/user-guide/docs/usage/streams.html)说明 API 入队和设备完成不同，同 group 混用 stream 也可能引入相互依赖；[PyTorch distributed 文档](https://docs.pytorch.org/docs/stable/distributed.html)区分异步 collective 与使用方 stream 的同步要求。这些是一手核验入口，不是国产平台支持证明，也不能替代当前安装版本/API 的实际语义核对。

## 3. 最小证伪与实际范围的完整链路验证

含 collective/P2P 的候选验证真实相关组内的生产—通信/同步—消费完整链路；单设备 copy-compute 或 kernel 内预取验证其完整公开调用与实际跨 stream 依赖即可。单 rank kernel capture/replay 不证明通信组/跨 stream 组合可被目标 graph 正确捕获；入选前按实际候选范围补齐适用 graph 证据。目标服务要求的 graph 路径不受支持时应拒绝该路径或在操作开始前选择已验证兼容路径，不能仅标“不适用”豁免。

**快速筛选。** 选择生产相关的小代表 shape、原拓扑/通信组和数据依赖，当前实际完整路径为 reference，保持等价输入、逻辑工作量和数值契约。只改变一个融合/排程/chunk/流水变量，先做数值和完整链路对照。若缩小 rank 组或改变拓扑，结果只属于该探针，不能当原生产组已验证。串行排程可作机制对照，但不能把人为变慢的串行路径冒充原服务基线。

**比较单元。** 多 rank harness 覆盖 producer→pack/copy→通信与同步→unpack/merge→consumer 的最终可用结果，包含实际经过的 launch、buffer 准备/复用、每链路的 pipeline 启动与排空、小 chunk 对算子效率的损失。模型加载、一次通信初始化/JIT/graph capture 按稳态契约预热并单列；每次链路真正发生的 fill/drain 不能当预热删掉。持久 buffer 的容量和分配/注册成本按实际调用与摊销口径记录，不把 reference 的额外同步/分配混进对照制造收益。

**时间与资源。** 相同输入、频率/功耗状态、同步边界、预热/迭代、计时方法、实际进程组与并发条件下比较完整 local elapsed；明确最终 consumer 与所有相关通信完成的测量边界，不只计 host enqueue。跨 Host 用逻辑 iteration/块序号/collective 对应、可信本地 elapsed 或原生报告关联；没有对齐误差界不能相减原始时间戳，不能推导精确隐藏收益。多 rank/group 的完成时间按共同逻辑边界解释，缺少可比较边界时保留 makespan/关键路径未知。

分别保留当前 reference、候选完整链路，以及仅在需要判别争用时的组件单独/并发执行证据。检查通信与计算对执行单元、HBM/cache、copy engine、NIC/PCIe 与 CPU proxy 的争用；单独组件变快不代表合起来变快，分配更多通信资源可能让 GEMM 或其他请求变慢。并行探索使用 D0 的私有源码/cache/设备和相关共享资源隔离；争用测量串行。不能把 kernel duration 相加、把跨 stream 重叠区间全减掉，或只凭两条 stream 同时活动宣称收益。

**入选前补齐。** 快速部分通过后，才对入选实现补齐适用的多 rank/group、真实 shape 分布、dtype/layout、边界/非整分尾块、空 token/空专家、alias/workspace 与 fallback 行为。以独立 oracle 比较最终消费结果及必要中间状态，覆盖归约顺序、累加精度、量化 scale/舍入、routing/permutation/权重等原契约；不能只验证通信字节相同。适用 graph 完成 capture 和至少两次变输入 replay，核验 flags 重置、buffer 生命周期、真实路径和无漏算/旧数据。绑定未失效的成功局部检查可复用，不每个 tile 重跑完整矩阵。

现有证据足够就直接筛选。仅对会改变选择的能力、时间或多 rank 覆盖缺口，向原协调者返回最小诊断请求；按 C5 复用已有/在途/不可用证据及原预算。无须每 trial 新 trace、完整硬件计数器或 Roofline；不可用项保留 unknown 和重开条件，不自行开第二轮采集/规划。

## 4. 条件性首试示例

| 场景 | 可证伪候选 | 关键反例/停止边界 |
|---|---|---|
| TP 的 GEMM→reduce-scatter，或 all-gather→GEMM | 只有当前分片数学语义/布局允许且 runtime 或已有实现支持 tile/chunk 数据就绪交接时，试一项分块流水或现有融合实现；保持相同组、总工作和输出分片 | K 维未完整归约不能提前当最终值执行非线性；all-gather 分块未就绪不能读取。小 GEMM/更多 collective/pack 与 fill/drain 可能吞噬 overlap。没有实际原语或数值等价路径就暂缓，不推定默认 GEMM/NCCL 已支持 |
| EP 的 dispatch→expert GEMM→combine | 按真实专家路由/接收计数与数据就绪，在已支持实现中重叠一批可独立专家/块；验证最终 token 还原、权重与累加 | arrival skew 先查工作量/CPU；空专家、非均匀 token/小专家 GEMM、接收顺序和 combine 索引均需兼容。通信进展占满执行资源或小块效率变差时停止 |

这些示例不是实现承诺、平台推荐或新默认参数；已有快路径若不适合目标 shape，保留原 fallback 与小 shape guard。数值融合与框架排程组合分别记录依赖，最终测组合，不叠加孤立百分比。

## 5. 净收益、止损与批次集成

在原候选/规划记录写明机制分类、支持/反对/unknown、适用 group/shape/能力 guard、完整计时边界、可消除暴露成本及新增 pack/copy/launch/buffer/同步/争用成本、局部净收益区间与置信度。选择采纳、降级或暂缓及首个单变量实验/停止条件；无法由局部结果推出 Mixed/尾延迟收益时明确待测。

数值/语义、通信匹配、可见性、graph 或进展验证失败则拒绝/修复该候选；完整链路无可信净收益、小 shape 回退不稳、额外显存挤占 KV、同步成本/争用抵消收益，或预算耗尽时停止/暂缓，不靠更强 profiler 或更多 chunk 无限扫描。局部失败不污染可信隔离分支；已知服务精度阻塞仍按原规则处理。

局部入选且验证齐备才用既有 `pending` 说明“局部验证通过、整模待验证”，不进入当前组合；沿用 D0/D6 的唯一已集成点与实现身份计数，不按 trial 或批次重试推进 4–5。按 D0 回收/集成预算与 parent/实现绑定检查选择优胜互补方案：主线或依赖变化仅补受影响局部证据，再组成有界候选服务批次。模型 smoke/最小回归与服务性能覆盖按 D7 复用已有/在途合法结果，不固定依次重复 targeted、checkpoint、formal；所需覆盖通过后才晋级。含新数值融合/backend/算法或 rank 数据/通信等高风险的批次，在集成里程碑立即执行原正式精度一次，不要求离线每成员各自整模再重跑组合，不在未通过时继续叠加。组合失败按依赖/单变量二分并复用有效局部检查；无必要不机械做全部消融，未证明独立 E2E 贡献保持 unknown。最终正式精度、四场景与跨阶段守护不变。
