# Qwen3.6-27B

<!-- model-navigation:start -->
## 案例导航（2026-11-02 本地记录）

每个案例独立绑定 Host、拓扑与 baseline；下列状态来自本地账本，不表示已重新核验服务。

| 案例 | 优化状态 | 三阶段入口 |
|---|---|---|
| 20261015-qwen36-27b-metax-fg20-e2e | completed/requested-revert-and-Decode-diagnosis; performance-incomplete | [baseline](metax/20261015-qwen36-27b-metax-fg20-e2e/baseline/README.md) · [optimize](metax/20261015-qwen36-27b-metax-fg20-e2e/optimize/README.md) · [acceptance](metax/20261015-qwen36-27b-metax-fg20-e2e/acceptance/README.md) |
| 20261022-qwen36-27b-mx104-code-audit | completed | [baseline](metax/20261022-qwen36-27b-mx104-code-audit/baseline/README.md) · [optimize](metax/20261022-qwen36-27b-mx104-code-audit/optimize/README.md) · [acceptance](metax/20261022-qwen36-27b-mx104-code-audit/acceptance/README.md) |
| 20261022-qwen36-27b-mx104-plugin-regression | acc011_full_accuracy_completed_performance_paused | [baseline](metax/20261022-qwen36-27b-mx104-plugin-regression/baseline/README.md) · [optimize](metax/20261022-qwen36-27b-mx104-plugin-regression/optimize/README.md) · [acceptance](metax/20261022-qwen36-27b-mx104-plugin-regression/acceptance/README.md) |
| 20261012-qwen36-27b-metax-flash-attention | op010-completed-incomplete-original-FP32-reverted | [baseline](metax/baseline/README.md) · [optimize](metax/optimize/README.md) · [acceptance](metax/acceptance/README.md) |
<!-- model-navigation:end -->

## 对应的案例文档

- [20261012 Qwen3.6-27B / MetaX Flash Attention](../../docs/cases/20261012-qwen36-27b-metax-flash-attention/README.md)
- [Qwen3.6-27B / MetaX / 当前20FG端到端优化](../../docs/cases/20261015-qwen36-27b-metax-fg20-e2e/README.md)
- [Qwen3.6-27B / mx-104 verify 容器代码整理](../../docs/cases/20261022-qwen36-27b-mx104-code-audit/README.md)
- [Plugin release/0.2 迁移回归验证](../../docs/cases/20261022-qwen36-27b-mx104-plugin-regression/README.md)
