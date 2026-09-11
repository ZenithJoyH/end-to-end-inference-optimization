# 评测入口与验收证据

正式流程和例外边界由 [SOP](../docs/performance-optimization-sop.md) 管理。配置字段、可比性和记录格式见 [实验契约](../docs/experiment-contract.md)。本页维护实际命令，不重复定义验收政策。

端到端优化任务通过 [推理精度评测技能](../skills/inference-accuracy-evaluation/SKILL.md) 选择 baseline sanity、最小回归、正式 gate 或 gate check 模式；该 Skill 调用本页工具和命令，本页仍是实际执行接口的唯一维护位置。

当 Skill 实际启动 baseline sanity、最小回归或正式精度进程时，它会先创建绑定当前 Codex 任务的 heartbeat，默认每 30 分钟通知一次可验证进展，并在完成、失败、取消或提前停止后停用。`gate-check` 只核验证据，不创建监控；automation ID、实际频率和清理证据写入实验记录。

精度评测出现失败、回退或输出异常时，使用 [推理精度问题定位技能](../skills/inference-accuracy-diagnosis/SKILL.md) 冻结失败证据、区分测量/身份问题与真实模型回退，并组织最小复现、改动二分和原范围复测。本页工具提供评测证据，不自动给出代码根因。

无 profiler 性能测量通过 [推理性能评测技能](../skills/inference-performance-evaluation/SKILL.md) 选择 baseline、targeted、checkpoint 或 formal 模式；trace 采集与热点归因通过 [推理 Profiling 技能](../skills/inference-profiling/SKILL.md) 选择 capture、analyze 或 reprofile 模式。二者复用 `evaluation/performance/` 的维护版工具，不复制实现，也不把 profile 数据当作正式性能结果。

## 正式精度

在目标机器上的 `harbor.baai.ac.cn/flageval/flageval-llmeval:v1` 评测容器内，部署本项目 `test/Accuracy_test/` 与 `evaluation/accuracy/`，保留相对目录。模型仍运行在独立优化容器中。准备以下外部文件：

- 案例配置：从 [llm_config.example.json](accuracy/llm_config.example.json) 复制，填写目标、输出/数据集路径、生成参数及 `seed`。正式流程不读取原始示例默认目标。
- 契约：从 [contract.example.json](accuracy/contract.example.json) 复制，在评测前冻结正式 metric、最低分或可信 baseline、完整样本 ID，以及下面采集的任务/数据证据。
- 服务身份：从 [service-manifest.example.json](accuracy/service-manifest.example.json) 复制，依据当前进程/容器只读检查填写。SHA 必须来自实际权重/文件清单、tokenizer、实际引擎/源码副本和运行证据；revision 字符串不能代替未提交代码的内容指纹。
- 评测容器 inspect：目标机器上对精确评测容器执行 `docker inspect` 的结果，保存在外部产物目录。工具检查规定镜像引用和 image ID；执行者仍需确认命令确实运行在该容器中。

先在规定评测容器中采集实际解析的任务和数据，尚不调用模型服务：

```bash
python3 evaluation/accuracy/formal_accuracy.py \
  --config /external/case-config.json \
  --evaluation-inspect /external/evaluator.inspect.json \
  --capture-provenance /external/task-provenance.json
```

将命令输出的 `dataset_revision` 和 `task_provenance` 原样写入案例契约，再冻结契约。revision 使用实际原始 split 内容指纹；provenance 同时包含处理后题目、有效 task 配置、评测器/辅助源码与版本。配置中的 dataset path/name/split 必须与真实 task 一致；不会自动重写镜像中的任务或把预检路径当作实际评测数据。

然后进行服务预检：

```bash
python3 evaluation/accuracy/formal_accuracy.py \
  --config /external/case-config.json \
  --contract /external/contract.json \
  --service-manifest /external/service.json \
  --evaluation-inspect /external/evaluator.inspect.json \
  --preflight-only
```

预检通过后以同一参数去掉 `--preflight-only` 执行。包装器调用 SHA 校验后的原始 `test/Accuracy_test/llmrun.py` 模块，保持模型 API、任务与生成实现；额外设置显式 seed、每次运行独立缓存命名空间及更严格检查，以采集任务的同一 Python 解释器运行 lm-eval。它不是另一个模型评测实现。直接运行原件不会获得这些外层检查，不能单独产生正式验收记录。

