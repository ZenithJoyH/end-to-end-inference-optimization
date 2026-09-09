# 端到端推理优化

面向**已经完成适配的模型推理服务**，由 Agent 协同完成运行事实核验、性能基线、瓶颈定位、单变量优化、正确性回归和结果归档。

项目以端到端收益为依据，关注 TTFT、TPOT/ITL、吞吐、尾延迟、显存、稳定性和资源成本。局部 kernel 加速需要在真实服务路径中兑现；最终代码还需符合 `vllm-plugin-FL` 的框架设计，具备多模型、多平台兼容性及后续提交 PR 所需的证据。

本仓库保存独立的控制工具、评测入口、实验记录与知识库。模型权重、实际推理环境和大体积原始产物保留在目标机器或外部存储；运行时不依赖其他本地模型适配工作区。

## 文档导航

实际优化以 **SOP 为执行主线**。先确认任务规则，再根据当前阶段查阅专项说明；技术资料用于解释瓶颈和选择实验。

### 开始任务：规则与流程

- [AGENTS.md](AGENTS.md)：明确 Agent 的职责、授权范围、远端操作边界和必须遵守的约束。
- [性能优化 SOP](docs/performance-optimization-sop.md)：组织从目标预检、基线、诊断到实验、验收和复盘的完整流程。

### 执行任务：按阶段查阅

| 当前阶段 | 查阅文档 | 解决的问题 |
|---|---|---|
| 定义实验 | [实验契约](docs/experiment-contract.md) | 测什么、怎样比较、以什么标准判断、记录哪些字段 |
| 准备环境 | [容器隔离流程](docs/container-isolation.md) | 怎样继承有效适配状态、保持挂载一致并隔离源码修改 |
| 核验 vLLM 专用算子栈 | [FlagGems-vllm 仓库讲解](docs/flaggems-vllm-analysis.md) | Plugin 怎样调用 vLLM 专用算子、如何定位通用实现与 vendor backend |
| 核验通用算子后端 | [FlagGems 仓库讲解](docs/flaggems-analysis.md) | ATen 注册、通用/vendor 实现选择、算子测试和调优入口在哪里 |
| 设计与整理改动 | [Plugin 设计与 PR 准备](docs/plugin-change-review.md) | 改动放在哪个扩展点、影响哪些模型/平台、如何准备最终补丁 |
| 执行评测与验收 | [评测入口](evaluation/README.md) | 使用哪个 runner、怎样运行、如何核验精度与性能证据 |

### 分析问题：查架构、算子和案例

- **理解执行与接入层**：[Plugin 架构分析](docs/vllm-plugin-FL-analysis.md) 用于定位调用链、模块职责和扩展点。
- **理解 vLLM 专用算子层**：[FlagGems-vllm 仓库讲解](docs/flaggems-vllm-analysis.md) 用于追踪 Plugin 显式调用的 MoE、Attention、KV、量化和采样等专用算子。
- **理解通用算子层**：[FlagGems 仓库讲解](docs/flaggems-analysis.md) 用于追踪 PyTorch/ATen 注册、通用实现、vendor 特化和调优入口。三份分析资料使用时都要核对目标代码 revision 与真实导入路径。
- **深入具体算子**：[关键算子技能](skills/key-operator-analysis/SKILL.md) 在已有算子级瓶颈证据时使用，按需读取 MLA、mHC 等材料。
- **借鉴已有实验**：[案例索引](docs/cases/README.md) 提供具体环境、结果和失败证据；[优化模式](docs/optimization-patterns.md) 提供提炼后的候选思路与适用边界。

## 优化范围

本项目从请求接入到输出返回定位瓶颈，检查请求与排队、prefill/decode、调度与批处理、KV/graph、并行通信和具体算子。确定耗时位置后，**实施工作按收益机制分为框架层和算子层；算子层再分为接入已有实现和优化当前实现。**

```text
端到端推理优化
├── 框架层 framework          改善任务、数据和算子的执行组织
└── 算子层 operator           改善具体运算的执行效率
    ├── replace              选择并接入更好的已有实现
    └── improve              调优或重新实现当前算子
```

