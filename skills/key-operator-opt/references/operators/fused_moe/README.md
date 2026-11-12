# Fused MoE 配置与执行路径

当前收录 MetaX 案例的配置语义/阶段配置及受控端到端证据，以及PPU的MoE自有TP数值边界诊断；两类证据不可互相替代，范围以case-index为准，不是跨平台性能结论。

Fused MoE 将 token 路由到 top-k 专家，执行 GEMM1、门控激活、GEMM2 与加权归约。Prefill 的大 M 和 Decode 的小 M 应分别检查每个 GEMM 的有效 shape、tile、stage、融合与归约选择。

模型外层与MoE runner可能分别拥有collective，shared/routed合并也可能原地复用输出buffer。检查数值边界应从真实运行对象及早/晚归约互斥条件确认所有权，不能由外层FP32 helper推定内部已使用FP32；抓局部专家输出时须在别名原地修改前取得独立副本。当前PPU限域证据见case-index，不推定其他实现同样具有此路径。

配置文件的存储目录、序列化格式、查表键和执行策略是不同边界。同一 JSON 格式可以由不同实现加载，但不能据此认定它们保留相同的阶段覆盖、最近/精确 M、默认启发式或 fast-path 行为。

本案例 FlagGems-vllm MetaX 私有版本把完整配置表命中标为 is_embedded=True，并据此绕过默认 per-stage fast 配置选择。此结论只针对所记录源码，不外推到所有 vLLM/FlagGems 实现。

- [检查顺序与首个实验](optimization-map.md)
- [案例证据及限制](case-index.md)

根表仍是共享配置基准。只有GEMM2阶段表覆盖实际M范围且BM对齐时，根表非BM调整才可在该范围内限定为GEMM1变化；必须重放真实选择器全域并核验实际dispatch，不能仅凭文件目录命名判断独立性。
