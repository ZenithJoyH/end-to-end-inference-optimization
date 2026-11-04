# 基线事实

PPU-13 的 `minimaxM3` 为新发布镜像容器，原 Plugin HEAD `cafe6363` 且有本地改动。检查时无模型服务，16 卡空闲。原 checkout 保留，不清理工作区。

未运行性能 baseline；四正式场景均为 not_run。本任务仅按用户要求更换 Plugin 并检查推理。

<!-- baseline-record-review:start -->
## 正式目标覆盖与历史测量

本节是记录审查：原测量状态与角色保持不变，不是新评测回执。`incomplete` 表示此表未闭合正式基线证据；历史、缩减或有观察器的结果须按原范围解释。

| 正式目标 | 正式基线证据状态 | 已记录指标数 | 边界 |
|---|---|---:|---|
| p1024-d1024-c64-n128 | not_run | 0 | 框架组件支持；原状态 current.performance=not_run。 |
| p4096-d1024-c64-n128 | not_run | 0 | 框架组件支持；原状态 current.performance=not_run。 |
| p16384-d1024-c64-n128 | not_run | 0 | 框架组件支持；原状态 current.performance=not_run。 |
| p32768-d1024-c64-n128 | not_run | 0 | 框架组件支持；原状态 current.performance=not_run。 |

吞吐、TTFT、TPOT/ITL、E2E：—。本阶段没有独立 E2E baseline 数值；精度或组件实验与历史观测见原记录及 optimize，不填造数据。
<!-- baseline-record-review:end -->