### 框架层：改善执行组织

框架层关注一次请求中算子何时执行、怎样组成 batch、数据和 KV 如何流转，以及主机、设备和通信怎样协同。目标是减少重复工作、等待、同步和组织开销，并选择适合目标 workload 的执行配置。

| 优化方向 | 典型动作 | 需要验证的取舍 |
|---|---|---|
| 调度与批处理 | 调整批处理 token 预算、prefill 分块、并发准入和执行顺序 | 吞吐、TTFT、decode 延迟和 KV 抢占 |
| KV 与数据流 | 消除多余复制/分配，调整 cache 使用和数据复用 | 显存、重算、缓存语义及冷热请求表现 |
| 主机与 graph 执行 | 减少 Python/dispatch 开销、设备同步和 graph break | eager/graph 正确性、动态输入及启动开销 |
| 并行与通信组织 | 调整通信时序、rank 数据组织及计算通信重叠 | 通信等待、负载均衡和多卡稳定性 |

默认通过运行配置和 Plugin 已有的调度、Worker/ModelRunner、graph、dispatch 等扩展点实现。进入通用执行主链路前，需要证明更窄的配置或扩展点不足，并检查共享调用方。

### 算子层：改善具体运算

算子层以实际热点及其 shape、dtype、layout 为起点，比较完整调用成本，包括必要的数据转换、归约和接入开销。

- **接入更好的算子（`operator/replace`）**：已有 FlagGems、vendor/native 或其他兼容实现可选时，在相同条件下比较，再通过既有 backend/dispatch 接入。工作包括适配调用契约、支持条件、实现选择和 fallback。例如，为特定 MoE shape 接入更快的已有 backend。
- **优化当前算子（`operator/improve`）**：改进当前实现的 tile、warp、stage、访存、layout、并行划分或算法，也包括开发新的融合 kernel。例如，根据每 rank 的有效 head 数调整 MLA tile，或将相邻运算合并为一个新 kernel。

替换与实现优化都需要可信数值对照、实际命中证据、eager/graph 验证，以及同条件端到端复测。选择新 backend 或得到更快的 microbenchmark 后，仍需检查接入成本和非目标输入。

### 如何判断容易混淆的改动

代码所在仓库与优化分类分别判断：Plugin 可以承载框架逻辑，也可以承载算子接入；FlagGems 的 kernel 调整属于算子实现优化。模型 shim、dispatch 和 vendor backend 是代码职责边界，本身不决定收益分类。

| 改动示例 | 分类依据 |
|---|---|
| 为更快的已有算子增加 dispatch、shape 白名单和 fallback | `operator/replace`：收益来自替换实现，接入代码是必要组成部分 |
| 减少所有算子共同承担的 dispatch 查询或 Python 开销 | `framework`：收益来自通用调用组织 |
| 改变 kernel 的 tile、访存或归约方式 | `operator/improve`：收益来自具体实现效率 |
| 调整执行顺序，消除已有流程中的冗余中间步骤 | `framework`：收益来自流程组织 |
| 编写新的融合 kernel，减少中间张量和 kernel launch | `operator/improve`；若融合实现已经存在、只需接入，则为 `operator/replace` |
| 调整 collective 的发起时序与计算重叠 | `framework`；若替换 collective 实现，则为 `operator/replace` |

跨层方案拆为关联实验，分别验证贡献，再测组合收益。例如，框架调整产生更大的 batch，算子再针对新 shape 调优，需要记录两项变化各自的效果和依赖。

### 如何决定先优化什么

1. 先用端到端证据识别主指标上的瓶颈，检查框架中的明显浪费和低风险配置，建立合理的执行配置。
2. 热点已收敛到算子时，优先比较兼容的已有实现；没有合适实现、接入成本过高或当前实现的改进机制更明确时，投入实现优化。
3. 每次保留改动后重新测量、重新排序。算子变快可能改变最优 batch 和调度配置，框架调整也可能改变热点 shape。

