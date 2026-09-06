# 目标环境评测与性能工具

本目录保存从新模型适配流程纳入当前项目的公共测试工具。模型或平台专用的配置、包装脚本和
简要结果应放回对应的 `models/<model-name>/<platform>/`，避免直接修改公共测试基线。

本目录名中的 `test` 表示在目标机器或评测容器内实际执行的模型验收与性能 workload。当前项目代码自身的自动化单元测试统一放在 `unit_tests/`，两者不混用。

## 目录

- `perf_test/`：vLLM、SGLang 的推理性能测试和 Profiling 工具。
- `Accuracy_test/`：精度评测工具；正式流程必须在目标机器上进入基于
  `harbor.baai.ac.cn/flageval/flageval-llmeval:v1` 镜像的容器，使用 `llmrun.py`
  执行完整 198 题 GPQA Diamond 评测。默认任务为 `gpqa_diamond_generative_cot`，
  `limit=0`、`expected_samples=198`；`llmrun_parallel.py` 不能替代默认正式入口。
- `nccl_test/`：平台通信测试脚本，仅在对应平台和通信后端适用时使用。

## 数据与结果

`perf_test/ShareGPT_V3_unfiltered_cleaned_split.json` 是约 642 MB 的本地性能测试数据，
已通过仓库 `.gitignore` 排除。测试生成的 `outputs/`、`results/` 和 `logs/` 同样不提交。
仓库只保存可复用测试代码、无敏感信息的配置和适配结果摘要。
