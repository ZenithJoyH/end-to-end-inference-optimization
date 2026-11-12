# 20261104-qwen3vl-opt16-performance-gap / baseline

<!-- e2e:summary:start -->

- 案例：20261104-qwen3vl-opt16-performance-gap
- 当前状态：incomplete
- 当前候选：—
- 下一步：After current user matrix ends, design same-device steady-state comparison; no new baseline run.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1024-c64-n128 | opt15_historical_unbound | total_throughput | 3181.19 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p1024-d1024-c64-n128 | opt15_historical_unbound | output_throughput | 1590.6 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p1024-d1024-c64-n128 | opt15_historical_unbound | TTFT_mean | 1626.23 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p1024-d1024-c64-n128 | opt15_historical_unbound | TPOT_mean | 38.63 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p1024-d1024-c64-n128 | opt15_historical_unbound | ITL_median | 37.03 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p1024-d1024-c64-n128 | opt15_historical_unbound | duration | 82.41 | s | existing CSV last-two summary; observational, not new controlled measurement |
| p4096-d1024-c64-n128 | opt15_historical_unbound | total_throughput | 5621.01 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p4096-d1024-c64-n128 | opt15_historical_unbound | output_throughput | 1124.2 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p4096-d1024-c64-n128 | opt15_historical_unbound | TTFT_mean | 4737.52 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p4096-d1024-c64-n128 | opt15_historical_unbound | TPOT_mean | 52.14 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p4096-d1024-c64-n128 | opt15_historical_unbound | ITL_median | 43.19 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p4096-d1024-c64-n128 | opt15_historical_unbound | duration | 116.59 | s | existing CSV last-two summary; observational, not new controlled measurement |
| p16384-d1024-c64-n128 | opt15_historical_unbound | total_throughput | 6499.96 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p16384-d1024-c64-n128 | opt15_historical_unbound | output_throughput | 382.35 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p16384-d1024-c64-n128 | opt15_historical_unbound | TTFT_mean | 73664.12 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p16384-d1024-c64-n128 | opt15_historical_unbound | TPOT_mean | 77.93 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p16384-d1024-c64-n128 | opt15_historical_unbound | ITL_median | 47.75 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p16384-d1024-c64-n128 | opt15_historical_unbound | duration | 342.81 | s | existing CSV last-two summary; observational, not new controlled measurement |
| p32768-d1024-c64-n128 | opt15_historical_unbound | total_throughput | 6013.93 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p32768-d1024-c64-n128 | opt15_historical_unbound | output_throughput | 182.24 | token/s | existing CSV last-two summary; observational, not new controlled measurement |
| p32768-d1024-c64-n128 | opt15_historical_unbound | TTFT_mean | 215246.07 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p32768-d1024-c64-n128 | opt15_historical_unbound | TPOT_mean | 82.0 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p32768-d1024-c64-n128 | opt15_historical_unbound | ITL_median | 38.09 | ms | existing CSV last-two summary; observational, not new controlled measurement |
| p32768-d1024-c64-n128 | opt15_historical_unbound | duration | 719.23 | s | existing CSV last-two summary; observational, not new controlled measurement |

<!-- e2e:summary:end -->

仅导入历史CSV观察，未建立同机anchor。正式四场景均未新测；不能将历史opt15视为已绑定当前设备的baseline。
