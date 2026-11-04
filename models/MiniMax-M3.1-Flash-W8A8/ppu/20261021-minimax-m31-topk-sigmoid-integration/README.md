# 20261021-minimax-m31-topk-sigmoid-integration

- [基线](baseline/README.md)
- [接入与验证](optimize/README.md)
- [验收](acceptance/README.md)

完整experts与Plugin桥接兼容核对：实际Thead CPU量化与vLLM源码算术参照在BF16/FP16半整数各4/7不同，FP16零行scale=0；默认tile不命中既有K256白名单，完整入口尚未接入激活量化融合。保留桥接，源码和模型服务未改；详见 optimize/compat-004.md。无新精度/性能结论。

op-005已在独立容器实现完整split动态W8A8的量化/融合/受限配置修复，仅FV两文件；58 FV+118 Plugin CPU通过。16卡全部占用，实机/graph/model未运行，Plugin桥接仍保持，无新精度gate或性能结果。详见 optimize/op-005.md。
