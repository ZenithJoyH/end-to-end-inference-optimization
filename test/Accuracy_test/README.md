# 原始 GPQA Diamond 评测资产

本目录的 runner、配置与阶段计分脚本保留导入字节基准，校验值见 [IMPORT_MANIFEST](../IMPORT_MANIFEST.md)。`llmrun.py` 仍是默认正式模型评测实现；`llmrun_parallel.py` 仅用于用户明确要求的多服务/多 shard。

实际正式启动统一通过 [evaluation/README.md](../../evaluation/README.md) 中的 wrapper 命令，显式传入案例配置、预冻结阈值、当前服务身份与规定评测容器的 inspect。wrapper 调用本目录原始 runner，补充预检、seed、样本检查和绑定验收，不替换其模型评测逻辑。

原始 `llm_config.json` 和 `llm_parallel_config.json` 包含历史模型、路径及超时策略，仅作为导入记录，不能直接当成新任务配置。新任务从 [参数化模板](../../evaluation/accuracy/llm_config.example.json) 建立配置。直接运行 `python3 llmrun.py` 使用的原始默认值没有外层保护，退出 0 不代表正式验收。

评测始终在目标机器上的 `harbor.baai.ac.cn/flageval/flageval-llmeval:v1` 独立评测容器执行，访问优化容器中的候选 graph 服务。阶段计分仅用于排障；完整 samples、results 与输出健康审查共同支撑最终精度结论。
