# 20261024-qwen3vl-metax-fixed-splits / baseline

<!-- e2e:summary:start -->

- 案例：20261024-qwen3vl-metax-fixed-splits
- 当前状态：preparing-independent-validation
- 当前候选：Fixed explicit native KV-cache splits2/4/8/16 vs reference1; not yet applied
- 下一步：Clone exact source without pausing it, verify image/mount/content/import parity; component minimal-regression before any model patch or GPQA

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
| p1024-d1024-c64-n128 | not_run | 0 | split 数值与精度有限验证；无性能控制器或正式基线。 |
| p4096-d1024-c64-n128 | not_run | 0 | split 数值与精度有限验证；无性能控制器或正式基线。 |
| p16384-d1024-c64-n128 | not_run | 0 | split 数值与精度有限验证；无性能控制器或正式基线。 |
| p32768-d1024-c64-n128 | not_run | 0 | split 数值与精度有限验证；无性能控制器或正式基线。 |

吞吐、TTFT、TPOT/ITL、E2E：—。本阶段没有独立 E2E baseline 数值；精度或组件实验与历史观测见原记录及 optimize，不填造数据。
<!-- baseline-record-review:end -->
