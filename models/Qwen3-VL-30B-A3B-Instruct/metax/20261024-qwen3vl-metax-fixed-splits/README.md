# 20261024-qwen3vl-metax-fixed-splits

- [baseline](baseline/README.md)
- [optimize](optimize/README.md)
- [acceptance](acceptance/README.md)

先前诊断系列保留原 split1，prefix cache 开启；本轮 single finally 恢复并核验 graph16/C8/source/argv/env。split16 两次 GPQA 低于64分，拒绝晋级。有限实际采样窗口确认：相同noise下，logits差异跨越top-p边界改变候选集合；CPU参考与实际过滤概率逐位一致。目标窗口结论不外推全部formal错题，整体观测中性未成立。无新端到端性能收益，先前诊断系列终态，其监控当时已停用。详细证据、限制和后续冻结方向见 [op-001](optimize/op-001-fixed-kvcache-splits.md)。

最新用户授权已完成 [op-002 split0完整精度验证](optimize/op-002-auto-kvcache-formal.md)：独立容器保持其他配置和prefix cache开启，先验证正确性/graph，再完整GPQA198（64分）及ERQA400（40分），结束后恢复原split1服务。GPQA完整198题为126正确、63.6364分，低于64，未晋级；ERQA完整400题176正确、44.00分，通过40分。原split1/prefixON已恢复，graph16/C8/source/argv/env当前复核通过，监控已删除。
