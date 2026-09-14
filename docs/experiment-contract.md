# 实验契约与记录格式

本文件维护 workload 可比性、指标决策、实验 schema 和报告字段，供 AGENTS 与 SOP 共同引用。未知指标保持 `null`；历史记录不自动升级为符合新规则。

新案例同时记录 `policy_version`、`policy_date`、`acceptance_scope`（`formal|performance_only|diagnostic`）、`accuracy_status` 和 `performance_status`。用户暂缓正式精度时使用 `performance_only` 并引用明确指示；不得因此填写正式门禁 passed。

历史记录保留原 schema 和测量结果。规则版本不明时写 `null`；缺少镜像谱系、挂载 diff、权重指纹等证据时列为缺口，不能通过改字段名补造已通过状态。当前状态与历史测量分开记录；任何环境变更后的测量另建记录。

## 1. Workload 和可比性

正式比较必须固定并记录：

- 输入、输出 token 长度及其分布
- 并发、请求数、到达模式和请求速率
- 数据集、随机种子、prompt 模板和 endpoint
- EOS 策略、采样参数和最大生成长度
- 模型、tokenizer、dtype、量化和权重 revision
- graph、TP/PP/EP/DP、KV cache 和 prefix cache 配置
- Host、设备数量与拓扑、容器镜像和软件 revision
- 预热轮数、正式轮数、失败和超时处理方式

默认 vLLM 性能比较的 baseline、candidate 和 revert 服务均在启动时显式追加 `--no-enable-prefix-caching`；不要求追加 `--no-enable-log-requests`。服务 manifest 的 `launch_config.enable_prefix_caching` 记录为 `false`，`performance_context.prefix_cache_state` 记录为 `disabled`，并保存进程/runtime 侧证据。只有 prefix cache 被用户明确声明为主要变量时才允许例外；此时必须建立独立基线并记录缓存准备、复用比例和命中证据。

以下维度存在未声明或未控制的差异时，不能归因为优化收益：

- 不同硬件或设备数量
- 不同长度、并发、请求数或到达模式
- `/v1/completions` 与 `/v1/chat/completions`
- `ignore_eos` 开启与关闭
- 随机 token workload 与真实对话 workload
- profiler 开启与关闭
- graph 请求模式、实际 capture/replay 与 backend
- 精度、量化、采样或 cache 配置不同
- 一方包含失败请求而另一方不包含

随机 workload 用于受控吞吐和延迟分析；真实或代表性数据用于业务结论。两类结果分开报告。

### 性能场景和执行层级

本项目的正式目标场景目录固定为 `p1024-d1024-c64-n128`、`p4096-d1024-c64-n128`、`p16384-d1024-c64-n128` 和 `p32768-d1024-c64-n128`。四项均为 finite batch，P/D/C/N 分别是输入 token、输出 token、并发上限和请求数。它们约束正式测试结果，不要求每轮原样执行；模型或平台不支持时保留该项并记录 `unsupported/incomplete`，不能静默省略。任务可增加额外业务场景，但不能覆盖或替换这组目录。

目标场景默认按 `p1024 → p4096 → p16384 → p32768` 顺序每次选取一个。每个目标场景独立经历入口 baseline、milestone、优化、当前场景 formal 和完成决策；达到预冻结的场景完成条件后才切换下一项。中间 formal 的 `scenario_ids` 只需包含当前目标场景，最终 formal 才必须包含全部 `required_acceptance_scenario_ids`。

大模型或单轮较慢时，不要求每个优化点重复完整矩阵，也不要求先跑完全部场景基线。可以按场景串行闭环：先冻结一个稳定 `scenario_id` 及其 workload，建立当前代码状态的入口基线，完成该场景的定位和优化，再进入下一场景。例如：`4k-1k baseline → 4k-1k optimize → 16k-1k baseline → 16k-1k optimize`。

