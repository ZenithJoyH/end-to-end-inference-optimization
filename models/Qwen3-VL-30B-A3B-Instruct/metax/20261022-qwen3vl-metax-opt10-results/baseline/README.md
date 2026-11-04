# 基线状态

本案例仅导入生产GPU6/7的opt10结果，没有新建性能服务或采集未优化anchor。四个标准场景的同配置anchor均为not_run；不能计算当前组合的累计加速比。

此前GPU0/1受控P1K B/C/R和完整采样预热证据保留在[父案例](../../20261021-qwen3vl-metax-p1k-opt9/baseline/README.md)，不直接充当此处生产GPU6/7的对照。

当前组合五场景人工观测及全部指标见[优化总览](../optimize/README.md)。

<!-- baseline-record-review:start -->
## 正式目标覆盖与历史测量

本节是记录审查：原测量状态与角色保持不变，不是新评测回执。`incomplete` 表示此表未闭合正式基线证据；历史、缩减或有观察器的结果须按原范围解释。

| 正式目标 | 正式基线证据状态 | 已记录指标数 | 边界 |
|---|---|---:|---|
| p1024-d1024-c64-n128 | not_run | 0 | 原字段 formal_scenarios 的四项 anchor_status 均为 not_run；opt10 CSV 为已优化快照观测。 |
| p4096-d1024-c64-n128 | not_run | 0 | 原字段 formal_scenarios 的四项 anchor_status 均为 not_run；opt10 CSV 为已优化快照观测。 |
| p16384-d1024-c64-n128 | not_run | 0 | 原字段 formal_scenarios 的四项 anchor_status 均为 not_run；opt10 CSV 为已优化快照观测。 |
| p32768-d1024-c64-n128 | not_run | 0 | 原字段 formal_scenarios 的四项 anchor_status 均为 not_run；opt10 CSV 为已优化快照观测。 |

吞吐、TTFT、TPOT/ITL、E2E：—。本阶段没有独立 E2E baseline 数值；精度或组件实验与历史观测见原记录及 optimize，不填造数据。
<!-- baseline-record-review:end -->
