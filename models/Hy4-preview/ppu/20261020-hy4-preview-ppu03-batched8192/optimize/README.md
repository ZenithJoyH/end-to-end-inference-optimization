# 20261020-hy4-preview-ppu03-batched8192 / optimize

<!-- e2e:summary:start -->

- 案例：20261020-hy4-preview-ppu03-batched8192
- 当前状态：completed_8192_rejected_original2048_restored
- 当前候选：env031-original2048-prefixenabled-source8010
- 下一步：No auto nexttrial;profiling proposed only;fullaccuracy/formal4scenario notrun

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| fw-002 | not_retained_no_primary_gain_and_TTFT_guard_failure | scout-p1024-d128-c8-n8 | [fw-002.md](fw-002.md) |

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
| scout-p128-d128-c8-n8 | candidate8192 | output_throughput | 44.39107260181002 | token/s | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p128-d128-c8-n8 | candidate8192 | mean_ttft_ms | 8864.555848063901 | ms | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p128-d128-c8-n8 | candidate8192 | mean_tpot_ms | 111.54528903109426 | ms | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p128-d128-c8-n8 | candidate8192 | mean_itl_ms | 111.54529057199312 | ms | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p128-d128-c8-n8 | candidate8192 | mean_e2el_ms | 23030.80755501287 | ms | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p1024-d128-c8-n8 | candidate8192 | output_throughput | 10.174575157755502 | token/s | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p1024-d128-c8-n8 | candidate8192 | mean_ttft_ms | 77515.81860985607 | ms | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p1024-d128-c8-n8 | candidate8192 | mean_tpot_ms | 181.88087859165333 | ms | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p1024-d128-c8-n8 | candidate8192 | mean_itl_ms | 181.88088137049624 | ms | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p1024-d128-c8-n8 | candidate8192 | mean_e2el_ms | 100614.69019099604 | ms | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p1024-d1-c8-n8 | candidate8192 | output_throughput | 0.09098368963675235 | token/s | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p1024-d1-c8-n8 | candidate8192 | mean_ttft_ms | 78319.13344975328 | ms | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p1024-d1-c8-n8 | candidate8192 | mean_e2el_ms | 78319.13326354697 | ms | targeted finite_batch C8 N8 prefixdisabled env031;2admittedmeasured |
| scout-p1024-d1-c8-n8 | candidate8192 | input_throughput | 93.16729818803441 | token/s | P1024 D1 C8 N8;clientphase proxy |
| scout-p128-d128-c8-n8 | baseline2048 | output_throughput | — | token/s | incomplete:4warmupfailedstability;0measured |

<!-- e2e:summary:end -->

唯一变量为CLI2048→8192。当前Prefill/Mixed基线有效，Decode预热不稳，整体性能证据仍incomplete；完整GPQA和正式四场景均未执行。用户显式指定8192方向，后续不自动追加其他参数或源码优化。

新版FGV45e/env031同anchor，唯一变量CLI max_num_batched_tokens2048→8192，TP16/FULL_AND_PIECEWISE/10桶/GPU.85/100K固定，性能prefix关闭，所有admitted测量轮保留。

| 缩减场景/指标 | 2048 | 8192 |
|---|---:|---:|
| Prefill P1024/D1/C8/N8输入吞吐 | 95.95token/s | 93.17token/s |
| Prefill平均TTFT | 52.14s | 78.32s |
| Mixed P1024/D128/C8/N8输出吞吐 | 10.2022token/s | 10.1746token/s |
| Mixed平均TTFT | 59.58s | 77.52s |
| Mixed平均TPOT | 319.81ms | 181.88ms |
| Mixed平均E2E | 100.19s | 100.61s |
| Decode P128/D128/C8/N8输出吞吐 | —（预热未稳） | 44.39token/s |
| GPU KV容量（startup日志口径） | 347152tokens | 308701tokens |

8192 Mixed吞吐未提高（观察-0.27%），TTFT增加30.11%，TPOT降低43.13%，总延迟基本不变（+.42%）；Prefill吞吐-2.90%、TTFT+50.22%。两项延迟的反向变化不能当作净吞吐收益。整段Prefill探针含预热同32768输入/32输出，原生迭代20→8，证明批处理组织改变；CPU/具体kernel瓶颈未由trace定位。

按预设未达5%主指标收益/TTFT守护越界停止，不保留8192、不追加独立revert，维护比较器真实incomplete；Decode基线4warmup未稳定（70.68%），无measured，不以候选单独通过补齐参考。以上为有界同plan A/B观察，非完整因果/正式验收。四原始D1K/C64/N128场景和完整198题GPQA均not_run。

plan-001：当前无累计性能收益，已恢复原2048；旧FGV下512记录独立。下一轮建议先定位CPU/device/rank的Prefill/Mixed开销，具体算子热点未知，不自动启动新实验。当前原服务恢复及归档见[state.yml](state.yml)。
