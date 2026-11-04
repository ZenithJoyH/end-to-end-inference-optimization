# 20261023-qwen3vl-metax-mx104-migration / baseline

<!-- e2e:summary:start -->

- 案例：20261023-qwen3vl-metax-mx104-migration
- 当前状态：targeted-baselines-complete
- 当前候选：Exact stopped mx-59 qwen3vl-pr977-20261022 writable-layer snapshot; scalar num_splits1, prefix cache ON, sampling/gems-opt/MoE unchanged
- 下一步：Preserve two independent split0 baselines for this exact scope; new expanded workload requires matching new baseline.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1024-c64-n128 | baseline | output_throughput | 1599.3521083554203 | token/s | targeted/performance_only;median of process medians,all rounds retained |
| p1024-d1024-c64-n128 | baseline | total_token_throughput | 3198.7042167108407 | token/s | targeted/performance_only;median of process medians,all rounds retained |
| p1024-d1024-c64-n128 | baseline | mean_ttft_ms | 1661.4832275736262 | ms | targeted/performance_only;median of process medians,all rounds retained |
| p1024-d1024-c64-n128 | baseline | mean_tpot_ms | 38.379025382303794 | ms | targeted/performance_only;median of process medians,all rounds retained |
| p65536-d128-c8-n16-kv-sentinel | baseline | output_throughput | 13.961980791378382 | token/s | targeted/performance_only;median of process medians,all rounds retained |
| p65536-d128-c8-n16-kv-sentinel | baseline | total_token_throughput | 7162.49614597711 | token/s | targeted/performance_only;median of process medians,all rounds retained |
| p65536-d128-c8-n16-kv-sentinel | baseline | mean_ttft_ms | 28216.505092161242 | ms | targeted/performance_only;median of process medians,all rounds retained |
| p65536-d128-c8-n16-kv-sentinel | baseline | mean_tpot_ms | 353.0850218353229 | ms | targeted/performance_only;median of process medians,all rounds retained |

<!-- e2e:summary:end -->

<!-- baseline-record-review:start -->
## 正式目标覆盖与历史测量

本节是记录审查：原测量状态与角色保持不变，不是新评测回执。`incomplete` 表示此表未闭合正式基线证据；历史、缩减或有观察器的结果须按原范围解释。

| 正式目标 | 正式基线证据状态 | 已记录指标数 | 边界 |
|---|---|---:|---|
| p1024-d1024-c64-n128 | incomplete | 4 | 已列出原始观测；是否满足正式基线契约仍以原回执和稳态/身份条件为准。 |
| p4096-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p16384-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p32768-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |

数值见上方由 `state.yml/metrics` 生成的指标表；每条新增指标保留 source_pointer，外部原件按原 evidence 查阅。
<!-- baseline-record-review:end -->
