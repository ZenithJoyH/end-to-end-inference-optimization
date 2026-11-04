# Qwen3.6-27B / MetaX 基线

以下为用户2026-10-10两组CSV全部三轮中位数，属于历史观察，缺少原服务身份及独立进程重复。TTFT/TPOT是客户端阶段代理；不是纯设备时间。历史SUMMARY排除了Run1，新测量不延续该做法。

| 场景 | begin输出tok/s | addattention输出tok/s | 变化 | 平均TTFT ms | 平均TPOT ms |
|---|---:|---:|---:|---:|---:|
| P4096 / D1024 / C64 / N128 | 584.92 | 329.78 | -43.62% | 14395.42 → 15562.32 | 95.15 → 178.38 |
| P16384 / D1024 / C64 / N128 | 216.56 | 100.55 | -53.57% | 106993.33 → 191048.03 | 173.43 → 395.38 |
| P65536 / D1024 / C64 / N128 | 53.10 | 14.46 | -72.77% | 807003.43 → 2820228.75 | 200.05 → 765.03 |

当前新容器正式基线：P1K/P4K/P16K/P32K均 not_run；P64K仅为额外历史诊断。

2026-10-13已建立OP001的P1K诊断阶段入口：Prefill P1K/D1/C64/N128，meanTTFT8367.33ms；Decode P1K/D512/C64/N64，输出929.526tok/s、meanTPOT56.220ms；Mixed P1K/D256/C64/N128，输出706.646tok/s、meanTPOT69.277ms。各三测量轮，稳态准入与全部轮保留；对应回退漂移分别为输出+0.127%/+0.223%/−0.109%。这些是scenario-entry reduced probes，含网络/排队残余，不替代未优化anchor或四场景正式基线。比较器因required_metrics声明缺口incomplete，候选Mixed也零测量；原冻结配置不改。记录/SHA在本目录state.yml及[组合001](../optimize/combo-001-fa-splits-warps.md)。

Framework001新冻结契约的P1K三阶段基线/回退已完成，原始SHA与轮次见state.yml的framework001_scenario_entry。基线Prefill输出5.981416tok/s（D1代理）、meanTTFT8353.339ms；Decode输出931.768815tok/s、meanTPOT56.069247ms；Mixed输出708.317032tok/s、meanTPOT69.307164ms。incomplete为候选晋级结果，不能追认为正式四场景或未优化anchor。

Framework001诊断基线与回退（三测量轮中位数，P1K，客户端阶段代理）：

| 阶段 / D/C/N | baseline 输出tok/s | revert 输出tok/s | baseline meanTTFT ms | baseline meanTPOT ms | 状态 |
|---|---:|---:|---:|---:|---|
| Prefill / 1/64/128 | 5.981416 | 5.971807 | 8353.339 | — | 原生完整，D1输出代理；非纯设备时间 |
| Decode / 512/64/64 | 931.768815 | 933.245831 | 6386.535 | 56.069 | 原生完整，含初始Prefill残余 |
| Mixed / 256/64/128 | 708.317032 | 710.938702 | 5352.699 | 69.307 | 原生完整；比较因TTFT回退漂移1.244%>1%而incomplete |

四原始正式目标仍not_run；本表不替代anchor或最终验收。

[OP009](../optimize/op-009-gdn-prefill-fp32-performance-cost.md)精度修复前的全21项FlagGems参考（2026-10-14，P1024、诊断缩减）：

| phase / D/C/N | baseline | revert | 完整性与边界 |
|---|---:|---:|---|
| Prefill 1/64/128 总tok/s | 6183.139 | 6233.579 | 各3measured，回退漂移+0.816%；meanTTFT8285.204→8216.764ms |
| Decode 512/64/64 输出tok/s | 930.070 | 934.948 | 各3measured；meanTPOT56.573→56.313ms；候选无稳态测量 |
| Mixed 256/64/128 输出tok/s | — | 712.453* | baseline0measured；revert3measured含351.367慢轮，散差50.73%，incomplete |

*完整原生计数不证明稳态，全部慢轮保留。旧BF16算子数值失败只作用户要求的速度参考，不可保留晋级；本周期已恢复正确FP32。不能补成原始anchor或正式四场景基线。

