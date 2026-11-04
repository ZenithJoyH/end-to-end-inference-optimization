# Flash1019 当前环境

本轮仅评测精度；性能baseline不在用户请求范围。服务身份与新Flash权重指纹见[state.yml](state.yml)。

| 性能场景 | 状态 | 吞吐/延迟 |
|---|---|---|
| P1024/D1024/C64/N128 | not_run/out_of_scope | — |
| P4096/D1024/C64/N128 | not_run/out_of_scope | — |
| P16384/D1024/C64/N128 | not_run/out_of_scope | — |
| P32768/D1024/C64/N128 | not_run/out_of_scope | — |

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
