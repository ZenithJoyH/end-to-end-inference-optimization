# 当前env031独立性能基线

当前状态：原版本无profiler三阶段各9轮均完成，前后服务/源码/权重清单/tokenizer身份及原生证据校验通过。B/C/R终态已完成，详见[优化比较](../optimize/README.md)：Prefill/Mixed passed，Decode TTFT spread incomplete。下面仅保留原版本基线事实；完整C64父场景未运行。

| 正式目标 | 状态 | 吞吐 / TTFT / TPOT / E2E |
|---|---|---|
| P1024/D1024/C64/N128 | not_run，当前目标 | — |
| P4096/D1024/C64/N128 | not_run | — |
| P16384/D1024/C64/N128 | not_run | — |
| P32768/D1024/C64/N128 | not_run | — |

将先按相同规则运行PrefillP1024D1C8N8、DecodeP128D128C8N8和MixedP1024D128C8N8；每项6预热+3测量，预热末3轮吞吐相对spread<=15%。全部已准入测量轮保留，失败/不稳定记incomplete。随后用相同计划测候选/回退，不跨workload计算收益。

外部证据根：`/workspace/.hy4-preview-migration-20261018-01/perf-20261021-01`。原adaptation acc006精度92.42%通过；本性能服务的完整精度gate待候选冻结后生成，不能套用旧实例。

<!-- e2e:summary:start -->

- 案例：20261021-hy4-preview-ppu03-e2e
- 当前状态：completed_frozen_baseline
- 当前候选：env031-FGV45e14232-batched2048
- 下一步：Refer optimize/fw-001.md for completed B/C/R; fixed four formal targets remainnotrun.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| scout-p1024-d1-c8-n8 | baseline | output_throughput | 0.09171123676562414 | token/s | diagnostic targeted milestone; passed |
| scout-p1024-d1-c8-n8 | baseline | total_token_throughput | 94.00401768476475 | token/s | diagnostic targeted milestone; passed |
| scout-p1024-d1-c8-n8 | baseline | mean_ttft_ms | 53344.21521250624 | ms | diagnostic targeted milestone; passed |
| scout-p1024-d1-c8-n8 | baseline | mean_e2el_ms | 53344.21497920994 | ms | diagnostic targeted milestone; passed |
| scout-p128-d128-c8-n8 | baseline | output_throughput | 44.6016774023528 | token/s | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | baseline | total_token_throughput | 89.2033548047056 | token/s | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | baseline | mean_ttft_ms | 8789.069547434337 | ms | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | baseline | mean_tpot_ms | 111.08593440405643 | ms | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | baseline | mean_itl_ms | 111.08593563787551 | ms | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | baseline | mean_e2el_ms | 22922.00695676729 | ms | diagnostic targeted milestone; incomplete |
| scout-p1024-d128-c8-n8 | baseline | output_throughput | 10.211998833787057 | token/s | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | baseline | total_token_throughput | 91.90798950408352 | token/s | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | baseline | mean_ttft_ms | 59557.19456530642 | ms | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | baseline | mean_tpot_ms | 319.30519125101665 | ms | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | baseline | mean_itl_ms | 319.3051937305713 | ms | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | baseline | mean_e2el_ms | 100098.61227648798 | ms | diagnostic targeted milestone; passed |

<!-- e2e:summary:end -->

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