这是默认排查顺序。实际优先级由预期端到端净收益、证据强度、验证成本和维护风险决定；已有充分证据时可以直接进入对应方向。候选同时满足正确性、稳定性和框架设计要求，收益不能豁免多模型/多平台兼容问题。

用户已授权在明确指定的模型、Host 和隔离源码副本内修改 Plugin 与 FlagGems。vLLM、权重、tokenizer、基础镜像及共享系统配置的修改仍受 [AGENTS.md](AGENTS.md) 中的授权边界约束。源适配容器用于读取事实，不承载本任务的源码修改、profiling 或性能实验。提交、推送和创建 PR 需有明确指示。

## 快速开始

### 1. 准备本地控制环境

在仓库根目录执行。控制环境使用 Bash、Python 3.12 或更新版本，以及 [requirements.txt](requirements.txt) 中的依赖；初始化需要能够获取 Python 包。

```bash
./scripts/bootstrap-control-node
./scripts/validate-local
```

初始化脚本创建本仓库的 `.venv/`；可通过 `PYTHON_BIN` 显式指定 Python 解释器。`validate-local` 检查 Python/Shell/Playbook 语法、工具单元测试、帮助入口、原始评测资产 SHA 和 Git diff，不连接目标机器，也不安装模型推理环境。

目标 Host 与平台组配置见 [inventory/hosts.yml](inventory/hosts.yml)。SSH 用户、端口、堡垒机和私钥路径由本机 `~/.ssh/config` 管理，不复制到项目或实验日志。

### 2. 解析目标，再做只读预检

仅在任务需要连接目标机器时执行下列远端检查。先将 `TARGET_HOST` 替换为本任务明确指定的 inventory Host 别名：

```bash
./scripts/inventory
TARGET_HOST='YOUR_HOST_ALIAS'

# 只解析目标，不连接远端
./scripts/connectivity-check --limit "$TARGET_HOST" --list-hosts

# 验证实际连接，然后按需检查环境和设备
./scripts/connectivity-check --limit "$TARGET_HOST"
./scripts/health-check --limit "$TARGET_HOST"
./scripts/accelerator-check --limit "$TARGET_HOST"
```

检查入口拒绝缺失 `--limit`、组名和通配符。明确指定多个 Host 时，使用逗号分隔的别名，工具会串行执行。加速卡查询由平台组选择原生命令；配置覆盖 NVIDIA、PPU、MetaX、Ascend、Moore Threads 和 Hygon，这不代表所有模型/平台组合均已完成运行验证。

### 3. 给 Agent 一个明确任务

可按下面的格式描述优化对象，未知项留空，由只读预检补充事实：

```text
模型及 served-model-name：
模型权重路径：
平台 / inventory Host：
源适配容器：
优化容器：尚未创建时留空
推理引擎及版本：
主指标：例如输出吞吐、P99 TTFT、TPOT、峰值显存
代表性 workload：输入/输出长度、并发、请求数、数据集或到达模式
守护指标及通过门槛：精度、错误率、尾延迟、显存等
资源与修改约束：
```

开始实际实验前，Agent 阅读 SOP、实验契约并检索相似案例，使用 [案例模板](docs/cases/TEMPLATE.md) 和 [验收模板](evaluation/ACCEPTANCE_TEMPLATE.md) 建立记录。模型身份、业务 workload 或验收门槛不能由 Agent 猜测；信息不足时先形成诊断和候选方案。

## 从基线到验收

| 阶段 | 主要工作与产物 |
|---|---|
| 目标与环境 | 核验当前容器、服务、代码导入路径、revision 和资源；记录未知项与已有改动 |
| 独立优化环境 | 从有效适配状态创建新容器；完成 `image_lineage=verified` 和 `mount_parity=passed`，隔离设备及源码影响 |
| 正确性护栏 | 固定单请求、小批量及 C8 sanity，检查实际输出；涉及算子等改动时增加数值/参考对照 |
| 无 profiler 基线 | 分离启动、预热和稳态，冻结 workload，多轮记录端到端指标、失败及资源情况 |
| 诊断与实验 | 从请求、阶段、框架、通信收敛到算子；按证据排序，单变量比较并保留失败/回退记录 |
| 候选回归 | 验证代表性 workload、eager/graph、边界与非目标路径；复核最终补丁设计和实际命中 |
| 正式验收 | 完整精度及输出健康门禁通过后测同一候选 graph 配置，完成可比的 baseline/candidate/revert 性能对比 |
| 复盘与交付 | 归档配置、逐轮结果、补丁、限制与回退入口，更新案例和有证据支持的知识差量 |

