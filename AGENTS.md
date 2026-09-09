# 端到端推理优化 Agent 说明

## 1. 项目定位

本项目用于对用户已经完成适配的模型进行端到端推理优化。模型适配结果是本项目的输入，不在本项目中复刻另一套适配工作流，也不依赖其他本地仓库的目录、状态文件或脚本。

Agent 的职责是：

1. 根据用户指定的模型、平台、机器和服务确认当前运行事实。
2. 建立可复现且正确的端到端性能基线。
3. 从请求接入到输出返回分层定位瓶颈。
4. 用单变量实验优化延迟、吞吐、显存、稳定性或成本。
5. 完成正确性回归、性能复测、结果归档和回退准备。

不得因为局部 kernel 变快、单轮 benchmark 更高或 profiler 中某个算子占比下降，就宣称端到端优化完成。

### 优化工作分类

本项目的优化工作分为两个层面，不能按代码所在目录简单区分：

1. **框架层优化（`framework`）**：在 `vllm-plugin-FL` 的扩展点和配置范围内，优化调度、批处理、KV 管理、graph 执行、主机开销、数据流及并行通信组织。关注“算子如何被组织和执行”，默认不修改 vLLM 源码。
2. **算子层优化（`operator`）**：关注具体算子或融合算子的实现效率，细分为：
   - **接入更好的算子（`replace`）**：比较现有 FlagGems、平台 vendor/native 等实现，通过 Plugin dispatch/backend 接入在目标 shape 上更快且数值兼容的实现。
   - **优化当前算子（`improve`）**：对当前实现做 tile、warp、stage、并行划分、访存、layout、融合或算法调整；需要时形成当前实现的特化版本。

分类按主要收益机制：为替换算子增加 dispatch、shape 白名单和 fallback，仍归入 `operator/replace`；降低通用 dispatch 开销归入 `framework`；新增融合 kernel 归入 `operator/improve`。跨层方案拆成关联实验，明确依赖并分别验证贡献，不重复计算收益。

默认先检查框架中的明显浪费和低风险配置，再评估热点算子的已有实现，最后投入当前算子的深度优化。这是默认排查顺序而不是强制串行阶段；实际执行按瓶颈、预期端到端净收益、证据强度、验证成本和风险排序，每次保留改动后重新排序。具体规则见 SOP 的“两层优化分类与优先级”。

## 2. 当前工作区提供的本地资源

按用途选择资源，优先使用当前仓库中的副本。除非用户明确要求比较或重新导入，不回到其他本地目录查找或执行同名文件。

### 2.1 规范文档：确定流程与设计约束

| 文档 | 职责 | 使用时机 |
|---|---|---|
| [性能优化 SOP](docs/performance-optimization-sop.md) | 优化阶段、实验顺序、候选决策与验收流程 | 每个实际优化任务开始前必读 |
| [实验契约](docs/experiment-contract.md) | workload、指标、通过标准及实验记录字段 | 开始任务时确定契约，测量前冻结 |
| [容器隔离流程](docs/container-isolation.md) | 容器复刻、挂载比较与共享源码隔离 | 创建优化环境和修改共享目录中的源码前 |
| [Plugin 设计与 PR 准备](docs/plugin-change-review.md) | 扩展点选择、多模型/多平台兼容与最终补丁要求 | Plugin 修改前及形成最终候选时 |

### 2.2 执行工具：控制环境、评测与本地验证

| 资源 | 职责与入口 |
|---|---|
| `inventory/`、`playbooks/`、`scripts/` | 本地远端控制面；Host/平台配置来自 inventory，通过 scripts 执行连接、健康、设备检查及挂载比较。依赖与 Ansible 配置由 `requirements.txt`、`ansible.cfg` 管理；连接限制见第 5 节 |
| [evaluation/](evaluation/README.md) | 维护版评测入口、参数模板、样本/分数检查及绑定验收。正式精度通过 `formal_accuracy.py` 调用原始 runner；命令与证据要求在目录说明中维护 |
| [test/](test/README.md) | 原始目标环境评测资产；`Accuracy_test/llmrun.py` 为正式模型精度实现，`perf_test/` 保存原始性能与 profiling 工具。保留导入基准，不裸跑原始示例默认配置 |
| [unit_tests/](unit_tests/README.md) | 本项目工具的本地测试，不承担模型精度或设备性能验收。完整本地检查入口为 `scripts/validate-local`，使用规则见第 14 节 |

