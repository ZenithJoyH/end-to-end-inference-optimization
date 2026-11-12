# 20261104-qwen3vl-opt16-performance-gap / optimize

<!-- e2e:summary:start -->

- 案例：20261104-qwen3vl-opt16-performance-gap
- 当前状态：incomplete
- 当前候选：existing opt16 unchanged
- 下一步：CPU diagnosis complete; proposed next falsifier is hot same-device P1K with actual sampler shape/dtype warmup after current run naturally ends.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| diag-001-opt16-gap | incomplete | p1024-d1024-c64-n128,p4096-d1024-c64-n128,p16384-d1024-c64-n128,p32768-d1024-c64-n128 | [diag-001-opt16-gap.md](diag-001-opt16-gap.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1024-c64-n128 | opt16_observed | total_throughput | 2061.18 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p1024-d1024-c64-n128 | opt16_observed | output_throughput | 1030.59 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p1024-d1024-c64-n128 | opt16_observed | TTFT_mean | 2688.43 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p1024-d1024-c64-n128 | opt16_observed | TPOT_mean | 49.94 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p1024-d1024-c64-n128 | opt16_observed | ITL_median | 38.8 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p1024-d1024-c64-n128 | opt16_observed | duration | 127.41 | s | existing CSV last-two summary; observational, not new controlled measurement |
| p1024-d1024-c64-n128 | opt15_historical_unbound | total_throughput | 3181.19 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p1024-d1024-c64-n128 | opt15_historical_unbound | output_throughput | 1590.6 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p1024-d1024-c64-n128 | opt15_historical_unbound | TTFT_mean | 1626.23 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p1024-d1024-c64-n128 | opt15_historical_unbound | TPOT_mean | 38.63 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p1024-d1024-c64-n128 | opt15_historical_unbound | ITL_median | 37.03 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p1024-d1024-c64-n128 | opt15_historical_unbound | duration | 82.41 | s | existing CSV last-two summary; observational, not new controlled measurement |
| p4096-d1024-c64-n128 | opt16_observed | total_throughput | 5432.63 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p4096-d1024-c64-n128 | opt16_observed | output_throughput | 1086.53 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p4096-d1024-c64-n128 | opt16_observed | TTFT_mean | 4816.11 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p4096-d1024-c64-n128 | opt16_observed | TPOT_mean | 54.03 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p4096-d1024-c64-n128 | opt16_observed | ITL_median | 45.32 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p4096-d1024-c64-n128 | opt16_observed | duration | 120.63 | s | existing CSV last-two summary; observational, not new controlled measurement |
| p4096-d1024-c64-n128 | opt15_historical_unbound | total_throughput | 5621.01 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p4096-d1024-c64-n128 | opt15_historical_unbound | output_throughput | 1124.2 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p4096-d1024-c64-n128 | opt15_historical_unbound | TTFT_mean | 4737.52 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p4096-d1024-c64-n128 | opt15_historical_unbound | TPOT_mean | 52.14 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p4096-d1024-c64-n128 | opt15_historical_unbound | ITL_median | 43.19 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p4096-d1024-c64-n128 | opt15_historical_unbound | duration | 116.59 | s | existing CSV last-two summary; observational, not new controlled measurement |
| p16384-d1024-c64-n128 | opt16_observed | total_throughput | 6363.5 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p16384-d1024-c64-n128 | opt16_observed | output_throughput | 374.32 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p16384-d1024-c64-n128 | opt16_observed | TTFT_mean | 75051.89 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p16384-d1024-c64-n128 | opt16_observed | TPOT_mean | 79.73 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p16384-d1024-c64-n128 | opt16_observed | ITL_median | 49.91 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p16384-d1024-c64-n128 | opt16_observed | duration | 350.16 | s | existing CSV last-two summary; observational, not new controlled measurement |
| p16384-d1024-c64-n128 | opt15_historical_unbound | total_throughput | 6499.96 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p16384-d1024-c64-n128 | opt15_historical_unbound | output_throughput | 382.35 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p16384-d1024-c64-n128 | opt15_historical_unbound | TTFT_mean | 73664.12 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p16384-d1024-c64-n128 | opt15_historical_unbound | TPOT_mean | 77.93 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p16384-d1024-c64-n128 | opt15_historical_unbound | ITL_median | 47.75 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p16384-d1024-c64-n128 | opt15_historical_unbound | duration | 342.81 | s | existing CSV last-two summary; observational, not new controlled measurement |
| p32768-d1024-c64-n128 | opt16_observed | total_throughput | 5817.9 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p32768-d1024-c64-n128 | opt16_observed | output_throughput | 176.3 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p32768-d1024-c64-n128 | opt16_observed | TTFT_mean | 222514.89 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p32768-d1024-c64-n128 | opt16_observed | TPOT_mean | 84.95 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p32768-d1024-c64-n128 | opt16_observed | ITL_median | 40.98 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p32768-d1024-c64-n128 | opt16_observed | duration | 743.46 | s | existing CSV last-two summary; observational, not new controlled measurement |
| p32768-d1024-c64-n128 | opt15_historical_unbound | total_throughput | 6013.93 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p32768-d1024-c64-n128 | opt15_historical_unbound | output_throughput | 182.24 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p32768-d1024-c64-n128 | opt15_historical_unbound | TTFT_mean | 215246.07 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p32768-d1024-c64-n128 | opt15_historical_unbound | TPOT_mean | 82.0 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p32768-d1024-c64-n128 | opt15_historical_unbound | ITL_median | 38.09 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p32768-d1024-c64-n128 | opt15_historical_unbound | duration | 719.23 | s | existing CSV last-two summary; observational, not new controlled measurement |

<!-- e2e:summary:end -->

| 输入 / D1K C64 N128 | opt15总token/s | opt16总token/s | 变化 | 中位ITL ms |
|---|---:|---:|---:|---:|
| 1K | 3181.19 | 2061.18 | -35.21% | 37.03 → 38.80 |
| 4K | 5621.01 | 5432.63 | -3.35% | 43.19 → 45.32 |
| 16K | 6499.96 | 6363.50 | -2.10% | 47.75 → 49.91 |
| 32K | 6013.93 | 5817.90 | -3.26% | 38.09 → 40.98 |

[只读诊断](diag-001-opt16-gap.md)：P1K长停顿/采样JIT是首要假设；新out-of-place拷贝成本未隔离。P64K待完成。当前服务/benchmark完全未改，无新增请求或性能收益。
