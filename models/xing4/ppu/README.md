# xing4 / PPU-01

本页记录 2026-09-04 至 09-06 的历史实验：在独立容器 `xingchen4-e2e-20260904`、物理PPU4–7上优化输出及总token吞吐，当时保留原容器 `xingchen4-24-new`、PPU0–3和8000端口。再次执行前重新核验服务身份与资源，不能把这些记录当作当前状态。

2026-09-06按用户要求扩展为映射全部16张PPU，当时在容器内用`CUDA_VISIBLE_DEVICES=4,5,6,7`选择物理4–7，保留`/mnt`完整读写映射；调整后只完成映射/命中/C8 核验，未重跑完整性能矩阵。见[设备映射修复](optimize/history/20260906-all-ppu.md)。

- [优化结果与复现](acceptance/README.md)
- [性能配置](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/models/XingChen4-29B-A4B/ppu/acceptance/performance-config.yml)
- [精度配置与正确性护栏](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/models/XingChen4-29B-A4B/ppu/acceptance/accuracy-config.yml)
- [正式精度验收状态](acceptance/accuracy-result.md)
- [基线清单](baseline/state.yml)
- [多轮优化记录](optimize/README.md)
- [MLA补丁](optimize/history/patch-mla-tile16-pr.md)
- [完整案例和实验历史](../../../docs/cases/20260904-xing4-ppu-isolated-e2e/README.md)

GPQA按用户指示暂缓；本轮不声明正式模型精度验收通过。

MLA补丁已在2026-09-07整理为不含实验开关或一次性日志的shape自动分派实现，并完成PPU算子、graph、C8及同设备candidate/revert吞吐复测，`pr_readiness=ready_for_review`。未测试的其他平台和正式模型精度范围见[PR重构实验](optimize/history/20260907-mla-pr-refactor.md)。

<!-- record-archive:start -->
## 本地过程材料归档（2026-11-02）

本案例 2 个过程文件已逐文件 SHA256 校验后移出记录目录。恢复副本：[归档目录](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/models/XingChen4-29B-A4B/ppu)；逐文件原路径、SHA 和恢复路径见[迁移清单](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/migration-manifest.json)。远端原始证据的位置保持不变。

原文中未展开的 `commands/`、脚本文件名及历史命令属于执行时路径；查阅使用上述归档，重新执行前先核验环境和路径。该本地归档不随 Git 提交，也不能替代远端长期保存。
<!-- record-archive:end -->

<!-- case-navigation:start -->
## 完整案例入口

- legacy-platform-layout：[baseline](./baseline/README.md) · [optimize](./optimize/README.md) · [acceptance](./acceptance/README.md)
<!-- case-navigation:end -->