### 2.3 知识与记录：定位问题、复用证据

- **推理栈架构资料**：[vllm-plugin-FL-analysis.md](docs/vllm-plugin-FL-analysis.md) 用于理解 Plugin 调用链与扩展点；[FlagGems-vllm 仓库讲解](docs/flaggems-vllm-analysis.md) 用于理解 vLLM 专用算子、vendor backend 和测试/benchmark；[FlagGems 仓库讲解](docs/flaggems-analysis.md) 用于理解通用算子、ATen 注册和多后端特化。三者都是特定 revision 的静态分析，分阶段使用要求见第 6 节。
- **算子知识**：[关键算子技能](skills/key-operator-analysis/SKILL.md) 包含 MLA Attention、mHC、固定版本 vLLM 源码快照及通用分析方法。仅在端到端测量或 profiler 已收敛到具体算子、dispatch、layout 或相邻融合路径时按需读取；不提前加载整套知识库，不直接套用历史硬件、shape、revision 和性能判断。
- **案例与经验**：[案例索引](docs/cases/README.md) 用于检索相似实验，[优化模式](docs/optimization-patterns.md) 用于选择有边界的候选思路。实际任务开始前检索案例，并用 [案例模板](docs/cases/TEMPLATE.md) 创建记录；结束时更新复盘与索引，判断证据是否足以修订 SOP。
- **模型实验产物**：`models/<model>/<platform>/` 保存该目标的 `baseline/`、`optimize/` 和 `acceptance/`。案例目录保留可读摘要并链接到具体产物；归档与知识沉淀要求见第 11 节。

### 2.4 事实来源：按当前证据判断

运行事实的来源优先级为：

1. 当前目标机器、容器、进程和服务的只读检查结果。
2. 本项目中带日期、revision、命令和原始产物路径的实验记录。
3. 用户在当前任务中明确提供的信息和文件。
4. 本项目已有文档中的静态分析结论。

静态文档不能替代当前运行时验证。发现冲突时，记录冲突、采用的证据和理由，不静默拼接不一致的信息。

## 3. 任务输入

一个正式优化任务应尽量明确：

```text
模型：<模型或 served-model-name>
模型路径：<远端权重路径>
平台：<nvidia|ppu|metax|ascend|mthreads|hygon>
目标机器：<inventory 中的 SSH Host 别名>
源适配容器：<已经完成模型适配、用于复刻优化环境的容器名称>
优化容器：<为本次优化新建的独立容器名称；未创建时留空>
推理引擎：<vLLM|SGLang|其他及版本>
优化目标：<TTFT|TPOT|ITL|吞吐|显存|稳定性|成本|综合目标>
工作负载：<输入长度、输出长度、并发、请求数、数据集或流量分布>
约束：<精度阈值、SLO、资源、可修改组件和禁止项>
```

如果信息不完整：

- 先做安全的本地检查和目标机器只读预检。
- 可以从正在运行的目标服务解析端口、镜像、启动参数和 revision，但不能猜测模型身份或业务 workload。
- 多个模型、平台、Host 或服务都可能是目标时，不自行选择一个执行变更。
- 缺少主指标、代表性 workload 或正确性标准时，可以形成诊断报告和候选方案，但不能自行宣布优化达标。

一次实验只属于一个明确的 `<model>/<platform>/<host>/<baseline>`。跨模型、跨平台和跨硬件数量的结果必须分开记录。

## 4. 工作边界

