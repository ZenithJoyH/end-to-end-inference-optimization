# Baseline scope

Effective production source was snapshotted into a new isolated container; image lineage and identical mount mappings passed. Private original repository fingerprints match before any candidate change.

On idle GPU0/1, original MoE passed18/18 BF16/FP16 numerical/resource cases,14captures and28changed-input/routing replays. This is a numerical/graph baseline, not an E2E performance baseline. Candidate failed the resource gate before any model service or benchmark promotion, so E2E baseline/candidate/revert throughput remains not_run.

See ../optimize/op-001-upstream977-no943.md and structured state for source identity and remote evidence. Production GPU6/7 service is unchanged.

<!-- baseline-record-review:start -->
## 正式目标覆盖与历史测量

本节是记录审查：原测量状态与角色保持不变，不是新评测回执。`incomplete` 表示此表未闭合正式基线证据；历史、缩减或有观察器的结果须按原范围解释。

| 正式目标 | 正式基线证据状态 | 已记录指标数 | 边界 |
|---|---|---:|---|
| p1024-d1024-c64-n128 | not_run | 0 | 组件 numeric/graph 检查；current.status 明确 E2E-not-run。 |
| p4096-d1024-c64-n128 | not_run | 0 | 组件 numeric/graph 检查；current.status 明确 E2E-not-run。 |
| p16384-d1024-c64-n128 | not_run | 0 | 组件 numeric/graph 检查；current.status 明确 E2E-not-run。 |
| p32768-d1024-c64-n128 | not_run | 0 | 组件 numeric/graph 检查；current.status 明确 E2E-not-run。 |

吞吐、TTFT、TPOT/ITL、E2E：—。本阶段没有独立 E2E baseline 数值；精度或组件实验与历史观测见原记录及 optimize，不填造数据。
<!-- baseline-record-review:end -->
