# 精度工具

实际评测由 [推理精度评测技能](../../skills/inference-accuracy-evaluation/SKILL.md) 编排。启动 baseline sanity、最小回归或正式评测进程前，Skill 创建绑定当前 Codex 任务的 heartbeat 进度通知，默认每 30 分钟一次，并在终态后停用；本目录工具不自行创建或管理计划任务。

当分数低于阈值时，由 [推理精度问题定位技能](../../skills/inference-accuracy-diagnosis/SKILL.md) 消费冻结产物进行定位。输出异常可作为运行问题单独诊断，但不否决已达阈值的精度结论。

正式命令与证据要求统一见 [评测入口](../README.md)。

| 工具 | 职责 |
|---|---|
| `formal_accuracy.py` | 采集实际 task/数据来源、预检身份并调用原始正式 runner；冻结运行输入及结果证据 |
| `sample_validation.py` | 唯一 ID、完整集合与可选输出健康观察 |
| `verify_accuracy.py` | 纯分数 `score >= threshold` 比较；不代表服务身份已绑定 |
| `acceptance.py` | 按单一阈值条件签发 gate，并绑定服务/契约/结果证据 |
| `llmrun.py` | 维护版辅助 runner，复用严格样本检查；非默认正式模型评测实现 |
| `llmrun_parallel.py` | 显式指定多服务/分片时使用；不自动签发单服务正式 gate |
| `score_progress.py` | 阶段计分，仅用于排障 |

原始正式 runner 与导入 SHA 位于 [test/Accuracy_test](../../test/Accuracy_test/README.md)。维护版与原始副本不要求字节一致，正式 wrapper 记录它实际调用的原始 SHA。

正式契约只冻结 `metric` 和数值型 `threshold`。候选分数大于或等于阈值即通过，等于阈值不视为失败；不能在看到候选分数后改变指标或阈值。
配置中的 `allow_timeouts` 仅为兼容原 runner 保留，取值 `true` 或 `false` 都不影响正式 gate；本项目示例使用 `true` 以避免原始执行层提前拦截超时样本。

服务端精度评测必须开启 prefix cache，具体配置与切换流程见下节。评测器响应缓存与服务端 KV prefix cache 是两类缓存：每次正式启动采用独立 UUID 响应缓存；同一运行内普通失败重试保留原 runner 行为，不跨候选复用响应。Ctrl+C 取消会清理本次评测及计分子进程并向上传播，不自动重试或发布完成记录；并行入口同时取消当前分片，停止重试及合并。正式 wrapper 使用维护侧进程执行函数，原始 runner 文件及 SHA 不变。输出健康信息可保留为诊断观察，但不参与精度 gate 判定。

### 用户明确选择已有 GPQA 参考请求协议

默认任务仍是 `gpqa_diamond_generative_cot`。用户明确要求沿用一套已有的完整 GPQA 参考协议时，
配置、契约和 provenance 可以携带相同的 `reference_protocol`：`task`、用户原话 `authorization`，
以及 `manifest`、`requests`、`parameters`、`implementation` 四个 `{path, sha256}` 引用。
这些资源放在同一个已冻结的协议目录；原 manifest 的 `files` 必须匹配后三项，
`reference_sha256` 标识交付参考源。不能只换任务名或把新结果标成默认任务。

参考 requests 为 198 行 JSONL，按 `index=0..197` 排列，每行含 `gold` 和完整 `request`。
所有请求除 model/messages 外的字段必须等于 parameters；任务只读取该 requests 文件。
使用 `local-chat-completions`、`dataset_path=json`、`dataset_name=null`、`dataset_split=test`，
`gen_kwargs` 为空，由请求自带生成参数，lm-eval seed 与 parameters 一致。
`include_path` 指向该协议目录，完整集合、model、endpoint 和并发仍显式冻结。

