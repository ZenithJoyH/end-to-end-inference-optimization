# Gated Delta Rule：限域实现与状态精度

本目录目前只有Qwen3.6-27B/MetaX C550案例，未形成跨平台不变量。先确认实际运行函数、版本和state ABI：本案例FG-vLLM29e80363的MetaX runtime prefill是V-major `[N,H,V,K]`，同仓generic实现是K-major；K=V时shape不足以验证布局。

递推可按V-major写为 `H'=exp(g)*H`，`delta=beta*(v-H'@k)`，`H=H'+delta[:,None]*k[None,:]`，输出为`scale*H@q`。参考应从相同的量化后输入建立，额外比较FP64公式，避免把输入量化误差混进实现误差。最终state采用FP32存储不能证明WY、创新量、状态投影和跨组块更新都保持FP32。

原.002/.02下单个BF16组块state失败在CPU显式舍入模型中复现；移除空序列后的active state逐位相同，排除该失败来自空段语义。FP32加权输入 alone修复小矩阵，但未修复257token慢衰减状态，完整FP32中间链通过。此结论不证明上游数学公式或所有shape存在错误，不等于历史GPQA根因，也未证明性能收益。

先读[优化地图](optimization-map.md)，再读[证据卡](case-index.md)。FP32中间链是正确性基准，性能代价需要Prefill/Decode/Mixed实测。后续补偿BF16或tile优化必须保留多组块、慢衰减、空段、非对称/非方形state、非连续输入及graph回归。
