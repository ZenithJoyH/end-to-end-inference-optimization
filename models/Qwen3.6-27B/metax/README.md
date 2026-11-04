# Qwen3.6-27B / MetaX

- [20261022 mx-104 verify 容器代码整理](20261022-qwen36-27b-mx104-code-audit/README.md)：独立代码审计及Plugin迁移至release/0.2@7cb55994，原优化和回退备份保留；来源为当前容器，以下 mx-59 历史不作为其运行事实。

以下既有优化记录对应 Host：mx-59；源容器：qwen3.6-27B。与上面的 mx-104 代码审计分开维护。

- 当前：[20261015 当前脚本20项FlagGems端到端优化](20261015-qwen36-27b-metax-fg20-e2e/README.md)。独立容器继承现役优化环境，原服务暂停/恢复已获用户明确授权；旧全21项结果保留在以下历史入口，不能直接比较。

- [基线](baseline/README.md)
- [优化](optimize/README.md)
- [验收](acceptance/README.md)

<!-- case-navigation:start -->
## 完整案例入口

- 20261015-qwen36-27b-metax-fg20-e2e：[baseline](20261015-qwen36-27b-metax-fg20-e2e/baseline/README.md) · [optimize](20261015-qwen36-27b-metax-fg20-e2e/optimize/README.md) · [acceptance](20261015-qwen36-27b-metax-fg20-e2e/acceptance/README.md)
- 20261022-qwen36-27b-mx104-code-audit：[baseline](20261022-qwen36-27b-mx104-code-audit/baseline/README.md) · [optimize](20261022-qwen36-27b-mx104-code-audit/optimize/README.md) · [acceptance](20261022-qwen36-27b-mx104-code-audit/acceptance/README.md)
- 20261022-qwen36-27b-mx104-plugin-regression：[baseline](20261022-qwen36-27b-mx104-plugin-regression/baseline/README.md) · [optimize](20261022-qwen36-27b-mx104-plugin-regression/optimize/README.md) · [acceptance](20261022-qwen36-27b-mx104-plugin-regression/acceptance/README.md)
- 20261012-qwen36-27b-metax-flash-attention：[baseline](./baseline/README.md) · [optimize](./optimize/README.md) · [acceptance](./acceptance/README.md)
<!-- case-navigation:end -->
