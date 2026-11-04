# P1K 入口基线

独立容器 qwen3vl-p1k-opt9-20261021，mx-59 GPU0/1，TP2、graph、端口18144。原 opt9 的 sampling、gems-opt、MoE、blacklist 保留。镜像谱系/挂载门禁及最小正确性通过；正式 GPQA 按用户要求暂缓。本表仅性能研究，不是最终四场景验收。

三轮预热后末两轮差幅4.87%，通过8%稳态准入。两轮计时均128/128成功，全部保留，TPS差幅3.17%。下表为两轮指标的中位数，P99非合并请求的分位数。

| 场景 | 状态/范围 | 输出tok/s | 平均TTFT ms | P99 TTFT ms | 平均TPOT ms | 中位ITL ms | P99 ITL ms | P99 E2EL ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| P1024/D1024/C64/N128 | complete/performance_only | 1455.10 | 1758.81 | 3577.61 | 42.08 | 39.86 | 44.20 | 46958.27 |
| P4096/D1024/C64/N128 | not_run/本轮P1K范围外 | — | — | — | — | — | — | — |
| P16384/D1024/C64/N128 | not_run/本轮P1K范围外 | — | — | — | — | — | — | — |
| P32768/D1024/C64/N128 | not_run/本轮P1K范围外 | — | — | — | — | — | — | — |

两轮原值1432.036、1478.166tok/s。运行回执：/public-flash/jinghao/qwen3-VL/20261021-qwen3vl-metax-p1k-opt9/results/performance/hist-target-baseline/run-record.json，SHA96fef861f28799b42585e1aee3ab849aead7d8ff510f1fcf3d42fb04e9bdbb7a。历史opt9 CSV不与本轮计算加速比。阶段trace为诊断，其Profiler-on时间不进入该基线。

<!-- record-metrics:start -->
## 已记录指标（按 state.yml 展示）

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1024-c64-n128 | baseline | output_throughput | 1455.101068101872 | token/s | performance_only-3warm2measured-one-service-process |
| p1024-d1024-c64-n128 | baseline | mean_ttft_ms | 1758.8088228767447 | ms | performance_only-3warm2measured-one-service-process |
| p1024-d1024-c64-n128 | baseline | p99_ttft_ms | 3577.61412137188 | ms | performance_only-3warm2measured-one-service-process |
| p1024-d1024-c64-n128 | baseline | mean_tpot_ms | 42.07523147196639 | ms | performance_only-3warm2measured-one-service-process |
| p1024-d1024-c64-n128 | baseline | p99_tpot_ms | 43.10856974846206 | ms | performance_only-3warm2measured-one-service-process |
| p1024-d1024-c64-n128 | baseline | median_itl_ms | 39.85620941966772 | ms | performance_only-3warm2measured-one-service-process |
| p1024-d1024-c64-n128 | baseline | p99_itl_ms | 44.19904221314937 | ms | performance_only-3warm2measured-one-service-process |
| p1024-d1024-c64-n128 | baseline | p99_e2el_ms | 46958.26573625207 | ms | performance_only-3warm2measured-one-service-process |
<!-- record-metrics:end -->

<!-- baseline-record-review:start -->
## 正式目标覆盖与历史测量

本节是记录审查：原测量状态与角色保持不变，不是新评测回执。`incomplete` 表示此表未闭合正式基线证据；历史、缩减或有观察器的结果须按原范围解释。

| 正式目标 | 正式基线证据状态 | 已记录指标数 | 边界 |
|---|---|---:|---|
| p1024-d1024-c64-n128 | incomplete | 8 | 已列出原始观测；是否满足正式基线契约仍以原回执和稳态/身份条件为准。 |
| p4096-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p16384-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p32768-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |

| 场景 / 角色 | 已记录性能数值（附单位） | 证据范围 / 原字段 |
|---|---|---|
| p1024-d1024-c64-n128 / baseline | output_throughput = 1455.101068101872 token/s；mean_ttft_ms = 1758.8088228767447 ms；p99_ttft_ms = 3577.61412137188 ms；mean_tpot_ms = 42.07523147196639 ms；p99_tpot_ms = 43.10856974846206 ms；median_itl_ms = 39.85620941966772 ms；p99_itl_ms = 44.19904221314937 ms；p99_e2el_ms = 46958.26573625207 ms | performance_only-3warm2measured-one-service-process；`/metrics` |
<!-- baseline-record-review:end -->
