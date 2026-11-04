# opt10 端到端优化结果总览

更新日期：2026-10-22。五个完整场景均已归档；今日1K复测已完成4轮并由用户确认稳态。当前生产TP2/GPU6,7；完成性能归档及本轮完整精度评测，源码和服务保持不变。

以下为原CSV的SUMMARY，D1024/C64/N128；1K采用10月22日复测第3–4轮，其余采用10月21日第3–4轮。当前1K稳态已由用户确认；GPQA **130/198=65.66分**（阈值64），ERQA **162/400=40.50分**（阈值40），两项均通过。最终性能验收仍未完成。

| 输入/输出 | 轮数 | 输出 token/s | 总 token/s | 平均 TTFT ms | 平均 TPOT ms | P99 ITL ms |
|---|---:|---:|---:|---:|---:|---:|
| 1K/1K | 4 | 1511.12 | 3022.26 | 1694.59 | 40.68 | 42.18 |
| 4K/1K | 4 | 1082.16 | 5410.82 | 4808.72 | 54.27 | 462.89 |
| 16K/1K | 4 | 374.66 | 6369.18 | 75029.02 | 79.66 | 642.51 |
| 32K/1K | 4 | 175.74 | 5799.26 | 223132.14 | 85.22 | 1006.30 |
| 64K/1K | 4 | 76.44 | 4968.68 | 588038.78 | 92.34 | 1559.34 |

当前1K复测4轮差幅1.45%，用户已确认稳态；旧1K8轮差幅63.49%、4K32.78%的历史证据保留。完整轮次、尾延迟、文件SHA和复测结果见 [records-008-opt10-full-results.md](records-008-opt10-full-results.md)。旧组快轮未单独替代整组；当前1K采用独立完成的新复测。全部吞吐为finite batch端到端指标。

- 今日1K复测已完成4轮，SUMMARY为输出1511.12、总3022.26token/s；全部4轮差幅1.45%，用户明确确认稳态。

<!-- e2e:summary:start -->

