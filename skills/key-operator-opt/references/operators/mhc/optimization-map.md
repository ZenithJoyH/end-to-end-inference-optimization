# mHC 优化地图

## Decode pre backend 替换

| 字段 | 决策 |
|---|---|
| 信号 | 端到端 phase trace 中 `mhc_pre` 是稳定热点，且候选实现能在真实 shape 上复现明显延迟差异。 |
| 匹配键 | stage=Decode、hc_mult、hidden、dtype、residual layout、TP、graph 模式、目标平台和实际 dispatch 均须一致。 |
| 机制 | 替换 pre 实现，减少每层 RMSNorm、mix 生成与 residual 聚合的 kernel 时间；不改变模型语义。 |
| 首个实验 | 先覆盖真实小 M、边界 M 与 Prefill M 的数值和 graph capture/两次 replay，再立即做一个同 workload 的短端到端 A/B；不要仅凭单算子加速扩大实现范围。 |
| 通过证据 | 真实服务 rank 命中目标 impl、direct correctness、graph replay、稳定重复轮，以及端到端主指标达到预冻结门槛且跨阶段 guard 不回退。 |
| 停止条件 | 服务吞吐不升、TTFT/TPOT 回退、图执行改变 overlap/scheduling、或 backend 命中不完整时立即恢复原 dispatch。 |
| 证据等级 | `reproduced`，但仅限 GLM-5.3-Flash/PPU/TP16/hc_mult=4/hidden=4096/P1K-D1K。 |
| 来源 | [GLM-5.3-Flash PPU mHC 负优化案例](case-index.md#glm-53-flash--ppu--graph-decode-pre-backend-替换)。 |

当前反例表明，mHC 属于每层高频小算子时，graph 中的调度、相邻 kernel 和潜在重叠
会使 isolated kernel 时间与端到端收益脱钩。后续相同场景的验证顺序应是“小矩阵
correctness/graph → 最小服务 A/B → 完整 shape 扩展”，而不是在微基准通过后直接做
大范围 backend 切换。