- 本项目不自动读取、更新或同步其他模型适配工作区。
- 不重新执行模型架构分析、环境适配、模型注册或正式适配验收，除非它们成为当前优化的明确阻塞且用户要求处理。
- 用户声明模型已完成适配时，将其作为任务前提；仍需用最小 smoke test 确认当前服务没有漂移或失效。
- 每次性能优化都必须从用户指定的已适配容器复刻一个新的专用优化容器。源适配容器只作为环境事实和基线来源，不直接承载源码修改、profiling 或性能实验。
- 默认不改模型权重和 tokenizer，不重新训练，不改变输出语义。
- 用户已授权在端到端性能优化任务中直接修改目标模型推理环境内的 `vllm-plugin-FL` 和 `FlagGems` 源码。针对当前任务的框架优化、算子接入和算子实现优化，无需仅因修改这两个仓库而再次申请授权。
- 默认保持 vLLM 源码只读；优先使用启动参数、Plugin 扩展点、FlagGems、平台 backend 或独立 Triton 实现。
- 上述授权仅限当前任务明确指定的模型、Host、容器和源码副本，不自动扩大到其他服务、共享安装或其他工作区。工具权限要求及共享环境保护规则仍然适用。
- 确实必须修改 vLLM、基础镜像、权重或共享系统配置时，先说明证据、替代方案、影响范围和回退方式，取得用户明确同意。
- 不提交模型权重、数据集、完整日志、trace、容器导出、密钥或大体积 benchmark 产物。
- 不长期保存仅反映某一时刻 PID、容器 ID、进程列表或 health 输出的原始 TXT；把仍有效的镜像、revision、挂载、命中和验证结论写入结构化配置或 Markdown，并记录外部原始产物位置。
- 不提交或推送代码，除非用户明确要求。

## 5. 远端连接和安全

### 5.1 连接来源

目标机器以本仓库 `inventory/hosts.yml` 为准。SSH 用户、端口、堡垒机和私钥路径由本机 `~/.ssh/config` 管理，禁止复制到仓库或实验日志。

连接前：

1. 用 `./scripts/inventory` 检查 Host 与平台组。
2. 明确限制到用户指定的 Host；不要为了单机任务探测整个 `managed` 组。
3. 用 `./scripts/connectivity-check --limit <host>` 验证实际连接。
4. 需要环境概览时使用 `./scripts/health-check --limit <host>`。
5. 需要设备信息时使用 `./scripts/accelerator-check --limit <host>`。

不能用普通 SSH 的退出码代替连接验证，因为堡垒机可能返回成功退出码但同时报告资产匹配失败。

### 5.2 平台命令

加速卡查询由 `inventory/group_vars/` 选择：

| 平台 | 查询命令 |
|---|---|
| NVIDIA | `nvidia-smi` |
| Huawei Ascend | `npu-smi info` |
| T-Head PPU | `ppu-smi` |
| MetaX | `mx-smi` |
| Hygon | `hy-smi`；进程查询为 `hy-smi --showpids` |
| Moore Threads | `mthreads-gmi` |

命令不存在时报告缺失，不回退到其他厂商命令。

### 5.3 远端操作规则

- 状态、日志、磁盘、进程、版本和配置检查属于只读操作。
- 聚焦的只读诊断可使用 SSH；可复现或多 Host 操作优先写成 Ansible Playbook。
- 变更前解析精确 Host、容器、服务、PID、端口和代码目录。
- 新的远端变更命令先保存到当前实验目录，再执行。
- 先在一台 Host 验证；扩大到多 Host 时串行执行并逐台报告。
- Ansible 模块支持时，变更前先使用 `--check --diff`。
- 只停止或重启当前任务明确指定的推理服务及其关联进程，并记录操作原因、PID、端口、命令、时间和 readiness。
- 不停止、重启或删除承载适配环境的容器，除非用户明确要求并确认影响。
- 不影响共享或无关工作负载。
- 删除数据、覆盖外部配置、重启主机或修改共享服务前必须获得用户明确确认。
- 不关闭 SSH host-key checking，不使用宽泛的破坏性命令，不掩盖失败验证。
- 不在日志中记录密码、Token、密钥内容、SSH 用户或堡垒机细节。

### 5.4 优化容器复刻与挂载一致性

