# 沐曦平台算子优化经验

热点已经定位到算子时，按下面与现场最接近的一项选择首个实验。这里的算子数据来自 C550。迁移到 C588、不同模型或新版 MACA / FlagTree 时，先核对当前 worker 的实际实现、每 rank 的输入和 graph 中的调用频率。主机供给、跨 die 通信和 KV 容量问题另见[平台端到端经验](../../../../docs/metax-optimization-experience.md)。

## vLLM 融合与专用算子

| 现场信号 | 首个实验 | 历史结果与适用范围 |
|---|---|---|
| Fused MoE 某个 M 的 GEMM 很慢 | 从 graph 实际回放计数取 M，再查选择器最终使用的配置。按每 rank 的专家数、dtype 和路由集中度，分别改 GEMM1 或 GEMM2 的一个参数，计时含对齐、激活和归约的完整调用。 | Qwen3.6-35B 的新版主线在 M64 集中路由下，候选完整 MoE 调用慢 9.70%。更换基线后需复测完整入口。[主线复测](../../../../models/Qwen3.6-35B-A3B/metax/20261104-qwen36-mx59-pr1067-verification-001/optimize/pr1067-hardware-001.md) |
| Attention 调 splits 后延迟或答案变化 | 固定 Q/K/V、页映射、采样参数和噪声，比较输出、logits、top-p 集合及首个分叉 token。归约顺序改变时，微测胜出仍要过模型精度。 | Qwen3-VL 在历史同契约下，split=1 的两轮 GPQA 均为 131/198，split=16 的两轮均为 120/198，低于当轮 64% 门槛。单个窗口复现了候选集合从 2 变 1，不能据此解释全部错题或选定其他模型的 splits。[固定 splits 对照](../../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261024-qwen3vl-metax-fixed-splits/optimize/op-001-fixed-kvcache-splits.md) |

## ATen 派发、布局与整数位宽

| 现场信号 | 首个实验 | 历史结果与适用范围 |
|---|---|---|
| BF16 投影前出现转置 copy，随后执行通用 MM | 从上层投影追到运行中的 provider，记录两输入 stride 和输出 dtype。同一份 X/W 对照旧链路、直接消费转置视图的通用实现、能返回 FP32 的 native 实现。用 trace 查旧 copy 是否消失，并测完整投影。 | DeepSeek-V4 的高层 router 入口曾绕过已接入的 vendor MM。M4096/N2048/K4096 的 graph 微测从 2.1495 降到 0.3371 ms，模型 trace 也确认命中 mcBLAS。其他来源的三维 copy 仍存在，该时延只属于受测投影。[调用链与布局对照](../../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/op-004.md) |
| 替换 ATen 后端看似能消除停顿 | 精确到 overload，看各 worker 的注册表及实际调用。固定 MoE、采样和输入，分别切换一个 overload，原实现回切后复测。 | Qwen3-VL 同时关闭 FlagGems 的 `copy_` 和默认 `cumsum` 后，P1K 输出吞吐下降 10.05%，长停顿仍出现。`cumsum.out` 当时仍走 FlagGems，这个组合实验只支持撤回两项一起关闭的方案，单项贡献待测。[两项隔离实验](../../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261013-qwen3vl-metax-flaggems-e2e-opt1/optimize/diag-002-aten-copy-cumsum-isolation.md) |
| 随机采样 trace 中 radix histogram 耗时高，或大物理页 gather 发生地址错误 | 先写出整数表示的量及其上界。局部计数看单 CTA 最多累加多少，地址看物理页号 × 实际 stride，注明元素或字节单位。前者可试收窄累加器，后者必要时在乘法**之前**扩位。 | Qwen3-VL 每 CTA 计数至多 8192，改用 int32 后，固定 top_k=20、top_p=0.8 的 P1K/D1K 输出吞吐提高 19.73%，正式模型精度暂缓。DeepSeek-V4 的 scale 页偏移则需要 int64；修复后 P32 三轮无非法地址，但吞吐波动超出当轮预算。前者验证吞吐，后者验证寻址正确性。[排序与采样对照](../../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261013-qwen3vl-metax-flaggems-e2e-opt1/optimize/op-005-flaggems-sort-sampling.md) · [分页 gather 证据卡](../operators/kv_cache_gather/case-index.md) |
| Mixed 尾批出现新 GEMM 二进制和停顿 | 先区分 FP32 输出投影和 BF16 输出 NT，然后记录实际 M/N/K、配置缓存键、候选试跑数和最终选中的 tile。若只有配置选择需要分桶，仍按实际形状判定边界 mask 和对齐。 | DeepSeek-V4 的 BF16 NT 在 M3688/N64/K4096 每 rank 实际试跑 6 个配置。限定形状域并准备配置后，三轮 P32 测量的 NT 新编译均为零，第三轮仍有两个其他算子的编译。该实验验证了 NT 搜索机制，缺少独立三方对照来量化它对总耗时的贡献。[NT 选参与缓存实验](../../../../models/DeepSeek-V4-Flash-W8A8/metax/20261022-thinking-gpqa-metax103/optimize/op-006.md) |

## 把经验用于当前场景

先确定优化归属。通用 ATen 实现归 FlagGems，vLLM 专用或融合计算归 FlagGems-vllm，Plugin 负责接入公开 API 和选择实现。已有后端适配目标输入时，可先做 `operator/replace` 对照；改变计算、布局、tile 或流水线时，按 `operator/improve` 验证一个机制。同名算子跨库时，以 worker 中的函数来源、注册 key 和设备 kernel 确认实际修改点。[算子层开发规范](../../../../docs/operator-development-standard.md)

若证据指向编译器特性，先核对现场 FlagTree 构建、具体原语及编译产物，再用相同算法、输入和输出语义比较优化过的普通 Triton 与特化实现。观察完整调用里哪笔访存、重排或同步实际减少。沿用当前实验的数值边界、变输入 graph replay 和无 profiler Mixed 对照；记录未命中、回退漂移和另一阶段的指标。新案例若改变了这里的适用范围，补上支持或反驳它的实验链接。[SOP C4](../../../../docs/performance-optimization-sop.md#c4-利用平台编译器特性做算子特化)
