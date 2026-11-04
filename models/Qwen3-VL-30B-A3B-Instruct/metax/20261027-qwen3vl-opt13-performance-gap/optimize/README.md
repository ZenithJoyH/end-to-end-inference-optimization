# 20261027-qwen3vl-opt13-performance-gap / optimize

<!-- e2e:summary:start -->

- 案例：20261027-qwen3vl-opt13-performance-gap
- 当前状态：PR638-reverted-on-disk
- 当前候选：024plugin-opt-original-FLA-default-split0;other-optimizations-preserved
- 下一步：User next model start loads reverted FLA; no automatic restart or performance/accuracy measurement. Historical opt13 observations remain tied to old source.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| diag-001-opt13-gap | causal-attribution-incomplete | p1024/p4096/p16384-d1024-c64-n128 | [diag-001-opt13-gap.md](diag-001-opt13-gap.md) |
| op-002-revert-pr638 | reverted-PR638-per-user | all-existing-scenarios;disk-rollback-only | [op-002-revert-pr638.md](op-002-revert-pr638.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1024-c64-n128 | historical-opt10 | total | 3022.26 | tok/s | original SUMMARY Run3/4; cross-host observation |
| p1024-d1024-c64-n128 | existing-opt13 | total | 2316.93 | tok/s | original SUMMARY Run3/4; cross-host observation |
| p1024-d1024-c64-n128 | historical-opt10 | output | 1511.12 | tok/s | original SUMMARY Run3/4; cross-host observation |
| p1024-d1024-c64-n128 | existing-opt13 | output | 1158.46 | tok/s | original SUMMARY Run3/4; cross-host observation |
| p1024-d1024-c64-n128 | historical-opt10 | ttft | 1694.59 | ms | original SUMMARY Run3/4; cross-host observation |
| p1024-d1024-c64-n128 | existing-opt13 | ttft | 2940.14 | ms | original SUMMARY Run3/4; cross-host observation |
| p1024-d1024-c64-n128 | historical-opt10 | tpot | 40.68 | ms | original SUMMARY Run3/4; cross-host observation |
| p1024-d1024-c64-n128 | existing-opt13 | tpot | 45.67 | ms | original SUMMARY Run3/4; cross-host observation |
| p1024-d1024-c64-n128 | historical-opt10 | median_itl | 38.8 | ms | original SUMMARY Run3/4; cross-host observation |
| p1024-d1024-c64-n128 | existing-opt13 | median_itl | 36.92 | ms | original SUMMARY Run3/4; cross-host observation |
| p1024-d1024-c64-n128 | historical-opt10 | p99_itl | 42.18 | ms | original SUMMARY Run3/4; cross-host observation |
| p1024-d1024-c64-n128 | existing-opt13 | p99_itl | 40.08 | ms | original SUMMARY Run3/4; cross-host observation |
| p4096-d1024-c64-n128 | historical-opt10 | total | 5410.82 | tok/s | original SUMMARY Run3/4; cross-host observation |
| p4096-d1024-c64-n128 | existing-opt13 | total | 5516.31 | tok/s | original SUMMARY Run3/4; cross-host observation |
| p4096-d1024-c64-n128 | historical-opt10 | output | 1082.16 | tok/s | original SUMMARY Run3/4; cross-host observation |
| p4096-d1024-c64-n128 | existing-opt13 | output | 1103.26 | tok/s | original SUMMARY Run3/4; cross-host observation |
| p4096-d1024-c64-n128 | historical-opt10 | ttft | 4808.72 | ms | original SUMMARY Run3/4; cross-host observation |
| p4096-d1024-c64-n128 | existing-opt13 | ttft | 5057.44 | ms | original SUMMARY Run3/4; cross-host observation |
| p4096-d1024-c64-n128 | historical-opt10 | tpot | 54.27 | ms | original SUMMARY Run3/4; cross-host observation |
| p4096-d1024-c64-n128 | existing-opt13 | tpot | 52.91 | ms | original SUMMARY Run3/4; cross-host observation |
| p4096-d1024-c64-n128 | historical-opt10 | median_itl | 45.58 | ms | original SUMMARY Run3/4; cross-host observation |
| p4096-d1024-c64-n128 | existing-opt13 | median_itl | 42.96 | ms | original SUMMARY Run3/4; cross-host observation |
| p4096-d1024-c64-n128 | historical-opt10 | p99_itl | 462.89 | ms | original SUMMARY Run3/4; cross-host observation |
| p4096-d1024-c64-n128 | existing-opt13 | p99_itl | 461.39 | ms | original SUMMARY Run3/4; cross-host observation |
| p16384-d1024-c64-n128 | historical-opt10 | total | 6369.18 | tok/s | original SUMMARY Run3/4; cross-host observation |
| p16384-d1024-c64-n128 | existing-opt13 | total | 4804.64 | tok/s | original SUMMARY Run3/4; cross-host observation |
| p16384-d1024-c64-n128 | historical-opt10 | output | 374.66 | tok/s | original SUMMARY Run3/4; cross-host observation |
| p16384-d1024-c64-n128 | existing-opt13 | output | 282.62 | tok/s | original SUMMARY Run3/4; cross-host observation |
| p16384-d1024-c64-n128 | historical-opt10 | ttft | 75029.02 | ms | original SUMMARY Run3/4; cross-host observation |
| p16384-d1024-c64-n128 | existing-opt13 | ttft | 105108.36 | ms | original SUMMARY Run3/4; cross-host observation |
| p16384-d1024-c64-n128 | historical-opt10 | tpot | 79.66 | ms | original SUMMARY Run3/4; cross-host observation |
| p16384-d1024-c64-n128 | existing-opt13 | tpot | 102.88 | ms | original SUMMARY Run3/4; cross-host observation |
| p16384-d1024-c64-n128 | historical-opt10 | median_itl | 49.52 | ms | original SUMMARY Run3/4; cross-host observation |
| p16384-d1024-c64-n128 | existing-opt13 | median_itl | 48.31 | ms | original SUMMARY Run3/4; cross-host observation |
| p16384-d1024-c64-n128 | historical-opt10 | p99_itl | 642.51 | ms | original SUMMARY Run3/4; cross-host observation |
| p16384-d1024-c64-n128 | existing-opt13 | p99_itl | 1432.66 | ms | original SUMMARY Run3/4; cross-host observation |

<!-- e2e:summary:end -->
