# MLA Decode 的 head tile 从 64 调到 16

xing4 在 PPU-01 上使用 TP4，每个 rank 处理 8 个 head。四个 rank 的短 trace 中，dense decode 占 kernel 累计时间约 61%。原实现按 64 个 head 分块，这次将 BLOCK_H 调到 16，减少无效 head 计算。

本轮修改 FlagGems 的 MLA dense decode kernel，初始条件为 H8、DQK576、DV512、SQ1、BF16、page16/64。reference 数值检查、graph 回放与 C8 最小回归通过。后续 PR 按能力和 shape 自动分派，H8/H16 覆盖记录见[PR 重构实验](history/20260907-mla-pr-refactor.md)。

| P/D/C/N | 角色 | 输出 tok/s | 总 tok/s | mean TTFT (ms) | P99 TPOT (ms) |
|---|---|---:|---:|---:|---:|
| 1024 / 1024 / 64 / 128 | baseline | 757.01 | 1514.02 | 4080.64 | 85.98 |
| 1024 / 1024 / 64 / 128 | candidate | 1337.59 | 2675.18 | 5190.97 | 46.95 |
| 4096 / 256 / 64 / 64 | candidate | 400.17 | 6802.95 | 14762.07 | 151.30 |
| 16384 / 256 / 32 / 32 | candidate | 54.86 | 3566.05 | 67736.65 | 547.15 |
| 1024 / 1024 / 64 / 128 | revert | 809.12 | 1618.25 | 3611.44 | 77.13 |
| 4096 / 256 / 64 / 64 | revert | 231.04 | 3927.70 | 17976.70 | 264.38 |
| 16384 / 256 / 32 / 32 | revert | 41.59 | 2703.56 | 70683.40 | 706.99 |
| 1024 / 1024 / 64 / 128 | fresh-candidate | 1582.19 | 3164.38 | 3038.42 | 40.67 |

每行取该历史运行两轮测量值的中位数。P1K 同配置回退与重新启动候选的输出吞吐为 809.12 和 1582.19 tok/s，原记录保留该改动。P4K、P16K 使用缩减负载。GPQA 暂缓，正式四场景验收状态为 incomplete。

逐轮结果和 SHA 见[测量账本](performance-measurements.json)。路径命中、误差阈值和回退方法见[单变量实验](../../../../docs/cases/20260904-xing4-ppu-isolated-e2e/mla-tile-experiment.md)。
