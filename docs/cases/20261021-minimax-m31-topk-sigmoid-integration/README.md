# MiniMax-M3.1 算子接入与适配整理

独立容器 `minimaxM3.1-opt-topk-sigmoid-20261021`：FV官方main0dfb5cd加保留优化，Thead完整experts已补齐packed SwiGLU-OAI及3个gemm1参数；Plugin桥接按要求保留。FV29+Plugin118 CPU契约通过，GPU/graph仅收集未执行，无模型服务或正式精度/性能结果。

[当前状态](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-minimax-m31-topk-sigmoid-integration/optimize/README.md) · [Thead完整入口支持](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-minimax-m31-topk-sigmoid-integration/optimize/op-003.md) · [整体适配审查](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-minimax-m31-topk-sigmoid-integration/optimize/review-002.md)

远端 `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-integration`。

完整experts与Plugin桥接兼容核对：实际Thead CPU量化与vLLM源码算术参照在BF16/FP16半整数各4/7不同，FP16零行scale=0；默认tile不命中既有K256白名单，完整入口尚未接入激活量化融合。保留桥接，源码和模型服务未改；详见 ../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-minimax-m31-topk-sigmoid-integration/optimize/compat-004.md。无新精度/性能结论。

op-005已在独立容器实现完整split动态W8A8的量化/融合/受限配置修复，仅FV两文件；58 FV+118 Plugin CPU通过。16卡全部占用，实机/graph/model未运行，Plugin桥接仍保持，无新精度gate或性能结果。详见 ../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-minimax-m31-topk-sigmoid-integration/optimize/op-005.md。