OP010 r2（2026-10-15，正确OP007 FP32/all21，原.002/.02）完成同配置三角色对照。新入口源6ea，与前述BF16/不同source历史基线分开：Prefill baseline/revert总token吞吐5636.350/5584.052tok/s、meanTTFT9085.535/9177.321ms（后者漂移1.010247%>1%）；Decode输出896.414/890.815tok/s、TPOT57.648/58.001ms，P99ITL漂移2.415935%>1%；Mixed输出572.813/668.501tok/s，baseline吞吐spread26.781%、回退+16.705%，incomplete。三阶段各3measured全部保留，全部原始计数/SHA/原生check_run通过但比较可靠性未过。current原FP32及166gate已恢复，未产生新的anchor或四场景正式结果；详见[OP010](../optimize/op-010-gdn-prefill-fp32-hotspot-optimization.md)。

<!-- baseline-record-review:start -->
## 正式目标覆盖与历史测量

本节是记录审查：原测量状态与角色保持不变，不是新评测回执。`incomplete` 表示此表未闭合正式基线证据；历史、缩减或有观察器的结果须按原范围解释。

| 正式目标 | 正式基线证据状态 | 已记录指标数 | 边界 |
|---|---|---:|---|
| p1024-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p4096-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p16384-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p32768-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |

