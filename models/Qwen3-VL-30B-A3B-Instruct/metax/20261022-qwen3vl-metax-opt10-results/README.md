# Qwen3-VL / MetaX / opt10 最新端到端记录

2026-10-22更新。当前生产容器`qwen3vl-p64k-opt-20261015`，mx-59/MetaX C550/TP2/GPU6,7，端口9999。原有gems-opt、内联MoE调优、通用FlagGems采样适配和局部histogram优化保持。

以下为用户opt10完整CSV的SUMMARY；均D1024/C64/N128。1K采用10月22日复测第3–4轮，其余场景采用10月21日第3–4轮；全部原始轮次仍保留，未事后剔除慢轮。

| 输入/输出 | 轮数 | 输出 token/s | 总 token/s | 平均 TTFT ms | 平均 TPOT ms | P99 ITL ms |
|---|---:|---:|---:|---:|---:|---:|
| 1K/1K | 4 | 1511.12 | 3022.26 | 1694.59 | 40.68 | 42.18 |
| 4K/1K | 4 | 1082.16 | 5410.82 | 4808.72 | 54.27 | 462.89 |
| 16K/1K | 4 | 374.66 | 6369.18 | 75029.02 | 79.66 | 642.51 |
| 32K/1K | 4 | 175.74 | 5799.26 | 223132.14 | 85.22 | 1006.30 |
| 64K/1K | 4 | 76.44 | 4968.68 | 588038.78 | 92.34 | 1559.34 |

当前1K/1K稳态已由用户确认：四轮总吞吐3011.30/3039.13/3044.21/3000.31token/s，差幅1.45%。10月21日有波动的8轮及JIT诊断保留为历史，当前表采用新复测；4K旧波动和其他场景数据不变。

- [全部逐轮结果、波动与证据](optimize/records-008-opt10-full-results.md)
- [优化总览及结构化指标](optimize/README.md)
- [当前缺少的基线](baseline/README.md)
- [验收边界](acceptance/README.md)

本案例保存性能归档及本轮全量精度结果；未修改或重启推理服务。GPQA **130/198=65.66分**（阈值64），ERQA **162/400=40.50分**（阈值40），两项均通过。五场景人工数据完整，最终性能验收incomplete。原始结果在`/public-flash/jinghao/qwen3-VL/test/perf_test/benchmark_results/qwen3vl-opt10`，快照在`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-metax-opt10-results`。历史受控GPU0/1与本案例生产GPU6/7分开记录，不混算收益。

当前精度任务：[acc-009 GPQA与ERQA完整评测](optimize/acc-009-gpqa-erqa.md)。新用户实例开启prefix cache，评测保持该配置，不复用先前性能服务身份。
