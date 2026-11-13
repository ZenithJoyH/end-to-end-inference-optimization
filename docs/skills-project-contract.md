# 端到端推理优化项目：Skills 项目契约

本项目以仓库内 `skills/` 的维护版为唯一方法入口，不依赖尚未安装或未冻结版本的 `skills-hub`。
测试步骤、并发、预热、指标、比较、进度监控、证据校验和三态判定属于对应 Skill；本契约负责项目映射。

## 发现、版本与缺失处理

- 精度入口：[inference-accuracy-evaluation](../skills/inference-accuracy-evaluation/SKILL.md)。
- 性能入口：[inference-performance-evaluation](../skills/inference-performance-evaluation/SKILL.md)。
- 其他技能按 AGENTS 中的相对路径加载；自动发现不可用时，直接完整读取对应 `SKILL.md` 及其本次必读引用，
  不假装调用了已安装公共插件，也不安装到用户全局目录。
- 版本由仓库 revision 与完整 Skill bundle 的文件 SHA 集合共同标识；使用 `scripts/skill_bundle.py`，包括未提交资源变更。
- 本地能力 ID 为 `e2e/accuracy`、`e2e/performance`，模式由调用方显式传入；不能从目录同名推断 Hub 兼容性。
- 长任务的执行前后检查、进度和恢复记录见 [执行记录](agent-execution.md)，不替代 `state.yml` 和原生 gate。
- 同名全局 Skill 不静默覆盖本地方法。若用户要求切换公共版本，先核对方法、模式与项目映射，再显式迁移。
- 入口或必读引用缺失时，报告 `incomplete` 并停止该项评测；不得自行编造替代方法。

## 项目标识与规则

- 项目：端到端推理优化。
- 根目录标记：`AGENTS.md`、`evaluation/`、`test/`；`models/` 是可选的本地案例记录。
- 项目内解析顺序：用户当前指令 → 本仓库 `AGENTS.md` → 本契约 → 本地 Skill 方法；上层工具与安全约束仍适用。
- 项目执行顺序和授权边界由 `AGENTS.md`、`docs/performance-optimization-sop.md` 和
  `docs/experiment-contract.md` 维护。

## Skill 方法与执行归属

