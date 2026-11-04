# MiniMax-M3 / PPU Baseline

当前状态：`baseline_sanity_passed_performance_pending`。`image_lineage=verified`、`mount_parity=passed`；独立优化容器的 TP16 graph 服务在 `8023` ready，使用 AABS0、65K、max-seqs 32、6 个 capture size，并显式关闭 prefix cache。北京/巴黎双 replay 正确；固定十题 GPQA greedy/C8 strict-match 10/10、0 timeout。doc_id 7/8 达到 30K 上限，作为非门禁输出健康观察保留。

| 场景 | 当前状态 | output tok/s | TTFT | TPOT/ITL | E2E | 说明 |
|---|---|---:|---:|---:|---:|---|
| P1024/D1024/C64/N128 | not_run | — | — | — | — | 当前目标场景 |
| P4096/D1024/C64/N128 | historical diagnostic | 600.25 | P99 31,324.42 ms | P99 104.91 / 978.11 ms | — | Run2/3 平均；维护版工具基线待重建 |
| P16384/D1024/C64/N128 | historical diagnostic | 228.32 | P99 257,544.39 ms | P99 145.63 / 1,116.55 ms | — | Run2/3 平均；维护版工具基线待重建 |
| P32768/D1024/C64/N128 | historical diagnostic | 120.16 | P99 494,478.18 ms | P99 114.31 / 1,210.06 ms | — | Run2/3 平均；维护版工具基线待重建 |

原始历史结果：`/mnt/nfs/users/jinghao/minimaxM3/test/perf_test/benchmark_results/MiniMax-M3`。这些结果没有 P1K、E2E、当前 service manifest/run-record 与显式 temperature，只用于诊断参考。

<!-- baseline-record-review:start -->
## 正式目标覆盖与历史测量

本节是记录审查：原测量状态与角色保持不变，不是新评测回执。`incomplete` 表示此表未闭合正式基线证据；历史、缩减或有观察器的结果须按原范围解释。

| 正式目标 | 正式基线证据状态 | 已记录指标数 | 边界 |
|---|---|---:|---|
| p1024-d1024-c64-n128 | not_run | 0 | 本阶段原记录明确未执行性能测试。 |
| p4096-d1024-c64-n128 | incomplete | 5 | 已列出原始观测；是否满足正式基线契约仍以原回执和稳态/身份条件为准。 |
| p16384-d1024-c64-n128 | incomplete | 5 | 已列出原始观测；是否满足正式基线契约仍以原回执和稳态/身份条件为准。 |
| p32768-d1024-c64-n128 | incomplete | 5 | 已列出原始观测；是否满足正式基线契约仍以原回执和稳态/身份条件为准。 |

| 场景 / 角色 | 已记录性能数值（附单位） | 证据范围 / 原字段 |
|---|---|---|
| p4096-d1024-c64-n128 / historical-reference | output_throughput_tps = 600.25 token/s；total_throughput_tps = 3001.26 token/s；p99_ttft_ms = 31324.42 ms；p99_tpot_ms = 104.91 ms；p99_itl_ms = 978.11 ms | 历史人工/导入观测；非本案例当前 anchor；原始可比性未重新核验；`/historical_performance/p4096-d1024-c64-n128` |
| p16384-d1024-c64-n128 / historical-reference | output_throughput_tps = 228.32 token/s；total_throughput_tps = 3881.52 token/s；p99_ttft_ms = 257544.39 ms；p99_tpot_ms = 145.63 ms；p99_itl_ms = 1116.55 ms | 历史人工/导入观测；非本案例当前 anchor；原始可比性未重新核验；`/historical_performance/p16384-d1024-c64-n128` |
| p32768-d1024-c64-n128 / historical-reference | output_throughput_tps = 120.16 token/s；total_throughput_tps = 3965.18 token/s；p99_ttft_ms = 494478.18 ms；p99_tpot_ms = 114.31 ms；p99_itl_ms = 1210.06 ms | 历史人工/导入观测；非本案例当前 anchor；原始可比性未重新核验；`/historical_performance/p32768-d1024-c64-n128` |
<!-- baseline-record-review:end -->