仍通过 `formal_accuracy.py --capture-provenance`、`--preflight-only`、完整评测及
`acceptance.py issue/check`；原始 runner 不变。仅允许来源文件与冻结 implementation 完全相同的
ConfigurableTask 子类，并实际调用其请求构造，逐题核对 messages、全部生成字段和空 stop 列表。
原始请求内容、任务源码、评分函数、样本/结果 metadata、服务身份及 198 题完整性共同绑定，
任何漂移均拒绝签发或消费 gate。这是用户授权的协议选择，不是放宽正确性阈值。

无额外生成覆盖时，已核验的 lm-eval 会把原生结果 `config.gen_kwargs` 写为显式 `null`，
而 provenance 的解析值是 `{}`。校验器仅在该键存在、冻结配置 `gen_kwargs=""` 且
provenance 覆盖为 `{}` 时接受这两种等价表示；缺键、错误类型及任何非空参数漂移仍拒绝。
若完整原生运行仅因此被旧封装拒绝，可在保存旧工具/失败回执和新工具 SHA、完成回归后，
用 `formal_accuracy.py --finalize-run <原UUID目录>` 复验同一完整结果，再原生 issue/check。
该路径不查询模型，不改写原始样本、结果、协议或阈值；其他证据缺陷仍阻止签发。

## 精度开启缓存与性能关闭缓存

精度评测服务必须显式设置 `--enable-prefix-caching`，移除 `--no-enable-prefix-caching`。
先确认目标 CLI 支持，再核验实际进程参数和 runtime 状态；不能只依赖默认值或预期启动脚本。
服务 manifest 必须记录 `launch_config.enable_prefix_caching=true`、包含显式开关的 `launch_args`，
以及 `performance_context.prefix_cache_state=cold/warm/mixed` 和非空 `cache_preparation`。
开启但尚无命中的 cold 状态符合要求，不增加命中率门槛。示例不是运行证据，必须替换为实测值。
纯算子测试没有服务缓存；只读 `gate-check` 不发精度请求。

`formal_accuracy.py` 在预检及实际请求前强制检查；新 run-record 与原始 gate 带
`accuracy_prefix_cache_required=true`，后续复验继续检查。`acceptance.py issue` 不允许对关闭
缓存的旧记录新签发 gate。历史记录保留原貌，可按原协议审计，不按新规则追认开启状态。
精度结论仍只比较 `score >= threshold`；配置检查用于确保评测按规定执行。

默认性能测量仍显式使用 `--no-enable-prefix-caching`。开启状态的精度 gate 不能直接用于关闭
状态的性能实例，也不能用严格 `rebind` 绕过配置差异。使用专用绑定：

```bash
python3 evaluation/accuracy/acceptance.py performance-bind \
  --source-gate /external/original-accuracy-gate.json \
  --service-manifest /external/performance-service.json \
  --evidence /external/prefix-cache-transition.json \
  --output /external/performance-bound-gate.json
```

该流程直接引用完整证据仍有效的原始 schema3 gate，原精度服务须开启缓存，新性能实例须关闭。
相较下节严格重启绑定，仅额外允许四处差异：`launch_config.enable_prefix_caching`、
`launch_args` 中对应开关、`performance_context.prefix_cache_state`、`cache_preparation`。
其他启动参数、代码、权重、tokenizer、Host/容器/endpoint、设备、runtime、调参DB指纹必须相同。
保留两份真实 manifest；禁止改写旧证据或伪造相同实例。它不授权重启其他或共享服务。

证据采用下节 schema1 重启回执及全部核验要求：两份服务引用、当前 runtime、graph capture、
至少两次 replay、绑定当前实例的最小运行回归。另增加 `prefix_cache_regression` 的 `{path, sha256}`
引用，指向缓存切换对照回执：

```json
{
  "status": "passed",
  "source_service_sha256": "<开启缓存的精度服务 manifest SHA>",
  "current_service_sha256": "<关闭缓存的性能服务 manifest SHA>",
  "contract": {"path": "/external/cache-switch-contract.json", "sha256": "<SHA>"},
  "source_result": {"path": "/external/cache-on-result.json", "sha256": "<SHA>"},
  "current_result": {"path": "/external/cache-off-result.json", "sha256": "<SHA>"}
}
```

