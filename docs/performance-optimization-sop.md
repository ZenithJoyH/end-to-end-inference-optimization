# 端到端推理性能优化 SOP

## 文档状态

- 版本：`0.36`
- 状态：已包含本项目实际案例与导入案例；导入案例的性能数字尚未在本项目复测
- 最后更新：2026-09-14
- 维护方式：由已完成或明确失败的实际优化案例持续修订

本 SOP 是工作入口，不是固定真理。它只保留能够提高诊断效率、实验可比性、正确性或交付质量的步骤。不同模型、平台和业务 workload 可以有不同分支，但任何删减都需要说明原因。

## 1. 使用方式

每个优化任务开始前：

1. 阅读本 SOP。
2. 在 [cases/README.md](cases/README.md) 中按模型结构、平台、引擎、瓶颈层级和优化目标检索相关案例。
3. 只复用与当前 shape、dtype、执行模式和软件 revision 相符的经验。
4. 创建独立案例目录，并从 [cases/TEMPLATE.md](cases/TEMPLATE.md) 初始化记录。

任务结束时：

1. 完成案例记录，包括失败实验和回退。
2. 判断本次结果是偶发现象、环境内可复现经验，还是具备迁移价值的模式。
3. 只有证据改变了后续决策时才修改 SOP。
4. 更新案例索引和 SOP 变更记录。

workload 可比性、指标决策、schema 与最终报告字段统一见 [实验契约](experiment-contract.md)，每次任务同时记录执行规则版本和验收范围。

正式精度 runner 位于 [`test/Accuracy_test/`](../test/Accuracy_test/README.md)；参数化工具、结果门禁、性能工具和验收模板见 [`evaluation/`](../evaluation/README.md)。

端到端优化中的正确性和精度步骤统一由 [推理精度评测技能](../skills/inference-accuracy-evaluation/SKILL.md) 编排。SOP 定义触发时机和门禁，Skill 根据 `baseline-sanity`、`minimal-regression`、`formal-gate`、`gate-check` 模式调用现有工具，不维护第二套 runner；前三种模式实际启动评测进程时创建绑定当前任务的 heartbeat 进度通知，默认每 30 分钟一次。

正式分数低于预冻结阈值、必要的最小回归失败或评测证据无效时，调用独立的 [推理精度问题定位技能](../skills/inference-accuracy-diagnosis/SKILL.md)。超时、空输出、截断、重复或格式异常可按需诊断，但不单独使精度失败或中断性能优化。

端到端优化中的无 profiler 性能测量统一由 [推理性能评测技能](../skills/inference-performance-evaluation/SKILL.md) 编排，按 `baseline`、`targeted`、`checkpoint`、`formal` 模式调用现有 benchmark 和比较工具。Trace 采集与热点归因由独立的 [推理 Profiling 技能](../skills/inference-profiling/SKILL.md) 编排，按 `capture`、`analyze`、`reprofile` 模式调用 profiler 工具；两者不维护第二套 runner，也不混用计时结论。

多轮实验后的证据归纳和下一轮方向重排由 [推理优化规划复盘技能](../skills/inference-optimization-planning/SKILL.md) 执行。它消费已有实验与各评测 Skill 的结果，不自行补造测量；默认每 2–3 个实验触发一次，遇到组合交互、热点迁移、结论冲突、连续失败或高成本决策时提前触发。

### 按阶段查阅源码资料

| 当前阶段或信号 | 优先查阅 | 查阅边界 |
|---|---|---|
| A：核验执行栈、Plugin 注入和框架扩展 | [vllm-plugin-FL 架构分析](vllm-plugin-FL-analysis.md) | 先核对目标 revision、安装方式与真实导入路径 |
| C：热点指向 vLLM 专用/融合算子 | [FlagGems-vllm 仓库讲解](flaggems-vllm-analysis.md) | 沿 Plugin 显式调用、包级导出和 vendor backend 证明命中 |
| C/D：热点指向普通 `torch.*`、ATen 注册或通用算子 | [FlagGems 仓库讲解](flaggems-analysis.md) | 沿注册 key、最终函数对象和 profiler 区分通用/vendor 实现 |
| C/D：已收敛到具体关键算子 | [关键算子技能](../skills/key-operator-analysis/SKILL.md) | 只加载相关算子材料，不套用历史硬件、shape 和 revision 结论 |
| D/E：形成 Plugin 最终候选 | [Plugin 设计与 PR 准备](plugin-change-review.md) | 同时复核非目标模型/平台、可选依赖和跨仓库改动 |

FlagGems 和 FlagGems-vllm 可能存在同名或相近实现。不得按仓库名或文件名猜测服务来源；以目标代码 import、ATen 注册、运行中函数对象和 profiler 命中证据为准。静态分析只帮助缩短定位路径，不能代替目标环境测量。

## 2. 证据等级

经验采用以下等级，避免把单次实验过早泛化：

| 等级 | 含义 | 可用于 |
|---|---|---|
| `observation` | 单个案例中的现象，尚未稳定复现或因果未闭合 | 提醒和后续假设 |
| `reproduced` | 同一环境重复出现，A/B 与回退能复现实验方向 | 当前模型/平台决策 |
| `transferred` | 在不同 workload、模型或硬件条件下复现，且适用边界明确 | SOP 推荐路径 |
| `invariant` | 由正确性、安全或测量有效性决定，不依赖具体性能结果 | SOP 强制门禁 |

单个成功案例默认不得高于 `reproduced`。公开资料、理论推导和源码分析可以增强机制解释，但不能代替目标环境实测。

## 3. 阶段 A：定义目标与冻结环境

### A0. 读取已完成的模型适配交付（按需）

当用户指定基于“新模型适配”项目中已经完成适配的某个模型开展性能优化时，只读访问 `/Users/baai/Documents/ChatGPT/新模型适配`，仅检索该模型相关案例、配置和交付记录。提取模型/served name、权重路径、平台与 Host、源适配容器及镜像、启动参数、引擎与 Plugin/FlagGems-vllm/FlagGems revision、挂载、graph 配置、已有精度/性能结论和已知问题。

在当前案例记录上游来源绝对路径、读取时间、文件 revision/SHA 和事实摘要。上游记录用于缩短交接，不直接证明当前环境仍相同；进入容器复刻前重新核对目标机器、容器和服务。不得修改、回写、同步或执行上游项目的流程脚本，也不在当前配置中建立必须依赖上游目录长期存在的链接。用户没有指定具体模型时不扫描整个上游项目。

### A1. 定义验收契约

记录：

- 主指标：例如 P99 TTFT、P99 TPOT、输出吞吐或峰值显存。
- 守护指标：正确性、失败率、尾延迟、显存、功耗或成本。
- 目标 workload：长度分布、并发、请求数、到达模式、endpoint 和数据集。
- 通过门槛：绝对 SLO、相对改善和允许波动。
- 修改边界：允许修改的配置、Plugin、backend、算子和禁止项。
- 工程约束：Plugin 以可提交上游 PR 的设计为目标，明确共享调用方、非目标模型/平台、默认行为与可选依赖影响。
- 远程工作目录：用户可选提供目标 Host 上的绝对路径；记录规范化路径、权限/空间检查及本案例专属子目录。

没有明确通过门槛时，可以完成测量和比较，但结论只能是“改善/回退/未证实”，不能写“达标”。

源码修改范围：用户已授权直接修改当前目标模型推理环境内的 `vllm-plugin-FL`、`FlagGems-vllm` 与 `FlagGems`，覆盖框架逻辑、vLLM 专用/融合算子、通用算子接入、当前算子实现和调优配置。vLLM 源码仍默认只读；权重、tokenizer、基础镜像和共享系统配置不因这项授权而开放修改。

修改前核对实际导入路径、安装方式、目标源码副本、revision 和工作区状态，保留已有改动。分别保存各仓库的补丁和回退方法，记录必要的构建/安装及目标服务重载步骤，并验证实际加载和执行路径。若副本被其他服务共享，先隔离影响或取得相应授权，不影响无关工作负载。

#### 远程工作目录

预计在目标机器产生脚本、inspect、日志、profile、benchmark/精度原始结果或临时补丁时，可以让用户提供一个远程工作目录。该目录必须属于当前目标 Host，并解析为明确的绝对路径；不接受 `~`、未解析环境变量、通配符、`/`、home 根目录、模型权重根目录或共享源码根目录作为直接任务目录。

