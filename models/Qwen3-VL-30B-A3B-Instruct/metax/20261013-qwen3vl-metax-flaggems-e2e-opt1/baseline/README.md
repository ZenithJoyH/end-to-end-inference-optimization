# 20261013-qwen3vl-metax-flaggems-e2e-opt1 / baseline

<!-- e2e:summary:start -->

- 案例：20261013-qwen3vl-metax-flaggems-e2e-opt1
- 当前状态：imported-and-profiled-formal-anchor-incomplete
- 当前候选：—
- 下一步：Optimization/diagnostic results in optimize; user defers model accuracy; retained op002 private, ATen temporary blacklist reverted

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d256-c64-n128-sampling | baseline | output_throughput | 977.8944082636442 | token/s | D256 milestone performance_only; not original D1024/four-scene acceptance |
| p1024-d256-c64-n128-sampling | baseline | p99_ttft_ms | 3750.2232788782567 | ms | D256 milestone performance_only; not original D1024/four-scene acceptance |
| p1024-d256-c64-n128-sampling | baseline | p99_tpot_ms | 63.411635457958084 | ms | D256 milestone performance_only; not original D1024/four-scene acceptance |
| p1024-d256-c64-n128-sampling | baseline | p99_itl_ms | 443.4572266507894 | ms | D256 milestone performance_only; not original D1024/four-scene acceptance |
| p1024-d1024-c64-n128 | baseline | output_throughput | 1133.5905555746235 | token/s | original P1K sampled performance_only; no four-scene/model-accuracy acceptance |
| p1024-d1024-c64-n128 | baseline | p99_ttft_ms | 3705.6466626096517 | ms | original P1K sampled performance_only; no four-scene/model-accuracy acceptance |
| p1024-d1024-c64-n128 | baseline | p99_tpot_ms | 56.08798338772177 | ms | original P1K sampled performance_only; no four-scene/model-accuracy acceptance |
| p1024-d1024-c64-n128 | baseline | p99_itl_ms | 56.57907929271458 | ms | original P1K sampled performance_only; no four-scene/model-accuracy acceptance |

<!-- e2e:summary:end -->

## 用户提供的当前性能记录

历史脚本预先设置三轮、跳过第一轮，以下P4K/P16K为Run2/3的CSV SUMMARY。保留全部原始轮次；P64K当前仅Run1，仍在测试，不计为稳态汇总。尚缺原生JSON、样本与当时服务身份，不能直接作为新软件候选的严格A/B基线。

| 场景（D1024/C64/N128） | 范围 | 输出吞吐 token/s | Mean TTFT ms | Mean TPOT ms | P99 ITL ms | 状态 |
|---|---|---:|---:|---:|---:|---|
| P1024 | 当前正式入口 | — | — | — | — | not_run；独立环境准备后建立 |
| P4096 | 用户历史Run2/3 | 827.88 | 4937.94 | 72.27 | 494.90 | imported-observation |
| P16384 | 用户历史Run2/3 | 321.61 | 86952.51 | 85.03 | 665.01 | imported-observation |
| P32768 | 正式目标 | — | — | — | — | not_run |
| P65536 | 额外场景Run1 | 66.05 | 680644.35 | 99.96 | 1566.47 | incomplete；测试仍在运行 |

TTFT/TPOT包含客户端、排队与调度，不能当作纯设备阶段时间。当前Prefill/Decode/Mixed热点均待trace与实际backend命中确认。约束：保持FlagGems开启，不增加blacklist，不以native/vendor替换获取收益；既有黑名单固定为mm,mm_out,layer_norm,log_softmax。

<!-- baseline-record-review:start -->
## 正式目标覆盖与历史测量

本节是记录审查：原测量状态与角色保持不变，不是新评测回执。`incomplete` 表示此表未闭合正式基线证据；历史、缩减或有观察器的结果须按原范围解释。

| 正式目标 | 正式基线证据状态 | 已记录指标数 | 边界 |
|---|---|---:|---|
| p1024-d1024-c64-n128 | incomplete | 4 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p4096-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p16384-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p32768-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |

数值见上方由 `state.yml/metrics` 生成的指标表；每条新增指标保留 source_pointer，外部原件按原 evidence 查阅。
<!-- baseline-record-review:end -->