- Skill 中的“调用”“执行”“分析”和 `run/execute/invoke` 描述方法步骤，不指定由主 Agent 亲自执行。
  本项目具体执行遵循 [AGENTS.md 第 5.5 节](../AGENTS.md#55-主-agent-协调与-dsh-headless-执行)和
  [执行说明](agent-execution.md#具体执行必须委派)：除明确例外外，分析、实现和测试必须委派。
- 主 Agent 选择模式、冻结目标与契约、分配任务并复核原始证据和原生回执。执行子 Agent 必须读取
  所派任务的本地 Skill 入口及必读引用，按其完整方法执行并交付产物；委派不降低测试或证据要求。
- 远端默认使用对应目标机器上的 `dsh headless`，按恢复规则回退到内置子 Agent；纯本地任务在本地
  委派。入口缺失、权限不足或执行器故障不自动允许主 Agent 接管，也不授权安装工具或扩大范围。
- 规划复盘与最终决策由主 Agent 负责，需要新增源码/trace 分析、统计、代码或实验时另行委派。
  主 Agent 可按明确例外调用不启动新 workload 的现成校验器；需重跑评测时仍须委派，不改 Skill
  方法、runner、接口或原生 gate 来适应执行者差异。

## 运行身份与产物

Host、源适配容器、独立优化容器、模型/权重、tokenizer、engine、Plugin、FlagGems-vllm、FlagGems、设备拓扑、
graph 模式、启动参数、endpoint、服务实例、客户端和 workload 必须来自当前运行取证。完整
JSON、日志、响应、样本和 Trace 保存在用户批准的远端 case 目录；本地案例记录只保存摘要、
准确路径和必要 SHA。

## 精度评测映射

- 方法入口：`skills/inference-accuracy-evaluation/SKILL.md`；模式为 `baseline-sanity`、`minimal-regression`、`formal-gate`、`gate-check`。
- 本项目的精度通过条件只有一个：预冻结的正式指标值 `score >= threshold`，等于阈值视为通过。
  不再使用相对 baseline、最大允许回退或输出健康审查作为附加精度门槛。
- 每个优化点执行最小回归；低风险改动默认累计 4–5 个后触发 `formal-gate`，高风险改动和缺少
  当前正式性能所需有效 gate 时提前触发。正式分数低于阈值后必须调用精度定位 Skill，修复或回退并
  重跑相同正式契约，新的 `score >= threshold` gate 生成前不恢复性能优化。
- `baseline-sanity`：在当前 graph 优化服务上使用项目冻结的 10 个 GPQA 类问题、并发 8；按
  本地方法生成早期观察，不代替正式阈值判定，也不增加独立精度通过条件。
- `formal-gate` evaluator：目标机器上基于
  `harbor.baai.ac.cn/flageval/flageval-llmeval:v1` 的评测容器。
- provenance/preflight/full-run 入口：`evaluation/accuracy/formal_accuracy.py`，包装调用原始
  `test/Accuracy_test/llmrun.py`；配置、契约、服务 manifest 和 evaluator inspect 使用案例
  目录中冻结的实际文件。
- 当前正式 task 是镜像中已核实注册的 `gpqa_diamond_generative_cot`，完整集合 198 个唯一
  问题；graph 和正式并发等执行方法来自本地精度方法。超时、空输出、截断、重复或格式异常
  只记录为诊断观察，不阻止得分与 gate 的生成。
- 精度服务必须显式使用 `--enable-prefix-caching`，删除相反开关，并以当前进程/runtime 取证；
  manifest 记录 `enable_prefix_caching=true`、完整启动参数、实际 `cold/warm/mixed` 状态及缓存准备。
  正式预检、执行及 gate 签发会拒绝缺失、关闭或矛盾状态；不能用性能服务的关闭配置执行精度评测。
- 精度开启→性能关闭时，通过 [performance-bind](../evaluation/accuracy/README.md#精度开启缓存与性能关闭缓存)
  核验两份真实配置、同候选身份和切换回归，签发绑定当前性能实例的 schema7 回执；不修改原分数或旧 manifest。
- gate 签发：使用
  `python3 evaluation/accuracy/acceptance.py issue --run-record <run-record.json> --output <accuracy-gate.json>`。
  输出健康信息可用 `--health-observation` 附加为诊断证据，但不改变阈值结论。
- `gate-check`：使用
  `python3 evaluation/accuracy/acceptance.py check --gate <accuracy-gate.json> --service-manifest <current-service.json>`，只读执行，不发送精度流量。
- 困难样本作为 `minimal-regression` 的显式范围，不是额外模式；未冻结版本化列表时返回 `incomplete`。
- 短精度任务使用前台进度；长任务需后台跟进或用户已要求定时通知时，按本地 Skill 使用 heartbeat。
  保留用户已指定的频率和通知偏好，终态停用并记录；调度工具不可用不阻断评测。

## 性能评测映射

- 方法入口：`skills/inference-performance-evaluation/SKILL.md`；模式为 `baseline`、`targeted`、`checkpoint`、`formal`。
- runner：`evaluation/performance/vllm_perf.py`；计划：
  `evaluation/performance/performance_plan.py`；比较：
  `evaluation/performance/compare_performance.py`。
- `single-scenario`：从当前案例的版本化 plan 解析一个稳定 `scenario_id`。可以先对该场景运行
  `scenario-entry baseline`，随即完成定位、多轮优化和 candidate/revert，然后才为下一场景建立基线；
  默认按 P1K→P4K→P16K→P32K 顺序从正式目录中每次选择一个，不要求先跑完其他场景的 baseline。
  场景入口基线必须记录它包含的已保留候选作为
  `baseline_parent_candidate`，同一轮的 baseline/candidate/revert 使用相同缩减范围和唯一 run ID。
- `phase-decomposition`：为当前目标场景分别维护 `prefill`、`decode`、`mixed` 证据。可用客户端
  TTFT/TPOT/ITL 与 token 吞吐建立低开销代理，也可在归因不足时调用 Profiling Skill；不得把代理指标
  当作纯设备阶段时间。阶段专项以 `stage` 标识并建立自身同配置 baseline，单阶段候选必须回到父目标
  场景的 `mixed` 测量，并把另一阶段指标作为守护项。
- `milestone`：这是项目规划概念，不是本地 Skill 的新模式。可使用目标场景子集、缩短输出、减少
  请求/并发、阶段专项或其他低成本 workload；记录 `milestone_id`、`parent_target_scenario_ids`、
  与最终场景的差异、成功/停止条件和晋级验证。实际端到端测量根据范围调用本地 `targeted` 或
  `checkpoint`，达标结果不能替代固定四场景的 `full-suite`。
- `anchor-baseline`：未优化原路径在场景上的基线。它可以按场景延后采集，但在声明相对原路径的累计收益前，
  必须与最终候选在同一 full 场景集合和契约下补齐，不能用中途的场景入口基线代替。
- `deferred-baseline/recovery`：这是项目控制分支，不是本地性能 Skill 的新增通过模式。baseline 运行前
  冻结诊断时间预算；超预算仍未完成时，安全停止 benchmark 客户端并把本地 Skill 回执记录为
  `incomplete`，同时保存部分进度和服务证据。之后可以通过 `reduced-measurement` 减少输入/输出、请求或
  并发并调用 targeted 获取该 milestone 的可比数字，也可以选择 `static-first` 或 `hybrid`。当前恢复状态、
  结论、旧决策摘要和外部证据索引写入 `optimize/state.yml`，本优化点的方向、内容和效果写入
  `optimize/<experiment-id>.md`，多轮总览写入 `optimize/README.md`，不得创建逐轮或历史子目录。
  缩减 workload 的数据不构成原目标 baseline。候选满足晋级条件后，
  重新调用本地 Skill 执行目标场景或 formal；没有完成的可比 anchor 时不得计算精确加速比。
- `formal-after-major-milestone`：当前目标场景的 milestone 达到预冻结的显著提升阈值或热点发生迁移时，
  可调用本地 `formal`，只测当前一个目标场景。达到场景完成条件后切换顺序中的下一项。中间 formal 结果
  保存到 `optimize/`；全部目标完成后的最终 formal 才测固定四场景并保存到 `acceptance/`。两种生命周期
  都必须满足各自范围内相同的精度 gate、身份、重复和 baseline/candidate/revert 要求。
- `full-suite`：仅用于最终组合验收，使用预冻结 plan 的全部验收场景，不得静默遗漏。正式 purpose 还必须使用
  当前 `accuracy-gate.json` 与候选 service manifest。本项目的最小 full 集合固定为
  `p1024-d1024-c64-n128`、`p4096-d1024-c64-n128`、`p16384-d1024-c64-n128`、
  `p32768-d1024-c64-n128`；任务可增加场景但不能删除这四项。
  不支持的场景必须以 `unsupported/incomplete` 留在回执中，不能用 targeted 探针冒充完成。
- 每个角色先以 `evaluation/performance/vllm_perf.py --config <plan.json> --comparison-contract <comparison.json> --service-manifest <service.json> --role <baseline|candidate|revert> --run-id <id> --output-dir <dir> --dry-run`
  预览；核对后只移除 `--dry-run`。独立运行次数、预热、测量轮和阈值从冻结 plan/comparison
  读取，不在本契约另设默认值。
- 收齐 run-record 后使用
  `python3 evaluation/performance/compare_performance.py --contract <comparison.json> --run-record <...> --output <comparison-result.json>`。
- 本项目默认性能服务的 prefix cache 关闭：启动前核对目标 CLI 支持
  `--no-enable-prefix-caching`，在 baseline/candidate/revert 启动命令中显式设置，并保存运行
  证据；仅用户明确将其作为实验变量时才能在独立契约和新基线中改变。
- profiler-on 结果不进入无 profiler 性能结论；Trace 由 `$inference-profiling` 单独管理。

## 其他本地 Skill 映射

- 精度问题记录与复现：当前案例的 `optimize/` 及批准的远端 case 目录。
- Profiling：`evaluation/performance/vllm_profile.py`、`sglang_profile.py` 和
  `trace_to_summary.py`；实际 Trace 目录和 rank/worker 覆盖必须现场核实。
  仅缺 FLOPs/HBM 计数器时复用有效时间线，在现有 Profiling 模式下按实际厂商工具补采原生报告，
  单独校验指标、范围及绑定；这些 trace runner 不提供通用 native-counter 包装器，也不要求为补采再生成 trace。
- Roofline 定位：[inference-roofline-analysis](../skills/inference-roofline-analysis/SKILL.md) 消费当前案例已有的
  阶段/shape、FLOPs、HBM 流量、计时和上限证据，输出瓶颈、上限距离及下一项可证伪实验。
  它不自行启动采集或 workload；缺口路由 Profiling，算子实验路由关键算子 Skill，排名路由规划复盘，
  收益回到无 profiler 性能 Skill。现有 runner 不自动产出全链 FLOPs/HBM 计数器，也不新增能力 ID、
  执行模式、强制记录 schema 或 native gate。计数器不可用时保留估算与缺口，不伪造实测。
  四个 Skill 的交接、有效/在途/不可用证据复用及补证停止规则统一见 [SOP C5](performance-optimization-sop.md#c5-用-roofline-连接瓶颈证据与下一步实验)；
  主 Agent 合并并派发任务，子任务返回原决策点，不通过互相调用展开第二套优化循环。
- 关键算子实现、测试和知识沉淀遵守 Plugin/FlagGems 源码边界及当前案例记录规则。

### 离线分析辅助工具

[集成说明](analysis-tooling-integration.md)维护 trace 分层与 overlap/fusion、上游 PR 检索、显存/KV 分账、shape/FLOPs 估算和离线 CLI 参数检查的路由。具体输入和命令分别位于现有 Profiling、关键算子、Roofline 引用与性能工具说明中，按当前问题加载。

这些工具只读取明确提供的文件，不连接目标服务、不执行输入命令，不新增 Skill 能力 ID、评测模式或原生 gate。报告是外部诊断 sidecar；在当前优化点已有的 evidence/hypothesis/next-action 记录其路径、SHA、适用范围及决策影响，不新增模型历史目录或必填 schema。离线文件哈希只绑定所读文件，现场服务、rank、graph 和实现命中仍由原流程核实。

## 生命周期和结论

优化容器、共享服务、源码修改和破坏性操作的授权仍由 `AGENTS.md` 管理。本地 Skill 不扩大
授权。正式精度的业务通过条件只是 `score >= threshold`；原生 gate 和 run-record 用于证明
指标、阈值和服务身份未被替换，它们的证据有效性检查不是第二个精度门槛。

## 人工交接与项目验收映射

人工暂停、接管、补交原生回执和恢复统一使用 [执行记录协议](agent-execution.md#人工暂停接管和恢复)。
Skill 仍决定测量方法，操作者可以是人；原生 runner、身份绑定及验收器保持一致。
新案例采用 `case_records.py` 的 case 级身份和紧凑视图，旧案例不自动迁移。

项目最终验收由 `evaluation/performance/final_acceptance.py` 包装原生比较器：测量前
`prepare` 冻结 `project_scope`，测量后 `check` 核验生命周期、基线身份、四场景和阶段证据。
`compare_performance.py` 的 passed 仍只表示对应比较契约通过，不自行代表全项目完成。
规划字段留在案例文档，runner 仅接收其支持的原生字段。
