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

本仓库自包含以下控制和分析材料：

```text
ansible.cfg
requirements.txt
inventory/
  hosts.yml
  group_vars/
playbooks/
  connectivity-check.yml
  health-check.yml
  accelerator-check.yml
scripts/
  bootstrap-control-node
  inventory
  connectivity-check
  health-check
  accelerator-check
  ansible
  playbook
  syntax-check
docs/
  vllm-plugin-FL-analysis.md
  performance-optimization-sop.md
  cases/
evaluation/
  README.md
  ACCEPTANCE_TEMPLATE.md
  accuracy/
  performance/
test/
  Accuracy_test/
    README.md
    llmrun.py
    llm_config.json
    score_progress.py
  perf_test/
unit_tests/
  README.md
  test_verify_accuracy.py
skills/
  key-operator-analysis/
    SKILL.md
    references/
```

这些文件是当前项目的一部分。后续任务必须优先使用当前仓库中的副本，不回到其他本地目录查找或执行同名文件，除非用户明确要求比较或重新导入。

事实来源优先级为：

1. 当前目标机器、容器、进程和服务的只读检查结果。
2. 本项目中带日期、revision、命令和原始产物路径的实验记录。
3. 用户在当前任务中明确提供的信息和文件。
4. 本项目已有文档中的静态分析结论。

静态文档不能替代当前运行时验证。发现冲突时，记录冲突、采用的证据和理由，不静默拼接不一致的信息。

### 关键算子知识技能

当端到端测量或 profiler 已把瓶颈收敛到具体算子、dispatch、layout 或相邻融合路径时，使用 `skills/key-operator-analysis/SKILL.md`。该技能包含 MLA Attention、mHC、固定版本 vLLM 源码快照和通用算子分析方法。

不要在尚无算子级证据时加载整套知识库，也不要把历史分析中的硬件、shape、revision 或性能判断直接套用到当前目标。

关键算子知识以实际端到端案例驱动演进，而不是把每次案例按日期追加到算子长文：完整环境、命令、patch、性能数字和失败过程保留在 `docs/cases/`；算子目录的 `case-index.md` 保存可匹配的证据卡；`optimization-map.md` 保存由案例提炼的触发信号、适用条件、首个实验、反例和停止条件；稳定 `README.md` 只在语义、实现模型或跨案例瓶颈理解发生变化时更新。具体规则见技能中的 `references/case-to-knowledge.md`。

### 性能优化 SOP 与案例库

每个实际优化任务开始前阅读 `docs/performance-optimization-sop.md`，并在 `docs/cases/README.md` 中检索相似案例。开始执行时使用 `docs/cases/TEMPLATE.md` 创建案例记录；任务结束时完成复盘、更新案例索引，并判断是否有足够证据修订 SOP。

单次案例结论先记录为 observation 或 reproduced，不直接升级为通用规则。只有跨场景复现、机制和边界明确的经验，或正确性/安全/测量有效性要求，才进入 SOP。不得为了让知识库显得完整而填写未执行的数据或虚构案例。

### 正式精度评测入口

`test/Accuracy_test/` 是本项目正式模型级精度评测工具目录。默认正式流程固定为：在目标机器上进入基于 `harbor.baai.ac.cn/flageval/flageval-llmeval:v1` 镜像的评测容器，使用 `test/Accuracy_test/llmrun.py` 对候选 graph 服务执行完整 GPQA Diamond（`gpqa_diamond_generative_cot`）评测。

`evaluation/accuracy/` 中的参数化副本和 `verify_accuracy.py` 用于配置模板、预检、结果门禁或工具维护，不能在未说明等价性时替代上述正式 runner。`llmrun_parallel.py` 只在用户明确指定多服务或多 shard 时使用，不是默认正式入口。

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

源、目标 inspect 原文可以保存在外部产物路径；当前项目至少记录校验后的镜像身份、规范化挂载清单路径、diff 结果、例外及批准依据。只有 `image_lineage=verified` 且 `mount_parity=passed` 后，优化容器才可用于 baseline、candidate 和 revert 测量。