切换前冻结固定请求/token、生成参数、seed、数值容差及判定方法，覆盖重复前缀命中和相关边界；
在两份服务上实际执行并保存原生结果。随机生成不得简单要求文本逐字相等，应使用冻结的可比
数值/语义回归方法。工具检查回执和 SHA 关联，执行者负责真实采集与按契约判定，不能手填成功
替代对照。切换后的关闭缓存运行回归用于确认性能执行路径，不冒充新的正式精度评测。
证据缺失保持 `incomplete`；回归失败进入定位、修复或回退，不关闭精度缓存重新跑 GPQA 来绕行。

输出为 schema7、`evaluation_reused=true`，保留原分数和阈值，绑定当前性能实例。
性能比较和最终验收会递归复验源 gate、两份 manifest 及转换证据。每个独立性能进程都直接从
原始 gate 创建新绑定，不支持链式绑定，也不同时放宽调参DB或其他配置漂移。

## 服务身份与重启复用

服务 manifest 必须填实测布尔值 `flaggems_vllm_installed`。已安装时
`flaggems_vllm_sha256` 必须是实际使用源码（含未提交改动）的内容 SHA；未安装时为 `null`。
缺失不能当作未安装。旧 manifest 缺字段时保持证据不足，不回填猜测值或改写已冻结回执。

默认 `check` 仍严格绑定原实例。相同候选仅重启服务时，可显式创建新的 schema 4 绑定回执：

```bash
python3 evaluation/accuracy/acceptance.py rebind \
  --source-gate /external/original-accuracy-gate.json \
  --service-manifest /external/current-service.json \
  --evidence /external/rebind-evidence.json \
  --output /external/rebound-accuracy-gate.json
```

原 gate 必须为真实评测生成的 schema 3，仍须通过完整证据复验，禁止链式 rebind。
新旧 manifest 仅允许 `service_instance_id` 和 `runtime_evidence_sha256` 变化；endpoint、Host、容器、
源码/权重/tokenizer、启动配置、设备/镜像/runtime 等其余字段逐项相等。设备与环境字段必须明确，
不得用删除字段或改写原始 manifest 来凑一致。

`rebind-evidence.json` 为 schema 1，包含四个 `{path, sha256}` 引用：`source_service`、
`current_service`、`runtime_evidence`、`minimal_regression`。运行证据 JSON 必须由当前实例取证生成，包含：

- `service_instance_id`；
- `stable_identity_sha256`：用 `acceptance.content_sha256(acceptance.stable_service_identity(service))` 计算；
- `graph_capture_completed: true`、`graph_replays >= 2`；
- 建议同时保存实际导入路径、进程参数、设备/环境和 capture/replay 的原生证据路径。

最小回归回执包含 `status: passed`、当前 `service_sha256` 和指向原始回归结果的 `evidence` 引用。
工具核验文件及关联，不替代远程实际取证，不能从期望配置伪造观察值。
新 gate 标记 `evaluation_reused: true`，保留原分数和阈值，并绑定当前服务；这不是新跑出的精度分数。
严格 `rebind` 不接受任何代码、配置或环境变化；证据缺失、回归失败必须诊断或重新完整评测。精度开启→性能关闭只能按上节专用流程处理。

正式案例中的整数参数必须写为 JSON 整数，不能使用浮点数、字符串或布尔值；包装器在原 runner 的类型转换前检查，避免 `limit: 0.9` 被转换成完整评测的 `0`。并发、超时必须为正数，重试次数与等待时间不得为负数。

`run-record.json` 只在分数达到预冻结阈值且其身份、原生结果和样本来源可核验时生成。后三者用于防止拿错分数，不是额外的精度通过条件。

先使用 `--capture-provenance` 采集数据/任务内容指纹，再冻结 schema 3 契约。正式签发交叉检查原生结果 metadata 与实际题目内容，字段缺失或不支持时记为证据无效，不产生可消费的 gate。

## 真实接口与镜像集成边界

### 同一实例的正常调参缓存写入

调参DB内容是可变运行状态，不等同于模型代码或启动参数。默认schema3/4检查不放宽；
用户明确授权处理该差异后，可以使用新增`cache-update`签发schema5回执：

