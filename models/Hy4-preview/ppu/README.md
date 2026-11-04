# Hy4-preview / PPU

当前任务：`20260914-hy4-preview-ppu-e2e`。当前处于 P16K 优化阶段；最新缩减
milestone 已通过并保留，正式父场景与当前源码精度 gate 尚未完成。

## 当前快照（2026-09-21）

- 目标环境：`PPU-07`，16× PPU-ZW810E；源适配容器 `hy4`，独立优化容器
  `hy4-opt-20260914`。
- 模型：`/mnt/cpfs/models/Hy4-preview-W8A8-linear-moe/`，served model `hy4`。
- 当前正式目标：`P16384/D1024/C64/N128`。
- 最新保留候选：cached-prefill sparse MLA hybrid，即 full-prefix grouped、
  cached-prefill native 与 small-SQ split-K 的分段选择。
- 最新性能证据：`P16384/D128/C16/N16` profiler-off A/B/revert 的 output
  throughput 为 `12.9728 / 13.5640 / 12.9755 tok/s`，候选相对基线提升
  `4.558%`；该数字只属于缩减 milestone，不能替代正式 P16K 结果。
- 精度边界：2026-09-19 冻结身份的正式 GPQA 为 `92.93%`，但不覆盖当前
  未提交候选源码；当前组合仍需重新绑定或重新评测。
- 运行状态：候选源码尚未提交、未推送；模型服务已停止，端口 8010 空闲。

## 文档入口

- [基线记录](baseline/README.md)：初始 P4K scout 基线及其适用边界。
- [优化实验](optimize/README.md)：当前候选、实验索引、保留/拒绝结论与下一步。
- [验收状态](acceptance/README.md)：历史正式精度 gate 与最终验收缺口。
- [案例总览](../../../docs/cases/20260914-hy4-preview-ppu-e2e/README.md)：跨阶段时间线与证据摘要。

`baseline/` 保存进入优化阶段的基线，`optimize/` 保存单变量实验、失败项和候选
补丁，`acceptance/` 只记录可审计的 gate 与最终验收状态。结构化事实以各目录的
`state.yml` 为准。

## PPU-03 独立案例（2026-10-20）

- [2026-10-21端到端优化](20261021-hy4-preview-ppu03-e2e/README.md)：profiling主机OOM已定位；81轮缩减B/C/R完成，Prefill/Mixed通过（Mixed4.84x），Decode异步分批与Prefill干扰已取证；补采28.6s定位TopK首次JIT/TTGIR，原incomplete保留；当前仅保留fw002固定版本的一处PPU编译参数补丁，启动/16rank replay/分页及精确5行Mixed均通过，未开始精度评测。
- [初步性能探索](20261020-hy4-preview-ppu03-initial-perf/README.md)：三阶段缩减初测完成；512候选未保留，原8010已恢复并验证，两个gems-opt不变，未跑GPQA。
- [Plugin迁移与graph修复](20261018-hy4-preview-ppu03-migration/README.md)：性能任务的已验证输入。

- [PPU-03 env031 / 8192预算独立对比](20261020-hy4-preview-ppu03-batched8192/README.md)：新版FGV独立初测完成；8192未保留，原2048已恢复并验证；无GPQA。

<!-- record-archive:start -->
## 本地过程材料归档（2026-11-02）

本案例 6 个过程文件已逐文件 SHA256 校验后移出记录目录。恢复副本：[归档目录](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/models/Hy4-preview/ppu)；逐文件原路径、SHA 和恢复路径见[迁移清单](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/migration-manifest.json)。远端原始证据的位置保持不变。

原文中未展开的 `commands/`、脚本文件名及历史命令属于执行时路径；查阅使用上述归档，重新执行前先核验环境和路径。该本地归档不随 Git 提交，也不能替代远端长期保存。
<!-- record-archive:end -->

<!-- case-navigation:start -->
## 完整案例入口

- 20261015-hy4-preview-ppu13-clone：[baseline](20261015-hy4-preview-ppu13-clone/baseline/README.md) · [optimize](20261015-hy4-preview-ppu13-clone/optimize/README.md) · [acceptance](20261015-hy4-preview-ppu13-clone/acceptance/README.md)
- 20261018-hy4-preview-ppu03-migration：[baseline](20261018-hy4-preview-ppu03-migration/baseline/README.md) · [optimize](20261018-hy4-preview-ppu03-migration/optimize/README.md) · [acceptance](20261018-hy4-preview-ppu03-migration/acceptance/README.md)
- 20261020-hy4-preview-ppu03-batched8192：[baseline](20261020-hy4-preview-ppu03-batched8192/baseline/README.md) · [optimize](20261020-hy4-preview-ppu03-batched8192/optimize/README.md) · [acceptance](20261020-hy4-preview-ppu03-batched8192/acceptance/README.md)
- 20261020-hy4-preview-ppu03-initial-perf：[baseline](20261020-hy4-preview-ppu03-initial-perf/baseline/README.md) · [optimize](20261020-hy4-preview-ppu03-initial-perf/optimize/README.md) · [acceptance](20261020-hy4-preview-ppu03-initial-perf/acceptance/README.md)
- 20261021-hy4-preview-ppu03-e2e：[baseline](20261021-hy4-preview-ppu03-e2e/baseline/README.md) · [optimize](20261021-hy4-preview-ppu03-e2e/optimize/README.md) · [acceptance](20261021-hy4-preview-ppu03-e2e/acceptance/README.md)
- legacy-platform-layout：[baseline](./baseline/README.md) · [optimize](./optimize/README.md) · [acceptance](./acceptance/README.md)
<!-- case-navigation:end -->
