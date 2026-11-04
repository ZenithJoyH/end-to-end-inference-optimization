# Qwen3.6-27B / mx-104 / baseline

这是已优化容器的代码审计起点，不是未优化 anchor baseline。环境与来源见 [state.yml](state.yml)。没有运行推理服务，也未采集新的性能或精度数据。

| 正式场景 | 状态 | 吞吐 / TTFT / TPOT / E2E |
|---|---|---|
| P1024/D1024/C64/N128 | not_run：本次不做性能测试 | — |
| P4096/D1024/C64/N128 | not_run：本次不做性能测试 | — |
| P16384/D1024/C64/N128 | not_run：本次不做性能测试 | — |
| P32768/D1024/C64/N128 | not_run：本次不做性能测试 | — |


<!-- e2e:summary:start -->

- 案例：20261022-qwen36-27b-mx104-code-audit
- 当前状态：completed
- 当前候选：preserved-container-snapshot
- 下一步：none within requested scope

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|

<!-- e2e:summary:end -->

<!-- baseline-record-review:start -->
## 正式目标覆盖与历史测量

本节是记录审查：原测量状态与角色保持不变，不是新评测回执。`incomplete` 表示此表未闭合正式基线证据；历史、缩减或有观察器的结果须按原范围解释。

| 正式目标 | 正式基线证据状态 | 已记录指标数 | 边界 |
|---|---|---:|---|
| p1024-d1024-c64-n128 | not_run | 0 | 本阶段原记录明确未执行性能测试。 |
| p4096-d1024-c64-n128 | not_run | 0 | 本阶段原记录明确未执行性能测试。 |
| p16384-d1024-c64-n128 | not_run | 0 | 本阶段原记录明确未执行性能测试。 |
| p32768-d1024-c64-n128 | not_run | 0 | 本阶段原记录明确未执行性能测试。 |

吞吐、TTFT、TPOT/ITL、E2E：—。本阶段没有独立 E2E baseline 数值；精度或组件实验与历史观测见原记录及 optimize，不填造数据。
<!-- baseline-record-review:end -->
