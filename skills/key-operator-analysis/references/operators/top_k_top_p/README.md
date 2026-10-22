# Top-k / top-p sampling

先核验真实输入值和调用路径：FP32 dtype不等于值无法用BF16精确表示。当前MetaX values-only实现以设备端全batch检查选择BF16 counting或FP32 radix；任意一行存在非精确值可使整个batch进入radix。

排序、top-k阈值、softmax/CDF、稳定tie掩码和RNG是不同环节。优化整数计数应保持每桶精确值与原有序key映射；缩短CDF或改变浮点归约则需要额外数值论证，不能混为同一低风险改动。

使用顺序：[优化地图](optimization-map.md) → [限域证据卡](case-index.md)。当前仅有MetaX C550/FlagTree3.6.0/Qwen3-VL TP2证据，不是跨平台调参建议。