## 6. `vllm-plugin-FL` 分析资料的使用

本地分析文档为 `docs/vllm-plugin-FL-analysis.md`。它基于文档中记录的特定 revision 做静态分析，用于快速理解：

- Plugin entry point 与启动注入链路
- `PlatformFL`、Worker、ModelRunner 和 Scheduler 扩展
- `CachedOp → OpManager → OpRegistry` dispatch 结构
- FlagGems、reference、vendor backend 和 Triton 实现的选择关系
- attention、MoE、量化、通信、KV cache 与 graph 路径
- 测试体系、已知风险和代码评审清单

使用规则：

1. 开始 Plugin 相关优化前先读该文档的报告信息、核心结论和对应专题。
2. 在目标环境中重新核对 Plugin、vLLM、FlagGems revision 和真实目录。
3. 文档路径、类名或结论与当前 revision 不一致时，以当前代码为准并记录差异。
4. 优先选择最窄扩展点：配置参数，其次 Plugin shim/dispatch/backend，再次 Plugin 内 Triton，最后才考虑 runtime patch。
5. 不以 fallback 成功证明目标 backend 已命中；必须记录实际 `impl_id`、dispatch 日志或等价证据。
6. Plugin hook 必须幂等，因为 general plugin 可能在多个 worker 中重复加载。
7. 新实现必须同时考虑 eager 与 graph capture/replay，不能只在 eager 下验证。

## 7. 标准优化流程

### 阶段 0：目标预检

1. 检查当前仓库状态，保护用户已有改动。
2. 阅读当前 SOP，并检索相似案例和相关算子知识。
3. 解析模型、平台、Host、源适配容器、服务和优化目标。
4. 检查连接、设备、无关工作负载和可用资源。
5. 只读检查源适配容器，记录有效适配状态、镜像身份、完整目录挂载和运行配置。
6. 基于源适配容器创建新的专用优化容器；复用原目录映射，并为容器名、宿主机端口和日志路径分配不冲突的值。
7. 对源容器与优化容器执行镜像谱系和规范化挂载 diff；未达到 `image_lineage=verified`、`mount_parity=passed` 时不得继续。
8. 在优化容器内记录权重、tokenizer、引擎、Plugin、FlagGems、驱动/runtime、启动参数和实际导入路径。
9. 仅在优化容器内启动目标服务，查询 `/v1/models`、readiness 和当前 endpoint。
10. 创建案例记录并形成 `baseline-manifest.yml`，未知项保持未知，不自行补值。

### 阶段 1：正确性护栏

1. 固定 prompt、随机样、随机种子、采样参数、模型名称和 tokenizer。
2. 运行最小单请求 smoke test。
3. 运行固定小批量和 8 并发 sanity case。
4. 检查每条输出，而不只检查 HTTP 状态码。
5. 记录错误、超时、空回复、截断、机械重复、乱码和格式异常。
6. 对量化、算子替换、采样、KV cache 或 graph 变化增加数值、logits 或参考输出对照。

正确性护栏失败时不进入正式性能优化。先判断是当前服务漂移、适配缺陷、评测问题还是优化改动导致的回归。

本项目的公共评测入口位于 `evaluation/`。每个正式案例在开始测试前从 `evaluation/ACCEPTANCE_TEMPLATE.md` 建立案例专属验收记录，并冻结绝对精度门槛或可信 baseline 的最大允许回退。不得在看到 candidate 分数后选择更有利的 metric、样本子集或放宽门槛。

其中，验收记录和结果门禁位于 `evaluation/`，正式 GPQA Diamond 执行入口固定为 `test/Accuracy_test/llmrun.py`。评测必须在目标机器上的独立评测容器内发起；该容器的镜像必须核验为 `harbor.baai.ac.cn/flageval/flageval-llmeval:v1`。模型服务仍运行在本次新建的优化容器中，评测容器作为客户端访问其 OpenAI 兼容 endpoint，不能把评测容器当成模型推理容器。

