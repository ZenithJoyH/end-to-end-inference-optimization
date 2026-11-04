# 更新前参考环境

从当前源容器快照的专用A clone恢复原Plugin d1653d9及dirty/metadata。已通过镜像/挂载门禁，双卡 graph capture/replay和最小回归已通过；不使用历史分数/性能。原始证据位于 `/public-flash/jinghao/qwen3.6-27B/20261022-qwen36-27b-mx104-plugin-regression`。

完整198题GPQA参考经原生验收器核验：**155/198（78.2828%）**，strict-match，零超时。它是本次迁移精度下限，B启动前已冻结；候选尚未评测。旧版首个性能尝试 `a1-performance` 因三轮预热吞吐波动12.65%未进入稳态，零正式测量轮；全部原始材料保留。新 `a1-performance-warmup5` 按四场景、五预热三测量重跑，所有A/B/A统一用perf-plan-v2，5%窗口与比较阈值不变；尚无性能比较结论。

旧版首个A实例完整矩阵原生check_run复验通过：32/32轮，每场景五预热、三测量，每轮128成功、零失败。P1K/P4K/P16K/P32K三轮输出吞吐中位数为 **1162.73、692.10、230.01、113.68 output token/s**。独立重复与迁移比较待完成，单run核验不代表迁移验收通过。完整指标及SHA见state.yml，原生核验回执位于远端 performance/verification/a1-performance-warmup5.json。

<!-- e2e:summary:start -->

- 案例：20261022-qwen36-27b-mx104-plugin-regression
- 当前状态：incomplete
- 当前候选：release02-7cb5599-contiguous-prefill
- 下一步：diagnose P1K median TTFT 10.015% spread before new comparable baseline; preserve complete first-run evidence

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1024-c64-n128 | baseline | output_throughput | 1162.7258019368135 | token/s | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p1024-d1024-c64-n128 | baseline | total_token_throughput | 2325.451603873627 | token/s | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p1024-d1024-c64-n128 | baseline | mean_ttft_ms | 5230.113986879587 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p1024-d1024-c64-n128 | baseline | p99_ttft_ms | 10936.986049544066 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p1024-d1024-c64-n128 | baseline | mean_tpot_ms | 49.90777721005104 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p1024-d1024-c64-n128 | baseline | p99_tpot_ms | 54.22700027149546 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p1024-d1024-c64-n128 | baseline | mean_itl_ms | 49.90777735751899 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p1024-d1024-c64-n128 | baseline | p99_itl_ms | 45.86456432938575 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p1024-d1024-c64-n128 | baseline | median_e2el_ms | 56260.329329408705 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p1024-d1024-c64-n128 | baseline | p99_e2el_ms | 62146.53339808807 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p4096-d1024-c64-n128 | baseline | output_throughput | 692.1013833697906 | token/s | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p4096-d1024-c64-n128 | baseline | total_token_throughput | 3460.5069168489526 | token/s | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p4096-d1024-c64-n128 | baseline | mean_ttft_ms | 14138.528529423638 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p4096-d1024-c64-n128 | baseline | p99_ttft_ms | 44571.96385836229 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p4096-d1024-c64-n128 | baseline | mean_tpot_ms | 78.47470971366779 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p4096-d1024-c64-n128 | baseline | p99_tpot_ms | 90.85039106883175 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p4096-d1024-c64-n128 | baseline | mean_itl_ms | 78.47470987941453 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p4096-d1024-c64-n128 | baseline | p99_itl_ms | 1424.728146865964 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p4096-d1024-c64-n128 | baseline | median_e2el_ms | 94136.94303762168 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p4096-d1024-c64-n128 | baseline | p99_e2el_ms | 134574.45830577984 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p16384-d1024-c64-n128 | baseline | output_throughput | 230.0051055573704 | token/s | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p16384-d1024-c64-n128 | baseline | total_token_throughput | 3910.0867944752968 | token/s | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p16384-d1024-c64-n128 | baseline | mean_ttft_ms | 98312.22663301742 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p16384-d1024-c64-n128 | baseline | p99_ttft_ms | 253538.64131763577 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p16384-d1024-c64-n128 | baseline | mean_tpot_ms | 166.53699346137574 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p16384-d1024-c64-n128 | baseline | p99_tpot_ms | 240.64593754756123 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p16384-d1024-c64-n128 | baseline | mean_itl_ms | 166.53699364117654 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p16384-d1024-c64-n128 | baseline | p99_itl_ms | 1570.5361649766564 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p16384-d1024-c64-n128 | baseline | median_e2el_ms | 262830.75525797904 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p16384-d1024-c64-n128 | baseline | p99_e2el_ms | 451686.2021176517 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p32768-d1024-c64-n128 | baseline | output_throughput | 113.68311987996138 | token/s | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p32768-d1024-c64-n128 | baseline | total_token_throughput | 3751.5429560387256 | token/s | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p32768-d1024-c64-n128 | baseline | mean_ttft_ms | 302420.17927151755 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p32768-d1024-c64-n128 | baseline | p99_ttft_ms | 523667.3704718612 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p32768-d1024-c64-n128 | baseline | mean_tpot_ms | 193.65055960464395 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p32768-d1024-c64-n128 | baseline | p99_tpot_ms | 257.8025676629061 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p32768-d1024-c64-n128 | baseline | mean_itl_ms | 193.65055979555427 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p32768-d1024-c64-n128 | baseline | p99_itl_ms | 1753.2835177145898 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p32768-d1024-c64-n128 | baseline | median_e2el_ms | 533334.9035624415 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |
| p32768-d1024-c64-n128 | baseline | p99_e2el_ms | 735072.9479982704 | ms | 单 baseline 进程；原校验完整但 P1K TTFT 波动10.01%超5%，整套 incomplete，不能作为有效迁移收益 |

<!-- e2e:summary:end -->

性能比较准入补查：P1K三正式轮TTFT中位数波动 **10.015% > 5%**，因此当前性能结论为 **incomplete**。32轮完整性原生复验通过不能替代比较准入；所有轮次保留，需定位波动后复测。其余主/守护指标轮内波动未超5%；候选尚无性能结果，不能归因迁移回退。

<!-- baseline-record-review:start -->
## 正式目标覆盖与历史测量

本节是记录审查：原测量状态与角色保持不变，不是新评测回执。`incomplete` 表示此表未闭合正式基线证据；历史、缩减或有观察器的结果须按原范围解释。

| 正式目标 | 正式基线证据状态 | 已记录指标数 | 边界 |
|---|---|---:|---|
| p1024-d1024-c64-n128 | incomplete | 10 | 已列出原始观测；是否满足正式基线契约仍以原回执和稳态/身份条件为准。 |
| p4096-d1024-c64-n128 | incomplete | 10 | 已列出原始观测；是否满足正式基线契约仍以原回执和稳态/身份条件为准。 |
| p16384-d1024-c64-n128 | incomplete | 10 | 已列出原始观测；是否满足正式基线契约仍以原回执和稳态/身份条件为准。 |
| p32768-d1024-c64-n128 | incomplete | 10 | 已列出原始观测；是否满足正式基线契约仍以原回执和稳态/身份条件为准。 |

数值见上方由 `state.yml/metrics` 生成的指标表；每条新增指标保留 source_pointer，外部原件按原 evidence 查阅。
<!-- baseline-record-review:end -->
