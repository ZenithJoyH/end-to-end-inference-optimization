# 20261027-qwen3vl-opt13-performance-gap / baseline

<!-- e2e:summary:start -->

- 案例：20261027-qwen3vl-opt13-performance-gap
- 当前状态：historical-observation-only
- 当前候选：—
- 下一步：Use opt10 original CSV; no same-host scenario-entry baseline established.

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
| p1024-d1024-c64-n128 | not_run | 0 | 只有跨 Host 历史观测；未建立同机同配置 scenario-entry baseline。 |
| p4096-d1024-c64-n128 | not_run | 0 | 只有跨 Host 历史观测；未建立同机同配置 scenario-entry baseline。 |
| p16384-d1024-c64-n128 | not_run | 0 | 只有跨 Host 历史观测；未建立同机同配置 scenario-entry baseline。 |
| p32768-d1024-c64-n128 | not_run | 0 | 只有跨 Host 历史观测；未建立同机同配置 scenario-entry baseline。 |

吞吐、TTFT、TPOT/ITL、E2E：—。本阶段没有独立 E2E baseline 数值；精度或组件实验与历史观测见原记录及 optimize，不填造数据。
<!-- baseline-record-review:end -->