每个新的端到端性能优化任务都必须创建独立优化容器，并把“容器来源正确”和“目录映射一致”作为进入正确性与性能测试前的硬门禁：

1. 先精确解析用户指定的源适配容器，保存其容器 runtime 的只读 inspect 结果，并记录镜像引用、镜像 ID/digest、entrypoint、command、working directory、user、关键环境变量、设备、IPC、共享内存、ulimit、网络和资源限制。
2. 新优化容器必须以源适配容器的有效适配状态为起点。若适配结果全部位于挂载目录和启动配置中，可使用相同镜像与配置复刻；若必要适配改动仍在源容器 writable layer 中，先生成并校验不可变的适配状态镜像或等价快照，不能静默退回适配前的基础镜像。
3. 从源容器 inspect 结果生成规范化目录挂载清单。所有目录型 bind mount 和 named volume 必须逐项保持相同的宿主机/volume `Source`、容器内 `Destination`、只读/可写模式、传播属性及适用的 subpath 选项；不得用复制文件、符号链接或另一个宿主机目录伪装成相同映射。
4. 容器启动后再次生成优化容器的规范化挂载清单并做机器可读 diff。存在缺失、额外挂载、源路径变化、目标路径变化或访问模式变化时，`mount_parity` 判定失败，停止后续源码修改、正确性评测和性能测试，先修正容器创建配置。
5. 容器名、宿主机端口和日志路径必须使用不会冲突的新值；它们不属于目录映射一致性的要求。容器内服务端口、设备拓扑和其他影响可比性的运行参数应保持一致，任何必要差异都必须记录为环境变量并触发相应的新基线。
6. 启动前检查设备、端口、共享内存和宿主机资源冲突。保留源适配容器，不在本任务中直接停止、重启、修改或删除它；若其正在占用本次优化所需的独占资源，先隔离资源或取得影响该服务的明确授权，不能通过争抢资源得到基线。
7. 相同目录映射意味着新旧容器可能共享模型、Plugin、FlagGems、缓存或输出目录。修改前记录这些目录的 revision、工作区状态和共享使用者，并保存补丁与回退方法；不得把“新建容器”误认为“宿主机挂载内容已经隔离”。

共享源码的隔离分支见 [容器隔离流程](docs/container-isolation.md)。挂载完全保持一致；允许在优化容器未挂载的私有目录建立真实源码副本并切换实际导入路径，不能用它伪装挂载相等。

源、目标 inspect 原文可以保存在外部产物路径；当前项目至少记录校验后的镜像身份、规范化挂载清单路径、diff 结果、例外及批准依据。只有 `image_lineage=verified` 且 `mount_parity=passed` 后，优化容器才可用于 baseline、candidate 和 revert 测量。

## 6. Plugin、FlagGems-vllm 与 FlagGems 分析资料的使用

本地分析文档按调用层次分为：

| 文档 | 主要解决的问题 | 典型查阅阶段 |
|---|---|---|
| `docs/vllm-plugin-FL-analysis.md` | Plugin entry point、Worker/ModelRunner/Scheduler 扩展、执行组织与 Plugin 内 dispatch | 环境核验、框架瓶颈定位、Plugin 改动设计 |
| `docs/flaggems-vllm-analysis.md` | vLLM 专用/融合算子、包级导出、vendor backend、测试与 microbenchmark | 专用算子命中定位、`operator/replace`、`operator/improve` |
| `docs/flaggems-analysis.md` | 通用 PyTorch/ATen 算子注册、通用/vendor 实现选择、FlagTune 与算子测试 | ATen 热点定位、通用算子替换和当前实现优化 |

三份文档共同用于快速理解：

- Plugin entry point 与启动注入链路
- `PlatformFL`、Worker、ModelRunner 和 Scheduler 扩展
- `CachedOp → OpManager → OpRegistry` dispatch 结构
- Plugin → FlagGems 通用 ATen 注册及 Plugin → FlagGems-vllm 专用算子的两类路径
- FlagGems/FlagGems-vllm 中 reference、通用实现、vendor backend 和 Triton 实现的选择关系
- attention、MoE、量化、通信、KV cache 与 graph 路径
- 测试体系、已知风险和代码评审清单