- 案例：20261022-qwen3vl-metax-opt10-results
- 当前状态：accuracy-passed;P1K-steady-confirmed;full-performance-acceptance-pending
- 当前候选：Existing production stack: gems-opt + inline G1/G2 MoE + common sampling adapter + local sampling histogram
- 下一步：Accuracy request complete; preserve current service. Full performance acceptance remains separate.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| records-008-opt10-full-results | use-new-completeP1Ksummary-for-current-table;preserve-all-old-rounds | p1024/p4096/p16384/p32768/p65536-d1024-c64-n128 | [records-008-opt10-full-results.md](records-008-opt10-full-results.md) |
| acc-009-gpqa-erqa | both-frozen-thresholds-passed;preserve-current-service | GPQA-Diamond198+ERQA-native-full | [acc-009-gpqa-erqa.md](acc-009-gpqa-erqa.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1024-c64-n128 | user-opt10-historical-wave-summary | request_throughput_rps | 1.29 | req/s | historical20261021sourceSUMMARY; not current steadyP1Kresult |
| p1024-d1024-c64-n128 | user-opt10-historical-wave-summary | output_throughput_tps | 1318.08 | token/s | historical20261021sourceSUMMARY; not current steadyP1Kresult |
| p1024-d1024-c64-n128 | user-opt10-historical-wave-summary | total_throughput_tps | 2636.17 | token/s | historical20261021sourceSUMMARY; not current steadyP1Kresult |
| p1024-d1024-c64-n128 | user-opt10-historical-wave-summary | duration_s | 104.7 | s | historical20261021sourceSUMMARY; not current steadyP1Kresult |
| p1024-d1024-c64-n128 | user-opt10-historical-wave-summary | mean_ttft_ms | 2622.54 | ms | historical20261021sourceSUMMARY; not current steadyP1Kresult |
| p1024-d1024-c64-n128 | user-opt10-historical-wave-summary | p99_ttft_ms | 6582.76 | ms | historical20261021sourceSUMMARY; not current steadyP1Kresult |
| p1024-d1024-c64-n128 | user-opt10-historical-wave-summary | mean_tpot_ms | 45.37 | ms | historical20261021sourceSUMMARY; not current steadyP1Kresult |
| p1024-d1024-c64-n128 | user-opt10-historical-wave-summary | p99_tpot_ms | 53.05 | ms | historical20261021sourceSUMMARY; not current steadyP1Kresult |
| p1024-d1024-c64-n128 | user-opt10-historical-wave-summary | median_itl_ms | 38.68 | ms | historical20261021sourceSUMMARY; not current steadyP1Kresult |
| p1024-d1024-c64-n128 | user-opt10-historical-wave-summary | p99_itl_ms | 42.38 | ms | historical20261021sourceSUMMARY; not current steadyP1Kresult |
| p4096-d1024-c64-n128 | user-opt10-CSV-summary | request_throughput_rps | 1.06 | req/s | source-SUMMARY;human-import;steady-admission-unproven |
| p4096-d1024-c64-n128 | user-opt10-CSV-summary | output_throughput_tps | 1082.16 | token/s | source-SUMMARY;human-import;steady-admission-unproven |
| p4096-d1024-c64-n128 | user-opt10-CSV-summary | total_throughput_tps | 5410.82 | token/s | source-SUMMARY;human-import;steady-admission-unproven |
| p4096-d1024-c64-n128 | user-opt10-CSV-summary | duration_s | 121.12 | s | source-SUMMARY;human-import;steady-admission-unproven |
| p4096-d1024-c64-n128 | user-opt10-CSV-summary | mean_ttft_ms | 4808.72 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p4096-d1024-c64-n128 | user-opt10-CSV-summary | p99_ttft_ms | 14751.95 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p4096-d1024-c64-n128 | user-opt10-CSV-summary | mean_tpot_ms | 54.27 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p4096-d1024-c64-n128 | user-opt10-CSV-summary | p99_tpot_ms | 58.21 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p4096-d1024-c64-n128 | user-opt10-CSV-summary | median_itl_ms | 45.58 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p4096-d1024-c64-n128 | user-opt10-CSV-summary | p99_itl_ms | 462.89 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p16384-d1024-c64-n128 | user-opt10-CSV-summary | request_throughput_rps | 0.36 | req/s | source-SUMMARY;human-import;steady-admission-unproven |
| p16384-d1024-c64-n128 | user-opt10-CSV-summary | output_throughput_tps | 374.66 | token/s | source-SUMMARY;human-import;steady-admission-unproven |
| p16384-d1024-c64-n128 | user-opt10-CSV-summary | total_throughput_tps | 6369.18 | token/s | source-SUMMARY;human-import;steady-admission-unproven |
| p16384-d1024-c64-n128 | user-opt10-CSV-summary | duration_s | 349.85 | s | source-SUMMARY;human-import;steady-admission-unproven |
| p16384-d1024-c64-n128 | user-opt10-CSV-summary | mean_ttft_ms | 75029.02 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p16384-d1024-c64-n128 | user-opt10-CSV-summary | p99_ttft_ms | 125121.55 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p16384-d1024-c64-n128 | user-opt10-CSV-summary | mean_tpot_ms | 79.66 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p16384-d1024-c64-n128 | user-opt10-CSV-summary | p99_tpot_ms | 109.12 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p16384-d1024-c64-n128 | user-opt10-CSV-summary | median_itl_ms | 49.52 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p16384-d1024-c64-n128 | user-opt10-CSV-summary | p99_itl_ms | 642.51 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p32768-d1024-c64-n128 | user-opt10-CSV-summary | request_throughput_rps | 0.17 | req/s | source-SUMMARY;human-import;steady-admission-unproven |
| p32768-d1024-c64-n128 | user-opt10-CSV-summary | output_throughput_tps | 175.74 | token/s | source-SUMMARY;human-import;steady-admission-unproven |
| p32768-d1024-c64-n128 | user-opt10-CSV-summary | total_throughput_tps | 5799.26 | token/s | source-SUMMARY;human-import;steady-admission-unproven |
| p32768-d1024-c64-n128 | user-opt10-CSV-summary | duration_s | 745.85 | s | source-SUMMARY;human-import;steady-admission-unproven |
| p32768-d1024-c64-n128 | user-opt10-CSV-summary | mean_ttft_ms | 223132.14 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p32768-d1024-c64-n128 | user-opt10-CSV-summary | p99_ttft_ms | 326359.34 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p32768-d1024-c64-n128 | user-opt10-CSV-summary | mean_tpot_ms | 85.22 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p32768-d1024-c64-n128 | user-opt10-CSV-summary | p99_tpot_ms | 117.06 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p32768-d1024-c64-n128 | user-opt10-CSV-summary | median_itl_ms | 40.91 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p32768-d1024-c64-n128 | user-opt10-CSV-summary | p99_itl_ms | 1006.3 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p65536-d1024-c64-n128 | user-opt10-CSV-summary | request_throughput_rps | 0.07 | req/s | source-SUMMARY;human-import;steady-admission-unproven |
| p65536-d1024-c64-n128 | user-opt10-CSV-summary | output_throughput_tps | 76.44 | token/s | source-SUMMARY;human-import;steady-admission-unproven |
| p65536-d1024-c64-n128 | user-opt10-CSV-summary | total_throughput_tps | 4968.68 | token/s | source-SUMMARY;human-import;steady-admission-unproven |
| p65536-d1024-c64-n128 | user-opt10-CSV-summary | duration_s | 1714.67 | s | source-SUMMARY;human-import;steady-admission-unproven |
| p65536-d1024-c64-n128 | user-opt10-CSV-summary | mean_ttft_ms | 588038.78 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p65536-d1024-c64-n128 | user-opt10-CSV-summary | p99_ttft_ms | 811156.53 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p65536-d1024-c64-n128 | user-opt10-CSV-summary | mean_tpot_ms | 92.34 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p65536-d1024-c64-n128 | user-opt10-CSV-summary | p99_tpot_ms | 96.17 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p65536-d1024-c64-n128 | user-opt10-CSV-summary | median_itl_ms | 36.39 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p65536-d1024-c64-n128 | user-opt10-CSV-summary | p99_itl_ms | 1559.34 | ms | source-SUMMARY;human-import;steady-admission-unproven |
| p1024-d1024-c64-n128 | user-opt10-steady-P1K-summary | request_throughput_rps | 1.48 | req/s | 20261022user-confirmedsteady;4completedrounds;sourceSUMMARYlast2 |
| p1024-d1024-c64-n128 | user-opt10-steady-P1K-summary | output_throughput_tps | 1511.12 | token/s | 20261022user-confirmedsteady;4completedrounds;sourceSUMMARYlast2 |
| p1024-d1024-c64-n128 | user-opt10-steady-P1K-summary | total_throughput_tps | 3022.26 | token/s | 20261022user-confirmedsteady;4completedrounds;sourceSUMMARYlast2 |
| p1024-d1024-c64-n128 | user-opt10-steady-P1K-summary | duration_s | 86.74 | s | 20261022user-confirmedsteady;4completedrounds;sourceSUMMARYlast2 |
| p1024-d1024-c64-n128 | user-opt10-steady-P1K-summary | mean_ttft_ms | 1694.59 | ms | 20261022user-confirmedsteady;4completedrounds;sourceSUMMARYlast2 |
| p1024-d1024-c64-n128 | user-opt10-steady-P1K-summary | p99_ttft_ms | 3582.65 | ms | 20261022user-confirmedsteady;4completedrounds;sourceSUMMARYlast2 |
| p1024-d1024-c64-n128 | user-opt10-steady-P1K-summary | mean_tpot_ms | 40.68 | ms | 20261022user-confirmedsteady;4completedrounds;sourceSUMMARYlast2 |
| p1024-d1024-c64-n128 | user-opt10-steady-P1K-summary | p99_tpot_ms | 41.82 | ms | 20261022user-confirmedsteady;4completedrounds;sourceSUMMARYlast2 |
| p1024-d1024-c64-n128 | user-opt10-steady-P1K-summary | median_itl_ms | 38.8 | ms | 20261022user-confirmedsteady;4completedrounds;sourceSUMMARYlast2 |
| p1024-d1024-c64-n128 | user-opt10-steady-P1K-summary | p99_itl_ms | 42.18 | ms | 20261022user-confirmedsteady;4completedrounds;sourceSUMMARYlast2 |
| GPQA | accuracy-acc-009 | accuracy_score | 65.65656565656566 | percent | current prefix-cache-enabled production service; full dataset |
| ERQA | accuracy-acc-009 | accuracy_score | 40.5 | percent | current prefix-cache-enabled production service; full dataset |

<!-- e2e:summary:end -->
