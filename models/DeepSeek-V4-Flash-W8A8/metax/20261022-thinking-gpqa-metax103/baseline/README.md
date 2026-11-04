# 20261022-thinking-gpqa-metax103 / baseline

<!-- e2e:summary:start -->

- 案例：20261022-thinking-gpqa-metax103
- 当前状态：three_p32_measurements_completed_variability_incomplete
- 当前候选：mx59-acc003-5ea09be+fw-001+op-001
- 下一步：gather修复及32K三轮测量完成；第三轮变慢，spread12.913%超过10%，稳态结果incomplete。全部轮次保留；P16属于fw001-only，未做正式组合验收。

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1024-c64-n128 | diagnostic_current_baseline | request_throughput | 0.6272371133550654 | request/s | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | output_throughput | 642.290804075587 | token/s | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | total_token_throughput | 1284.581608151174 | token/s | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | mean_ttft_ms | 6682.626925641671 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | median_ttft_ms | 4032.0440884679556 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | p95_ttft_ms | 17145.268865209073 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | p99_ttft_ms | 18101.15803470835 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | mean_tpot_ms | 92.98437484808893 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | median_tpot_ms | 94.94581030734531 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | p95_tpot_ms | 97.37471533567806 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | p99_tpot_ms | 98.1835796869745 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | mean_itl_ms | 92.98437502106184 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | median_itl_ms | 81.99385646730661 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | p95_itl_ms | 87.17956515029073 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | p99_itl_ms | 784.322493933141 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | mean_e2el_ms | 101747.69324024965 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | median_e2el_ms | 101535.81806458533 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | p95_e2el_ms | 114334.88282561302 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | p99_e2el_ms | 115847.7112262696 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | benchmark_duration | 204.06955722905695 | s | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | request_throughput | 0.4276101819376811 | request/s | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | output_throughput | 437.8728263041854 | token/s | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | total_token_throughput | 2189.364131520927 | token/s | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | mean_ttft_ms | 19049.124712357298 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | median_ttft_ms | 4365.717804990709 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | p95_ttft_ms | 59620.5686694011 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | p99_ttft_ms | 64984.39759889618 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | mean_tpot_ms | 126.36681695622123 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | median_tpot_ms | 139.49585494604455 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | p95_tpot_ms | 140.727292735745 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | p99_tpot_ms | 142.10201382147238 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | mean_itl_ms | 126.36681714909456 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | median_itl_ms | 83.01894180476665 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | p95_itl_ms | 88.37300669401883 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | p99_itl_ms | 1020.1140977256 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | mean_e2el_ms | 148586.3469212054 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | median_e2el_ms | 147306.15263525397 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | p95_e2el_ms | 203199.22011969608 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | p99_e2el_ms | 208355.3481924348 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | benchmark_duration | 299.3380546271801 | s | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p16384-d1024-c64-n128 | fw001_only_baseline | request_throughput | 0.18714453515933124 | request/s | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | output_throughput | 191.6360040031552 | token/s | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | total_token_throughput | 3257.812068053638 | token/s | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | mean_ttft_ms | 70752.14057367702 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | median_ttft_ms | 9754.533527418971 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | p95_ttft_ms | 236470.8114918321 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | p99_ttft_ms | 257340.93551166359 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | mean_tpot_ms | 260.9264776931275 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | median_tpot_ms | 315.95076265620145 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | p95_tpot_ms | 318.2095663559205 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | p99_tpot_ms | 318.6691467407162 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | mean_itl_ms | 260.9264778820036 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | median_itl_ms | 90.66702611744404 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | p95_itl_ms | 988.6310052126646 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | p99_itl_ms | 1472.7796279452741 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | mean_e2el_ms | 337507.6729493594 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | median_e2el_ms | 332586.70236263424 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | p95_e2el_ms | 560984.7536621615 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | p99_e2el_ms | 581777.4182157033 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | benchmark_duration | 683.9633328914642 | s | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | request_throughput | 0.10694989016939468 | request/s | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | output_throughput | 109.51668753346016 | token/s | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | total_token_throughput | 3614.0506886041853 | token/s | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | mean_ttft_ms | 140343.06927179568 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | median_ttft_ms | 15989.924564026296 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | p95_ttft_ms | 473795.3542062081 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | p99_ttft_ms | 516671.1899105273 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | mean_tpot_ms | 439.0424904395456 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | median_tpot_ms | 551.376257097223 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | p95_tpot_ms | 555.4177873228055 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | p99_tpot_ms | 556.1495798993 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | mean_itl_ms | 439.042490628877 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | median_itl_ms | 96.24035842716694 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | p95_itl_ms | 1345.595386531204 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | p99_itl_ms | 1537.668632157147 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | mean_e2el_ms | 589336.1018699215 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | median_e2el_ms | 579107.886461541 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | p95_e2el_ms | 1041540.157169476 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | p99_e2el_ms | 1082963.0328418317 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | benchmark_duration | 1196.822173424065 | s | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |

