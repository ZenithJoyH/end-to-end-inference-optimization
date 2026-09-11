# 端到端推理优化项目：公共 Skills 项目契约

本文件把 `skills-hub` 的公共方法映射到本项目现有工具。测试步骤、并发、预热、指标、比较、
进度监控、证据校验和三态判定属于对应 Skill 包；本契约不复制这些方法。

## 项目标识与规则

- 项目：端到端推理优化。
- 根目录标记：`AGENTS.md`、`evaluation/`、`models/`、`test/`。
- 解析顺序：用户当前指令 → 本仓库 `AGENTS.md` → 本契约 → 公共 Skill 方法。
- 项目执行顺序和授权边界由 `AGENTS.md`、`docs/performance-optimization-sop.md` 和
  `docs/experiment-contract.md` 维护。

## 运行身份与产物

Host、源适配容器、独立优化容器、模型/权重、tokenizer、engine、Plugin、FlagGems、设备拓扑、
graph 模式、启动参数、endpoint、服务实例、客户端和 workload 必须来自当前运行取证。完整
JSON、日志、响应、样本和 Trace 保存在用户批准的远端 case 目录；本地案例记录只保存摘要、
准确路径和必要 SHA。

## 精度评测映射

- 公共方法：`inference-accuracy-evaluation/references/accuracy-method.md`。
- `service-sanity`：在当前 graph 优化服务上使用项目冻结的 10 个 GPQA 类问题、并发 8；按
  公共方法逐题核对正确性、输出健康和明显性能异常。未提供版本化 manifest 和入口时返回
  `incomplete`。
- `formal-full` evaluator：目标机器上基于
  `harbor.baai.ac.cn/flageval/flageval-llmeval:v1` 的评测容器。
- provenance/preflight/full-run 入口：`evaluation/accuracy/formal_accuracy.py`，包装调用原始
  `test/Accuracy_test/llmrun.py`；配置、契约、服务 manifest 和 evaluator inspect 使用案例
  目录中冻结的实际文件。
- 当前正式 task 是镜像中已核实注册的 `gpqa_diamond_generative_cot`，完整集合 198 个唯一
  问题；graph、正式并发至少 32、无允许超时等执行规则来自公共精度方法。
- 输出健康审查和 receipt：填写与 run-record 同一 samples SHA 的 health review，使用
  `python3 evaluation/accuracy/acceptance.py issue --run-record <run-record.json> --health-review <health-review.json> --output <accuracy-gate.json>`。
- `gate-check`：使用
  `python3 evaluation/accuracy/acceptance.py check --gate <accuracy-gate.json> --service-manifest <current-service.json>`，只读执行，不发送精度流量。
- `hard-case`：当前没有统一正式清单；未冻结版本化 case 列表和项目入口时返回
  `incomplete`。
- 交通型精度任务需要进度监控时，按公共 Skill 的监控方法创建当前任务 heartbeat；本项目
  默认 30 分钟，用户指定频率优先，终态必须停用并记录。

## 性能评测映射

- 公共方法：`inference-performance-evaluation/references/performance-method.md`。
- runner：`evaluation/performance/vllm_perf.py`；计划：
  `evaluation/performance/performance_plan.py`；比较：
  `evaluation/performance/compare_performance.py`。
- `single-scenario`：从当前案例的版本化 plan 解析一个稳定 `scenario_id`，为同一缩减范围
  运行匹配 baseline/candidate，使用唯一 run ID；不得用完整历史汇总代替。
- `full-suite`：使用预冻结 plan 的全部验收场景，不得静默遗漏。正式 purpose 还必须使用
  当前 `accuracy-gate.json` 与候选 service manifest。
- 每个角色先以 `evaluation/performance/vllm_perf.py --config <plan.json> --comparison-contract <comparison.json> --service-manifest <service.json> --role <baseline|candidate|revert> --run-id <id> --output-dir <dir> --dry-run`
  预览；核对后只移除 `--dry-run`。独立运行次数、预热、测量轮和阈值从冻结 plan/comparison
  读取，不在本契约另设默认值。
- 收齐 run-record 后使用
  `python3 evaluation/performance/compare_performance.py --contract <comparison.json> --run-record <...> --output <comparison-result.json>`。
- 本项目默认性能服务的 prefix cache 关闭：启动前核对目标 CLI 支持
  `--no-enable-prefix-caching`，在 baseline/candidate/revert 启动命令中显式设置，并保存运行
  证据；仅用户明确将其作为实验变量时才能在独立契约和新基线中改变。
- profiler-on 结果不进入无 profiler 性能结论；Trace 由 `$inference-profiling` 单独管理。

## 其他公共 Skill 映射

- 精度问题记录与复现：当前案例的 `optimize/` 及批准的远端 case 目录。
- Profiling：`evaluation/performance/vllm_profile.py`、`sglang_profile.py` 和
  `trace_to_summary.py`；实际 Trace 目录和 rank/worker 覆盖必须现场核实。
- 关键算子实现、测试和知识沉淀遵守 Plugin/FlagGems 源码边界及当前案例记录规则。

## 生命周期和结论

优化容器、共享服务、源码修改和破坏性操作的授权仍由 `AGENTS.md` 管理。公共 Skill 不扩大
授权。所有正式结论必须消费本项目原生 gate、run-record 或 comparison result；口头结论、
Markdown 标签、单一分数或原始 CSV 不能替代。