使用规则：

1. 不在任务开始时通读三份资料。先核验实际依赖和调用路径，再按表中阶段读取对应文档的报告信息、核心结论和专题。
2. 在目标环境中重新核对 Plugin、vLLM、FlagGems-vllm、FlagGems revision、版本、安装方式和真实导入目录；未安装的组件记为不适用。
3. 文档路径、类名或结论与当前 revision 不一致时，以当前代码为准并记录差异。
4. 优先选择最窄扩展点：配置参数，其次 Plugin shim/dispatch/backend，再次 Plugin 内 Triton，最后才考虑 runtime patch。
5. 不以 fallback 成功证明目标 backend 已命中；必须记录实际 `impl_id`、dispatch 日志或等价证据。
6. Plugin hook 必须幂等，因为 general plugin 可能在多个 worker 中重复加载。
7. 新实现必须同时考虑 eager 与 graph capture/replay，不能只在 eager 下验证。
8. FlagGems 与 FlagGems-vllm 存在同名或相近算子时，从运行中函数对象、import、注册 key 和 profiler 反向确认来源，不按文件名推断。
9. 当前常规修改授权只覆盖 `vllm-plugin-FL` 和 `FlagGems`；对独立 `FlagGems-vllm` 的只读分析不扩大为修改授权，确需修改时先确认本次任务边界。

## 7. 执行流程与门禁入口

完整阶段步骤统一维护在 [SOP](docs/performance-optimization-sop.md)，workload 可比性、指标、实验 schema 和最终报告字段统一维护在 [实验契约](docs/experiment-contract.md)。开始实际优化前必须阅读两者并创建案例。

执行顺序：目标与授权 → 源容器事实 → 独立优化容器及镜像/挂载门禁 → smoke/C8 护栏 → 无 profiler 基线 → 分层诊断与单变量实验 → 候选回归 → 正式精度 → 同配置正式性能及回退 → 复盘。

- 正式精度在目标机器上基于 `harbor.baai.ac.cn/flageval/flageval-llmeval:v1` 镜像的评测容器内执行，通过 `evaluation/accuracy/formal_accuracy.py` 包装调用原始 `test/Accuracy_test/llmrun.py`，对候选 graph 服务运行完整 GPQA Diamond（`gpqa_diamond_generative_cot`，默认 198 题）。必须显式提供案例配置、预冻结契约、当前服务身份和评测容器 inspect。
- `evaluation/accuracy/` 中的辅助 runner 不能在未说明等价性时替代原始正式模型评测实现；`verify_accuracy.py` 仅作分数检查。`llmrun_parallel.py` 只在用户明确指定多服务或多 shard 时使用，不是默认正式入口。
- 完成样本结构与分数检查后，还需对同一 samples SHA 的输出健康做审查，由 `evaluation/accuracy/acceptance.py issue` 生成正式记录。单独数值阈值通过不是正式验收。
- 正式性能必须核对 gate 与当前服务身份及结果文件 SHA。配置、源码、权重、tokenizer 或服务实例变化后旧 gate 不再适用。baseline/revert 的比较记录与候选正式精度身份分别保存。
- 原始 `test/` runner 和示例配置保持导入基准；正式流程不裸跑示例默认配置。执行命令见 [评测入口](evaluation/README.md)。
- 缺少正式精度或主指标门槛时，只报告诊断/性能研究及未完成状态；用户已批准暂缓的步骤按明确范围记录，不反复申请相同授权。

## 10. Plugin、FlagGems 和 Triton 改动要求

**Plugin 修改必须同时考虑端到端收益与上游可维护性。** 用户后续将基于优化代码提交 PR；修改前及形成最终候选前，必须按 [Plugin 优化设计与 PR 准备](docs/plugin-change-review.md) 核对目标 revision 的框架设计、现有扩展点、多模型/多平台影响和验证证据。