正式执行前写出 `effective_config.json` 和 `frozen-inputs.json`；运行前后重验实际任务/数据证据。结束后核对 198 个唯一题目的有效响应与全部冻结 filter、实际题目指纹、重复/缺失项、超时、显式截断、结果文件唯一性和冻结分数阈值，同时检查原生 results 中的模型/endpoint、任务配置、生成参数、seed、缓存运行标识与有效样本数。同题多 filter 可以产生多行，要求原始题目与模型响应一致；不能用行数代替题数。失败保持非零退出，保留外部产物。通过后写出 `run-record.json` 和待填写的 `health-review.template.json`。

正式精度 contract/run-record/gate 当前使用 schema 2；它们与通用实验记录的 schema 独立。旧记录缺少任务来源证据时不能仅改版本号转为新 gate。当前解析器依据 lm-eval v0.4.9 的 ConfigurableTask 与结果结构编写；目标镜像的实际版本、任务定制或字段不符时拒绝正式签发，需先核对并适配。本地负例测试不代表已经在 `flageval-llmeval:v1` 完成集成验证。不要绕过来源检查来恢复旧行为。

人工或 Agent 逐条检查完整输出与必要日志，填写健康审查的 reviewer、method 和各项结论。缺少 finish_reason/token 信息时不能凭“没看到 length”断言未截断；证据不足保持 pending。结构检查不会把错误答案的空过滤结果误判为空模型输出。

```bash
python3 evaluation/accuracy/acceptance.py issue \
  --run-record /external/run/run-record.json \
  --health-review /external/run/health-review.json \
  --output /external/run/accuracy-gate.json
```

新 gate 不覆盖旧文件。它绑定服务身份、原始 runner、配置、契约、结果、样本和审查文件 SHA；签发或消费时均重新检查。`verify_accuracy.py` 仅检查分数阈值，不生成正式 gate。

## 正式性能与诊断

启动性能测试前重新核验当前服务身份，再检查：

```bash
python3 evaluation/accuracy/acceptance.py check \
  --gate /external/run/accuracy-gate.json \
  --service-manifest /external/current-service.json
```

核验服务身份不等于自动远程采集。工具检测的是文件一致性，执行者必须根据当前进程、实际导入路径与源码内容重新确认 manifest；不能将旧快照当成当前事实。服务重启改变 `service_instance_id`，权重、代码、tokenizer、启动参数或运行身份变化均使旧 gate 失效。证据文件在消费端必须可访问；需搬运时保持内容 SHA 并明确更新引用，不能仅复制一个 `passed=true`。

XingChen 的 [性能 wrapper](../models/XingChen4-29B-A4B/ppu/optimize/tools/standard_perf.py) 正式模式要求 `--accuracy-gate` 和 `--service-manifest`，并核对实际 benchmark 模型/host/port。单独部署它时用 `--acceptance-tools` 指定随同部署的 `evaluation/accuracy/`。用户批准的纯性能研究使用 `--performance-only`，不生成正式精度达标声明。候选与 baseline/revert 的服务身份分别记录，不能为原路径伪造候选 gate。

[evaluation/performance](performance/README.md) 提供维护版诊断客户端，检查失败退出与完整轮次；[test/perf_test](../test/IMPORT_MANIFEST.md) 保留原始性能资产。直接运行诊断客户端不会自动成为正式验收。正式性能需同一候选 graph 配置、固定 workload、预热与多轮稳态，并完成 baseline/candidate/revert 对比。

需要自动比较时使用 `vllm_perf.py --config` 的计划入口，每次运行通过 `--comparison-contract` 绑定预冻结阈值并生成逐轮 `run-record.json`，最后使用 `compare_performance.py`。比较器重验原始结果/输出/命令、SHA、环境差异和独立进程数，并检查主指标、守护、波动和 SLO；正式范围还重验候选精度 gate。服务 manifest 的 `performance_context` 保存实际设备/runtime与缓存条件，仍由执行者取证。完整示例、三态判定和能力范围见[性能文档](performance/README.md#配置执行与比较)。

## 证据与目录

- `accuracy/`：正式 wrapper、样本检查、分数检查、绑定验收及模板；参数化和分片副本仅用于辅助/显式指定流程。
- `performance/`：维护版诊断、profiling 与 trace 汇总；原始工具的语义/矩阵变更需重新证明可比性。
- [ACCEPTANCE_TEMPLATE.md](ACCEPTANCE_TEMPLATE.md)：案例验收记录。
- [IMPORT_MANIFEST.md](IMPORT_MANIFEST.md)：历史导入与本地化说明；原始 `test/` 文件校验以 [test/IMPORT_MANIFEST.md](../test/IMPORT_MANIFEST.md) 为准。

完整日志、响应、数据集和 trace 留在外部产物路径；项目保存配置、摘要、校验值、失败原因及复现入口。历史记录不因新工具加入而自动通过新门禁。
