# PR #943：按模型拆分 TP2 MoE helper

已更新 [PR #943](https://github.com/flagos-ai/FlagGems-vllm/pull/943)，提交 `97da71f9`。新增 `_is_qwenvl_tp2_moe_shape` / `_qwenvl_tp2_config`，原Qwen TP2 shape/config helper恢复为upstream逻辑。所有调参/五个Triton kernel/public算子行为不变。

553360项主机行为对照及仓库格式/lint检查通过，远端文件与候选逐字节一致；PR仍正式待评审且最后mergeableTrue。未重跑GPU/graph或完整模型，未改运行容器。[详细记录](optimize/op-001-separate-qwenvl-tp2-helpers.md)。
