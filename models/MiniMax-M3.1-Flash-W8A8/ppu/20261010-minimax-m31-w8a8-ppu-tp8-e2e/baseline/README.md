# 20261010-minimax-m31-w8a8-ppu-tp8-e2e / baseline

本案例固定为 **TP8**。由原混合记录按已记录身份拆分；不表示新的评测或当前运行事实。

<!-- e2e:summary:start -->

- 案例：20261010-minimax-m31-w8a8-ppu-tp8-e2e
- 当前状态：P1K singleinstance steady baseline passed; Prefill incomplete; remaining phase baselines planned
- 当前候选：TP8 user configuration + fix-001
- 下一步：—

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1024-c64-n128 | baseline | total_token_throughput_mean | 1968.2341084239304 | token/s | correct TP8 single-instance scenario-entry baseline facts; no candidate speedup/formal scenario closure/final acceptance |
| p1024-d1024-c64-n128 | baseline | total_token_throughput_median | 1968.3652400773008 | token/s | correct TP8 single-instance scenario-entry baseline facts; no candidate speedup/formal scenario closure/final acceptance |
| p1024-d1024-c64-n128 | baseline | p99_ttft_ms | 9031.903886528065 | ms | correct TP8 single-instance scenario-entry baseline facts; no candidate speedup/formal scenario closure/final acceptance |
| p1024-d1024-c64-n128 | baseline | p99_tpot_ms | 63.88286447691746 | ms | correct TP8 single-instance scenario-entry baseline facts; no candidate speedup/formal scenario closure/final acceptance |
| p1024-d1024-c64-n128 | baseline | p99_itl_ms | 58.33761019011338 | ms | correct TP8 single-instance scenario-entry baseline facts; no candidate speedup/formal scenario closure/final acceptance |
| p1024-d1024-c64-n128 | baseline | p99_e2el_ms | 71918.42344960508 | ms | correct TP8 single-instance scenario-entry baseline facts; no candidate speedup/formal scenario closure/final acceptance |
| p128-d256-c64-n64-tp8-decode | baseline | total_token_throughput | 1642.0511934841834 | token/s | Single TP8 instance baseline facts only; phase metrics are frontend/scheduler proxies, no candidate gain or formal scenario closure; ALL3 measured rounds retained |
| p128-d256-c64-n64-tp8-decode | baseline | p99_ttft_ms | 1576.6203322075307 | ms | Single TP8 instance baseline facts only; phase metrics are frontend/scheduler proxies, no candidate gain or formal scenario closure; ALL3 measured rounds retained |
| p128-d256-c64-n64-tp8-decode | baseline | p99_tpot_ms | 53.810884261357714 | ms | Single TP8 instance baseline facts only; phase metrics are frontend/scheduler proxies, no candidate gain or formal scenario closure; ALL3 measured rounds retained |
| p128-d256-c64-n64-tp8-decode | baseline | p99_itl_ms | 53.93938830122352 | ms | Single TP8 instance baseline facts only; phase metrics are frontend/scheduler proxies, no candidate gain or formal scenario closure; ALL3 measured rounds retained |
| p128-d256-c64-n64-tp8-decode | baseline | p99_e2el_ms | 14965.055108834058 | ms | Single TP8 instance baseline facts only; phase metrics are frontend/scheduler proxies, no candidate gain or formal scenario closure; ALL3 measured rounds retained |
| p1024-d128-c64-n64-tp8-mixed-milestone | baseline | total_token_throughput | 4648.994518552233 | token/s | Single TP8 instance baseline facts only; phase metrics are frontend/scheduler proxies, no candidate gain or formal scenario closure; ALL3 measured rounds retained |
| p1024-d128-c64-n64-tp8-mixed-milestone | baseline | p99_ttft_ms | 9044.042515568435 | ms | Single TP8 instance baseline facts only; phase metrics are frontend/scheduler proxies, no candidate gain or formal scenario closure; ALL3 measured rounds retained |
| p1024-d128-c64-n64-tp8-mixed-milestone | baseline | p99_tpot_ms | 112.2923370356136 | ms | Single TP8 instance baseline facts only; phase metrics are frontend/scheduler proxies, no candidate gain or formal scenario closure; ALL3 measured rounds retained |
| p1024-d128-c64-n64-tp8-mixed-milestone | baseline | p99_itl_ms | 1067.8901153057814 | ms | Single TP8 instance baseline facts only; phase metrics are frontend/scheduler proxies, no candidate gain or formal scenario closure; ALL3 measured rounds retained |
| p1024-d128-c64-n64-tp8-mixed-milestone | baseline | p99_e2el_ms | 15844.752472620457 | ms | Single TP8 instance baseline facts only; phase metrics are frontend/scheduler proxies, no candidate gain or formal scenario closure; ALL3 measured rounds retained |

<!-- e2e:summary:end -->

<!-- baseline-record-review:start -->
## 正式目标覆盖与历史测量

本节是记录审查：原测量状态与角色保持不变，不是新评测回执。`incomplete` 表示此表未闭合正式基线证据；历史、缩减或有观察器的结果须按原范围解释。

| 正式目标 | 正式基线证据状态 | 已记录指标数 | 边界 |
|---|---|---:|---|
| p1024-d1024-c64-n128 | incomplete | 6 | 已列出原始观测；是否满足正式基线契约仍以原回执和稳态/身份条件为准。 |
| p4096-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p16384-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p32768-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |

数值见上方由 `state.yml/metrics` 生成的指标表；每条新增指标保留 source_pointer，外部原件按原 evidence 查阅。
<!-- baseline-record-review:end -->
