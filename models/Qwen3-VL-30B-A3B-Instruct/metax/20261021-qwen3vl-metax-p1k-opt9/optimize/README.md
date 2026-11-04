补充只读分析：[main.py Flash Attention 对比](analysis-006-main-flash-attention.md)。既有三阶段 trace 实际为原生 mcFlashAttn；库内 FlagGems Triton D128 的策略差异不能直接归为服务瓶颈。候选存在 paged Prefill ABI、Decode 入口、显式 splits 和非因果 ALiBi 兼容问题，尚未 GPU 测试或接入。

算子实测：[op-007 main.py vs 原生](op-007-fa-main-native-micro.md)：18/18数值与graph通过，所有形状原生更快；B64/KV1K为66.20 vs133.75μs，B8/Q1K Prefill为393.71 vs822.39μs。候选未部署，GPU2已释放；仅算子graph设备计时，不是E2E结果。

<!-- e2e:summary:start -->

- 案例：20261021-qwen3vl-metax-p1k-opt9
- 当前状态：opt10-read-only-diagnosis-complete-shape-JIT
- 当前候选：op005 local histogram only;source and private clone patched;op003/op004 excluded
- 下一步：P1K retest complete and userconfirmedsteady; see latestproductionrecord; no new rerun or mutation requested

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| diag-001-p1k-phase-baseline | stop-own-service-and-defer | p1024-d1024-c64-n128 | [diag-001-p1k-phase-baseline.md](diag-001-p1k-phase-baseline.md) |
| analysis-002-p1k-steady-candidates | ranked-not-implemented | p1024-d1024-c64-n128 | [analysis-002-p1k-steady-candidates.md](analysis-002-p1k-steady-candidates.md) |
| op-003-sampling-guard-counts | do-not-promote-pending-live-trace | p1024-d1024-c64-n128 | [op-003-sampling-guard-counts.md](op-003-sampling-guard-counts.md) |
| op-004-sampling-sweep-groups | reject-no-repository-edit | p1024-d1024-c64-n128 | [op-004-sampling-sweep-groups.md](op-004-sampling-sweep-groups.md) |
| op-005-sampling-local-histogram | retained-after-full-P1K-BCR-numerical-graph-audits | p1024-d1024-c64-n128 | [op-005-sampling-local-histogram.md](op-005-sampling-local-histogram.md) |
| diag-006-opt10-throughput-variance | preserve-user-run; require-same-complete-shape-warmup-before-new-comparison | p1024-d1024-c64-n128 | [diag-006-opt10-throughput-variance.md](diag-006-opt10-throughput-variance.md) |
| analysis-006-main-flash-attention | do-not-replace-without-ABI-correctness-and-native-baseline-validation | p1024-d1024-c64-n128 | [analysis-006-main-flash-attention.md](analysis-006-main-flash-attention.md) |
| op-007-fa-main-native-micro | retain-native-for-tested-shapes; no-source-or-service-change | p1024-d1024-c64-n128 | [op-007-fa-main-native-micro.md](op-007-fa-main-native-micro.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1024-c64-n128 | baseline | output_throughput | 1455.101068101872 | token/s | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | baseline | mean_ttft_ms | 1758.8088228767447 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | baseline | p99_ttft_ms | 3577.61412137188 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | baseline | mean_tpot_ms | 42.07523147196639 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | baseline | p99_tpot_ms | 43.10856974846206 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | baseline | median_itl_ms | 39.85620941966772 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | baseline | p99_itl_ms | 44.19904221314937 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | baseline | p99_e2el_ms | 46958.26573625207 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | candidate | output_throughput | 1509.8609154655164 | token/s | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | candidate | mean_ttft_ms | 1820.7766329796868 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | candidate | p99_ttft_ms | 3699.0605820994824 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | candidate | mean_tpot_ms | 40.58342364917887 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | candidate | p99_tpot_ms | 41.92475893670823 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | candidate | median_itl_ms | 38.85574406012893 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | candidate | p99_itl_ms | 42.88781989831476 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | candidate | p99_e2el_ms | 45887.47147148941 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | revert | output_throughput | 1485.0577503651614 | token/s | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | revert | mean_ttft_ms | 1749.6355436232989 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | revert | p99_ttft_ms | 3610.5930262058973 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | revert | mean_tpot_ms | 41.35550200088511 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | revert | p99_tpot_ms | 42.65389736991682 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | revert | median_itl_ms | 39.18532538227737 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | revert | p99_itl_ms | 42.924661072902374 | ms | targeted-performance_only;3warm2measured;roundmedian |
| p1024-d1024-c64-n128 | revert | p99_e2el_ms | 46224.33452210389 | ms | targeted-performance_only;3warm2measured;roundmedian |

<!-- e2e:summary:end -->