- 优先复用现有 registry/dispatch/backend/config 边界；平台特例留在平台边界，模型语义差异留在模型边界。性能特化按能力和真实 shape 等条件选择，禁止以模型路径、served name 或机器身份代替支持条件。
- 保持非目标模型/平台的导入、默认选择和原路径行为；保护可选依赖、strict/fallback 语义、worker 生命周期及缓存隔离。未实测的平台如实标记，不把 mock 当作硬件通过。
- 区分实验补丁和可供 PR 评审的最终代码；整理后重新验证，报告 `pr_readiness`、跨仓库依赖及未测项。局部收益不能豁免设计问题，不擅自提交/推送或创建 PR。

- 修改前记录 Plugin、vLLM、FlagGems-vllm（若安装）和 FlagGems revision、branch 与工作区状态。
- 解析运行中服务实际使用的 Plugin、FlagGems-vllm（若安装）和 FlagGems 导入路径、安装方式及源码目录，确认修改的是目标服务使用的副本。已有未提交改动必须保留，不 reset、覆盖或擅自同步升级。
- 框架逻辑及接入代码优先在 Plugin 中修改；当前 FlagGems 算子的实现、调优配置或平台特化可以直接在 FlagGems 中修改，不要求为了避开 FlagGems 源码而复制到 Plugin。
- 涉及两个仓库时分别保存基线、补丁和回退方法；将源码修改、必要的构建/安装和目标服务重载步骤记录到本项目案例中。验证服务实际加载新代码，不以磁盘文件已更新代替生效证明。
- 验证请求确实进入修改路径，不以代码存在代替命中证据。
- 优先复用 Plugin 已有 dispatch、backend 和 OOT operator 入口。
- FlagGems 实现必须核对当前符号、支持 dtype、shape/layout 和 graph 能力。
- FlagGems 不具备兼容实现时，Plugin 内新增 Triton 实现必须有可信 reference。
- 覆盖数值、dtype、shape、stride/layout、设备、边界 batch 和 zero-token 场景。
- eager 和 graph capture/replay 分别测试；graph 至少完成 capture 和两次 replay。
- 避免 capture-time host sync、动态分配、数据依赖主机控制流和不稳定地址。
- fallback 只用于诊断或明确的兼容策略，不能掩盖目标 backend 失效。
- 性能改动附带最小正确性测试和同条件端到端 benchmark。

## 11. 项目产物结构

第一个实际任务开始时，按需创建：

```text
models/<model>/<platform>/
├── README.md
├── baseline/
│   ├── baseline-manifest.yml
│   ├── workload.yml
│   └── result-summary.md
├── optimize/
│   ├── README.md
│   ├── experiments/<experiment-id>/
│   ├── profiling/
│   ├── patches/
│   └── performance-measurements.json
└── acceptance/
    ├── accuracy-config.yml
    ├── performance-config.yml
    ├── accuracy-result.md
    ├── performance-result.md
    └── optimization-summary.md

benchmarks/              # 参数化 benchmark 客户端和 workload
evaluation/              # 公共精度/性能 runner、模板与验收门禁
scripts/                 # 通用控制与结果处理工具
test/                    # 目标环境中实际执行的精度评测、性能 benchmark 和 profiling 工具
unit_tests/              # 当前项目控制与评测代码的本地单元测试
docs/                    # 架构分析和跨模型方法记录
  performance-optimization-sop.md
  cases/                 # 已执行案例、失败实验与经验索引
skills/                  # 项目级可复用技能与按需加载的知识库
```

每个实际 `<model>/<platform>/` 下只准备 `baseline/`、`optimize/` 和 `acceptance/` 三个子目录；平台根部可以保留一个导航 `README.md`，不得再创建与三者并列的 `experiments/`、`profiling/`、`patches/` 或其他结果目录。

- `baseline/`：保存优化前的环境、workload、正确性状态和基线性能记录。
- `optimize/`：保存多轮瓶颈分析、假设、配置、命令、profiling 摘要、源码补丁、失败/回退以及每轮优化后的性能记录。每轮必须可区分，不能只覆盖为最终最好的一轮。
- `acceptance/`：只保存最终候选的正式性能优化记录、正式精度达标记录、验收配置、结论和回退入口；中间轮次或未达标结果留在 `optimize/`。

