# 精度与性能评测

本目录由“新模型适配”项目的公共评测资产迁入，已成为当前项目的独立副本，不与上游目录建立运行时联系。

## 评测闭环

```text
固定验收契约
  → eager / graph 启动验证
  → graph 下 8 并发固定小样本（正确性 + 性能 sanity）
  → 每轮候选的最小数值/行为回归
  → 最终候选的全量精度评测
  → 精度门禁通过
  → 同一 graph 服务配置下正式性能评测
  → baseline / candidate / revert 对比
```

探索阶段可以运行短性能测试帮助定位，但不能作为最终性能结论。正式性能评测必须在最终候选通过全量精度门禁后进行。

## 目录

- `accuracy/`：基于 `lm-evaluation-harness` 的单服务和分片评测入口、GPQA 阶段计分与精度门禁。
- `performance/`：vLLM、SGLang 的稳态 benchmark、Profiler 驱动与 trace 汇总工具。
- `ACCEPTANCE_TEMPLATE.md`：每个优化案例的精度/性能验收记录模板。
- `IMPORT_MANIFEST.md`：来源文件、校验值、本地化修改和未导入资产。

## 强制规则

1. 在看结果前固定任务、样本数、生成参数、并发、随机种子、指标和通过门槛。
2. baseline 与 candidate 使用同一权重、tokenizer、prompt/chat template、采样参数、服务模式和数据集 revision。
3. 优先使用已适配模型的可信结果作相对基线；没有可信基线时使用模型负责人给出的绝对门槛，不能在看到分数后放宽。
4. 进程退出 0 不等于精度通过；还要验证唯一样本数、结果文件、超时、空输出、截断、异常重复和正式 metric。
5. 中间阶段分数只用于提前发现异常，不能代替最终 `results_*.json`。
6. 性能正式结果与 profiler 结果分账；profile 轮不进入稳态吞吐/延迟汇总。
7. 数据集、权重、response cache、原始 trace 和大体积输出不提交仓库，只记录位置、revision 和校验信息。

## 来源与本地化

迁入时保留了上游 runner 的核心行为，并做了三项本地化：

- 示例配置不再包含上游模型或 NFS 路径；
- 默认不允许超时通过；
- 增加 `verify_accuracy.py`，用于执行预先确定的绝对或相对精度门禁。
