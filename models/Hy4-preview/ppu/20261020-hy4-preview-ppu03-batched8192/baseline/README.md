# 20261020-hy4-preview-ppu03-batched8192 / baseline

<!-- e2e:summary:start -->

- 案例：20261020-hy4-preview-ppu03-batched8192
- 当前状态：archived_prefill_mixed_valid_decode_warmup_incomplete
- 当前候选：env031-baseline2048-historical-measurements
- 下一步：Baseline evidence preserved; no further measurement running

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| scout-p1024-d128-c8-n8 | baseline2048 | output_throughput | 10.2022328999442 | token/s | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p1024-d128-c8-n8 | baseline2048 | mean_ttft_ms | 59579.14058980532 | ms | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p1024-d128-c8-n8 | baseline2048 | mean_tpot_ms | 319.80725685198695 | ms | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p1024-d128-c8-n8 | baseline2048 | mean_itl_ms | 319.80725939112426 | ms | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p1024-d128-c8-n8 | baseline2048 | mean_e2el_ms | 100194.66221000766 | ms | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p1024-d1-c8-n8 | baseline2048 | output_throughput | 0.09370177158729455 | token/s | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p1024-d1-c8-n8 | baseline2048 | mean_ttft_ms | 52135.89774345746 | ms | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p1024-d1-c8-n8 | baseline2048 | mean_e2el_ms | 52135.89748938102 | ms | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p1024-d1-c8-n8 | baseline2048 | input_throughput | 95.95061410538963 | token/s | P1024 D1 C8 N8;clientphase proxy |
| scout-p128-d128-c8-n8 | baseline2048 | output_throughput | — | token/s | incomplete:4warmupfailedstability;0measured |

<!-- e2e:summary:end -->

Decode固定4轮预热未稳定，末两轮21.409/44.812 token/s，spread70.68%，无measured。Prefill/Mixed为各自独立缩减plan，原生结果通过且完整保留；四原始D1K/C64/N128场景均not_run。TTFT/TPOT是客户端代理，含调度/网络/残余另一阶段。

| 正式目标（均非本轮缩减探针） | 状态 |
|---|---|
| P1024/D1024/C64/N128 | not_run |
| P4096/D1024/C64/N128 | not_run |
| P16384/D1024/C64/N128 | not_run |
| P32768/D1024/C64/N128 | not_run |

<!-- baseline-record-review:start -->
## 正式目标覆盖与历史测量

本节是记录审查：原测量状态与角色保持不变，不是新评测回执。`incomplete` 表示此表未闭合正式基线证据；历史、缩减或有观察器的结果须按原范围解释。

| 正式目标 | 正式基线证据状态 | 已记录指标数 | 边界 |
|---|---|---:|---|
| p1024-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p4096-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p16384-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p32768-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |

数值见上方由 `state.yml/metrics` 生成的指标表；每条新增指标保留 source_pointer，外部原件按原 evidence 查阅。
<!-- baseline-record-review:end -->