不要为未请求的模型或平台批量生成空目录。原始日志、CSV/JSONL、SQLite、trace、profile 和大数据集只记录外部绝对路径或对象存储位置。

### 案例摘要与知识沉淀

`docs/cases/<case-id>/` 默认只保留 `README.md`；瓶颈分析、单变量实验或多轮结果无法在摘要中清晰表达时，再增加少量专题 Markdown。完整配置、可复用命令、补丁和逐轮结果摘要归入模型/平台的 `optimize/`，案例中保留证据链接。

一次性的 `install-*`、`run-*`、PID/容器状态快照、监控和硬编码远端修复脚本，在结论提取后不长期保存。确实承担复现、正确性或结果校验作用的代码，参数化后放入对应模型/平台的 `optimize/`，或提升到 `test/`、`scripts/`、`unit_tests/` 的相应公共工具目录。

单次案例结论先记录为 `observation` 或 `reproduced`。只有跨场景复现、机制和边界明确的经验，或正确性/安全/测量有效性要求，才进入 SOP；不得填写未执行的数据或虚构案例。

关键算子知识按证据逐层维护：

- `case-index.md` 保存可匹配的证据卡，链接到案例与实验产物。
- `optimization-map.md` 保存会改变后续行动的触发信号、适用条件、首个实验、反例和停止条件。
- 稳定 `README.md` 只在语义、实现模型或跨案例瓶颈理解发生变化时更新，不按日期追加完整案例。

具体方法见 [案例到知识的沉淀规则](skills/key-operator-analysis/references/case-to-knowledge.md)。

## 12. 实验记录

使用 [实验契约中的 schema](docs/experiment-contract.md)，每轮实验独立编号，记录规则版本、验收范围、未知项和原始产物位置。配置是事实主记录；案例与报告引用它，避免重复维护同一状态。

## 13. 代码和配置要求

- 新 benchmark 必须参数化模型、tokenizer、Host、端口、endpoint、数据集和 case。
- 不在脚本中写入只适用于某台机器的默认绝对路径。
- 配置提供清晰默认值，并允许命令行或配置文件覆盖。
- Shell 脚本使用严格错误处理，打印解析后的目标但不泄露秘密。
- 性能敏感代码解释 shape/dtype/layout、同步和 graph 约束。
- 不提交临时调试代码、完整 trace 或大体积结果。
- 不删除失败或负优化记录以制造连续成功的叙事。

## 14. 本地验证命令

首次使用控制面：

```bash
./scripts/bootstrap-control-node
```

修改 inventory、group variables、脚本或 Playbook 后：

```bash
./scripts/inventory
./scripts/syntax-check
```

修改普通文档或提交前至少运行：

```bash
git diff --check
```

修改公共评测代码后运行：

```bash
PYTHONPYCACHEPREFIX=/tmp/e2e-eval-pycache \
  python3 -m py_compile evaluation/accuracy/*.py evaluation/performance/*.py
PYTHONPYCACHEPREFIX=/tmp/e2e-eval-pycache \
  python3 -m unittest discover -s unit_tests -p 'test_*.py'
python3 evaluation/accuracy/verify_accuracy.py --help
python3 evaluation/performance/vllm_perf.py --help
python3 evaluation/performance/vllm_profile.py --help
python3 test/Accuracy_test/llmrun.py --help
python3 evaluation/accuracy/formal_accuracy.py --help
python3 evaluation/accuracy/acceptance.py --help
```

只有任务确实需要连接目标机器时，才运行：

```bash
./scripts/connectivity-check --limit <host-alias>
./scripts/health-check --limit <host-alias>
./scripts/accelerator-check --limit <host-alias>
```

不得无目的地对整个 inventory 执行远端检查。

## 15. 最终报告

按 [实验契约的报告字段](docs/experiment-contract.md) 汇报对象、证据、对比、正确性、限制、复现与回退。只完成诊断或探索时，准确使用对应状态，不写成正式优化完成。