### 阶段 2：建立无 profiler 基线

区分以下阶段：

- 冷启动：容器/进程启动、模型加载、编译、graph capture 和首个请求。
- 预热：allocator、cache、JIT/compile 和 graph 稳定前的请求。
- 稳态：完成预热后的可比测量。

至少记录：

- 成功、失败和超时请求数
- 请求吞吐（req/s）
- 输入、输出和总 token 吞吐（tokens/s）
- TTFT、TPOT、ITL 的 P50/P95/P99
- 端到端延迟 P50/P95/P99
- 峰值与稳态显存
- 加速卡利用率和功耗
- 主机 CPU、内存和网络情况
- 多卡通信占比与负载不均衡
- OOM、EngineDead、graph capture/replay 和服务异常

工具只提供 mean、median 或 P99 时如实记录，不推导不存在的百分位。每个正式 case 至少一轮预热和多轮稳态测量，优先报告稳态中位数与波动范围。

### 阶段 3：分层定位瓶颈

按从外到内的顺序：

1. 请求级：客户端限速、网络、排队、调度、continuous batching、尾延迟。
2. 阶段级：tokenizer、prefill、decode、采样、detokenize、流式返回。
3. 框架级：KV cache、prefix cache、内存分配、CPU/设备同步、graph break、编译和数据搬运。
4. 并行级：TP/PP/EP/DP、collective、跨机网络、专家负载均衡。
5. 算子级：kernel 时间、launch gap、occupancy、访存、融合、shape/dtype/layout。

先用低开销指标缩小范围，再启用 profiler。Profiler 数据用于归因；有 profiler 与无 profiler 的性能数字不得直接比较。

当证据进入第 5 层时，按“关键算子知识技能”中的路由读取相关材料，并把算子结论重新关联到端到端主指标。

形成候选清单时，为每项标注 `framework`、`operator/replace` 或 `operator/improve`，记录排序依据、依赖、首个验证实验及暂缓理由。请求、通信、内存等是瓶颈定位维度，不额外成为第三类优化工作；超出 Plugin 或当前授权边界的事项单独报告。

### 阶段 4：单变量实验

每轮实验写明：

1. 瓶颈证据。
2. 可证伪的优化假设。
3. 唯一主要变量。
4. 主指标、守护指标和预期结果。
5. 修改文件、远端命令和服务生命周期操作。
6. 最小正确性回归。
7. 同条件 baseline 与 candidate 结果。
8. 保留、回退、未证实或继续实验的决定。

除诊断性 A/B 外，不同时叠加多项主要改动。差异处于测量噪声内时结论为“未证实提升”。失败和负优化也保留简洁证据。

### 阶段 5：候选方案回归

对保留方案：

- 重跑全部代表性 workload，不只跑受益 case。
- 覆盖短、中、长输入，不同输出长度和业务并发区间。
- 覆盖 graph capture/replay、混合 batch、cache 冷热和长稳。
- 检查显存、错误率、超时、尾延迟和输出质量。
- 多卡或多机方案检查 collective 和负载均衡。
- 保留可以恢复原基线的启动参数、配置或补丁。

### 阶段 6：最终验收

