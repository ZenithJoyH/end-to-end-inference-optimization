# ci-003-export-order 修复PR规则检查

- 状态：完成；范围仅PR #1069的MetaX `__all__`顺序，无推理代码或容器变更。
- 当前head：e635daac04def3f603714928858a977a1a31ea9f。
- 原始失败：[rule-check run 41799746290](https://github.com/flagos-ai/FlagGems-vllm/actions/runs/41799746290)，job126472314404。`basic ci` run41799746664已通过。
- 根因：`check_init_exports.py`要求casefold排序，MetaX列表将`top_k_top_p`放在`SUPPORTED_FP8_DTYPE`前。其余metadata、测试marker、ATen及benchmark规则通过。
- 修复：只重排这两个导出项，不改变import、导出集合、算子实现、测试条件或CI门禁。
- 验证：本地先复现原失败，再执行完整rule-check等价命令及pre-commit，提交后检查GitHub新head的CI终态。
- 原始日志与有限修复工作文件：本机临时目录`/tmp/qwen3vl-topk-pr-20261104/ci003`；不产生远端GPU任务，不重复原数值/性能测试。

## 修复与验证

采用仓库`sort_exports.py --fix --files <MetaX init>`，唯一补丁是交换两个相邻导出项。修复前本地精确复现原失败；修复后metadata、所有12个init导出、test markers、ATen及benchmark覆盖检查通过，54项CI工具单测和pinned actions检查通过，pre-commit全部适用hook通过。AST核验确认导出集合及其余代码不变。

已提交`ce0feddceb0d74a031081e57ce9ff9d24fef3b84`，发布文件读回与本地精确一致（git blob74993170）。新的[rule-check run41800956811](https://github.com/flagos-ai/FlagGems-vllm/actions/runs/41800956811)及[basic ci run41800957375](https://github.com/flagos-ai/FlagGems-vllm/actions/runs/41800957375)均completed/success；basic包含code style、目标选择、MetaX MACA3.7.2/3.8.1及汇总通过，NVIDIA按仓库策略skipped，CLA成功。CI选择/能力限制保持原状，不把环境CI通过冒充新增91项设备测试；原op002数值和性能证据保留。

最终PR head仍为ce0fedd，mergeable=true、Draft待review。未改CI配置、容器、算子或采样代码，无重跑数值/性能或生产部署。
