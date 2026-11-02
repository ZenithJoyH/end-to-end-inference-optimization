# env-011：24 个生产文件复查

已安装并验证：生产改动 24→23 个文件，新增行 7,830→7,775；model_runner 恢复 Plugin main 原文，全局多流 patch 已删除。30 项 CPU、42 项 GPU 缓存布局、3 项原生 helper、TP8 的 10 个 C1/C8 请求与七档 graph capture/replay 均通过。正式精度/性能及其他平台硬件未验证。完整证据与回退见 [当前交付](README.md)。

| 文件 | 处理 | 文件行数（旧→新） | 依据 |
|---|---|---|---|
| `vllm_fl/__init__.py` | 保留（本轮字节不变） | 280→280 | 原生 ModelRegistry 接入模型薄层；gdn 注册延后以避免当前 main 导入循环。未复制原生加载/推理流程。 |
| `vllm_fl/dispatch/backends/flaggems/impl/deepseek_v4.py` | 保留（本轮字节不变） | 368→368 | 删除不再调用的 qkv RMS / indexer query provider 方法；mHC、SiLU、hash/topk、MetaX GEMM 和 sparse attention provider 保留。 |
| `vllm_fl/dispatch/backends/flaggems/impl/deepseek_v4_attention.py` | 保留（本轮字节不变） | 290→290 | packed FP8 cache gather 直接引用 native Triton helper，12 项 block/window/offset 比较逐位一致；删除已被 native attention/Indexer 调用替代的 RMS/query wrappers。显式导出跨模块原生别名。 |
| `vllm_fl/dispatch/backends/flaggems/register_ops.py` | 保留（本轮字节不变） | 407→407 | 删除已原生接管的两个 provider 注册；沿用 main registry 和现有 opt-in 平台隔离。 |
| `vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/__init__.py` | 保留（本轮字节不变） | 1→1 | vendor package 标识，无计算副本；不为减少计数机械改 namespace。 |
| `vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/indexer.py` | 保留（本轮字节不变） | 26→26 | 独立 MetaX deep_gemm BF16 mqa 入口及空输入、缓存目录约定；原生 sparse indexer 的 DeepGEMM API 是 FP8/FP4，不能直接替代。 |
| `vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/mctlass_ops.py` | 保留（本轮字节不变） | 355→355 | 保留 W8A8 scaled-MM、MoE custom-op ABI、fake、kernel-M cache 与 native CutlassInt8 子类；去除在既有支持门禁后不可达的 W4 注册/初始化。 |
| `vllm_fl/dispatch/backends/vendor/metax/patches/__init__.py` | 保留（本轮字节不变） | 22→22 | 只延后 gdn 模型相关导入；修复 main 平台注册与模型层循环，不引入另一套 patch。 |
| `vllm_fl/dsv4_config.py` | 保留（本轮字节不变） | 56→56 | 现有 profile 的 typed opt-in/冻结配置，划分 framework/MoE policy；避免散落环境变量和模型路径特判。 |
| `vllm_fl/models/deepseek_v4.py` | 取消无用 stream 构造 | 356→350 | 模型不再创建从未使用的 3 个 torch.cuda.Stream；原构造、参数、原生模型方法、MetaX mHC 与 hash dtype 行为不变。 |
| `vllm_fl/ops/deepseek_v4.py` | 保留（本轮字节不变） | 130→130 | 删除 GateLinearFL 整个子类；保留 MetaX embedding masked-fill、INT8 舍入、SiLU custom-op 及 compressor 的 BF16/FP32 GEMM。 |
| `vllm_fl/ops/deepseek_v4_attention.py` | 清理构造与原生顺序路径 | 804→795 | 删除未使用的 indexer_aux_stream 选择，显式传 None，沿用原生 forward/attention_impl/Indexer.forward 与顺序 helper。原生 Attention/Indexer/Compressor 仅为 nn.Module/AttentionLayerBase，未实现 CustomOp/PluggableLayer 构造替换或组件工厂；因此保留一次静态注册的显式构造、MetaX SWA scheduler 与 Compressor PDL adapter，拒绝全局替换或重复构造。 |
| `vllm_fl/ops/deepseek_v4_indexer_decode.py` | 保留（本轮字节不变） | 490→490 | MetaX paged logits、tree topk 特化数值 kernel；原生 CUDA DeepGEMM/empty CUDA topk 不可用。JIT 数学本轮不改。 |
| `vllm_fl/ops/deepseek_v4_indexer_prefill.py` | 保留（本轮字节不变） | 459→459 | TP query-row sharding、rowshard logits 与通信优化；原生无此分布式计算组织。本轮不改数学或 group lifecycle。 |
| `vllm_fl/ops/deepseek_v4_metax/__init__.py` | 保留（本轮字节不变） | 1→1 | 数值 kernel package 标识，无逻辑副本；不以机械合并减少计数。 |
| `vllm_fl/ops/deepseek_v4_metax/decode.py` | 保留（本轮字节不变） | 1733→1733 | MetaX half-D/QK-fold/blockdiag、HQ16、调参及调度 metadata；native FlashMLA CUDA 扩展不随 empty wheel 安装。 |
| `vllm_fl/ops/deepseek_v4_metax/policy.py` | 保留（本轮字节不变） | 75→75 | 仅对本地 kernel 绑定 launch/autotune metadata，避免改全局编译器或 vendor autotuner；策略本轮不变。 |
| `vllm_fl/ops/deepseek_v4_metax/prefill.py` | 保留（本轮字节不变） | 950→950 | MetaX sparse prefill、half-D/staged/headpack 数值 kernel；原生 NVIDIA FlashMLA 不兼容 MetaX。 |
| `vllm_fl/ops/fused_moe/router.py` | 保留（本轮字节不变） | 284→284 | 现有 RouterFL 的 CachedOp 窄接入，保留 checkpoint hash table alias；native sqrtsoftplus 使用 empty wheel 缺失的 topk_hash_softplus_sqrt CUDA op。 |
| `vllm_fl/ops/prefill_topk_native_op.py` | 保留（本轮字节不变） | 182→182 | mcoplib topk 的 graph-visible custom-op/fake/mutates 契约；native empty 无 persistent_topk CUDA 实现。 |
| `vllm_fl/ops/sparse_attn_indexer.py` | 保留（本轮字节不变） | 642→642 | 非 MetaX 平台直接调用 native forward_native，包含 native FP4/ROCm/XPU/CUDA 分派；FL custom-op 只承担 MetaX FP8 logit/topk，删除旧 CUDA/FP4 副本。所有 MetaX paged/logit、graph-safe、query-row sharding、tree topk 与开关保留。其他平台只有 mock 路由验证，非硬件通过。 |
| `vllm_fl/patches/deepseek_v4_metax.py` | 删除全局多流 patch | 419→381 | 删除 run_pair_serially/run_branches_serially/install_serial_execution 与版本 source-hash 配置；使用原生 aux_stream=None 顺序分支，3 项禁止访问事件/stream 的行为检查及重复 initialize 身份检查通过。RMS4096 是 Torch Inductor 生成 kernel 的 MetaX launch 调优，native vLLM CustomOp/PluggableLayer 无按生成数学体配置 tuner 的扩展点，原精度与 rank tuning 保留；vendor guard/幂等 bootstrap/hash 验证不变。 |
| `vllm_fl/quantization/w8a8/deepseek_v4.py` | 保留（本轮字节不变） | 243→243 | 直接复用 native workspace_shapes/_resize_cache、moe_problem_size、activation、moe_sum 与 quantization；只保留 MCTlass GEMM/no-TLE/kernel-M。去掉 functional 自有 scratch 分配和 output.copy_；chunk 使用各自 workspace slice，保护输出 alias。H-config/SPLIT_K 语义保留，旧未传入 vendor ABI 的 Triton tile/stage 字段不再解析。 |
| `vllm_fl/worker/model_runner.py` | 恢复 main 原文 | 7864→7864 | 移除两行 per-spec cache_dtype 覆盖。原生 get_attn_backend/get_kv_cache_shape 已区分 MLA/SWA packed FP8、Indexer 与 FP32 Compressor；7 种原生 spec × 0/1/3 blocks × 普通/packed 页的 42 项 GPU shape/dtype/stride/offset/alias 比较通过。当前无 Mamba，hybrid 分支不执行。保留 Plugin main runner 生命周期，不引入 Worker/runner 替换。 |