在其下创建唯一的 `<case-id>/` 子目录，并在案例契约中记录 `remote_work_root`、`remote_case_dir`、owner/权限、可用空间和符号链接解析结果。所有新文件使用不覆盖的名称；不清理既有内容。建议按实际需要保存 `commands/`、`manifests/`、`logs/`、`profiles/`、`results/`、`patches/`，不批量创建空目录。项目内只保留可复现配置、摘要、远程绝对路径与 SHA，大体积原始产物留在远端。

远程工作目录不是容器隔离机制。若它不是源适配容器的既有挂载，不得给优化容器增加该目录挂载；Host 侧控制文件和容器产物可通过不改变挂载清单的 runtime 文件传输衔接，并记录源/目标路径与校验。删除或整体归档远程工作目录必须单独确认影响范围。

### A2. 复刻独立优化容器

每次性能优化都从用户指定的已适配容器新建一个专用优化容器。源适配容器只用于读取客观配置和确认适配状态，不直接承载 baseline、profiling、源码修改或 candidate 测试。

执行顺序：

1. 保存源容器的只读 inspect，解析镜像引用与 ID/digest、writable layer 中是否存在必要适配改动、entrypoint/command、working directory、user、关键环境变量、设备、IPC、共享内存、ulimit、网络和资源限制。
2. 确认新容器继承的是有效适配状态。适配结果位于挂载目录时复用原镜像和启动配置；必要改动位于 writable layer 时，先形成可识别、可回退的不可变镜像或等价快照并验证内容，不能使用适配前镜像代替。
3. 规范化源容器的所有目录型 bind mount 和 named volume，字段至少包括 `Type`、`Source`、`Destination`、读写模式、传播属性和适用的 subpath。
4. 用相同目录映射创建优化容器。bind mount 的宿主机源路径和容器目标路径必须分别完全相同；named volume 必须复用同一 volume 及目标路径；访问模式和传播选项不得漂移。
5. 新容器使用独立且不冲突的容器名、宿主机端口和日志路径。容器内端口、设备拓扑及其他影响性能的配置保持一致；必要差异显式记录，不能混入未标注的 baseline。
6. 启动后从优化容器重新提取挂载清单，执行机器可读 diff。只有 `image_lineage=verified` 且 `mount_parity=passed` 才能进入服务预检和 baseline。

目录映射一致是硬门禁：不得用文件复制、符号链接或不同的宿主机路径绕过。若发现缺失、额外挂载、Source/Destination 变化、读写模式或传播属性变化，先修复复刻配置，不运行性能测试。

独立容器不等于独立数据。相同挂载会让 Plugin、FlagGems、模型和缓存目录对源容器或其他使用者可见。源码修改前必须记录挂载目录的 revision、已有改动、共享使用者、补丁和回退方法；同时确认源容器不会与优化容器争抢目标设备、端口或宿主机资源。默认保留且不修改、停止、重启或删除源适配容器。

共享源码的私有副本、实际导入路径验证和回退分支见 [容器隔离流程](container-isolation.md)。通过 `scripts/verify-container-mounts.py` 生成机器可读比较；该工具不自动证明镜像谱系。远端检查入口必须显式指定 inventory Host，多个 Host 串行执行。

### A3. 冻结可比环境

记录 Host、设备数量与拓扑、功耗状态、容器镜像、权重和 tokenizer、推理引擎、Plugin、FlagGems-vllm、FlagGems、驱动/runtime、dtype、量化、并行策略、graph、cache 配置和完整启动参数。

用于性能测试的 vLLM 服务必须对 baseline、candidate 和 revert 显式使用：

```bash
vllm serve <model> <其余冻结参数> \
  --no-enable-prefix-caching
```

`--no-enable-prefix-caching` 关闭 prefix caching；不要求增加 `--no-enable-log-requests`。先核对目标版本 CLI 确实支持 prefix cache 参数；不支持时停止并记录差异，不静默删除。启动后从完整进程参数、服务日志或等价 runtime 证据确认实际状态，并在 service manifest 中记录 `enable_prefix_caching=false`、`performance_context.prefix_cache_state=disabled`。缺少任一侧证据时不能进入正式比较。

只有用户明确要求研究 prefix cache 时，才在独立实验契约和新基线中改变缓存状态，并记录 cache preparation、前缀复用比例和命中证据。该结果不与默认关闭缓存的基线归因为其他优化收益。历史案例保留其原始缓存语义，不按新规则追认或改写。

任何一项变化都必须进入实验变量或触发新基线，不能作为未记录的背景变化。

配置声明与实际行为分别取证：graph 记录请求/实际模式、capture sizes、backend 和命中；并行记录设备总数、副本数及各 rank 分组；KV 记录有效预算、驻留负载与抢占/重算。先核对目标版本的 CLI、指标及平台能力，不能将 CUDA 文档中的默认值直接用于 PPU 或其他平台。

### A4. 正确性和服务预检

- 调用精度评测 Skill 的 `baseline-sanity` 模式，将结果绑定到当前优化容器和服务身份。
- 验证连接、设备、容器、进程、端口和 `/v1/models`。
- 固定请求执行单请求 smoke test。
- 执行小批量和 8 并发 sanity，并检查实际输出。
- 记录超时、空回复、截断、机械重复、乱码和服务错误。

预检失败时先处理运行时或正确性问题，不开始正式性能调优。

### A5. 建立真实执行路径证据

对 Plugin patch、backend dispatch、graph 特化和算子替换，至少记录一种运行时命中证据：

- profiler 中的目标 kernel symbol 与调用次数；
- backend/dispatch 的可控计数器或一次性日志；
- graph capture/replay 覆盖情况；
- 能区分目标路径和 fallback 的 A/B 开关。

源码中存在分支、环境变量已设置或 microbenchmark 能运行，都不能证明服务实际命中。若发现 no-op、reference fallback、CPU 同步或语义错误，应使依赖该路径的旧性能结果失效并重建基线。

## 4. 阶段 B：建立可信基线

### B1. 分离启动、预热和稳态

分别记录：

- 冷启动：模型加载、编译、graph capture、首请求。
- 预热：allocator、cache、JIT/compile 稳定过程。
- 测量：预热后的有限批次或持续负载；只有满足约定稳态条件时才称为稳态。

测量前冻结预热覆盖的 shape、观察窗口、完成判据和最大预算，例如编译/capture 已完成，连续窗口的主指标与资源波动进入约定范围。固定轮数只能说明执行了预热，不能自动证明稳定；预算内未稳定则记录未证实，不无限等待或选择最好窗口。时间窗口与完成请求数窗口可按 workload 选择，具体时长和容差由任务决定。[测量窗口参考](https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/perf_analyzer/docs/measurements_metrics.html)

编译/JIT、allocator 和业务 prefix cache 分开记录。默认性能测试已通过服务启动参数关闭 prefix cache，仍需证明实际状态为 disabled；不同 seed 不能替代该证据。显式研究 prefix cache 时才记录共享前缀比例、请求顺序、cache preparation 和每组开始前的队列排空条件。正式精度会改变服务历史，之后按契约恢复负载条件；涉及重启时重新满足同服务实例的精度门禁。cache 清理仅作用于任务服务，不影响共享目录或其他服务。

### B2. 验证客户端没有成为瓶颈

- 核对实际发送请求数、成功数、并发和到达模式。
- 检查客户端 CPU、网络和连接池。
- 确认 tokenizer 或数据生成是否计入计时范围。
- 固定 endpoint、EOS 和采样策略。
- 区分计划到达、实际发出和完成速率，记录客户端并发限制、等待队列及是否计入延迟。客户端限流可能隐藏服务过载。

客户端饱和时，服务吞吐数字只是客户端上限。

