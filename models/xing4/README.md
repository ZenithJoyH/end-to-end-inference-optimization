# xing4

模型规格为 29B-A4B。复现实验时，权重路径、容器名、reasoning parser 和内核开关以各轮实际记录为准。

<!-- model-navigation:start -->
## 案例导航（2026-11-02 本地记录）

每个案例独立绑定 Host、拓扑与 baseline；下列状态来自本地账本，不表示已重新核验服务。

| 案例 | 优化状态 | 三阶段入口 |
|---|---|---|
| legacy-platform-layout | historical_candidate_retained_acceptance_incomplete | [baseline](ppu/baseline/README.md) · [optimize](ppu/optimize/README.md) · [acceptance](ppu/acceptance/README.md) |
<!-- model-navigation:end -->

## 对应的案例文档

- [xing4 / PPU-01：隔离吞吐优化](../../docs/cases/20260904-xing4-ppu-isolated-e2e/README.md)
