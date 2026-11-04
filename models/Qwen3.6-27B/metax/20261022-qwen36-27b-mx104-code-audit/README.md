# Qwen3.6-27B / mx-104 verify 容器代码整理

2026-10-22。按用户要求保留现有实现，依据容器实况整理快照、补丁和优化点，不继承 mx-59 的历史优化结论。

当前：[env-003 Plugin迁移结果](optimize/env-003.md)。容器已更新到 `release/0.2@7cb55994`，保留原两处优化；10项CPU测试、真实CLI入口与MetaX路由通过，模型级graph/精度/性能未运行。

原审计入口：[代码与优化点报告](optimize/audit-001.md)。当前模型 GDN 静态主路径走 vLLM 自带 FLA；已安装的 FGV 改动不能直接视为本模型生效收益。当前未运行推理服务，未开展性能或精度验收。

远程交付：`/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-code-audit/code-review-bundle.tar.gz`。

增量交付：远程case下 `env-003-release02-bundle.tar.gz`；原audit包与原源码备份均保留。

- [baseline](baseline/README.md)
- [optimize](optimize/README.md)
- [acceptance](acceptance/README.md)