```bash
python3 evaluation/accuracy/acceptance.py cache-update \
  --source-gate /external/original-evaluated-gate.json \
  --service-manifest /external/current-service.json \
  --evidence /external/cache-update-evidence.json \
  --output /external/cache-bound-gate.json
```

原生`issue`仍从真实run-record签发原始schema3 gate。schema5只引用原gate，不改旧manifest、
样本、契约、分数或阈值，不代表重跑精度。只允许同一实例的
`launch_config.flaggems_db_sha256`及运行快照SHA变化；DB URL、调参策略、源码、设备、权重、
tokenizer、graph和启动参数仍严格相同。不同实例不能走此分支，禁止链式绑定。

证据schema1的`kind`为`flaggems_tuning_cache_update`，必须含用户授权原文`authorization`，以及
`source_service/current_service/before_runtime/current_runtime/cache_audit`五个SHA引用。
runtime SHA逐项对应原始/当前manifest。cache_audit包含`status: passed`、
`kind: flaggems_autotune_cache`、`service_instance_id/cache_url/before_sha256/after_sha256`、
以`tuning_cache_identity(current)`计算的`stable_identity_sha256`、实测布尔值
`cache_tables_only: true`与`manual_reset_copy_or_policy_override: false`，以及实际缓存表结构/
写入实现与当前服务检查的`inspection`引用。观察由调用方现场采集，不能用期望值代替。

开始DB未保存字节快照时，必须注明不能逐行证明全部历史写入者；不能伪造行级差分。
后续DB再次变化需新证据/新schema5回执，不能把所有未来DB变化默认视作相同身份。

### 同时重启且调参缓存发生正常写入

此时纯`rebind`和同实例`cache-update`都仍拒绝，不伪造中间实例或链式签发。
用户明确授权后，可用`cache-rebind`签发独立schema6回执，直接引用原始schema3 gate：

```bash
python3 evaluation/accuracy/acceptance.py cache-rebind \
  --source-gate /external/original-evaluated-gate.json \
  --service-manifest /external/current-service.json \
  --evidence /external/cache-restart-evidence.json \
  --output /external/cache-restart-gate.json
```

证据schema1/kind=`flaggems_cache_restart`，含非空`authorization`、原始/当前精确
`source_service/current_service`、`before_runtime/current_runtime`、`minimal_regression`、
`cache_audit`路径/SHA引用。只省略实例、已核验进程证据及DB内容SHA，URL、调参策略、源码、
环境、权重、tokenizer、设备和全部推理参数仍严格相等；必须真实新实例及当前完整最小回归。
当前runtime须含实例、`cache_restart_identity`的稳定身份SHA、capture完成、至少两次真实replay，
以及支撑这些断言的`observations`路径/SHA。不得以旧实例trace或CPU子图代替当前模型证据。

cache audit kind=`flaggems_autotune_cache_restart`，含原/当前实例ID、DB URL、前后内容SHA、
稳定身份SHA、`cache_tables_only=true`、`manual_reset_copy_or_policy_override=false`及真实
schema/writer/运行事实`inspection`引用。`historical_row_delta_available`必须显式为布尔值：
true时引用逐行差分，false时写非空`history_gap`，不能将较早快照冒充本次原始快照。
该回执复用原生精度结果，不声称仅靠SHA证明写入因果或性能缓存条件相同。
性能可比性仍须独立冻结和检查，不能因此允许性能比较忽略DB变化。
消费schema6时重验原生结果及上述全部引用，不链式绑定，不改变分数/阈值；新源码不适用。
此分支只修复缓存分类与绑定问题，不豁免性能实验的预热、缓存准备和可比性要求。

