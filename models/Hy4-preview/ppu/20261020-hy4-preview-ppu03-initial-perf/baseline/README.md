# HY4-preview PPU-03 初步稳态基线

独立8011性能服务，env030组合、TP16、FULL_AND_PIECEWISE、batched_tokens2048，prefix cache关闭；Gems固定且clean。运行护栏C8、三阶段16rank各2replay及2×2689-token分页通过，16观察器均已退出。

当前结果只覆盖P1K正式目标的缩减milestone。两轮预热后保留两轮测量，以下为每轮原生指标的中位数。

| 阶段 / 输入输出 / 并发与请求 | 输入吞吐 | 输出吞吐 | 平均TTFT | 平均TPOT | 状态 |
|---|---:|---:|---:|---:|---|
| Prefill P1024/D1/C8/N8 | 94.61 token/s | 0.0924 token/s | 52.87 s | 不适用D1 | complete，两轮各8/8成功 |
| Decode P128/D128/C8/N8 | — | 21.46 / 44.94 token/s | 23.57 / 9.66 s | 189.18 / 103.17 ms | 两测量原生有效，spread70.75%，稳态incomplete |
| Mixed P1024/D128/C8/N8 | — | 10.1771 token/s | 59.79 s | 320.07 ms | complete，两轮各8/8成功 |

TTFT包含排队、调度和网络，不能视为设备Prefill时间。Prefill预热吞吐spread0.51%；完整原生回执/root路径见state.yml，SHA b2564b5d00e0948b098f65e45abce30496ce50bca3c17d4718b967b15e73b822。D1哨兵复用维护原生结果/配置验证器和全部输入产物SHA，Mixed比较中的TPOT/ITL守护不适用于D1；未修改冻结计划/契约。

[完整测量契约](../optimize/env-001.md)。四个正式场景均not_run，精度gate未建立；本轮仅performance_only，不跑GPQA。

Mixed warmup末2spread0.60%，测量spread约0.15%；Decode4warmup末2spread0.15%但测量阶段存在共享早期30.83s长停顿，慢轮保留、不得以快轮替换。整体稳态结论incomplete；不能据此给出整体精确加速比。基线前后服务/四仓源码/模型/tokenizer/启动配置锁定passed，service manifest SHA前后均a807ca4ed905f2e86c4bf365e63873aec9b080c4ee83f64ad0861cfa24f1befe；identity-lock SHA df555d53c6891eaf8d9e4fa08ad4339aac98cdd6df25ff47013e774f37cc16c6。

<!-- e2e:summary:start -->

- 案例：20261020-hy4-preview-ppu03-initial-perf
- 当前状态：baseline_facts_archived_overall_decode_incomplete
- 当前候选：env030-source-unchanged
- 下一步：Reuse only matching stable reduced Prefill/Mixed facts; re-establish Decode before any formal performance claim

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| scout-p128-d128-c8-n8 | baseline | output_throughput | 33.19921444475973 | token/s | observed-unsteady |
| scout-p128-d128-c8-n8 | baseline | mean_ttft_ms | 16611.169643118046 | ms | observed-unsteady |
| scout-p128-d128-c8-n8 | baseline | mean_tpot_ms | 146.17504272839113 | ms | observed-unsteady |
| scout-p128-d128-c8-n8 | baseline | mean_e2el_ms | 35175.40006962372 | ms | observed-unsteady |
| scout-p1024-d128-c8-n8 | baseline | output_throughput | 10.177078522622795 | token/s | reduced milestone steady_state |
| scout-p1024-d128-c8-n8 | baseline | mean_ttft_ms | 59794.034089369234 | ms | reduced milestone steady_state |
| scout-p1024-d128-c8-n8 | baseline | mean_tpot_ms | 320.0689241863919 | ms | reduced milestone steady_state |
| scout-p1024-d128-c8-n8 | baseline | mean_e2el_ms | 100442.787461041 | ms | reduced milestone steady_state |
| scout-p1024-d1-c8-n8 | baseline | output_throughput | 0.09239060912793885 | token/s | reduced milestone steady_state |
| scout-p1024-d1-c8-n8 | baseline | mean_ttft_ms | 52869.71296131378 | ms | reduced milestone steady_state |
| scout-p1024-d1-c8-n8 | baseline | mean_e2el_ms | 52869.712739950046 | ms | reduced milestone steady_state |

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
