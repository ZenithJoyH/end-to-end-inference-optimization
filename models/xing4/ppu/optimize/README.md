# 多轮优化记录

本目录保存 xing4 / PPU 的当前优化状态和人类可读历史。Agent 事实入口为 [state.yml](state.yml)，历史结论位于 `history/`，原始脚本、补丁、日志和结果留在外部产物路径。未经最终验收的中间结果不得从本目录直接宣称达标。

优化点 [MLA Decode head tile](op-001-mla-decode-head-tile.md) 汇总了八组历史测量。P1K 的回退与重新启动候选分别为 809.12 和 1582.19 输出 tok/s。

## 当前轮次索引

| 阶段 | 内容 | 结果位置 |
|---|---|---|
| 瓶颈定位 | MLA dense decode 在四个 rank 上约占 GPU kernel 累计时间 60.6%–60.9% | [案例观测](../../../../docs/cases/20260904-xing4-ppu-isolated-e2e/mla-observation.md) |
| 单变量优化 | `BLOCK_H 64→16`，限定 H8/DQK576/DV512/SQ1/BF16/page16或64 | [实验记录](../../../../docs/cases/20260904-xing4-ppu-isolated-e2e/mla-tile-experiment.md) |
| 多轮性能复测 | baseline、candidate、revert 和 fresh candidate，多种输入长度 | [逐轮历史](../../../../docs/cases/20260904-xing4-ppu-isolated-e2e/throughput-results.md) / [紧凑测量](performance-measurements.json) |
| PR重构 | 去除实验环境变量，按能力与shape自动分派；同设备candidate/revert复测 | [实验记录](history/20260907-mla-pr-refactor.md) |
| 实现产物 | FlagGems MLA 最终源码 revision、SHA 与 PR 说明；patch 文件不再存放于模型目录 | [PR说明](history/patch-mla-tile16-pr.md) |

历史复现条件见 [history/reproduction.md](history/reproduction.md)。新任务执行仍统一使用公共 `scripts/`、
`evaluation/` 与 `test/`，完整结论和远端原始产物位置仍以
[案例目录](../../../../docs/cases/20260904-xing4-ppu-isolated-e2e/README.md) 为权威来源。