1. 分别确认 `eager` 与 `graph` 能运行；后续正式验收统一使用候选 `graph` 配置。
2. 使用候选配置完成固定小样本和 8 并发正确性/性能 sanity。
3. 在目标机器上核验或创建基于 `harbor.baai.ac.cn/flageval/flageval-llmeval:v1` 镜像的评测容器，记录容器名、镜像引用和 image ID/digest，并确认它能访问优化容器中的候选 graph 服务及 `/v1/models`。
4. 在评测容器内使用 `test/Accuracy_test/llmrun.py` 先执行 `--preflight-only`，再运行完整的 `gpqa_diamond_generative_cot`；默认单服务、`limit=0`、`expected_samples=198`，不得用阶段分数、抽样结果或 `llmrun_parallel.py` 替代，除非用户明确改变正式方案。
5. 核验正式进程、198 个唯一完整样本、`results_*.json`、`samples_*.jsonl`、effective config、异常回复、空输出、截断、重复和超时，不只看聚合分数或退出码。
6. 使用预先冻结的绝对门槛，或相对可信 baseline 的最大允许回退判定精度；阶段分数只用于排障。
7. 精度门禁通过后，使用同一 `graph` 服务配置运行 `test/perf_test/` 或项目中已验证等价的参数化性能工具完成正式性能测试。
8. 重跑 baseline、candidate 与 revert，避免把环境时间漂移当成提升。
9. 需要时完成通信和长时间稳定性验证。
10. 输出可复现配置、前后对比、限制和回退方法。

优化过程中可以运行探索性短 benchmark，但没有正式精度工具、可信 baseline 或预先确定的通过标准时，只能报告诊断性性能结果和正确性 sanity，不能宣称候选通过正式性能验收。

### 阶段 7：复盘与 SOP 演进

1. 完成案例记录，保留成功、失败、负优化、回退和阻塞证据。
2. 更新 `docs/cases/README.md` 索引与检索标签。
3. 判断经验等级：`observation`、`reproduced`、`transferred` 或 `invariant`。
4. 对实际分析过的关键算子写出知识差量：既有判断被确认、细化、反驳，还是没有新增理解。
5. 将完整证据保留在案例目录，在算子 `case-index.md` 增加证据卡；只有后续诊断动作改变时才更新 `optimization-map.md`，只有稳定理解改变时才更新算子 `README.md`。
6. 将跨算子的工作方法更新到 SOP。SOP 变更必须关联案例、证据等级、适用范围、收益和风险；单次成功不自动形成强制规则。

## 8. Workload 和可比性

正式比较必须固定并记录：

- 输入、输出 token 长度及其分布
- 并发、请求数、到达模式和请求速率
- 数据集、随机种子、prompt 模板和 endpoint
- EOS 策略、采样参数和最大生成长度
- 模型、tokenizer、dtype、量化和权重 revision
- eager/graph、TP/PP/EP/DP、KV cache 和 prefix cache 配置
- Host、设备数量与拓扑、容器镜像和软件 revision
- 预热轮数、正式轮数、失败和超时处理方式

以下结果不能直接比较：

- 不同硬件或设备数量
- 不同长度、并发、请求数或到达模式
- `/v1/completions` 与 `/v1/chat/completions`
- `ignore_eos` 开启与关闭
- 随机 token workload 与真实对话 workload
- profiler 开启与关闭
- eager 与 graph
- 精度、量化、采样或 cache 配置不同
- 一方包含失败请求而另一方不包含

随机 workload 用于受控吞吐和延迟分析；真实或代表性数据用于业务结论。两类结果分开报告。

## 9. 指标和决策

任务开始时定义：

```text
主指标：本轮必须改善的指标
守护指标：不得明显回退的正确性、稳定性、尾延迟、显存或成本指标
通过门槛：相对提升、绝对 SLO 和允许波动
```

若用户未指定门槛，Agent 只报告客观差异和不确定性，不自行宣布“达标”。

优化取舍规则：

- 正确性和稳定性是硬门槛。
- 业务 SLO 优先于孤立峰值吞吐。
- 尾延迟不能被平均值掩盖。
- 吞吐提升同时报告设备数量、显存和功耗变化。
- 显存换吞吐、TTFT 换 TPOT、prefill 换 decode 等取舍必须显式说明。

## 10. Plugin、FlagGems 和 Triton 改动要求

