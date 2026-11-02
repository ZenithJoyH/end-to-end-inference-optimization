# env-009：30 个生产文件逐项审查

基线 main a696859b；vLLM 0.24 empty ee0da84a。恢复主线项按 HEAD 字节核对。当前候选为 25 个生产文件、8,519 新增生产行；28 项 CPU、14 项组件数值与 TP8/C1/C8/graph 最小回归通过。正式精度和性能未运行。

| 文件 | 决定 | 文件总行数（旧→现） | 依据 |
|---|---|---|---|
| `vllm_fl/__init__.py` | 保留 | 280→280 | 原生 ModelRegistry 接入模型薄层；gdn 注册延后以避免当前 main 导入循环。未复制原生加载/推理流程。 |
| `vllm_fl/dispatch/__init__.py` | 恢复 main | 342→322 | 删除 CachedOp.bind 与专属 prewarm 跳过逻辑；直接使用 main 的预热、freeze、epoch 失效及 strict/fallback 机制。 |
| `vllm_fl/dispatch/backends/flaggems/impl/deepseek_v4.py` | 缩减 | 676→376 | 继承 main FlagGemsBackend 的 9 个通用方法；保留 PR755 mHC、tensor-limit SiLU、hash/topk、router GEMM 及 attention provider。原生 sqrtsoftplus 依赖 empty 包缺失的 CUDA op。 |
| `vllm_fl/dispatch/backends/flaggems/impl/deepseek_v4_attention.py` | 缩减/原生复用 | 347→338 | cache global-index 映射直接调用 vLLM common.ops.cache_utils；保留经验证的 MetaX FGV qkv/gather/concat 与 FP8 layout、attention kernel 契约适配。 |
| `vllm_fl/dispatch/backends/flaggems/register_ops.py` | 保留 | 422→423 | 现有 OpImpl registry 入口，profile opt-in 后才选择 DS provider；没有另建 dispatch；去除 W8A8 profile 不使用的 Marlin/FlagGems CUTLASS 注册。 |
| `vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/__init__.py` | 保留 | 1→1 | vendor package 标识，无计算副本；不为减少计数机械改 namespace。 |
| `vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/indexer.py` | 保留 | 26→26 | 独立 MetaX deep_gemm BF16 mqa 入口及空输入、缓存目录约定；原生 sparse indexer 的 DeepGEMM API 是 FP8/FP4，不能直接替代。 |
| `vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/mctlass_ops.py` | 缩减 | 680→355 | 保留 W8A8 scaled-MM、MoE custom-op ABI、fake、kernel-M cache 与 native CutlassInt8 子类；去除在既有支持门禁后不可达的 W4 注册/初始化。 |
| `vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/moe.py` | 缩减/原生复用 | 777→329 | native get_default_config、moe_kernel_quantize_input、activation、moe_sum；只保留 W8A8 vendor 序列、H 前缀配置与 no-TLE 对齐。原生 TritonExperts.apply 硬编码两次 Triton GEMM，无单独 GEMM hook，不能安全全量继承。 |
| `vllm_fl/dispatch/backends/vendor/metax/metax.py` | 恢复 main | 245→223 | 删除重复包装 native fused_indexer_q_rope_quant 的未命中 vendor 候选；当前 profile 仍使用已验证 FlagGems provider。 |
| `vllm_fl/dispatch/backends/vendor/metax/patches/__init__.py` | 保留 | 22→22 | 只延后 gdn 模型相关导入；修复 main 平台注册与模型层循环，不引入另一套 patch。 |
| `vllm_fl/dispatch/backends/vendor/metax/register_ops.py` | 恢复 main | 104→96 | 删除上一项重复 native-wrapper 的注册。 |
| `vllm_fl/dsv4_config.py` | 保留 | 56→56 | 现有 profile 的 typed opt-in/冻结配置，划分 framework/MoE policy；避免散落环境变量和模型路径特判。 |
| `vllm_fl/models/deepseek_v4.py` | 保留/已有原生复用 | 356→356 | 继承 native Model/LM 的权重加载、映射、logits、通用转发，MoE/MLP 直接原生；保留 MetaX attention、INT8 scheme、mHC graph 边界和 hash input dtype。 |
| `vllm_fl/ops/custom_ops.py` | 恢复 main | 197→189 | 删除 gated_layer 特例，使用 native GateLinear，通用 OOT registry 零改动。 |
| `vllm_fl/ops/deepseek_v4.py` | 缩减/原生复用 | 171→130 | 删除 GateLinearFL 整个子类；保留 MetaX embedding masked-fill、INT8 舍入、SiLU custom-op 及 compressor 的 BF16/FP32 GEMM。 |
| `vllm_fl/ops/deepseek_v4_attention.py` | 保留/已有原生复用 | 1046→1046 | 继承 native FlashMLA 的 cache spec/forward_mqa，原生 SWA metadata build、IndexerCache、Compressor 构造/状态缓存；保留 MetaX ctor 注入与 INT8/稀疏 graph 执行。原生 compressor 即使 launch_pdl=False 也被 FlagTree 拒绝，须省略 keyword。 |
| `vllm_fl/ops/deepseek_v4_indexer_decode.py` | 保留 | 490→490 | MetaX paged logits、tree topk 特化数值 kernel；原生 CUDA DeepGEMM/empty CUDA topk 不可用。JIT 数学本轮不改。 |
| `vllm_fl/ops/deepseek_v4_indexer_prefill.py` | 保留 | 459→459 | TP query-row sharding、rowshard logits 与通信优化；原生无此分布式计算组织。本轮不改数学或 group lifecycle。 |
| `vllm_fl/ops/deepseek_v4_metax/__init__.py` | 保留 | 1→1 | 数值 kernel package 标识，无逻辑副本；不以机械合并减少计数。 |
| `vllm_fl/ops/deepseek_v4_metax/decode.py` | 保留 | 1733→1733 | MetaX half-D/QK-fold/blockdiag、HQ16、调参及调度 metadata；native FlashMLA CUDA 扩展不随 empty wheel 安装。 |
| `vllm_fl/ops/deepseek_v4_metax/policy.py` | 保留 | 75→75 | 仅对本地 kernel 绑定 launch/autotune metadata，避免改全局编译器或 vendor autotuner；策略本轮不变。 |
| `vllm_fl/ops/deepseek_v4_metax/prefill.py` | 保留 | 950→950 | MetaX sparse prefill、half-D/staged/headpack 数值 kernel；原生 NVIDIA FlashMLA 不兼容 MetaX。 |
| `vllm_fl/ops/fused_moe/router.py` | 保留 | 284→284 | 现有 RouterFL 的 CachedOp 窄接入，保留 checkpoint hash table alias；native sqrtsoftplus 使用 empty wheel 缺失的 topk_hash_softplus_sqrt CUDA op。 |
| `vllm_fl/ops/prefill_topk_native_op.py` | 保留 | 182→182 | mcoplib topk 的 graph-visible custom-op/fake/mutates 契约；native empty 无 persistent_topk CUDA 实现。 |
| `vllm_fl/ops/sparse_attn_indexer.py` | 缩减/原生复用 | 911→821 | 直接原生 workspace shapes、quant cache view、fake；已有 native __init__。保留 MetaX BF16 logit、select-all/topk、graph 及 query-shard 分支；其他模型共享分支保留。 |
| `vllm_fl/patches/deepseek_v4_metax.py` | 缩减/主线复用 | 407→419 | 改调用 main prewarm 后只读审计绑定；保留版本守卫的 serial-stream、RMS4096 policy、hash 验证和禁 vllm_metax。serial/RMS 尚无更窄扩展点，PR readiness 仍 experimental。 |
| `vllm_fl/platform.py` | 恢复 main | 692→684 | attention backend 选择只发生在配置阶段，直接使用现有 call_op；不需要 DS CachedOp。 |
| `vllm_fl/quantization/w8a8/deepseek_v4.py` | 保留/已有原生复用 | 110→110 | native CompressedTensorsConfig/INT8 scheme/MoE method 继承，只选 MetaX linear kernel 与 experts_cls；不复制权重协议。 |
| `vllm_fl/worker/model_runner.py` | 保留 | 7864→7864 | 两行按每个 native KVCacheSpec.cache_dtype_str reshape，保护 FP8 MLA/Indexer 与 FP32 compressor 混合 cache；main WorkerFL 写死 ModelRunnerFL，换整 runner 需更大生命周期改动，收益不抵风险。 |