Profiler 用于归因，其性能数据与无 profiler 测量分开。随机 token 测试与代表性业务数据分开报告。吞吐改善同时披露尾延迟、显存、功耗和稳定性取舍；缺失指标保持 `null`，不用最好单轮或局部加速倍数代替端到端结论。

测量先区分有限批次、持续并发和业务到达率；容量结论需要负载曲线、排队及 SLO。预热完成、缓存历史、配置顺序与独立进程重复按实验契约冻结，固定“跑三轮”不能自动证明稳态。

## 评测工具如何选择

| 目录 / 工具 | 角色 |
|---|---|
| [`test/Accuracy_test/`](test/Accuracy_test/README.md) | 原始正式 GPQA Diamond 模型评测实现及阶段计分工具，保留导入字节基准 |
| [`test/perf_test/`](test/README.md) | 导入的原始性能 benchmark 与 profiling 资产 |
| [`evaluation/accuracy/`](evaluation/accuracy/README.md) | 正式评测包装入口、样本检查、分数检查、绑定验收与参数模板 |
| [`evaluation/performance/`](evaluation/performance/README.md) | 参数化性能计划、逐轮证据、baseline/candidate/revert 比较与 SLO 判定，以及 profiling/trace 工具 |
| [`unit_tests/`](unit_tests/README.md) | 本项目工具的本地测试；不执行模型级精度或加速卡性能验收 |

正式精度在目标机器上的 `harbor.baai.ac.cn/flageval/flageval-llmeval:v1` 评测容器内发起，模型服务继续运行在独立优化容器中。使用 `formal_accuracy.py` 包装调用原始 `test/Accuracy_test/llmrun.py`：显式提供案例配置、预冻结契约、当前服务身份和评测容器 inspect，先预检，再完成默认 **198 题 GPQA Diamond**。

样本与分数检查完成后，审查同一批输出的空回复、截断、重复、乱码和超时，由 `acceptance.py issue` 生成与服务、配置和结果 SHA 绑定的正式 gate。单独 `verify_accuracy.py` 的分数通过、进程退出 0 或阶段得分，都不能替代正式精度验收。完整命令及模板见 [评测入口](evaluation/README.md)。

正式性能启动前须重新核验当前服务身份和 gate；工具核对文件一致性，执行者仍需取得当前运行事实。原始示例配置不可直接当作新任务目标，维护版工具的 workload 变化也不能与历史默认结果直接混比。

新性能任务可通过 `vllm_perf.py --config … --dry-run` 审阅完整计划，再按冻结契约执行；`compare_performance.py` 重验各角色原始结果并输出 `passed/failed/incomplete`。目前支持有限批次和有限请求的到达率扫描，持续容量与长稳仍需相应观测，不能从工具通过状态自动推定。

验收范围使用 `formal`、`performance_only` 或 `diagnostic`，精度与性能状态分别记录。用户明确暂缓正式精度时，可以保留纯性能研究结果及轻量正确性证据，但不声明正式精度或全业务验收通过。

## Plugin 修改与后续 PR

优化代码需要与目标 revision 的框架职责、接口和贡献规范一致。每项 Plugin 修改先说明设计归属和支持范围，再按影响范围验证：