场景入口基线（`scenario-entry`）反映进入该场景时已保留的优化组合，用于判定该场景闭环的增量收益。原始未优化状态的基线（`anchor`）用于判定最终累计收益。如果某场景进入时已包含前序优化，必须记录 `baseline_parent_candidate`，不能把该入口基线冒充原始 anchor。在声明相对原路径的整体收益前，需要在最终 full 场景集合上补齐可比的 anchor baseline 和最终 candidate。

场景目录可以在任务开始时一次冻结，也可以在每个新场景首次 baseline 之前逐步追加；修改时保留版本和理由。最终要声明的验收场景集合必须在最终 full 测量前冻结，不能根据已看到的候选结果删除负优化场景。单轮记录 `test_scope`：`targeted` 只支持目标场景结论，`checkpoint` 支持列出的受影响场景，`full` 才支持最终验收集合。

targeted 可以减少请求数、重复轮和场景数，但同一实验的 baseline/candidate/revert 必须使用相同缩减配置，并记录相对正式场景省略了什么。选择依据在测量前固定；不能根据结果挑选通过的场景。调度、KV、batch、graph、公共 dispatch 或通信改动按影响面升级到 checkpoint。最终 full 的范围是预冻结的代表性场景，不要求穷举所有 shape。

中间 `milestone` 可以改变输入长度、输出长度、并发、请求数或测试层次，也可以采用阶段专项和 microbenchmark。它必须通过 `parent_target_scenario_ids` 映射回最终目标，记录 `workload_delta`、成功/停止条件及 `promotion_validation`。milestone 内部的 A/B 必须可比，但其结果不能与不同 workload 的目标 baseline 直接计算加速比。

每次 baseline 尝试可以预先设置诊断时间预算。到达预算仍未完成时，保留部分证据并标记 `deferred-too-slow/incomplete`，随后选择 `reduced-measurement`、`static-first` 或 `hybrid`。缩减测量可减少输入/输出长度、请求数或并发，建立自身可比 baseline/candidate 并输出明确的 milestone 性能数据；该数据不能冒充原目标 baseline。候选达到预记录的晋级条件后，再补目标场景数据。原路径在相同契约下仍未完成时，只能记录带 workload、计时边界和预算的有界结论。

当 milestone 达到任务预冻结的显著提升阈值，或当前场景主要瓶颈发生迁移时，可以触发只覆盖当前目标场景的中间 `formal`。该场景达到完成条件后切换下一目标。最终 formal 才覆盖全部四场景。中间和最终 formal 使用相同的可比性与证据要求，但归档位置和结论生命周期不同：中间结果进入 `optimize/`，最终组合结果进入 `acceptance/`。

若以上维度本身就是预先声明的主要变量，例如 cache 开关、graph 模式或服务并行配置，可以进行受控 A/B；其余条件固定，明确新增资源、语义及 SLO 取舍。不同卡数/硬件的容量或成本研究单列，不称为同硬件的软件加速比。该规则不扩大权重、量化、共享环境等修改授权。

### 负载模式与结论范围

| `load_mode` | 生成方式 | 可支持的结论 |
|---|---|---|
| `finite_batch` | 有限请求集中提交，可加并发上限；计入填充和排空 | 该批次完成时间、吞吐和延迟；N 等于并发时通常只有一波请求 |
| `closed_loop` | 在约定持续窗口内，请求完成后补充以维持并发 | 对应并发下的持续表现；记录实际驻留和窗口，不能由短批次推定 |
| `open_loop` | 按独立到达时间表发出请求，可重放真实 trace | 对应到达率及 burst 下的 SLO/容量；记录客户端限流和未发出请求 |

