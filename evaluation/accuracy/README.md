# 精度工具

实际评测由 [推理精度评测技能](../../skills/inference-accuracy-evaluation/SKILL.md) 编排。启动 baseline sanity、最小回归或正式评测进程前，Skill 创建绑定当前 Codex 任务的 heartbeat 进度通知，默认每 30 分钟一次，并在终态后停用；本目录工具不自行创建或管理计划任务。

当分数、样本完整性或输出健康检查失败时，由 [推理精度问题定位技能](../../skills/inference-accuracy-diagnosis/SKILL.md) 消费这些冻结产物进行分类、最小复现和改动二分；本目录工具的退出码或单一分数差不能独立证明根因。

正式命令与证据要求统一见 [评测入口](../README.md)。

| 工具 | 职责 |
|---|---|
| `formal_accuracy.py` | 采集实际 task/数据来源、预检身份并调用原始正式 runner；冻结运行输入及结果证据 |
| `sample_validation.py` | 有效响应、唯一 ID、完整集合、超时与显式截断检查 |
| `verify_accuracy.py` | 有限数阈值或可信 baseline 的纯分数比较；不代表正式验收 |
| `acceptance.py` | 绑定服务/契约/结果/健康审查的 gate 签发与核验 |
| `llmrun.py` | 维护版辅助 runner，复用严格样本检查；非默认正式模型评测实现 |
| `llmrun_parallel.py` | 显式指定多服务/分片时使用；不自动签发单服务正式 gate |
| `score_progress.py` | 阶段计分，仅用于排障 |

原始正式 runner 与导入 SHA 位于 [test/Accuracy_test](../../test/Accuracy_test/README.md)。维护版与原始副本不要求字节一致，正式 wrapper 记录它实际调用的原始 SHA。

相对门槛在契约中使用 `baseline: {"path": "/external/results.json", "sha256": "实测哈希"}`；该结果必须已有可信的完整性和可比性证据。`max_regression` 是分数的绝对差，如 0.01 表示一个百分点。不能在看到候选分数后改变该契约。

每次正式启动采用独立 UUID 缓存；同一运行内重试保留原 runner 行为，不跨候选复用响应。完整输出健康审查另行签发；不能用阶段分数或纯结构检查替代。

正式案例中的整数参数必须写为 JSON 整数，不能使用浮点数、字符串或布尔值；包装器在原 runner 的类型转换前检查，避免 `limit: 0.9` 被转换成完整评测的 `0`。并发、超时必须为正数，重试次数与等待时间不得为负数。

`run-record.json` 只在身份、原生结果、完整样本及分数门槛全部通过后生成；失败运行保留有效配置、冻结输入和原始结果，不能因原进程退出成功就记为完成。包装器和 gate 的 JSON 产物使用同目录临时文件完成写入后原子发布，拒绝覆盖既有文件；序列化或写入失败不会留下半截的正式产物。

先使用 `--capture-provenance` 采集数据/任务内容指纹，再冻结 schema 2 契约。正式签发交叉检查原生结果 metadata 与实际题目内容，字段缺失或不支持时拒绝；目标镜像兼容性及完整命令见评测入口。

## 真实接口与镜像集成边界

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
4. 当精度评测 Skill 的 `formal-gate` 触发条件满足，或用户明确恢复此前暂缓的正式评测后，才执行完整 GPQA、输出健康审查和 gate 签发；核对真实 metadata 与多 filter 样本，保留失败证据。镜像 API 或结果结构不支持时先形成有依据的适配，保持失败状态，不放宽门禁。