- 复用既有 registry、dispatch、backend 与配置入口；模型语义和平台实现分别留在对应边界。
- 性能特化使用真实能力、shape、dtype、layout 等条件，避免用模型路径、served name 或机器身份选择实现。
- 保持非目标模型/平台的默认选择、可选依赖、fallback、导入与缓存生命周期行为。
- 按共享调用方选择正例、反例和边界测试；未实测平台明确标注，mock 不代表设备性能或数值通过。
- 整理实验开关和诊断代码后，对最终补丁重新核验命中及受影响指标；Plugin/FlagGems 分别记录补丁、依赖与回退。

性能结论与 `pr_readiness`（`experimental`、`needs_revision`、`ready_for_review`）分别记录。当前 benchmark 更快不能豁免设计问题；具备评审条件也不代表上游接受。完整要求见 [Plugin 设计与 PR 准备](docs/plugin-change-review.md)。

## 项目结构与产物

```text
AGENTS.md                       # Agent 边界与执行导航
inventory/                      # Host 别名及平台变量
playbooks/                      # 只读连接、健康和设备检查
scripts/                        # 控制环境、目标限制、挂载比较、本地验证

evaluation/                     # 维护版评测工具、模板及验收门禁
test/                           # 原始目标环境评测资产
unit_tests/                     # 本地工具测试

docs/
  performance-optimization-sop.md
  experiment-contract.md
  container-isolation.md
  plugin-change-review.md
  vllm-plugin-FL-analysis.md
  flaggems-vllm-analysis.md
  flaggems-analysis.md
  optimization-patterns.md
  cases/                        # 少量可读案例摘要与证据链接

models/<model>/<platform>/
  README.md                     # 该模型/平台导航
  baseline/                     # 优化前环境、workload 和基线
  optimize/                     # 多轮实验、profiling 摘要、工具、补丁及回退
  acceptance/                   # 最终候选验收配置、结果/状态与总结

skills/key-operator-analysis/   # 按需使用的算子分析方法及知识库
```

每个实际模型/平台只使用 `baseline/`、`optimize/`、`acceptance/` 三个子目录；按需创建，不为未请求的目标批量生成空目录。中间和未达标实验数据留在 `optimize/`，案例摘要链接到对应记录。原始响应、日志、CSV/JSONL、trace、数据库和数据集放外部存储，项目记录绝对位置及必要校验值。

镜像谱系与挂载比较的工具说明见 [容器隔离流程](docs/container-isolation.md)。相同目录挂载可能共享源码和缓存；新建容器本身不证明修改已隔离。挂载比较通过也不能自动证明镜像继承了有效适配状态。

## 案例与知识积累

从 [案例索引](docs/cases/README.md) 检索同结构、阶段、平台和 workload 的证据，再核对当前运行条件。已有的 [XingChen4 / PPU](models/XingChen4-29B-A4B/ppu/README.md) 记录提供实际实验与产物导航；带 `imported` 标记的历史案例尚未在本项目复测，不与本项目实测结论混用。

当端到端测量已收敛到具体算子、dispatch、layout 或融合路径时，按需使用 [关键算子技能](skills/key-operator-analysis/SKILL.md)。知识按“案例证据 → 算子证据卡 → 优化地图 → 稳定理解”演进，当前包含 MLA Attention 与 mHC 资料。仅在证据改变下一次诊断或设计决策时更新相应层级。

经验等级采用 `observation`、`reproduced`、`transferred`、`invariant`。历史记录保留当时的 schema、已知条件和缺失证据，不追认为满足后来新增的规则；成功、失败和负优化均应可追溯。

## 维护与验证

修改公共工具或控制配置后，运行：

```bash
./scripts/validate-local
```

仅修改文档时，至少执行 `git diff --check` 并核验本地链接。原始评测资产 SHA 由 [test/IMPORT_MANIFEST.md](test/IMPORT_MANIFEST.md) 管理，维护版改动记录在 [evaluation/IMPORT_MANIFEST.md](evaluation/IMPORT_MANIFEST.md)。本地检查通过证明工具层验证完成，不替代目标环境的模型精度、性能或跨平台回归。

已确认的问题、官方参考资料如何进入流程，以及尚未自动化的环节见 [2026-09-06 项目复审](docs/project-review.md)。该报告用于维护导航，不替代执行规范。
