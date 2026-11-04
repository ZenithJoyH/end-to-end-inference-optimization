# 最新 C32 精度结果

GPQA **127/198=64.14分**（输出上限65,536）通过64分阈值；ERQA **176/400=44.00分**（输出上限18,000）通过40分阈值、0拒答。原服务保持运行，原生分数/数据/来源/默认采样和服务保留已独立核验。

[本轮完整记录](../optimize/acc-004-c32-gpqa-erqa.md)。GPQA gate仅绑定本次实际服务实例、C32及输出契约；未测性能，无端到端性能验收结论。

历史C64成绩保留：GPQA18K与64K两轮均125/198=63.13，ERQA182/400=45.50。C32相比同上限C64分别+1.01/-1.50分，不能单轮推断并发的稳定因果收益。[原C64全量](../optimize/acc-001-opt15-c64-default.md)、[64K全量](../optimize/acc-003-gpqa-full-cap65536.md)、[11题补测](../optimize/diag-002-cap65536-retest.md)不被覆盖。

<!-- record-metrics:start -->
## 已记录指标（按 state.yml 展示）

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| gpqa-c32-user-scoped-accuracy | candidate | accuracy | 64.14141414141415 | percent | 用户指定 C32 精度评测；不代表四场景性能验收 |
| erqa-c32-user-scoped-accuracy | candidate | accuracy | 44.0 | percent | 用户指定 C32 精度评测；不代表四场景性能验收 |
<!-- record-metrics:end -->