采集器按 lm-eval CLI 的实际行为，将解析后的 `model_args` 传给 `TaskManager(metadata=...)`；模型、endpoint 和请求参数会进入任务配置的 metadata，正式结果必须与之相等。忽略这一步会令采集配置与真正执行的配置不同。接口依据是 [lm-eval v0.4.9 CLI](https://github.com/EleutherAI/lm-evaluation-harness/blob/v0.4.9/lm_eval/__main__.py) 和 [TaskManager](https://github.com/EleutherAI/lm-evaluation-harness/blob/v0.4.9/lm_eval/tasks/__init__.py)。

正式验收始终检查 **198 个唯一题目**。lm-eval 对每个 filter 分别写 samples 行，存在多个 filter 时，行数可以多于 198；按冻结的 `task_config.filter_list` 检查每个 `(doc_id, filter)` 恰好一次，并核对同一题跨 filter 的原始 `doc/resps/target/arguments` 一致。允许过滤结果和 metric 不同，拒绝缺失 filter、未知 filter、重复同 filter 或内容冲突。普通 `validate_sample_file` 未显式传入 filter 集合时仍保持按题目严格去重。原生行结构见 [evaluator](https://github.com/EleutherAI/lm-evaluation-harness/blob/v0.4.9/lm_eval/evaluator.py)。

公开的 `lm_eval==0.4.9` wheel 不包含本项目固定的 `gpqa_diamond_generative_cot` 任务名。该任务必须来自规定评测镜像或明确核验的任务定义；不能静默替换为 `gpqa_diamond_cot_zeroshot` 等相近名称。采集时未注册精确任务即失败。

本地固定源码验证可以在不安装 torch/datasets、不加载模型的情况下执行：

```bash
E2E_LM_EVAL_WHEEL=/external/lm_eval-0.4.9-py3-none-any.whl \
  python3 -m unittest discover -s unit_tests -p 'test_lm_eval_source_interface.py'
```

该测试先校验公开 wheel 的 SHA，再执行其中未经修改的任务 metadata 合并、配置方法和原生 samples 字典构造代码；数据与依赖构造使用合成对象。它是固定源码接口检查，**不是完整包导入、规定镜像或正式 GPQA 通过证据**。未提供 wheel 时测试明确跳过，不联网下载或安装依赖。

规定镜像集成仍需在用户指定的目标机器和评测容器中执行以下核验；截至 2026-09-07，本次本地工作没有执行这些步骤：

1. 核验精确容器的镜像引用/image ID 和当前解释器；确认实际 `lm_eval/torch/datasets` 可导入，精确任务已注册，记录实际 task YAML/helper 的来源，不根据版本号推定定制任务存在。
2. 用同一案例配置执行两次 `--capture-provenance`，输出到不同新文件，确认任务 metadata、实际 dataset path/name/split、原始/处理后题目指纹和 filter 集合一致。采集不会查询模型服务或生成答案；不得为让采集通过而自动改写数据集路径。
3. 根据采集内容冻结契约，确认源码/schema 与适配器匹配后，再核验服务身份并执行 `--preflight-only`。这是服务 `/v1/models` 预检，不能代替精度评测。
4. 当精度评测 Skill 的 `formal-gate` 触发条件满足，或用户明确恢复此前暂缓的正式评测后，才执行完整 GPQA 和 gate 签发；核对真实 metadata 与多 filter 样本是为了确认分数属于当前候选。


### 已有原生 API 产物的 CPU 观察

`response_observations.py` 可在不调用模型的情况下核验返回 token/prompt/usage，
并通过完整原生 prompt 将日志对象映射到样本。原生 `lm_eval` 的 JSON 聊天参数先按
role/content 结构解码，再唯一匹配返回的完整 prompt；不按返回顺序、问题片段或模糊文本猜身份。
重复 doc、多轮歧义、残缺对象及未映射记录必须显式处理。其输出是完整解析 API 对象，
不是 HTTP wire，也不替代 native score、正式 acceptance 或服务身份绑定。
已有正式审计需要修正时另存新输出和 SHA，保留原失败回执、样本与分数。

公共观察器不预设模型词表或生成长度：`thinkend_token_id`、`eos_token_ids`、
`max_completion_tokens` 由调用方显式传入；未配置时相关观察为 `None`／空映射。
案例中已经冻结的旧观察器副本及模型专用字段保持原样，新审计记录各自代码SHA，不能
在已执行的评测中静默替换冻结工具。
