# env-010：25 个生产文件复查

已安装并验证：生产改动 25→24 个文件，新增行 8,519→7,830。复用原生 Attention/Indexer 编排、query quant、gather 与 modular MoE workspace；30 项 CPU、42 项设备逐位比较、TP8 的 10 个 C1/C8 请求和七档 graph capture/replay 均通过。正式精度和性能未运行；其他平台仅 mock 路由验证。完整证据、边界与回退见 [env-010 记录](README.md#env-010attentionindexer-与-moe-原生复用已完成)。

| 文件 | 处理 | 文件行数（旧→新） | 依据 |
|---|---|---|---|
| `vllm_fl/__init__.py` | 保留（本轮字节不变） | 280→280 | 原生 ModelRegistry 接入模型薄层；gdn 注册延后以避免当前 main 导入循环。未复制原生加载/推理流程。 |
| `vllm_fl/dispatch/backends/flaggems/impl/deepseek_v4.py` | 缩减 | 376→368 | 删除不再调用的 qkv RMS / indexer query provider 方法；mHC、SiLU、hash/topk、MetaX GEMM 和 sparse attention provider 保留。 |
| `vllm_fl/dispatch/backends/flaggems/impl/deepseek_v4_attention.py` | 原生 gather | 338→290 | packed FP8 cache gather 直接引用 native Triton helper，12 项 block/window/offset 比较逐位一致；删除已被 native attention/Indexer 调用替代的 RMS/query wrappers。显式导出跨模块原生别名。 |
| `vllm_fl/dispatch/backends/flaggems/register_ops.py` | 缩减 | 423→407 | 删除已原生接管的两个 provider 注册；沿用 main registry 和现有 opt-in 平台隔离。 |
| `vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/__init__.py` | 保留（本轮字节不变） | 1→1 | vendor package 标识，无计算副本；不为减少计数机械改 namespace。 |
| `vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/indexer.py` | 保留（本轮字节不变） | 26→26 | 独立 MetaX deep_gemm BF16 mqa 入口及空输入、缓存目录约定；原生 sparse indexer 的 DeepGEMM API 是 FP8/FP4，不能直接替代。 |
| `vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/mctlass_ops.py` | 保留（本轮字节不变） | 355→355 | 保留 W8A8 scaled-MM、MoE custom-op ABI、fake、kernel-M cache 与 native CutlassInt8 子类；去除在既有支持门禁后不可达的 W4 注册/初始化。 |
| `vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/moe.py` | 删除 | 329→0 | 删除重复 functional MoE 路径；新实现基于原生 modular Experts workspace/activation/reduction，而非将旧函数移入另一文件。 |
| `vllm_fl/dispatch/backends/vendor/metax/patches/__init__.py` | 保留（本轮字节不变） | 22→22 | 只延后 gdn 模型相关导入；修复 main 平台注册与模型层循环，不引入另一套 patch。 |
| `vllm_fl/dsv4_config.py` | 保留（本轮字节不变） | 56→56 | 现有 profile 的 typed opt-in/冻结配置，划分 framework/MoE policy；避免散落环境变量和模型路径特判。 |
| `vllm_fl/models/deepseek_v4.py` | 保留（本轮字节不变） | 356→356 | 继承 native Model/LM 的权重加载、映射、logits、通用转发，MoE/MLP 直接原生；保留 MetaX attention、INT8 scheme、mHC graph 边界和 hash input dtype。 |
| `vllm_fl/ops/deepseek_v4.py` | 保留（本轮字节不变） | 130→130 | 删除 GateLinearFL 整个子类；保留 MetaX embedding masked-fill、INT8 舍入、SiLU custom-op 及 compressor 的 BF16/FP32 GEMM。 |
| `vllm_fl/ops/deepseek_v4_attention.py` | 原生编排 | 1046→804 | forward/attention_impl 和 Indexer.forward 直接继承 vLLM；删除本地 attention custom-op 与整段复制编排；Native FULL 模式装饰器不产生 eager break。使用 native qkv RMS / FP8 query；保留无工厂扩展点的构造、Compressor PDL 适配、INT8 o-proj、MetaX compressor GEMM、HQ16/sparse kernel 边界。删除 checkpoint 中不存在且未使用的 indexer.k_norm。 |
| `vllm_fl/ops/deepseek_v4_indexer_decode.py` | 保留（本轮字节不变） | 490→490 | MetaX paged logits、tree topk 特化数值 kernel；原生 CUDA DeepGEMM/empty CUDA topk 不可用。JIT 数学本轮不改。 |
| `vllm_fl/ops/deepseek_v4_indexer_prefill.py` | 保留（本轮字节不变） | 459→459 | TP query-row sharding、rowshard logits 与通信优化；原生无此分布式计算组织。本轮不改数学或 group lifecycle。 |
| `vllm_fl/ops/deepseek_v4_metax/__init__.py` | 保留（本轮字节不变） | 1→1 | 数值 kernel package 标识，无逻辑副本；不以机械合并减少计数。 |
| `vllm_fl/ops/deepseek_v4_metax/decode.py` | 保留（本轮字节不变） | 1733→1733 | MetaX half-D/QK-fold/blockdiag、HQ16、调参及调度 metadata；native FlashMLA CUDA 扩展不随 empty wheel 安装。 |
| `vllm_fl/ops/deepseek_v4_metax/policy.py` | 保留（本轮字节不变） | 75→75 | 仅对本地 kernel 绑定 launch/autotune metadata，避免改全局编译器或 vendor autotuner；策略本轮不变。 |
| `vllm_fl/ops/deepseek_v4_metax/prefill.py` | 保留（本轮字节不变） | 950→950 | MetaX sparse prefill、half-D/staged/headpack 数值 kernel；原生 NVIDIA FlashMLA 不兼容 MetaX。 |
| `vllm_fl/ops/fused_moe/router.py` | 保留（本轮字节不变） | 284→284 | 现有 RouterFL 的 CachedOp 窄接入，保留 checkpoint hash table alias；native sqrtsoftplus 使用 empty wheel 缺失的 topk_hash_softplus_sqrt CUDA op。 |
| `vllm_fl/ops/prefill_topk_native_op.py` | 保留（本轮字节不变） | 182→182 | mcoplib topk 的 graph-visible custom-op/fake/mutates 契约；native empty 无 persistent_topk CUDA 实现。 |
| `vllm_fl/ops/sparse_attn_indexer.py` | 缩小到 MetaX | 821→642 | 非 MetaX 平台直接调用 native forward_native，包含 native FP4/ROCm/XPU/CUDA 分派；FL custom-op 只承担 MetaX FP8 logit/topk，删除旧 CUDA/FP4 副本。所有 MetaX paged/logit、graph-safe、query-row sharding、tree topk 与开关保留。其他平台只有 mock 路由验证，非硬件通过。 |
| `vllm_fl/patches/deepseek_v4_metax.py` | 保留（本轮字节不变） | 419→419 | 改调用 main prewarm 后只读审计绑定；保留版本守卫的 serial-stream、RMS4096 policy、hash 验证和禁 vllm_metax。serial/RMS 尚无更窄扩展点，PR readiness 仍 experimental。 |
| `vllm_fl/quantization/w8a8/deepseek_v4.py` | 原生 modular MoE | 110→243 | 直接复用 native workspace_shapes/_resize_cache、moe_problem_size、activation、moe_sum 与 quantization；只保留 MCTlass GEMM/no-TLE/kernel-M。去掉 functional 自有 scratch 分配和 output.copy_；chunk 使用各自 workspace slice，保护输出 alias。H-config/SPLIT_K 语义保留，旧未传入 vendor ABI 的 Triton tile/stage 字段不再解析。 |
| `vllm_fl/worker/model_runner.py` | 保留（本轮字节不变） | 7864→7864 | 两行按每个 native KVCacheSpec.cache_dtype_str reshape，保护 FP8 MLA/Indexer 与 FP32 compressor 混合 cache；main WorkerFL 写死 ModelRunnerFL，换整 runner 需更大生命周期改动，收益不抵风险。 |