请求数、持续时间、停止/排空条件与客户端队列计时方式必须同时清楚。需要容量结论时扫描代表性负载点，记录 offered/issued/completed rate、失败/超时、队列变化，以及同一请求同时满足全部 SLO 的成功请求数/测量秒数（goodput）。不能把分别满足 TTFT 和 TPOT 的请求数量相加。持续积压时不称为可持续容量；不为普通局部实验强制完整扫描。[vLLM 到达率/并发与 goodput 参数](https://docs.vllm.ai/en/v0.24.0/cli/bench/serve/)、[MLCommons 负载曲线方法](https://mlcommons.org/benchmarks/endpoints/)

`ignore_eos` 和固定长度适合受控计算量比较。业务测量另行保留自然 EOS、真实长度/前缀复用/采样及推理模式，不能把强制生成的 token 全部视为业务有效产出。

## 2. 指标和决策

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

### 计时和汇总口径

- 记录客户端版本、命令、原生结果 schema、计时起止、是否包含客户端排队/分词/网络；服务内部延迟与客户端端到端延迟分列。
- TTFT 明确首个有效内容还是首个流式事件；角色/空事件不能在未说明时当作首 token。TPOT 通常是每请求 `(总延迟 - TTFT)/(输出 token 数 - 1)`，单 token 请求不适用。
- ITL 说明统计对象是 token 还是响应 chunk，是否按 chunk token 数归一化；一个 chunk 可能包含多个 token，不能从其到达时间还原真实逐 token 时间。不同客户端的同名指标不能直接混用。[GenAI-Perf 指标定义](https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/perf_benchmark/genai-perf-README.html#metrics)
- 吞吐写清分子与完整测量窗口；跨轮聚合若采用总 token/总时长，与轮吞吐均值分别命名。百分位来自对应样本，不平均各轮 P99 后称为总体 P99；保留每轮、每进程结果和有效样本量。
- 失败、超时和未完成请求不能静默从 SLO 分母消失。失败轮可保留诊断证据，不能当作完整成功轮参与最终收益。
- 主指标与必要守护指标必须为可解释的有限数；缺失用 `null` 并保持验收未完成。资源采样注明范围、间隔与每设备口径；采样峰值不冒充绝对峰值，瞬时功率不推导能耗。

## 3. 实验记录最小字段

下面是记录格式，不是已实现的自动 schema 校验器；当前工具覆盖情况见[性能入口](../evaluation/performance/README.md)。具体 warmup/统计执行规则见 SOP B1/D5。不适用项说明原因，未知项保持空值，历史记录保留原版本。

工具配置与本节记录分别维护：`plan.example.json` 的 schema 1 用于实际 benchmark 计划，`comparison.example.json` 的 schema 1 用于预冻结比较阈值，精度 contract/gate 使用自己的 schema。性能执行器保存有效计划和 SHA；比较器只接受同一比较契约下的原始运行证据，不直接消费本节 YAML 或历史汇总。主指标、守护和可声明变量的实际支持范围以[工具文档](../evaluation/performance/README.md)为准。

```yaml
schema_version: 3
policy_version: "0.15"
policy_date: "2026-09-07"
acceptance_scope: diagnostic
accuracy_status: incomplete
performance_status: incomplete
experiment_id: YYYYMMDD-HHMM-short-name
objective: ""
status: planned
adaptation_handoff:
  source_project: null  # 用户指定时可为 /Users/baai/Documents/ChatGPT/新模型适配
  source_model_or_case: ""
  source_paths: []
  read_at: null
  source_revision_or_sha: ""
  imported_facts: ""  # 容器、模型路径、平台、启动参数、revision、挂载、评测状态、已知问题
  runtime_reverification: ""
accuracy_evaluation:
  skill: inference-accuracy-evaluation
  mode: minimal-regression  # baseline-sanity | minimal-regression | formal-gate | gate-check
  metric: ""
  score: null
  threshold: null
  criterion: score_greater_than_or_equal_to_threshold
  covered_experiment_ids: []
  result: incomplete  # passed | failed | incomplete
  evidence: ""
  next_trigger: ""
  progress_monitor:
    kind: heartbeat
    interval_minutes: 30
    automation_id: ""
    automation_name: ""
    status: not_created  # not_created | active | paused | deleted | unavailable | waived
    monitored_process_and_artifacts: ""
    last_notification_at: null
    cleanup_evidence: ""
accuracy_diagnosis:
  skill: inference-accuracy-diagnosis
  issue_id: ""
  trigger: ""
  status: not_triggered  # not_triggered | investigating | measurement-invalid | suspected | confirmed | resolved | not-reproduced
  last_known_good_identity: ""
  failing_candidate_identity: ""
  failing_evidence: ""
  minimal_reproducer: ""
  isolated_boundary_or_change: ""
  root_cause_confidence: ""
  fix_or_rollback: ""
  revalidation_evidence: ""
  performance_may_resume: false
performance_evaluation:
  skill: inference-performance-evaluation
  mode: targeted  # baseline | targeted | checkpoint | formal
  target_catalog_version: e2e-four-scenarios-v1
  required_acceptance_scenario_ids:
    - p1024-d1024-c64-n128
    - p4096-d1024-c64-n128
    - p16384-d1024-c64-n128
    - p32768-d1024-c64-n128
  scenario_ids: []
  target_scenario_order:  # 每次从中顺序选取一个
    - p1024-d1024-c64-n128
    - p4096-d1024-c64-n128
    - p16384-d1024-c64-n128
    - p32768-d1024-c64-n128
  current_target_scenario_id: null
  target_scenario_completion_criteria: ""
  target_scenario_status: null  # pending | optimizing | formally-checked | complete | incomplete
  milestone_id: null
  parent_target_scenario_ids: []
  milestone_workload_delta: ""
  milestone_success_criteria: ""
  milestone_stop_condition: ""
  promotion_validation: ""
  formal_trigger: null  # major-milestone | hotspot-migration | final-acceptance
  major_improvement_threshold: ""  # 结果出现前冻结；指标和幅度由任务定义
  formal_run_lifecycle: null  # intermediate-single-target | final-all-targets
  scenario_sequence_index: null
  baseline_kind: null  # anchor | scenario-entry
  baseline_parent_candidate: ""  # scenario-entry 时填写已保留组合身份
  baseline_status: null  # planned | running | complete | deferred-too-slow | failed | incomplete
  diagnostic_time_budget_seconds: null  # baseline 启动前冻结
  baseline_attempt_elapsed_seconds: null
  baseline_partial_evidence: ""  # 完成/失败请求数、最后进度、日志和服务状态
  baseline_recovery_strategy: null  # reduced-measurement | static-first | hybrid
  reduced_measurement_plan: ""
  static_analysis_evidence: ""
  measurement_resume_condition: ""  # 如：代表性探针在记录预算内完成
  incremental_comparison: ""  # scenario-entry baseline -> scenario candidate
  anchor_comparison: ""  # anchor baseline -> final candidate，通常在 full 阶段填写
  numeric_speedup_claim_allowed: false
  result: incomplete  # passed | failed | incomplete
  evidence: ""
  conclusion_boundary: ""
  next_trigger: ""
profiling:
  skill: inference-profiling
  mode: null  # capture | analyze | reprofile
  scenario_ids: []
  result: not_run  # not_run | passed | failed | incomplete
  trace_evidence: ""
  worker_rank_coverage: ""
  hotspot_summary: ""
  next_action: ""
planning_review:
  skill: inference-optimization-planning
  review_id: ""
  covered_experiment_ids: []
  evidence_cutoff: ""
  result: not_run  # not_run | complete | incomplete
  current_combined_candidate: ""
  cumulative_evidence: ""
  ranked_next_directions: []
  immediate_next_experiment: ""
  next_trigger: ""
target:
  model: ""
  model_path: ""
  weight_revision: ""
  platform: ""
  host: ""
  remote_work_root: ""  # 用户提供的目标 Host 绝对路径；未提供则为空
  remote_case_dir: ""  # remote_work_root 下唯一的 case-id 子目录
  remote_workspace_evidence: ""  # 规范路径、owner/权限、空间及符号链接检查
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
  data_parallel: null
  total_devices: null
  serving_replicas: null
  rank_topology_evidence: ""
  graph:
    requested_mode: null
    effective_mode: null
    capture_sizes: []
    attention_backend: null
    hit_evidence: ""
  kv:
    capacity: null  # 注明单位
    preemption_recompute_evidence: ""
  launch_args:
    - --no-enable-prefix-caching
workload:
  scenario_id: ""
  scenario_sequence_index: null
  stage: null  # prefill | decode | mixed
  test_scope: targeted  # targeted | checkpoint | full
  scenario_purpose: ""  # 目标瓶颈、哨兵或最终验收
  acceptance_scenario: false
  omitted_acceptance_scenarios: []
  selection_reason: ""
  dataset: ""
  dataset_sha256: null
  endpoint: ""
  load_mode: null  # finite_batch | closed_loop | open_loop
  requests: null
  concurrency: null
  request_rate_rps: null
  arrival_distribution: null
  duration_s: null
  drain_policy: ""
  client_queue_timing: ""
  input_tokens: ""
  output_tokens: ""
  generation_config: {}  # EOS、采样、模板及推理模式
  seed: null
  prefix_cache_state: null  # cold | warm | mixed | disabled | not_observed
  prefix_reuse_fraction: null
  cache_hit_evidence: ""
measurement:
  client_revision: ""
  result_schema: ""
  required_metrics: []
  slo: {}  # 指标、阈值、单位和分母定义；未定义不得声称达标
  warmup:
    shapes: []
    completion_rule: ""
    max_budget_s: null
    state_restore_and_queue_drain: ""
  repeats:
    rounds_per_process: null
    independent_processes: null
    configuration_order: []
    aggregation_and_uncertainty: ""
  search_budget: ""
  confirmation_workload: ""
  next_checkpoint_trigger: ""
stability:
  status: not_run  # not_run | passed | failed | incomplete | not_applicable
  duration_s: null
  load_cycle: ""
  idle_resume: ""
  sanity_and_resource_checks: ""
  failure_and_stop_rules: ""
  evidence: ""
change:
  optimization_layer: null  # framework | operator
  operator_strategy: null  # replace | improve；framework 时为 null
  hypothesis: ""
  primary_variable: ""
  files: []
engineering_review:  # 涉及 Plugin 时填写；不涉及则 status=not_applicable
  status: pending  # pending | passed | needs_revision | not_applicable
  design_record: ""  # optimize 中的设计归属、支持范围和非目标影响
  pr_readiness: experimental  # experimental | needs_revision | ready_for_review
  compatibility_evidence: []
  untested_scope: []
  cross_repo_dependencies: []
results:
  correctness: ""
  successful_requests: null
  failed_requests: null
  request_throughput_rps: null
  offered_rate_rps: null
  issued_rate_rps: null
  goodput_rps: null
  slo_attainment_fraction: null
  queue_trend: null
  output_throughput_tps: null
  total_throughput_tps: null
  ttft_p50_ms: null
  ttft_p95_ms: null
  ttft_p99_ms: null
  tpot_p50_ms: null
  tpot_p95_ms: null
  tpot_p99_ms: null
  itl_p99_ms: null
  e2e_p99_ms: null
  peak_memory_gb: null
decision: pending
artifacts:
  raw_results: ""  # 可记录 remote_case_dir 下的绝对路径与 SHA
  logs: ""
  traces: ""
  remote_manifest: ""  # 远程文件清单、大小、校验和与留存状态
notes: ""
```

不可用指标保持 `null`，不得用 `0` 伪装已测量。

## 4. 最终报告

每次优化任务至少汇报：

```text
优化对象：模型 / 平台 / Host / revision
容器谱系：源适配容器 / 新优化容器 / 镜像身份 / 挂载一致性证据
优化目标：主指标、守护指标、通过门槛
当前环境：容器、引擎、Plugin、FlagGems、硬件与启动配置
瓶颈证据：请求、阶段、框架、通信或算子证据
基线：负载模式、缓存历史、预热完成证据、轮次/进程重复、性能与资源结果
改动：文件、参数、补丁与服务操作
优化分类：框架层 / 算子接入 / 当前算子优化；排序依据与跨层依赖
工程复核：Plugin 设计归属、多模型/多平台影响、最终补丁验证、pr_readiness、跨仓库依赖与未测项
候选结果：同条件多轮对比、统计口径和不确定性；容量结论附负载曲线与 SLO
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
