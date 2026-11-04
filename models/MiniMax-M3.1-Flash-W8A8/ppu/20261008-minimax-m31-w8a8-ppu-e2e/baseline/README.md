# 20261008-minimax-m31-w8a8-ppu-e2e / baseline

本案例固定为 **TP16**。由原混合记录按已记录身份拆分；不表示新的评测或当前运行事实。

<!-- e2e:summary:start -->

- 案例：20261008-minimax-m31-w8a8-ppu-e2e
- 当前状态：original-target-incomplete; recovery diagnostic baseline complete
- 当前候选：—
- 下一步：—

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1-c64-n128-prefill | baseline | total_token_throughput_median | 9502.84585322317 | token/s | TP16 Prefill 诊断；10.744% 波动，比较精度受限 |
| p1024-d128-c64-n64-recovery | baseline | total_token_throughput_median | 988.826686996797 | token/s | TP16 缩减 Mixed；非正式 P1K/D1K |
| p1024-d128-c64-n64-recovery | baseline | p50_tpot_median_ms | 552.4913169751604 | ms | TP16 缩减 Mixed 中的 Decode 代理；非纯设备阶段时间 |
| p1024-d128-c64-n64-recovery | baseline | output_throughput_median | 109.869631888533 | token/s | TP16 缩减 Mixed 中的 Decode 代理；非纯设备阶段时间 |
| p1024-d1024-c64-n128 | baseline | total_token_throughput | 2466.068087893935 | token/s | TP16 实验配置基线；不同于原 anchor；formal_closure=false |
| p1024-d1024-c64-n128 | baseline | p99_ttft_ms | 6351.736887097359 | ms | TP16 实验配置基线；不同于原 anchor；formal_closure=false |
| p1024-d1024-c64-n128 | baseline | p99_tpot_ms | 51.242391312848106 | ms | TP16 实验配置基线；不同于原 anchor；formal_closure=false |
| p1024-d1024-c64-n128 | baseline | p99_itl_ms | 48.0322708748281 | ms | TP16 实验配置基线；不同于原 anchor；formal_closure=false |
| p1024-d1024-c64-n128 | baseline | p99_e2el_ms | 57016.24516127631 | ms | TP16 实验配置基线；不同于原 anchor；formal_closure=false |

<!-- e2e:summary:end -->

<!-- baseline-record-review:start -->
## 正式目标覆盖与历史测量

本节是记录审查：原测量状态与角色保持不变，不是新评测回执。`incomplete` 表示此表未闭合正式基线证据；历史、缩减或有观察器的结果须按原范围解释。

| 正式目标 | 正式基线证据状态 | 已记录指标数 | 边界 |
|---|---|---:|---|
| p1024-d1024-c64-n128 | deferred-too-slow/incomplete | 5 | first warmup exceeded pre-frozen600second round budget; no native complete result |
| p4096-d1024-c64-n128 | not_run | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p16384-d1024-c64-n128 | not_run | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p32768-d1024-c64-n128 | not_run | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |

数值见上方由 `state.yml/metrics` 生成的指标表；每条新增指标保留 source_pointer，外部原件按原 evidence 查阅。
<!-- baseline-record-review:end -->