在[实验契约](experiment-contract.md)中选择有限批次、持续并发或到达率扫描；单波请求不能证明持续服务容量。业务容量结论需展示负载扫描、队列趋势、失败和同时满足约定 SLO 的 goodput。vLLM 的 request rate 与 max concurrency 分别约束到达和执行，同时设置时实际发出速率可能低于设定值。[vLLM v0.24.0 benchmark 参数](https://docs.vllm.ai/en/v0.24.0/cli/bench/serve/)

### B3. 收集端到端基线

调用推理性能评测 Skill 的 `baseline` 模式，冻结当前场景、测量契约、服务身份和产物位置。不要求任务开始时先跑完全部场景 baseline；新场景可在进入自身优化闭环时才建立 baseline。

区分两类基线：

- `scenario-entry baseline`：新场景开始优化前的当前已保留代码状态，用于该场景本轮的增量对比。如已包含前序场景优化，记录 `baseline_parent_candidate`。
- `anchor baseline`：未优化原路径在该场景上的基线，用于最终累计收益。可以延后采集，但在最终 full 结论前必须与候选使用同契约补齐。

至少保存请求吞吐、输入/输出/总 token 吞吐、TTFT、TPOT、ITL、端到端延迟的 P50/P95/P99、失败/超时、峰值与稳态显存、设备利用率/功耗和服务错误。记录主机 CPU、内存、网络情况及多卡通信占比和负载不均衡；不可用指标标为 null，不从单点采样推导峰值或能耗。

工具没有提供某项指标时保持缺失，不从平均值推造百分位。

公共工具已提供参数化计划、客户端能力预检和失败记录。测量前通过 `--comparison-contract` 绑定比较阈值；收齐各角色的独立运行后，由 `compare_performance.py` 重验原始产物与条件，输出通过、失败或证据不足。工具只覆盖实际实现的负载范围，不能以一次返回 passed 代替完整任务范围；命令、支持指标及限制统一见[性能入口](../evaluation/performance/README.md)。

按实验契约定义计时边界、请求/token/流式 chunk 的统计单位及跨轮汇总口径。主指标或必要守护指标缺失时只能保留诊断结果，不能通过正式性能验收；精度 gate 通过只代表允许开始候选性能测量。

#### 基线过慢时的恢复分支

baseline 启动前记录本次诊断时间预算和停止条件。某场景在预算内仍无法完成时，这本身是原路径性能很差、值得优先处理的操作信号，不必无限等待完整结果：安全停止本次 benchmark 客户端，保留实际运行时长、已发出/完成/失败请求数、最后进度、部分日志和服务状态，并把该次尝试记为 `deferred-too-slow/incomplete`。诊断预算不是该场景的延迟或吞吐值，不能由它虚构目标 baseline、精确加速比或 passed/failed 性能结论。

随后选择一种 baseline-recovery 策略：

1. **缩减测量（`reduced-measurement`）**：减少请求数、并发、输入长度或输出长度，建立有稳定 ID 且映射到原目标场景的 milestone；用完全一致的缩减 workload 测 baseline/candidate，获得明确的吞吐和延迟数据。
2. **静态优先（`static-first`）**：针对实际加载的 Plugin、FlagGems-vllm、FlagGems 和配置检查调用链、dispatch/回退、算法复杂度、目标 shape、冗余计算、内存搬运、同步、graph、KV、调度与通信组织，并进行单变量、可回退调优。
3. **混合（`hybrid`）**：用缩减测量提供方向和数值反馈，同时通过静态分析解释机制并选择下一项改动。

缩减场景的数字只支持该 milestone，不能冒充原目标 baseline，也不能跨不同输入、输出、并发或请求数计算精确加速比。满足以下任一条件时退出恢复阶段：候选能在记录预算内完成 milestone；静态候选已耗尽，需要目标场景证据；或用户要求恢复整体测量。之后按晋级条件重新调用性能评测 Skill，逐步补做对应目标场景和正式矩阵。若原路径 anchor 仍无法完成，只能报告带 workload 和时间预算的有界结论，不能报告精确累计加速比。

## 5. 阶段 C：定位瓶颈

按以下顺序逐层收敛：

1. 请求与网络：到达、排队、连接、流式返回。
2. 调度与批处理：continuous batching、batch occupancy、prefill/decode 干扰。
3. 推理阶段：tokenizer、prefill、decode、采样、detokenize。
4. 内存与执行：KV cache、prefix cache、分配、同步、graph break、数据搬运。
5. 并行与通信：TP/PP/EP/DP、collective、跨机网络和负载均衡。
6. 算子与 Kernel：dispatch、fallback、launch、访存、occupancy、融合和精度。

对每个当前目标场景，先建立三个相互关联但不可混算的阶段视图：

- **Prefill**：prompt 排队与准入、chunked prefill、输入 token 处理、Prefill batch/shape、首 token 前的通信与 kernel；主要观察 TTFT、input-token 吞吐和服务内部 Prefill 事件。
- **Decode**：首 token 后的自回归循环、KV 读写、Decode batch/shape、采样与逐 token 通信；主要观察 TPOT、ITL、output-token 吞吐和服务内部 Decode 事件。
- **Mixed**：Prefill 与 Decode 共存时的调度、抢占、KV 压力、batch 变化、阶段干扰、排队和完整请求表现。

TTFT 包含排队、调度、网络等开销，TPOT/ITL 也可能包含调度、采样、流式传输或 chunk 口径，因此它们是低开销阶段代理而不是纯设备时间。低开销证据足以确定方向时不强制采 trace；不能区分阶段贡献时调用 Profiling Skill，按事件、iteration/token 边界或服务内标记切分。无法可靠切分时将阶段归因标记为 `unknown/incomplete`，不能把整段时间任意分摊。

只有低开销指标无法继续归因时才调用推理 Profiling Skill：没有当前有效 trace 时先用 `capture`，随后用 `analyze`；保留改动后需要确认热点迁移时使用 `reprofile`。Profiler 运行单独记录，不与无 profiler 的正式性能结果直接比较，所得假设必须回到性能评测 Skill 的 `targeted` 或 `checkpoint` 模式验证。

候选优化按预期端到端可兑现收益排序：

```text
优先级 ≈ 累计时间 × 可消除比例 × 生产命中率 - 新增开销与风险
```

优先排查与有效工作量无关却随容量或调用次数增长的成本，例如整 cache clone、逐请求 launch、CPU 同步、重复 Prefill、无效 padding/重排和未使用中间结果。

若瓶颈收敛到具体算子，使用 `skills/key-operator-analysis/SKILL.md`，并把算子收益重新映射到端到端指标。

### C1. 两层优化分类与优先级

瓶颈定位可以有请求、调度、通信、内存等多个维度；实施工作按用户指定的两个层面组织：

| 层面 | 子类 | 主要关注点 | 典型候选 |
|---|---|---|---|
| 框架层 `framework` | 不另设算子子类 | 在 vllm-plugin-FL 内改变执行组织、调度和数据流 | 消除主机同步/冗余复制，批处理和 KV 容量调整，graph 覆盖，通信组织 |
| 算子层 `operator` | 接入更好的算子 `replace` | 更换已有实现并接入 Plugin | 对比 FlagGems 与 vendor/native backend；按 Prefill/Decode 和 shape 选择实现 |
| 算子层 `operator` | 优化当前算子 `improve` | 改善当前实现或相邻推理链路的计算、访存与启动效率 | tile/warp/stage 调优，split-K/top-k，访存改造，跨算子融合，特化算法 |

分类以收益机制为准，不以修改文件所在目录为准：

- 为新 backend 增加 dispatch 和 fallback 是算子接入的必要步骤，归入 `operator/replace`。
- 减少通用 dispatch、Python 循环或请求组织开销，归入 `framework`。
- 移除框架中不必要的 copy 属于框架层；修改 kernel 支持新 layout 属于算子层。两者共同完成时记录关联实验与依赖。
- 通过重排调用消除中间步骤属于框架层；将现有推理链路中相邻算子的预处理、主体或 epilogue 合并为新的融合 kernel 属于 `operator/improve`；接入已有融合 kernel 属于 `operator/replace`。
- 通信排程、rank 数据组织属于框架层；替换 collective 实现属于算子接入，开发其 kernel 属于当前算子优化。

默认优先顺序（前提是正确性和测量门禁通过）：

1. **框架层先消除明显浪费。** 检查重复 Prefill、整 cache clone、主机同步、无效循环和运行路径未命中；没有问题则跳过，不做无证据重构。
2. **框架层建立合理工作点。** 小范围扫描并发、KV 预算、batched tokens、Prefill 分块和 graph 覆盖，得到代表性生产 shape；通信已是主瓶颈时提前处理通信组织，不固定排到末尾。
3. **热点算子先比较已有实现。** 在同设备、dtype、shape、layout 和执行模式下比较完整调用成本，通过 Plugin 白名单接入更优实现，保留 fallback。
4. **再优化现有热点算子。** 只有现有实现不满足需求、接入成本不划算，或当前实现的改善机制更明确时，投入 kernel 调优、融合和特化。记录为何不选择直接替换。
5. **回到框架层复测工作点。** 算子效率变化会改变最优 batch、调度和并行策略；重测后更新候选排名，而不是认为框架优化已经永久结束。

上述顺序是工程默认策略，不是性能定律或当前模型的实测结论。算子热点证据已经充分时，可以直接进入第 3 或第 4 步；跨层组合先分别 A/B，再评估组合收益，不能把单项百分比相加。

### C2. 生成并维护实际候选排名

每个案例维护一张跨两层的统一候选表：

| 排名 | 分类 | 候选 | 瓶颈与命中证据 | 主指标净收益估计 | 成本/风险 | 依赖 | 首个验证实验 | 暂缓理由 |
|---|---|---|---|---|---|---|---|---|

排序时优先考虑目标指标关键路径上的可消除时间和生产覆盖，再考虑实现、数值验证、集成与维护成本。kernel 累计时间不能直接等同于端到端时间，需排除跨流/跨卡重叠，并扣除新增 copy、通信、归约和 dispatch 成本。证据不足时收益写“待测”，先做小实验，不编造分数。

对 split、chunk、packing、tile 或调度阈值类候选，候选表同时写明限制资源、理论预算和完整调用新增成本。历史案例中的 S、M 阈值、内存预算和 token 上限只用于形成扫描范围，不能作为新目标的默认值。

设计与兼容性是候选保留约束，不仅是收益相近时的择优项；通用路径特例、隐藏依赖或非目标回归需先修订。收益相近时，优先选择侵入小、已有实现可复用、验证充分和易回退的方案。框架改动并不天然低风险，算子接入也不天然比当前实现更快。候选未命中、精度失败、净收益消失或守护指标越界时停止晋级；每项改动保留后重新测量并排序。

### C3. 从机制选择首个实验

下表由官方设计资料辅助形成候选路径，**不是当前模型/平台已经复现的性能结论**。先确认目标 revision 和平台支持，再把命中条件、保留标准写入候选表；不照抄其他硬件的参数值。

| 触发信号 | 首个单变量实验 | 共同观测与边界 |
|---|---|---|
| 长 prefill 进入时 decode 尾延迟变差 | 固定混合请求序列，小范围扫描 batched token 预算 | TTFT、ITL、排队和实际 batch shape；取舍取决于 SLO。[分块 prefill](https://docs.vllm.ai/en/v0.24.0/configuration/optimization/#chunked-prefill) |
| 长输出期间 KV 压力、重算持续增加 | 保持请求负载，单独降低服务 max-num-seqs | 对比重算成本、完成吞吐和排队；不把抢占恒为零当作普适最优。[Preemption](https://docs.vllm.ai/en/v0.24.0/configuration/optimization/#preemption) |
| 相同输入后续请求显著变快 | 编译预热完成后，对照受控冷/热前缀 | 记录复用比例、实际命中与 prefill 成本；APC 不直接减少新 token 的 decode 计算。[APC 边界](https://docs.vllm.ai/en/v0.10.2/features/automatic_prefix_caching.html#limits) |
| graph 已开启但 launch/padding 仍高 | 只调整实际支持的 capture sizes 或 mode 中的一项 | 实际模式覆盖、capture 成本、内存和 KV 容量；capture 成功不等于全 workload 命中。[Graph 设计](https://docs.vllm.ai/en/v0.24.0/design/cuda_graphs/) |
| 通信占关键路径或 MoE rank 负载偏斜 | 固定设备总预算，比较一个可行的并行布局 | 记录每 rank 形状/路由、通信和副本数；均匀模拟路由仅用于诊断。[Expert parallel](https://docs.vllm.ai/en/v0.24.0/serving/expert_parallel_deployment/) |

这些检查帮助缩小实验范围，不要求为每个任务全跑一遍。Plugin 仍使用已有能力判断与 dispatch 入口；相关版本组合和非目标路径按 D4 复核。

## 6. 阶段 D：优化实验循环

每轮只保留一个主要变量：

1. 写出证据和可证伪假设。
2. 预测主指标、守护指标和可能退化场景。
3. Plugin 修改前说明设计归属、复用扩展点、支持范围和非目标影响；保存可重复命令、配置和补丁。
4. 调用精度评测 Skill 的 `minimal-regression` 模式，执行与改动影响面匹配的最小正确性回归。
5. 用同一预冻结场景子集重测 baseline 与 candidate；该轮不要求运行完整验收矩阵。
6. 检查测量波动、失败、显存和服务日志。
7. 做回退复测，排除环境时间漂移。
8. 决定保留、回退、未证实或形成下一假设。

### D1. 阶段和 shape 分治

- Prefill、Decode 和 Mixed workload 分别统计实际 shape 分布、累计时间/调用次数、主指标、守护指标和热点；每个当前目标场景在确定优化优先级前都要给出三者的证据状态，允许某项为 `unknown/incomplete`，但不能将 Prefill 与 Decode 合并后直接归因。
- 阶段专项 milestone 可以通过单 token/短输出突出 Prefill，或用足够长的输出观察稳态 Decode；它们仍包含未完全消失的其他阶段和调度成本，必须记录 `phase_isolation_method`、残余开销与相对目标场景的 workload 差异，并建立自身同配置 baseline。
- backend/tile/config 的选择键至少考虑阶段、M/序列形状、dtype、拓扑与目标 graph 能力。
- 生产特化使用白名单；未验证 shape 必须走正确 fallback。
- 对 backend、融合或算法替换先冻结数值契约：输入/输出 dtype、cast 与舍入位置、归约或排序顺序、tie 处理、归一化/累计阈值、空输入和边界行为。随机输入误差不能替代这些边界检查。
- split、chunk、packing、tile 和调度阈值按目标环境的限制资源推导扫描范围，并测量 merge、通信、copy、临时内存和 graph 覆盖；不假设参数增大带来单调收益。
- 对 fused op 先展开真实数据流，分别核算 align/gather、GEMM、activation、通信、scatter/reduce，不能只测核心 kernel。

### D2. 分层兑现门禁

候选按以下层级晋级：

1. microbenchmark：证明机制和数值语义。
2. kernel profile：证明真实 shape、调用次数和目标路径命中。
3. 服务阶段指标：证明 Prefill/Decode/Mixed 的净收益。
4. 端到端 benchmark：证明 TTFT、TPOT、吞吐、显存和稳定性总体可接受。

任一层未命中或新增开销吞噬收益时，不得用上一层数字宣称端到端提升。

Prefill 候选至少以 Decode 指标和 Mixed 端到端结果为守护，Decode 候选至少以 Prefill/TTFT 和 Mixed 端到端结果为守护。调度、KV、通信、graph 或融合改动可能同时影响两个阶段，必须分别报告方向与幅度；单阶段专项通过只允许晋级，不等于当前目标场景完成。

对带 split、packing、融合或 layout 转换的候选，microbenchmark 与 kernel profile 均以完整调用为测量单元；主 kernel 变快但 merge、通信、copy 或隐式 materialization 使服务变慢时，候选不得晋级。

### D3. 调度与算子联动

调度参数会改变生产 shape，算子效率也会改变最优调度点。扫描 `max-num-seqs`、`max-num-batched-tokens`、long-prefill threshold 等参数时，同时记录 KV 抢占、重算 token、batch occupancy、TTFT、TPOT 和目标 kernel shape。容量按完整 Decode 生命周期计算，不按瞬时 Prompt 准入量计算。

诊断性组合 A/B 可以临时改变多个开关，但不得直接成为最终方案。最终保留方案必须拆分主要贡献来源。

### D4. Plugin 设计复核与 PR 准备

Plugin 候选在修改前与整理最终补丁后，按 [Plugin 优化设计与 PR 准备](plugin-change-review.md) 完成设计归属、能力/shape 边界、共享调用方与可选依赖检查。测试按影响范围覆盖目标、非目标和生命周期，复用目标仓库实际 CI 规范；无硬件项目记为未测，不扩大连接范围。

实验开关、日志和临时 patch 在形成 PR 候选时整理；最终 diff 改变后重新验证实际路径和受影响指标。Plugin、FlagGems-vllm、FlagGems 分别保存补丁与依赖关系。性能结论与 `pr_readiness` 分别记录，可用实验结果不自动等于可合入设计。该复核属于已授权工作，无需新增例行审批。

### D5. 控制波动与调优选择偏差

测量前固定重复数、配置顺序、统计单位、最小有意义改善和停止预算。同进程多轮与重新启动后的独立重复分别记录；按成本选择配对/交错的 baseline、candidate 顺序，并保留回退复测。出现明显进程差异或时间漂移时，先增加相应层级的重复，不能挑一个最慢 baseline 归因给改动。

报告每轮与进程间波动、请求样本数、分位数算法及不确定性。32/64 个请求的 P99 可以作为描述值，不能单凭它证明稳定的尾延迟 SLO；同一进程的大量请求也不等于大量独立实验。多轮分位数的平均值不得命名为全体请求的分位数。

搜索阶段与最终确认分开：用小范围扫描筛选方案，再按事先约定的代表性请求/到达序列验证最终候选。没有新机制、收益落在噪声内或预算耗尽时记为未证实/暂缓；不能不断换 seed、阈值或 workload 直到出现通过结果。

### D6. 精度评测节奏与风险触发

精度验证分为两层，降低完整 GPQA 的重复成本不能削弱每轮正确性护栏：

1. **每个优化点执行最小正确性回归。** 按改动覆盖 reference、数值边界、目标与 fallback shape、smoke/C8，以及目标 graph 的 capture/replay。性能优化不要求另行验证 eager 服务；该层失败时立即回退或修复，不进入性能候选，也不通过完整 GPQA 掩盖局部错误。
2. **低风险优化点分批执行完整精度。** 对不改变模型语义、数值边界和数据解释方式，且最小回归全部通过的候选，默认累计保留 4–5 个后，用正式 runner 执行一次完整 GPQA。每次记录本批包含的 experiment ID、源码/配置/服务身份、结果和 gate；未到触发点的候选只能标记“最小回归通过、完整精度待执行”。
3. **大优化点或高风险改动立即执行完整精度。** 改变量化/dtype/舍入、attention 或 KV cache 语义、MoE 路由、top-k/top-p/采样、跨算子融合、算法/backend、广泛 custom-op dispatch、rank 数据布局/通信、graph/fallback 覆盖，或已出现异常输出时，不与其他点凑批；最小回归后立即运行完整 GPQA。
4. **组合失败先定位和修复，不继续叠加。** 一批 4–5 个优化点的正式分数低于预冻结阈值时，冻结当前组合并调用精度定位 Skill，通过最小复现、回退/拆分和路径证明定位责任改动；修复或回退后执行最小回归，并重新运行原正式精度范围。只有新的 `score >= threshold` gate 生成后才恢复性能优化。组合通过只证明该组合在绑定身份下通过，不等于各单点有独立模型精度证据。
5. **最终候选必须有精确绑定的正式验收。** 最终代码与配置冻结后，若最近一次完整 GPQA 的 `score >= threshold` gate 已绑定完全相同的源码、配置与当前服务身份，可直接用于阶段 E；否则必须重跑。其后源码、权重、tokenizer、影响推理的配置或服务实例变化，旧 gate 失效。

“低风险”只决定完整 GPQA 的频率，不降低改动本身的数值测试、运行路径证明和性能测量要求。风险依据正确性影响面判断，不依据代码行数、实现者信心或预期加速比判断。

以上步骤通过 [推理精度评测技能](../skills/inference-accuracy-evaluation/SKILL.md) 执行：第 1 项使用 `minimal-regression`，第 2、3、5 项在需要新 gate 时使用 `formal-gate`；已有 gate 在进入正式性能前使用 `gate-check` 重新绑定当前服务事实。中间完整精度产物留在 `optimize/` 的实验记录，只有最终候选结论进入 `acceptance/`。

精度 Skill 在 `baseline-sanity`、`minimal-regression` 或 `formal-gate` 启动实际评测进程前创建当前任务 heartbeat，默认每 30 分钟报告评测阶段、运行时长、进程健康、产物更新时间、可验证的唯一题目进度及新错误。多 filter 场景不得用原始行数冒充完成题数，ETA 无可靠依据时保持不可用。评测完成、失败、取消或提前停止后发送终态并停用监控；短任务在首次触发前结束时直接清理。`gate-check` 不创建定时任务。

### D6.1 精度问题定位

baseline sanity 或必要的最小回归失败、完整 GPQA 分数低于预冻结阈值、或评测身份/产物无效时，冻结失败产物并调用推理精度问题定位 Skill，停止叠加新优化。必须定位精度下降原因并修复或回退，再以相同正式契约重跑；只有新的分数达到阈值后才能恢复性能优化。输出健康异常只是可选诊断观察，在 `score >= threshold` 时不影响候选通过与继续优化。

定位首先区分 `measurement-invalid`、服务/配置漂移、请求/输出健康、真实数值语义回退、graph/并发/rank 执行差异及可控随机性。task、dataset、filter、runner、样本集合、服务身份或比较条件无效时，先恢复同契约可比性，不能把工具问题写成算子精度问题。

从最后一个可信正确状态开始，用同一 prompt/token、生成参数、seed、endpoint、服务配置和输入 shape 建立最小复现，再按改动依赖做单变量二分。优先核对高正确性风险改动、graph capture/replay、C1/C8、目标/fallback shape、短/长上下文、单 rank/分布式、Plugin dispatch/backend 和算子数值边界。撤掉某改动后恢复只能形成嫌疑；重新启用可复现、真实路径命中和机制证据闭合后才能确认根因。

修复后先用精度评测 Skill 的 `minimal-regression` 覆盖复现与边界矩阵；原问题来自正式 GPQA 时必须对固定后的候选重新执行 `formal-gate`。相关重跑复用精度评测 Skill 的进度 heartbeat，不重复创建监控。定位记录保存在 `models/<model>/<platform>/optimize/accuracy-diagnosis/<issue-id>.md`，只有原失败范围重新通过后才恢复性能优化。

### D7. 性能场景与分层测试频率

当前统一目标场景目录如下，长度单位为 token，负载模式均为 `finite_batch`：

| `scenario_id` | 输入 P | 输出 D | 并发 C | 请求 N |
|---|---:|---:|---:|---:|
| `p1024-d1024-c64-n128` | 1024 | 1024 | 64 | 128 |
| `p4096-d1024-c64-n128` | 4096 | 1024 | 64 | 128 |
| `p16384-d1024-c64-n128` | 16384 | 1024 | 64 | 128 |
| `p32768-d1024-c64-n128` | 32768 | 1024 | 64 | 128 |

这四个场景是最终性能优化目标，不是每一轮优化都必须执行的固定矩阵。最终正式测试必须逐项覆盖；如果某项超出模型声明的上下文、实际可分配 KV 容量或平台能力，将该项记录为 `unsupported/incomplete` 并保留证据，不能静默删除、缩短或用中间 milestone 替代。

每个场景使用上述稳定 `scenario_id`，并补充阶段、endpoint、数据生成、主/守护指标和用途。将执行分成三层：

1. **定向诊断（`targeted`）**：每轮只跑能够证伪当前假设的目标场景。大模型可降低请求数、重复轮或只选择一个长度/并发点；baseline 与 candidate 使用完全相同的缩减配置。存在明显外溢风险时增加一个便宜的相邻 shape、fallback 或非目标阶段哨兵。
2. **阶段性检查点（`checkpoint`）**：累计保留多个点、热点迁移、准备组合候选，或改动调度、KV、batch、graph、公共 dispatch、通信等跨场景机制时，运行全部受影响场景。检查点失败后停止叠加，通过拆分或回退定位。
3. **正式测试（`formal`）**：中间 formal 只覆盖当前按顺序选中的一个目标场景；最终 formal 才覆盖全部四场景。两者都完成各自范围内的原路径 anchor baseline/candidate/revert、重复、守护指标和精度绑定要求。任务可以增加额外业务场景，但不能减少最终四项。

#### 中间优化 milestone

优化过程中允许建立比最终目标更小、更快的 milestone。milestone 可以是四个目标场景的子集，也可以缩短输入或输出长度、减少请求数或并发、使用 Prefill/Decode 阶段专项、短探针、microbenchmark 或特定热点 shape。阶段专项 milestone 必须明确它突出的是 Prefill 还是 Decode、如何隔离、仍混入哪些成本以及另一个阶段的守护指标。其目的可以是验证路径命中、消除主要瓶颈、达到可测状态或决定是否继续投入，并不要求参数与最终场景完全相同。

每个 milestone 必须记录稳定 `milestone_id`、映射的一个或多个最终 `scenario_id`、相对最终 workload 的缩减项、假设、主/守护指标、成功门槛、停止条件和晋级条件。同一 milestone 内比较 baseline/candidate 时仍保持 workload 和服务条件一致。milestone 达标只表示阶段目标完成；保留的改动按影响面晋级到对应目标场景或 checkpoint 验证。

当 milestone 达到预先定义的“显著提升”条件，或当前场景热点/资源瓶颈发生实质迁移时，可以触发一次中间正式性能测试：核验当前精度 gate，只使用当前目标场景完成同配置 baseline/candidate/revert。显著提升和“当前场景优化充分”的条件由任务在看到结果前定义，不在 SOP 中硬编码。中间 formal 达到场景完成条件后，保留当前组合并按 `P1K → P4K → P16K → P32K` 切换下一个目标场景；否则继续当前场景或回退。全部场景完成后再运行最终四场景 formal，中间结果保存在 `optimize/`，最终组合结果进入 `acceptance/`。

`milestone` 是项目的规划与记录概念，不新增公共性能 Skill 模式。实际无 profiler 测量仍根据覆盖范围调用 `targeted` 或 `checkpoint`；算子 microbenchmark 和静态分析分别按其证据边界记录。

#### 按场景串行优化

按照 `P1K → P4K → P16K → P32K` 从正式目录中每次选取一个目标场景，执行“入口基线 → Prefill/Decode/Mixed 分阶段定位 → 阶段 milestone 与单变量优化 → candidate/revert → Mixed 目标场景验证 → 当前目标场景 formal → 场景完成决策”闭环，然后再进入下一场景。例如：

```text
4k-1k scenario-entry baseline
→ 4k-1k profiling / optimization / targeted comparison
→ 保留或回退 4k-1k 候选
→ 16k-1k scenario-entry baseline（记录是否包含 4k-1k 已保留改动）
→ 16k-1k profiling / optimization / targeted comparison
```

任一场景的入口基线超过预记录诊断预算时，可将该步替换为“未完成 baseline 证据 → 缩减场景测量、静态分析或混合恢复 → milestone 数据 → 晋级当前目标场景”。该分支只改变等待与诊断顺序，不放宽同配置比较、精度回归、单场景 formal 和最终四场景要求。

场景入口基线只支持该场景相对当前代码状态的增量结论。如果新优化修改了全局调度、KV、batch、graph、公共 dispatch、通信或不具备稳定 shape guard 的实现，在保留前用 `checkpoint` 复测已完成的受影响场景。不要求场景特化改动在每轮都重跑全部无关场景。

场景和执行层级在测量前确定。不能在看到结果后删除负优化场景、改变请求数/重复轮后仍沿用原 baseline，或用 targeted 结果宣称完整任务达标。targeted 结果仅支持对应 `scenario_id`；checkpoint 支持列出的受影响集合；只有 full 才支持最终验收范围。

不同场景可以分别优化和保留不同候选。最优实现冲突时，先验证是否能用阶段、shape、dtype、layout 或 graph 能力建立稳定 dispatch guard；若无法安全分派，按预冻结主场景与 SLO 明确取舍并保留各场景结果，不计算一个掩盖回退的无权平均加速比。

以上无 profiler 性能测量通过 [推理性能评测技能](../skills/inference-performance-evaluation/SKILL.md) 执行：B3 使用 `baseline`；单点假设验证使用 `targeted`；累计变更、热点迁移和跨场景影响使用 `checkpoint`；最终验收使用 `formal`。需要 trace 归因时单独调用推理 Profiling Skill；每次结果都写回当前实验，模式不能只作为对话中的临时判断。

### D8. 阶段性优化规划复盘

默认完成 2–3 个有结果的实验后调用推理优化规划复盘 Skill；如果出现组合交互、热点迁移、不同场景结论冲突、连续 `failed/incomplete`，或下一步需要投入高成本算子开发/广泛框架改动，则提前触发。触发计数包含保留、回退和失败实验，避免只总结成功项。

复盘先统一各实验的服务身份、场景、正确性与性能覆盖、变更依赖和当前候选是否实际包含该改动。累计收益以同配置 baseline→当前组合 candidate 的可比测量为准，不能把各轮相对提升直接相加。多个已保留改动尚未完成受影响场景的组合测量时，先调用性能评测 Skill 的 `checkpoint`；热点仍不明确时调用 Profiling Skill；完整精度触发到期时调用精度评测 Skill。

下一轮规划通常只保留 1–3 个候选，按端到端瓶颈贡献、可消除比例、生产命中率、证据强度、实现/验证成本和正确性/兼容风险排序。每个候选必须注明分类、适用边界、支持/反对证据、预期主/守护指标、依赖、最小证伪实验、场景与评测模式、成功门槛、停止条件和回退。结果保存到 `models/<model>/<platform>/optimize/planning/<review-id>.md`，并记录下一次复盘触发条件。

## 7. 阶段 E：候选回归与验收

- 调用精度评测 Skill 的 `formal-gate` 或 `gate-check` 模式，取得与最终候选服务身份精确匹配的有效 gate；以下条目是该 Skill 不得省略的正式流程。
- 最终候选的精度 gate 核验通过后调用性能评测 Skill 的 `formal/final`；该模式覆盖全部四个目标场景，并完成可比的 baseline/candidate/revert、重复、波动与守护指标检查。中间单场景 formal 不代替本步骤。
- 测试前从 [`evaluation/ACCEPTANCE_TEMPLATE.md`](../evaluation/ACCEPTANCE_TEMPLATE.md) 固定任务、生成参数、metric 和单一 threshold。正式精度的唯一通过条件是 `score >= threshold`，等于阈值通过。
- 验证目标 graph 模式可以启动、capture 和 replay；正式 sanity、精度和性能使用最终候选的同一 graph 配置，不要求另行验证 eager 服务。
- 先运行固定小样本和 8 并发 sanity，逐条检查输出，同时观察明显性能异常。
- 对量化、采样、算子、cache 或图路径改动完成最小数值/行为回归。
- 在目标机器上进入基于 `harbor.baai.ac.cn/flageval/flageval-llmeval:v1` 镜像的评测容器。记录容器名、镜像引用与 image ID/digest，并验证容器内 `python3`、`lm_eval`、GPQA 离线数据集以及到候选服务 `/v1/models` 和 Chat Completions endpoint 的连通性。
- 模型服务继续运行在本次独立优化容器中；评测容器只作为精度客户端。两者的角色、网络路径、服务模型名和实际 endpoint 必须分别记录。
- 使用 [`formal_accuracy.py`](../evaluation/accuracy/formal_accuracy.py) 包装调用原始 [`test/Accuracy_test/llmrun.py`](../test/Accuracy_test/llmrun.py)，先执行 `--preflight-only`，通过后以同一案例专属配置、契约、服务身份及评测容器 inspect 运行完整 `gpqa_diamond_generative_cot`。默认正式路径是单服务 `llmrun.py`、`limit=0`、`expected_samples=198`；`llmrun_parallel.py` 仅在用户明确要求分片方案时使用。
- 核对冻结任务、`results_*.json`、`samples_*.jsonl`、effective config 和服务身份，确认正式 score 属于当前候选。这些是证据有效性检查，不是额外精度门槛。
- 中间分数只用于提前排障；不能代替最终结果。不得在看到分数后更换 metric、筛选样本或放宽门槛。
- 在评测前采集真实 task/数据内容证据并绑定契约，冻结配置/运行身份；结束后检查文件 SHA，由 `acceptance.py issue` 生成正式 gate。输出健康可另存为诊断观察，不参与 gate 判定。
- 精度门禁通过后，用同一候选 graph 配置测正式性能，并对原路径执行可比的 baseline/revert 复测。候选 gate 只关联候选身份，不能为 baseline/revert 伪造该身份；比较测试单独记录范围。任何服务实例、源码、权重、tokenizer 或配置变化使旧 gate 失效，重新核验当前事实。工具与命令统一见 [评测入口](../evaluation/README.md)。
- 重跑短、中、长输入和目标并发区间，覆盖真实或代表性 workload、cache 冷热、混合 batch 和长时间稳定性。
- 长稳在验收前冻结持续时长、负载循环、idle/resume、周期 sanity、错误/重启与资源趋势标准，按改动的生命周期风险选择；未执行保持 `not_run/incomplete`，短测成功不能代替。具体记录见验收模板。
- 多卡或多机方案检查通信、负载均衡和故障表现。
- 确认回退配置或补丁可以恢复原基线。

优化循环允许用短 benchmark 做诊断。若缺少正式精度工具或预先冻结的 metric/threshold，应明确标记“探索性性能验证完成、正式验收未完成”，不能将其升级为最终性能结论。

## 8. 阶段 F：案例复盘与经验沉淀

复盘必须回答：

1. 最初瓶颈判断是否正确？哪些证据最有区分度？
2. 哪些实验无效，为什么当时仍合理？
3. 是否存在客户端、配置、cache、warmup 或 profiler 测量陷阱？
4. 最终收益来自哪个机制，适用边界是什么？
5. 哪些检查可以更早暴露问题？
6. 哪些命令、脚本、测试或分析可被复用？
7. 对关键算子而言，案例开始前的判断是什么，本次确认、细化或反驳了什么？
8. 这项知识差量能让下一次该算子优化更早执行哪个检查、跳过哪个无效方向或提出哪个更深入的实验？

沉淀位置：

- 案例结论、关键失败和可追溯对比：案例目录中的少量 Markdown；案例目录不是一次性远端脚本和机器状态快照的归档区。
- 历史记录保留原 schema 与实际状态，不追认符合新规则；缺失的镜像谱系、挂载 diff 或正式精度按缺口记录。验收配置和未完成状态可保留在 acceptance 以便导航，未达标实验数据仍留 optimize。
- 模型/平台产物固定分为三类：`baseline/` 保存优化前基线；`optimize/` 保存多轮实验、profiling、补丁和逐轮性能；`acceptance/` 保存最终候选验收配置、达标记录、未完成状态说明及回退入口，不保存中间实验数据。不得在平台根部再建立并列结果目录。
- 某个算子的环境、benchmark、patch 和逐轮结果：模型/平台 `optimize/`；案例目录保存可读证据摘要与链接，关键算子知识库只建立证据卡。
- 由算子案例改变的诊断检查、适用边界、候选顺序、反例和停止条件：算子 `optimization-map.md`。
- 算子稳定语义、数据流、实现或跨案例性能模型：算子 `README.md`；单个新数字不进入稳定正文。
- 跨案例可复用的工作顺序、门禁或决策标准：本 SOP。
- 通用自动化：`scripts/`、`benchmarks/` 或 `unit_tests/`。`test/` 只保存需要在目标环境中实际执行的评测和性能工具。

案例收尾时清理一次性文件：硬编码 PID/容器名的一次性启动、安装、停止、监控、替换和核验脚本，在其有效结论已写入案例后删除；仍需复现的脚本必须参数化并迁入模型/平台 `optimize/` 或公共工具目录。瞬时机器状态只保留稳定字段和外部产物位置，不保存很快失效的 TXT dump。

## 9. SOP 更新规则

允许更新 SOP 的条件：

- 新案例证明现有步骤会导致错误结论或明显浪费。
- 新检查能稳定提前发现某类问题。
- 一个优化模式达到 `transferred` 级别且适用边界明确。
- 正确性、安全性或测量有效性要求形成新的 `invariant`。

每次更新必须在下方记录：日期、案例、原规则、变更、证据等级、预期收益和风险。不要仅因为一次实验成功就增加强制步骤。

## 10. 变更记录

| 日期 | 版本 | 关联案例 | 变更 | 证据等级 |
|---|---|---|---|---|
| 2026-09-03 | 0.1 | 无 | 建立初始端到端优化闭环、案例制度和经验升级规则 | initial |
| 2026-09-03 | 0.2 | DeepSeek-V4-Flash、GLM-5.2、Qwen3.6 MoE 历史案例 | 增加运行路径证明、可兑现收益排序、阶段/shape 分治、分层兑现门禁与调度-算子联动 | `invariant` / `transferred`（历史案例） |
| 2026-09-03 | 0.3 | 新模型适配公共评测资产 | 增加 eager/graph→C8 sanity→全量精度→同配置正式性能的验收顺序，以及样本完整性和预冻结精度门槛 | `invariant` |
| 2026-09-04 | 0.4 | 用户指定分类；参考现有三个历史案例 | 按框架层、算子接入、当前算子优化组织候选；明确交界、默认顺序和跨层动态排名。预期减少重复开发；风险是机械套用顺序，因此允许实测证据覆盖默认顺序 | 用户指定组织规则；排序为工程启发，非新增实测证据 |
| 2026-09-04 | 0.5 | 用户明确源码授权 | 允许直接修改目标环境中的 Plugin 和 FlagGems 源码；保留 vLLM 只读、共享环境保护及双仓库补丁/回退要求 | 用户授权边界，非性能证据 |
| 2026-09-06 | 0.6 | 用户指定容器复刻规则 | 每个优化任务必须从已适配容器新建优化容器；新增镜像谱系、目录挂载全量一致性、资源冲突和共享挂载影响门禁 | 用户指定执行约束与环境可比性 `invariant` |
| 2026-09-06 | 0.7 | 用户指定正式精度流程 | 固定目标机器上的 `flageval-llmeval:v1` 评测容器与 `test/Accuracy_test/llmrun.py`，默认执行完整 198 题 GPQA Diamond；区分评测容器与优化容器并强化产物完整性核验 | 用户指定验收规则与正确性 `invariant` |
| 2026-09-06 | 0.8 | 用户指出目录命名歧义 | 保留 `test/` 作为目标环境评测工具目录，将项目工具单元测试由 `tests/` 更名为 `unit_tests/`，同步测试命令和目录职责 | 项目结构澄清，非性能证据 |
| 2026-09-06 | 0.9 | 用户要求关键算子知识由实际案例持续加深 | 建立“完整案例→算子证据卡→优化地图→稳定理解”的分层演进机制；禁止把完整案例连续追加到算子 README，并要求每个案例写出可改变下次行动的知识差量 | 用户指定知识演进方式；案例可追溯性与防止错误泛化 `invariant` |
| 2026-09-06 | 0.10 | 用户指定模型/平台产物目录 | 每个模型/平台仅保留 `baseline/`、`optimize/`、`acceptance/` 三个子目录；多轮实验与性能进入 optimize，最终性能与精度达标记录进入 acceptance | 用户指定项目结构，非性能证据 |
| 2026-09-06 | 0.11 | 用户要求精简案例过程文件 | 将 `docs/cases/` 定位为少量可读证据摘要；一次性远端脚本和瞬时状态不长期保留，可复用代码参数化后进入 `optimize/` 或公共工具目录 | 用户指定知识整理方式；降低陈旧脚本误用风险 |
| 2026-09-06 | 0.12 | 本地工具审查：空样本、NaN 阈值及失败轮回归测试 | 增加严格样本与失败退出门禁、服务绑定验收、显式 Host 限制、共享源码隔离分支；抽取公共实验契约，保留历史规则缺口。收益是减少误验收与误目标；限制是当前服务身份仍需运行时取证 | 测量有效性 `invariant`；本地工具验证，非新性能案例 |
| 2026-09-06 | 0.13 | 用户明确要求 Plugin 修改面向后续 PR 与多模型/多平台支持 | 将框架职责、非目标路径、可选依赖与最终补丁复测纳入候选保留和 PR 准备；验证范围按共享影响选择，未测平台明示。收益为降低特例扩散与上游维护成本；避免无证据泛化或过度抽象 | 用户指定工程约束，非新增性能证据 |
| 2026-09-06 | 0.14 | 项目复审、XingChen 进程波动记录及官方测量/设计资料 | 区分批次/持续并发/到达率测量，补预热缓存、统计重复、长稳和运行模式证据；澄清受控变量可比较，强化任务数据与结果身份核验。收益是减少错误归因与误验收；新增成本按目标风险限定，不追认历史结果 | 测量有效性 `invariant`；C3 为来源支持的候选机制，未在目标平台新增实测 |
| 2026-09-07 | 0.15 | 工具修复与固定 lm-eval 源码接口核验 | 落实参数化性能计划、预冻结契约、原始证据重验和三态比较；统一模型 wrapper；修复真实 task metadata 与多 filter 样本兼容，198 题集合不变。收益是减少人工误汇总和正常结果误拒绝；镜像/设备集成与长期容量结论仍需实测 | 本地工具与固定源码接口证据，非模型性能或正式精度通过 |
| 2026-09-08 | 0.16 | 用户要求补充上游算子仓库讲解 | 增加 FlagGems-vllm 与 FlagGems 的独立仓库讲解，并将 Plugin、vLLM 专用算子、通用 ATen 算子的资料按 A/C/D/E 阶段路由；明确同名实现必须按真实调用链区分 | 用户指定文档导航；官方仓库静态源码证据，非目标环境性能证据 |
| 2026-09-10 | 0.17 | DeepSeek-V4-Flash、GLM-5.2 历史案例再提炼 | 将数值契约前置到 backend/融合/算法替换设计；要求 split、chunk、packing、tile 和调度阈值按限制资源选择扫描范围，并以含 merge、通信、copy 和物化成本的完整调用判定拐点。预期减少“随机误差通过但边界语义改变”和“局部 kernel 最优但服务负优化”；历史参数仍不得直接迁移 | `transferred`（两个历史案例的共同机制）；原性能结果仍为 `observation` |
| 2026-09-10 | 0.18 | 用户指定精度评测频率 | 将每轮最小正确性回归与完整 GPQA 分层：低风险改动累计保留 2–3 个后执行一次完整精度，高风险或大影响面改动立即执行，最终候选冻结后强制重跑；组合失败时先拆分定位。预期降低重复评测成本，同时限制未验组合规模和错误定位成本 | 用户指定执行节奏；正确性与验收边界 `invariant` |
| 2026-09-11 | 0.19 | 用户指定性能服务启动参数 | 要求 vLLM baseline/candidate/revert 显式使用 `--no-enable-prefix-caching`，并从命令与 runtime 两侧证明 prefix cache 已关闭；不要求关闭请求日志，缓存优化仅作为显式独立变量。历史结果不追认改写 | 用户指定测量条件；性能可比性 `invariant` |
| 2026-09-11 | 0.20 | 用户允许提供远程工作目录 | 将目标 Host 上的用户指定绝对路径纳入任务输入，在其下按 case 隔离远程命令和原始产物；增加权限、空间、路径范围、不覆盖和清理约束，并明确不能借此改变优化容器挂载清单 | 用户指定产物组织方式；远端安全与可追溯性 `invariant` |
| 2026-09-11 | 0.21 | 用户要求大模型优化时灵活选择性能场景 | 将性能测试分为 targeted、checkpoint、full：每轮允许仅跑当前瓶颈场景和低成本哨兵，跨场景改动运行受影响集合，最终只跑预冻结验收矩阵；限定子集结论范围并禁止事后挑选场景 | 用户指定实验节奏；测量效率与结论边界 `invariant` |
| 2026-09-11 | 0.22 | 用户要求将精度测试固化为 Skill | 新增 `inference-accuracy-evaluation` 项目级 Skill，以 baseline-sanity、minimal-regression、formal-gate、gate-check 四种模式编排现有精度工具，并在 baseline、每个优化点、阶段性 GPQA、最终候选和正式性能前显式触发 | 用户指定 Agent 能力拆分；正确性流程复用与触发一致性 `invariant` |
| 2026-09-11 | 0.23 | 用户要求将性能测试固化为 Skill | 新增 `inference-performance-evaluation` 项目级 Skill，以 baseline、targeted、checkpoint、profile、formal 五种模式编排现有性能工具；正式模式先核验精度 gate，并限制缩减场景与 profiler 结论范围 | 用户指定 Agent 能力拆分；性能流程复用、可比性与结论边界 `invariant` |
| 2026-09-11 | 0.24 | 用户要求将 Profiler 固化为独立 Skill | 新增 `inference-profiling`，以 capture、analyze、reprofile 编排 trace 采集、有效性/覆盖核验、热点归因和复查；性能评测 Skill 收敛为无 profiler 测量，Profiler 结论必须回到 targeted/checkpoint 验证 | 用户指定 Agent 能力拆分；诊断与性能证明分离 `invariant` |
| 2026-09-11 | 0.25 | 用户要求增加阶段性优化规划 Skill | 新增 `inference-optimization-planning`，默认每 2–3 个实验或在热点迁移、结论冲突、高成本决策前触发；统一保留/回退/失败证据，以组合实测重建累计收益并输出下一轮 1–3 个可证伪候选 | 用户指定 Agent 能力拆分；减少收益重复计算和方向惯性 `invariant` |
| 2026-09-11 | 0.26 | 用户要求精度评测期间定时通知进展 | 精度 Skill 在实际评测进程启动前创建当前任务 heartbeat，默认每 30 分钟报告一次可验证进度；终态后停用，记录 automation ID 与清理证据，gate-check 不创建监控 | 用户指定运行可观测性；防止长评测无反馈和残留任务 `invariant` |
| 2026-09-11 | 0.27 | 用户要求增加精度问题定位 Skill | 新增 `inference-accuracy-diagnosis`，在最小回归、GPQA 或输出健康失败时冻结候选，先排除测量/身份失效，再通过最小复现、单变量二分、路径证明和原范围复测定位并验证根因 | 用户指定 Agent 能力拆分；防止错误归因和带错继续优化 `invariant` |
| 2026-09-11 | 0.28 | 用户指定精度单阈值规则 | 正式精度只以预冻结的 `score >= threshold` 判定，等于阈值通过；移除相对 baseline、允许回退和输出健康审查等附加精度门槛，保留身份/产物检查用于确认分数可信 | 用户指定验收语义 `invariant` |
| 2026-09-11 | 0.29 | 用户取消超时等输出健康硬要求 | 取消 formal config 的 `allow_timeouts=false` 限制及维护版单/多服务 runner 的超时拦截；超时、空输出、截断、重复和格式异常只记录为诊断观察，在分数达阈值时不阻止 gate 或优化 | 用户指定验收语义 `invariant` |
| 2026-09-14 | 0.30 | 用户指定按场景串行优化 | 允许先完成 `4k-1k` 的 baseline 与优化，再为 `16k-1k` 建立 baseline 并优化；区分场景入口基线和原路径 anchor baseline，前者衡量增量收益，后者用于 full 阶段累计收益；跨场景改动保留前 checkpoint 已完成场景 | 用户指定实验组织规则 `invariant` |
| 2026-09-14 | 0.31 | 用户允许 baseline 过慢时先静态分析调优 | baseline 超过预记录诊断预算可标记 `deferred-too-slow/incomplete` 并转入 `static-first`；保留部分证据但不虚构基线或加速比，候选进入可测状态后补整体性能数据，原路径仍跑不完时只给有界结论且正式验收保持 incomplete | 用户指定实验节奏；测量可信度边界 `invariant` |
| 2026-09-14 | 0.32 | 用户指定统一性能优化目标场景 | 将 P1K/P4K/P16K/P32K/P64K、D1K、C64、N128 五组 finite-batch 场景提升为 Agent 正式目标目录；targeted/checkpoint 可取子集但 full 必须覆盖全部，能力不支持时显式 incomplete，禁止静默删减 | 用户指定正式 workload `invariant` |
| 2026-09-14 | 0.33 | 用户澄清最终场景与中间优化目标的关系 | 五场景只约束最终 full 结果；中间允许建立缩减 workload、阶段专项、短探针或 microbenchmark milestone，每项映射回最终场景并记录晋级条件，达标后仍须回到五场景实测 | 用户指定优化节奏与结论边界 `invariant` |
| 2026-09-14 | 0.34 | 用户调整源码授权、目标场景和阶段测试 | FlagGems-vllm 纳入目标环境直接修改授权；最终目标移除 P64K，保留 P1K/P4K/P16K/P32K；显著 milestone 后可触发中间正式四场景测试；baseline 过慢可通过缩减输入/输出/并发/请求获得 milestone 数值，不限于静态分析 | 用户指定任务边界与实验节奏 `invariant` |
| 2026-09-14 | 0.35 | 用户细化逐场景闭环、适配交接与精度节奏 | 支持按指定模型只读导入“新模型适配”交付；按 P1K→P4K→P16K→P32K 每次优化一个正式目标场景，中间 formal 只测当前场景，场景完成后切换；性能门禁改为 graph-only；明确跨算子融合；低风险完整精度改为每 4–5 点，低于阈值必须定位、修复并重跑 | 用户指定最新工作流 `invariant` |
| 2026-09-14 | 0.36 | 用户要求 Prefill/Decode 分开定位 | 每个当前目标场景先分别分析 Prefill、Decode 和 Mixed 阶段；阶段专项建立自身同配置 baseline，记录隔离方法与残余成本，单阶段收益必须回到 Mixed 端到端验证并守护另一阶段 | 用户指定诊断与晋级规则 `invariant` |
