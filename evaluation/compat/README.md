# 历史契约兼容工具

从 XingChen 模型目录迁入的四个参数化工具，保留历史回执解析、固定矩阵和控制行为的回归测试。
单元测试不再依赖任何 `models/` 文件。本目录不是新模型的默认执行入口；新任务使用
`evaluation/accuracy/`、`evaluation/performance/` 和项目控制面。

迁移不改变历史指标的诊断性质，不重新签发旧结果。原位置为
`models/XingChen4-29B-A4B/ppu/optimize/tools/`，同名文件在此可恢复。
