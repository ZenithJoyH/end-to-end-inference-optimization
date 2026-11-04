# Qwen3.6-35B-A3B

<!-- model-navigation:start -->
## 案例导航（2026-11-02 本地记录）

每个案例独立绑定 Host、拓扑与 baseline；下列状态来自本地账本，不表示已重新核验服务。

| 案例 | 优化状态 | 三阶段入口 |
|---|---|---|
| 20261013-qwen36-35b-metax-e2e-current | CPU_packet_complete_waiting_user_for_bounded_numeric_GPU | [baseline](metax/20261013-qwen36-35b-metax-e2e-current/baseline/README.md) · [optimize](metax/20261013-qwen36-35b-metax-e2e-current/optimize/README.md) · [acceptance](metax/20261013-qwen36-35b-metax-e2e-current/acceptance/README.md) |
| 20261013-qwen36-35b-metax-moe-public-api | retained | [baseline](metax/20261013-qwen36-35b-metax-moe-public-api/baseline/README.md) · [optimize](metax/20261013-qwen36-35b-metax-moe-public-api/optimize/README.md) · [acceptance](metax/20261013-qwen36-35b-metax-moe-public-api/acceptance/README.md) |
| 20261022-qwen36-35b-mx104-sampler-fix | completed | [baseline](metax/20261022-qwen36-35b-mx104-sampler-fix/baseline/README.md) · [optimize](metax/20261022-qwen36-35b-mx104-sampler-fix/optimize/README.md) · [acceptance](metax/20261022-qwen36-35b-mx104-sampler-fix/acceptance/README.md) |
| 20261022-qwen36-35b-mx104-stack-regression | container_slimmed_evaluation_user_paused_no_model_service | [baseline](metax/20261022-qwen36-35b-mx104-stack-regression/baseline/README.md) · [optimize](metax/20261022-qwen36-35b-mx104-stack-regression/optimize/README.md) · [acceptance](metax/20261022-qwen36-35b-mx104-stack-regression/acceptance/README.md) |
<!-- model-navigation:end -->

## 对应的案例文档

- [Qwen3.6-35B-A3B / mx-59 当前容器端到端优化](../../docs/cases/20261013-qwen36-35b-metax-e2e-current/README.md)
- [Qwen3.6-35B-A3B / mx-59：base 与 begin 性能 gap 诊断](../../docs/cases/20261013-qwen36-35b-metax-performance-gap/README.md)
- [Qwen3.6-35B / mx-104 verify 容器代码整理](../../docs/cases/20261022-qwen36-35b-mx104-code-audit/README.md)
- [Qwen3.6-35B / mx-104 Plugin 采样导入生命周期修复](../../docs/cases/20261022-qwen36-35b-mx104-sampler-fix/README.md)
- [Qwen3.6-35B / mx-104 整理与迁移完整回归](../../docs/cases/20261022-qwen36-35b-mx104-stack-regression/README.md)
- [11 月 3 日 mx-104 复测诊断与原 B 容器对照](metax/20261022-qwen36-35b-mx104-stack-regression/optimize/perf-retest-20261103-001.md)