<!-- e2e:summary:end -->

perf-001历史快照时间：2026-10-23 00:23:00（Asia/Shanghai）。该阶段诊断性基线：P1K 642.29 token/s、P4K 437.87 token/s；P16K首次预热MCCL OOM，P32K未执行，四场景整体incomplete。

使用用户指定vllm_perf.py的原run_once，源文件未改；COMMON_ARGS按冻结契约设置。D1024/C64/N128、finite batch、temperature0、ignore_eos、固定输入输出长度，prefix cache关闭。P1K/P4K恢复补测各固定4轮完整预热，末3轮输出吞吐spread≤5%后采集3个全新measured轮；全部保留，逐指标取三轮中位数，测量spread≤10%才称稳定。不重标旧warmup、不混合两实例、不丢弃较慢测量轮。

| 场景（D1024/C64/N128） | 状态 | 输出吞吐(token/s) | 总token吞吐(token/s) | mean TTFT(ms) | mean TPOT(ms) | mean ITL(ms) | mean E2EL(ms) | 批次耗时(s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| P1K | completed | 642.29 | 1,284.58 | 6,682.63 | 92.98 | 92.98 | 101,747.69 | 204.07 |
| P4K | completed | 437.87 | 2,189.36 | 19,049.12 | 126.37 | 126.37 | 148,586.35 | 299.34 |
| P16K | failed_oom_incomplete | — | — | — | — | — | — | — |
| P32K | not_run_incomplete | — | — | — | — | — | — | — |

TTFT与输入吞吐是Prefill客户端代理，TPOT/ITL是Decode客户端代理，均包含网络、排队和调度；完整批次吞吐/E2EL表示Mixed，不能冒充纯设备阶段时间。E2EL是请求延迟，benchmark_duration是整批墙钟耗时，两者不同。

## 逐轮与波动

### P1K逐轮数据

固定4轮预热全部保留，末3轮仅用于稳态准入；下表3轮是准入后的独立测量。

| 角色/轮次 | 输出吞吐(token/s) | mean TTFT(ms) | mean TPOT(ms) | mean ITL(ms) | mean E2EL(ms) | 批次耗时(s) | 原生证据 |
|---|---:|---:|---:|---:|---:|---:|---|
| measured / measure1 | 642.29 | 6,624.68 | 92.98 | 92.98 | 101,747.69 | 204.07 | `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/performance-001/recovery-v2/rounds/p1024-d1024-c64-n128/measure1/native.json` |
| measured / measure2 | 640.99 | 6,763.44 | 93.05 | 93.05 | 101,956.05 | 204.48 | `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/performance-001/recovery-v2/rounds/p1024-d1024-c64-n128/measure2/native.json` |
| measured / measure3 | 642.33 | 6,682.63 | 92.92 | 92.92 | 101,741.06 | 204.06 | `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/performance-001/recovery-v2/rounds/p1024-d1024-c64-n128/measure3/native.json` |

预热输出吞吐（token/s）：626.63 / 645.78 / 645.25 / 642.38。
末3轮预热spread：0.528%；3轮测量spread：0.208%。

| 指标 | 三轮中位数 | 三轮最小值 | 三轮最大值 | 单位 |
|---|---:|---:|---:|---|
| request_throughput | 0.63 | 0.63 | 0.63 | request/s |
| output_throughput | 642.29 | 640.99 | 642.33 | token/s |
| total_token_throughput | 1,284.58 | 1,281.99 | 1,284.66 | token/s |
| mean_ttft_ms | 6,682.63 | 6,624.68 | 6,763.44 | ms |
| median_ttft_ms | 4,032.04 | 4,023.61 | 4,082.17 | ms |
| p95_ttft_ms | 17,145.27 | 17,128.71 | 17,204.49 | ms |
| p99_ttft_ms | 18,101.16 | 18,041.09 | 18,479.84 | ms |
| mean_tpot_ms | 92.98 | 92.92 | 93.05 | ms |
| median_tpot_ms | 94.95 | 94.70 | 95.81 | ms |
| p95_tpot_ms | 97.37 | 97.31 | 97.53 | ms |
| p99_tpot_ms | 98.18 | 98.04 | 98.36 | ms |
| mean_itl_ms | 92.98 | 92.92 | 93.05 | ms |
| median_itl_ms | 81.99 | 81.37 | 82.04 | ms |
| p95_itl_ms | 87.18 | 86.55 | 87.39 | ms |
| p99_itl_ms | 784.32 | 744.99 | 820.94 | ms |
| mean_e2el_ms | 101,747.69 | 101,741.06 | 101,956.05 | ms |
| median_e2el_ms | 101,535.82 | 101,529.46 | 101,746.95 | ms |
| p95_e2el_ms | 114,334.88 | 114,117.06 | 115,619.87 | ms |
| p99_e2el_ms | 115,847.71 | 115,643.21 | 117,126.55 | ms |
| benchmark_duration | 204.07 | 204.06 | 204.48 | s |

### P4K逐轮数据

固定4轮预热全部保留，末3轮仅用于稳态准入；下表3轮是准入后的独立测量。

| 角色/轮次 | 输出吞吐(token/s) | mean TTFT(ms) | mean TPOT(ms) | mean ITL(ms) | mean E2EL(ms) | 批次耗时(s) | 原生证据 |
|---|---:|---:|---:|---:|---:|---:|---|
| measured / measure1 | 437.78 | 19,346.97 | 126.37 | 126.37 | 148,620.22 | 299.40 | `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/performance-001/recovery-v2/rounds/p4096-d1024-c64-n128/measure1/native.json` |
| measured / measure2 | 439.69 | 18,961.59 | 126.11 | 126.11 | 147,969.01 | 298.10 | `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/performance-001/recovery-v2/rounds/p4096-d1024-c64-n128/measure2/native.json` |
| measured / measure3 | 437.87 | 19,049.12 | 126.62 | 126.62 | 148,586.35 | 299.34 | `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/performance-001/recovery-v2/rounds/p4096-d1024-c64-n128/measure3/native.json` |

预热输出吞吐（token/s）：430.34 / 439.60 / 441.58 / 441.62。
末3轮预热spread：0.457%；3轮测量spread：0.435%。

| 指标 | 三轮中位数 | 三轮最小值 | 三轮最大值 | 单位 |
|---|---:|---:|---:|---|
| request_throughput | 0.43 | 0.43 | 0.43 | request/s |
| output_throughput | 437.87 | 437.78 | 439.69 | token/s |
| total_token_throughput | 2,189.36 | 2,188.90 | 2,198.43 | token/s |
| mean_ttft_ms | 19,049.12 | 18,961.59 | 19,346.97 | ms |
| median_ttft_ms | 4,365.72 | 4,345.90 | 4,538.87 | ms |
| p95_ttft_ms | 59,620.57 | 59,597.66 | 60,203.02 | ms |
| p99_ttft_ms | 64,984.40 | 64,727.83 | 65,053.34 | ms |
| mean_tpot_ms | 126.37 | 126.11 | 126.62 | ms |
| median_tpot_ms | 139.50 | 139.17 | 139.84 | ms |
| p95_tpot_ms | 140.73 | 140.30 | 140.89 | ms |
| p99_tpot_ms | 142.10 | 141.09 | 142.25 | ms |
| mean_itl_ms | 126.37 | 126.11 | 126.62 | ms |
| median_itl_ms | 83.02 | 83.01 | 83.12 | ms |
| p95_itl_ms | 88.37 | 88.35 | 88.53 | ms |
| p99_itl_ms | 1,020.11 | 1,004.80 | 1,035.33 | ms |
| mean_e2el_ms | 148,586.35 | 147,969.01 | 148,620.22 | ms |
| median_e2el_ms | 147,306.15 | 146,758.70 | 147,347.08 | ms |
| p95_e2el_ms | 203,199.22 | 201,989.20 | 203,532.18 | ms |
| p99_e2el_ms | 208,355.35 | 207,196.95 | 208,860.30 | ms |
| benchmark_duration | 299.34 | 298.10 | 299.40 | s |


## 原始尝试与恢复边界

初始实例P1K/P4K的3轮完整预热因首轮过渡未达≤5%准入，均零measured轮，所有旧轮次保留。P16K warmup1先出现MCCL内部44MiB/512MiB分配失败，随后indexer query-sharding all_gather报DistBackendError；日志不证明精确触发shape或allocator根因。按停止规则终止精确客户端；旧模型进程随后自行退出。同容器恢复同配置服务后仅补测P1K/P4K。P32K因前序服务故障未执行，不能宣称已证明unsupported。

恢复实例 `deepseekV4-flash:perf001-restore02:1282425:1110226189` 同配置/源码/cache，容器未重启；7/7 FULL capture完成，C1 FULL14次、C8 FULL2次。性能期间FULL padded64单条日志最大count为124，只保留最大一条，不跨rank或累计快照求和。证据 `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/performance-001/recovery-v2/completion-runtime-evidence.json`，SHA `61f4dbd1439b1bb42f4aaa8231df7d216ffa557609963ee276bdba70bcd7cc13`。

历史170/198＝85.86%由用户确认精度通过，仍属于原attempt01与同一批198份输出；原strict153/198＝77.27%及其证据完整保留。恢复实例仅有新10/10最小回归和graph验证，没有新的完整GPQA分数或正式精度gate。

这是已保留组合代码的scenario-entry诊断性当前基线。没有未优化anchor、candidate/revert A/B或单优化消融，没有设定性能SLO/通过阈值，不声称加速倍数或完整正式性能验收通过。生产源码、权重、tokenizer均未新增修改。

远端根 `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/performance-001`；最终summary SHA `94a776834acea80de320369c18e1bdd46edba8715e785447053cc1a689a9953a`。恢复plan/contract/preflight及每轮原生JSON、stdout日志的绝对路径和SHA保存在state.yml；原始输出、完整日志和脚本保留远端，不复制到模型目录。

详见[perf-001](../optimize/perf-001.md)。

<!-- long-context-repair:start -->

## 最新长场景修复与结果

| 输入 | 源码 | 输出吞吐(token/s) | mean TTFT(s) | mean TPOT(ms) | mean E2EL(s) | 整批耗时(s) |
|---|---|---:|---:|---:|---:|---:|
| p16384 | fw001_only_baseline | 191.64 | 70.752 | 260.926 | 337.508 | 683.963 |
| p32768 | fw001_op001_baseline | 109.52 | 140.343 | 439.042 | 589.336 | 1196.822 |

D1024/C64/N128、finite-batch、固定random长度、temperature0、ignore_eos；使用用户指定vllm_perf.py原run_once，prefix cache关闭。P16固定4预热+3测量；P32原4轮预热未稳态（零测量）全部保留，冻结恢复契约后再运行全新3轮预热（全部3轮spread≤5%）+3轮测量（要求spread≤10%，实际12.913%，未通过）。全部测量逐指标取描述性中位数，不丢第三轮；32K稳态性能结论为incomplete。TTFT/TPOT/ITL是含排队与调度的客户端代理。16K属于fw001-only，32K属于fw001+op001；没有同源码四目标正式验收或A/B加速结论。

32K每轮128/128成功，新恢复6轮合计768请求，无非法地址、OOM或服务ERROR；最终服务健康空闲。详细修复与逐轮值见[op-001](../optimize/op-001.md)和[fw-001](../optimize/fw-001.md)。32K结果：`/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/indexer-gather-oob-001/performance-recovery01/summary.json`，SHA `851fd8ff600e3fb412af18298f409352527c5d01670f117ec1c21373eeae805d`。

<!-- long-context-repair:end -->

<!-- baseline-record-review:start -->
## 正式目标覆盖与历史测量

本节是记录审查：原测量状态与角色保持不变，不是新评测回执。`incomplete` 表示此表未闭合正式基线证据；历史、缩减或有观察器的结果须按原范围解释。

| 正式目标 | 正式基线证据状态 | 已记录指标数 | 边界 |
|---|---|---:|---|
| p1024-d1024-c64-n128 | incomplete | 20 | 已列出原始观测；是否满足正式基线契约仍以原回执和稳态/身份条件为准。 |
| p4096-d1024-c64-n128 | incomplete | 20 | 已列出原始观测；是否满足正式基线契约仍以原回执和稳态/身份条件为准。 |
| p16384-d1024-c64-n128 | incomplete | 20 | 已列出原始观测；是否满足正式基线契约仍以原回执和稳态/身份条件为准。 |
| p32768-d1024-c64-n128 | incomplete | 20 | 已列出原始观测；是否满足正式基线契约仍以原回执和稳态/身份条件为准。 |

数值见上方由 `state.yml/metrics` 生成的指标表；每条新增指标保留 source_pointer，外部原件按原 evidence 查阅。
<!-- baseline-record-review:end -->