| 场景 / 角色 | 已记录性能数值（附单位） | 证据范围 / 原字段 |
|---|---|---|
| unresolved-workload-diagnostic_scenario_entry-prefill / baseline | output_throughput = 5.972303888674042 token/s；mean_ttft_ms = 8367.329767017509 ms | targeted/diagnostic; not anchor baseline or formal acceptance；逐字段定位原证据，未重验；TTFT/TPOT 为客户端代理；`/diagnostic_scenario_entry/baseline_records/0/median` |
| unresolved-workload-diagnostic_scenario_entry-decode / baseline | output_throughput = 929.5259409027419 token/s；mean_ttft_ms = 6394.51100784936 ms；mean_tpot_ms = 56.22020841910711 ms；p99_itl_ms = 50.58824219740927 ms | targeted/diagnostic; not anchor baseline or formal acceptance；逐字段定位原证据，未重验；TTFT/TPOT 为客户端代理；`/diagnostic_scenario_entry/baseline_records/1/median` |
| unresolved-workload-diagnostic_scenario_entry-mixed / baseline | output_throughput = 706.6461340620436 token/s；mean_ttft_ms = 5438.074094745389 ms；mean_tpot_ms = 69.27743577307054 ms；p99_itl_ms = 1381.2794481310996 ms | targeted/diagnostic; not anchor baseline or formal acceptance；逐字段定位原证据，未重验；TTFT/TPOT 为客户端代理；`/diagnostic_scenario_entry/baseline_records/2/median` |
| unresolved-workload-diagnostic_scenario_entry-prefill / revert | output_throughput = 5.9799156681079495 token/s；mean_ttft_ms = 8355.716048063186 ms | targeted/diagnostic; not anchor baseline or formal acceptance；逐字段定位原证据，未重验；TTFT/TPOT 为客户端代理；`/diagnostic_scenario_entry/revert_records/0/median` |
| unresolved-workload-diagnostic_scenario_entry-decode / revert | output_throughput = 931.5941798721243 token/s；mean_ttft_ms = 6391.122026441735 ms；mean_tpot_ms = 56.09158872751566 ms；p99_itl_ms = 50.381908835843205 ms | targeted/diagnostic; not anchor baseline or formal acceptance；逐字段定位原证据，未重验；TTFT/TPOT 为客户端代理；`/diagnostic_scenario_entry/revert_records/1/median` |
| unresolved-workload-diagnostic_scenario_entry-mixed / revert | output_throughput = 705.8768651881777 token/s；mean_ttft_ms = 5444.170852344541 ms；mean_tpot_ms = 69.3661726518436 ms；p99_itl_ms = 1386.3476772140712 ms | targeted/diagnostic; not anchor baseline or formal acceptance；逐字段定位原证据，未重验；TTFT/TPOT 为客户端代理；`/diagnostic_scenario_entry/revert_records/2/median` |
| p1024-d1-c64-n128-prefill / baseline | output_throughput = 5.9814164487585515 token/s；mean_ttft_ms = 8353.338965236617 ms | diagnostic reduced3phase; not originalanchor or formal target；逐字段定位原证据，未重验；TTFT/TPOT 为客户端代理；`/framework001_scenario_entry/baseline_records/0/median` |
| p1024-d512-c64-n64-decode / baseline | output_throughput = 931.7688147443101 token/s；mean_ttft_ms = 6386.535265337443 ms；mean_tpot_ms = 56.0692465423179 ms；p99_itl_ms = 50.41535192169249 ms | diagnostic reduced3phase; not originalanchor or formal target；逐字段定位原证据，未重验；TTFT/TPOT 为客户端代理；`/framework001_scenario_entry/baseline_records/1/median` |
| p1024-d256-c64-n128-mixed-milestone / baseline | output_throughput = 708.3170323577627 token/s；mean_ttft_ms = 5352.699464645411 ms；mean_tpot_ms = 69.30716433456766 ms；p99_itl_ms = 1384.395263446495 ms | diagnostic reduced3phase; not originalanchor or formal target；逐字段定位原证据，未重验；TTFT/TPOT 为客户端代理；`/framework001_scenario_entry/baseline_records/2/median` |
| p1024-d1-c64-n128-prefill / revert | output_throughput = 5.971806915293675 token/s；mean_ttft_ms = 8367.44487049873 ms | diagnostic reduced3phase; not originalanchor or formal target；逐字段定位原证据，未重验；TTFT/TPOT 为客户端代理；`/framework001_scenario_entry/revert_records/0/median` |
| p1024-d512-c64-n64-decode / revert | output_throughput = 933.2458309971548 token/s；mean_ttft_ms = 6383.6962016357575 ms；mean_tpot_ms = 55.97521667328842 ms；p99_itl_ms = 50.57608497329056 ms | diagnostic reduced3phase; not originalanchor or formal target；逐字段定位原证据，未重验；TTFT/TPOT 为客户端代理；`/framework001_scenario_entry/revert_records/1/median` |
| p1024-d256-c64-n128-mixed-milestone / revert | output_throughput = 710.9387020323065 token/s；mean_ttft_ms = 5419.304622519121 ms；mean_tpot_ms = 68.86583227474772 ms；p99_itl_ms = 1384.793538171798 ms | diagnostic reduced3phase; not originalanchor or formal target；逐字段定位原证据，未重验；TTFT/TPOT 为客户端代理；`/framework001_scenario_entry/revert_records/2/median` |
| p1024-d1-c64-n128-prefill / baseline | mean_ttft_ms = 8285.203922037908 ms；median_ttft_ms = 10464.311940129846 ms；output_throughput = 6.032330595302132 token/s；p99_e2el_ms = 10819.595539337024 ms；p99_ttft_ms = 10819.595924792811 ms；request_throughput = 6.032330595302132 request/s；total_token_throughput = 6183.138860184686 token/s | op009 缩减参考；存在 warmup 失败及回退波动，不能据此宣称有效收益；`/op009_precision_cost_reference/phases/0/metrics` |
| p1024-d1-c64-n128-prefill / revert | mean_ttft_ms = 8216.763846037793 ms；median_ttft_ms = 10382.150588091463 ms；output_throughput = 6.0815404302525025 token/s；p99_e2el_ms = 10725.498161586002 ms；p99_ttft_ms = 10725.498358150944 ms；request_throughput = 6.0815404302525025 request/s；total_token_throughput = 6233.5789410088155 token/s | op009 缩减参考；存在 warmup 失败及回退波动，不能据此宣称有效收益；`/op009_precision_cost_reference/phases/1/metrics` |
| p1024-d512-c64-n64-decode / baseline | mean_tpot_ms = 56.572526788629254 ms；mean_ttft_ms = 6155.490725170239 ms；output_throughput = 930.0700573072509 token/s；p99_e2el_ms = 35216.54535276815 ms；p99_itl_ms = 51.87719942070545 ms；p99_tpot_ms = 66.15050360513031 ms；p99_ttft_ms = 10744.503636388108 ms；request_throughput = 1.8165430806782243 request/s；total_token_throughput = 2790.2101719217526 token/s | op009 缩减参考；存在 warmup 失败及回退波动，不能据此宣称有效收益；`/op009_precision_cost_reference/phases/2/metrics` |
| p1024-d512-c64-n64-decode / revert | mean_tpot_ms = 56.3126409154316 ms；mean_ttft_ms = 6148.695533149294 ms；output_throughput = 934.9480051684494 token/s；p99_e2el_ms = 35035.24185379036 ms；p99_itl_ms = 51.92457548342645 ms；p99_tpot_ms = 65.88757525836053 ms；p99_ttft_ms = 10735.767879337072 ms；request_throughput = 1.8260703225946278 request/s；total_token_throughput = 2804.844015505348 token/s | op009 缩减参考；存在 warmup 失败及回退波动，不能据此宣称有效收益；`/op009_precision_cost_reference/phases/3/metrics` |
| p1024-d256-c64-n128-mixed-milestone / revert | mean_tpot_ms = 69.33770927711271 ms；mean_ttft_ms = 5237.0443937325035 ms；output_throughput = 712.4528997450406 token/s；p99_e2el_ms = 28265.305495923385 ms；p99_itl_ms = 1326.9478664640337 ms；p99_tpot_ms = 86.21987443884798 ms；p99_ttft_ms = 10752.407026514411 ms；request_throughput = 2.7830191396290647 request/s；total_token_throughput = 3562.2644987252024 token/s | op009 缩减参考；存在 warmup 失败及回退波动，不能据此宣称有效收益；`/op009_precision_cost_reference/phases/5/metrics` |
| p1024-d1-c64-n128-prefill-milestone / baseline | total_token_throughput = 5636.349978673761 token/s；mean_ttft_ms = 9085.534648802422 ms；p99_ttft_ms = 11853.526981109753 ms；p99_e2el_ms = 11853.526864293963 ms | op010r2 缩减诊断；Mixed 回退漂移，非正式 anchor；workload 由原 unchanged 性能契约确认；`/op010r2_scenario_entry/phase_evidence/prefill/metrics` |
| p1024-d1-c64-n128-prefill-milestone / revert | total_token_throughput = 5584.051954799324 token/s；mean_ttft_ms = 9177.321023285913 ms；p99_ttft_ms = 11971.473527103662 ms；p99_e2el_ms = 11971.473261807114 ms | op010r2 缩减诊断；Mixed 回退漂移，非正式 anchor；workload 由原 unchanged 性能契约确认；`/op010r2_scenario_entry/phase_evidence/prefill/metrics` |
| p1024-d512-c64-n64-decode-milestone / baseline | output_throughput = 896.4143952820822 token/s；mean_ttft_ms = 6963.16936922085 ms；mean_tpot_ms = 57.64818556841195 ms；p99_itl_ms = 50.902338167652495 ms；p99_e2el_ms = 36537.257829066366 ms | op010r2 缩减诊断；Mixed 回退漂移，非正式 anchor；workload 由原 unchanged 性能契约确认；`/op010r2_scenario_entry/phase_evidence/decode/metrics` |
| p1024-d512-c64-n64-decode-milestone / revert | output_throughput = 890.8146385479832 token/s；mean_ttft_ms = 7018.272555244039 ms；mean_tpot_ms = 58.00139633854947 ms；p99_itl_ms = 52.13210564106703 ms；p99_e2el_ms = 36768.75981274061 ms | op010r2 缩减诊断；Mixed 回退漂移，非正式 anchor；workload 由原 unchanged 性能契约确认；`/op010r2_scenario_entry/phase_evidence/decode/metrics` |
| p1024-d256-c64-n128-mixed-milestone / baseline | output_throughput = 572.8130151302091 token/s；mean_ttft_ms = 8914.043798678904 ms；mean_tpot_ms = 76.93429003017681 ms；p99_itl_ms = 1519.5477124582976 ms；p99_e2el_ms = 38065.89794953354 ms | op010r2 缩减诊断；Mixed 回退漂移，非正式 anchor；workload 由原 unchanged 性能契约确认；`/op010r2_scenario_entry/phase_evidence/mixed/metrics` |
| p1024-d256-c64-n128-mixed-milestone / revert | output_throughput = 668.5005349029103 token/s；mean_ttft_ms = 5962.2086378294625 ms；mean_tpot_ms = 72.4852189445907 ms；p99_itl_ms = 1523.967257849872 ms；p99_e2el_ms = 30936.62314643152 ms | op010r2 缩减诊断；Mixed 回退漂移，非正式 anchor；workload 由原 unchanged 性能契约确认；`/op010r2_scenario_entry/phase_evidence/mixed/metrics` |
<!-- baseline-record-review:end -->
