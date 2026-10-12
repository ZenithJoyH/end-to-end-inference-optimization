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
- 关键算子实现、测试和知识沉淀遵守 Plugin/FlagGems 源码边界及当前案例记录规则。

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