- 修改前记录 Plugin、vLLM 和 FlagGems revision、branch 与工作区状态。
- 解析运行中服务实际使用的 Plugin 和 FlagGems 导入路径、安装方式及源码目录，确认修改的是目标服务使用的副本。已有未提交改动必须保留，不 reset、覆盖或擅自同步升级。
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
├── experiments/
│   └── <experiment-id>/
│       ├── hypothesis.md
│       ├── config.yml
│       ├── commands.sh
│       └── result-summary.md
├── profiling/
│   ├── README.md
│   └── summaries/
├── acceptance/
│   ├── correctness-config.yml
│   ├── performance-config.yml
│   └── optimization-summary.md
└── patches/

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

不要为未请求的模型或平台批量生成空目录。原始日志、CSV/JSONL、SQLite、trace、profile 和大数据集只记录外部绝对路径或对象存储位置。

## 12. 实验记录最小字段

```yaml
schema_version: 2
experiment_id: YYYYMMDD-HHMM-short-name
objective: ""
status: planned
target:
  model: ""
  model_path: ""
  weight_revision: ""
  platform: ""
  host: ""
  source_container_name: ""
  optimization_container_name: ""
  source_image_ref: ""
  source_image_id: ""
  optimization_image_id: ""
  image_lineage: unverified  # unverified | verified | failed
  source_mount_manifest: ""
  optimization_mount_manifest: ""
  mount_diff: ""
  mount_parity: unverified  # unverified | passed | failed
runtime:
  engine: ""
  engine_revision: ""
  plugin_revision: ""
  flaggems_revision: ""
  mode: graph
  dtype: ""
  quantization: ""
  tensor_parallel: null
  pipeline_parallel: null
  expert_parallel: null
  launch_args: []
workload:
  dataset: ""
  endpoint: ""
  requests: null
  concurrency: null
  input_tokens: ""
  output_tokens: ""
  seed: null
  warmup_rounds: null
  measured_rounds: null
change:
  optimization_layer: null  # framework | operator
  operator_strategy: null  # replace | improve；framework 时为 null
  hypothesis: ""
  primary_variable: ""
  files: []
results:
  correctness: ""
  successful_requests: null
  failed_requests: null
  request_throughput_rps: null
  output_throughput_tps: null
  total_throughput_tps: null
  ttft_p50_ms: null
  ttft_p95_ms: null
  ttft_p99_ms: null
  tpot_p50_ms: null
  tpot_p95_ms: null
  tpot_p99_ms: null
  e2e_p99_ms: null
  peak_memory_gb: null
decision: pending
artifacts:
  raw_results: ""
  logs: ""
  traces: ""
notes: ""
```

不可用指标保持 `null`，不得用 `0` 伪装已测量。

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
```

只有任务确实需要连接目标机器时，才运行：

```bash
./scripts/connectivity-check --limit <host-alias>
./scripts/health-check --limit <host-alias>
./scripts/accelerator-check --limit <host-alias>
```

不得无目的地对整个 inventory 执行远端检查。

## 15. 最终报告

每次优化任务至少汇报：

```text
优化对象：模型 / 平台 / Host / revision
容器谱系：源适配容器 / 新优化容器 / 镜像身份 / 挂载一致性证据
优化目标：主指标、守护指标、通过门槛
当前环境：容器、引擎、Plugin、FlagGems、硬件与启动配置
瓶颈证据：请求、阶段、框架、通信或算子证据
基线：workload、轮次、性能、正确性和资源结果
改动：文件、参数、补丁与服务操作
优化分类：框架层 / 算子接入 / 当前算子优化；排序依据与跨层依赖
候选结果：同条件多轮对比和波动
正确性：sanity、正式评测、异常回复和超时
精度环境：目标机器 / 评测容器 / `flageval-llmeval:v1` 镜像身份 / `llmrun.py` 与配置校验值 / GPQA 198 题完整性
稳定性与资源：显存、利用率、错误和长稳
结论：保留、回退、未证实或阻塞
风险与限制：未覆盖场景和不可比项
复现：命令、配置和原始产物路径
下一步：按预期收益、证据强度和风险排序
经验沉淀：案例路径、证据等级、SOP/算子知识更新
```

只完成诊断、工具准备或探索性实验时，准确使用对应状态，不写成“优化完成”。
