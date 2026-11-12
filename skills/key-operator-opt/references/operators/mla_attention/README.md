# MLA Attention 算子分析

> 状态：**阶段性结果**。本文完成数学定义、主流实现调用链、理论性能模型和实验方案；当前环境没有目标 GPU，未执行自有 H800/H100/B200 profiler，因此所有性能数字均明确标注为上游项目公开结果，不能视为本项目实测。

本文只维护 MLA 的稳定语义、实现和性能模型。项目实际案例、平台数字和负面证据见 [case-index.md](case-index.md)；由案例提炼、可用于下一次快速决策的检查与候选见 [optimization-map.md](optimization-map.md)。不把单次案例流水账追加到本文。

## 1. 摘要

Multi-head Latent Attention（MLA）通过共享低秩 latent 压缩历史 K/V，并用 decoupled RoPE 保留可吸收的非位置投影。以 DeepSeek-V3/R1 的典型配置为例：`n_heads=128`、`kv_lora_rank=512`、`qk_nope_head_dim=128`、`qk_rope_head_dim=64`、`v_head_dim=128`。每 token、每层只缓存 `512+64=576` 个元素，而直接缓存展开后的 K/V 需要 `128*(192+128)=40,960` 个元素。

工程实现的核心不是“一套 MLA Kernel 通吃所有阶段”，而是按形状选择两种代数等价路径：

- **Prefill：展开后的 MHA 路径**。一次性用 `kv_b_proj` 恢复每个 head 的 K/V，使用 `qk_dim=192, v_dim=128` 的 FlashAttention 类 Kernel；这样避免 latent 维度带来的约 3.4 倍 attention FLOPs。
- **Decode：权重吸收后的 MQA 路径**。将 `W^UK` 吸收到 Query 侧、`W^UV` 吸收到输出侧，以共享的 latent KV Cache 做 `qk_dim=576, v_dim=512` 的 paged/split-KV attention。它增加 attention 计算量，但把理想 KV 读取量降低约 71 倍，适合生成阶段。

Dense Decode 的理想 arithmetic intensity 在 BF16 下约为 `241.8 FLOP/Byte`，恰好接近 FlashMLA 在 H800 上公开的有效 ridge point（`660 TFLOPS / 3 TB/s ≈ 220 FLOP/Byte`），因此 MLA Decode 不是简单的“纯带宽算子”：短上下文/小 batch 常受 launch、调度和占用率限制，长上下文可能在带宽与 Tensor Core 之间跨越。当前最有效的优化组合是：阶段分流、权重吸收、paged KV、split-KV + online-softmax merge、CUDA Graph、融合的 cache 写入，以及在可接受精度下使用 `fp8_ds_mla`。DeepSeek-V3.2 的 DSA 进一步用 indexer 选取 `topk=2048`，但把瓶颈转移到全历史打分、Top-K、稀疏 gather 和 FP8 dequantization。

## 2. 分析范围与环境

- 分析日期：2026-08-26。
- 模型主线：已公开的 DeepSeek-V2/V3/R1，以及 DeepSeek-V3.2-Exp 的 sparse MLA/DSA。
- 推理阶段：Prefill 与 Decode 分开建模；不展开训练反向传播。
- 硬件主线：单机 NVIDIA GPU，重点关注 Hopper（H800/H100/H200）与 Blackwell（B200）；补充 ROCm/其他后端现状。
- 精度：BF16/FP16 基线；补充 DeepSeek packed FP8 KV Cache。
- 框架主线：vLLM；横向比较 SGLang、FlashInfer、FlashMLA 和 TensorRT-LLM。
- 固定源码版本：DeepSeek-V3 `9b4e9788`、DeepSeek-V3.2-Exp `87e509a2`、vLLM `46638857`、FlashMLA `15f13e50`、FlashInfer `3bbfeba6`、SGLang `04c1036b`、TensorRT-LLM `b5875ec9`。

本文中的“MLA attention 算子”包括 Q/KV projection、RoPE、KV Cache 写入、attention core、Value up-projection 与 output projection 的关键边界；讨论 Kernel 时会明确缩小到 attention core 或 cache-update Kernel。DeepSeek-V3.2 的 DSA 不是把 MLA 替换掉，而是给 MLA 增加 lightning indexer 和 token-level sparse mask。

## 3. 定义、公式与张量形状

设 hidden state `h_t ∈ R^d`，head 数 `H`，KV latent 维度 `d_c`，非位置 Q/K 每 head 维度 `d_n`，RoPE 维度 `d_r`，Value 每 head 维度 `d_v`。

KV 联合压缩：

```text
c_t^KV = W^DKV h_t                         c_t^KV ∈ R^{d_c}
k_t^C  = W^UK c_t^KV                       k_t^C  ∈ R^{H·d_n}
v_t^C  = W^UV c_t^KV                       v_t^C  ∈ R^{H·d_v}
```

Query 低秩投影与 decoupled RoPE：

```text
c_t^Q = W^DQ h_t                           c_t^Q ∈ R^{d'_c}
q_t^C = W^UQ c_t^Q                         q_t^C ∈ R^{H·d_n}
q_t^R = RoPE(W^QR c_t^Q)                   q_t^R ∈ R^{H·d_r}
k_t^R = RoPE(W^KR h_t)                     k_t^R ∈ R^{d_r}，head 间共享
q_t,i = [q_t,i^C ; q_t,i^R]
k_t,i = [k_t,i^C ; k_t^R]
```

Attention：

```text
p_t,i,j = softmax_j((q_t,i^T k_j,i) / sqrt(d_n+d_r))
o_t,i   = Σ_j p_t,i,j v_j,i^C
u_t     = W^O concat_i(o_t,i)
```

生成时缓存 `c_j^KV` 与 `k_j^R`，每 token、每层为 `d_c+d_r` 个元素。RoPE 必须从 content 分量拆开：若直接对 `W^UK c_t^KV` 应用位置相关旋转，`W^UK` 就不能吸收到 Query 侧，Decode 将不得不为历史前缀重新计算逐 head K。

### DeepSeek-V3/R1 实例

| 变量 | 数值 | 说明 |
|---|---:|---|
| `d` | 7168 | hidden size |
| `H` | 128 | attention heads |
| `d'_c` | 1536 | Query LoRA rank |
| `d_c` | 512 | KV LoRA rank |
| `d_n` | 128 | non-RoPE Q/K dim/head |
| `d_r` | 64 | decoupled RoPE dim/head |
| `d_v` | 128 | Value dim/head |
| Cache | 576 elements/token/layer | `512 latent + 64 RoPE` |

BF16 下每层为 `576*2=1,152 Byte/token`；61 个 backbone layer 为约 `68.6 KiB/token`。128K context 单请求约占 `8.58 GiB`；FlashMLA 对 V3.2 的公开计算使用 62 层（计入额外层），对应约 `8.72 GiB`。直接缓存展开后的 `K[128,192]` 与 `V[128,128]` 则是 `81,920 Byte/token/layer`，是 latent cache 的约 71.1 倍。

`fp8_ds_mla` 并非简单把 576 个 BF16 全部改成 FP8：前 512 维 latent 使用 4 个 `1×128` tile，每 tile 配一个 FP32 scale；64 维 RoPE 仍保留 BF16。故每 token、每层实际为 `512 Byte + 16 Byte + 128 Byte = 656 Byte`，相对 BF16 的 1,152 Byte 减少 43.1%、容量提高约 1.76 倍。

## 4. 大模型推理中的使用场景

MLA 位于每个 Transformer block 的 RMSNorm 之后、残差和 FFN/MoE 之前：

```text
hidden_states
  -> Q/KV low-rank projection + RMSNorm
  -> decoupled RoPE
  -> KV Cache update
  -> MLA attention core
  -> Value up-projection + output projection
  -> residual add
  -> FFN / MoE
```

使用 MLA 的已公开主流模型包括 DeepSeek-V2、V3、R1 和 V3.2-Exp。V3.2-Exp 在相同 latent cache 上增加 64-head、128-dim lightning indexer，从全历史选 `topk=2048` token，再执行 sparse MLA。Dense MLA 仍是短上下文、fallback、prefill 的重要路径。

分布式部署时，Query heads 和 `W^UK/W^UV` 通常按 TP 切分；KV latent 与 RoPE key 为共享单 KV head。Decode Context Parallel（DCP）可切分长 KV 序列，并用每个 rank 的 output + log-sum-exp 做在线 softmax 合并，但会引入 Query gather 和结果通信。

## 5. Prefill 与 Decode 特征

| 阶段 | 推荐执行形态 | 核心张量 | 主要原因 |
|---|---|---|---|
| 新请求 Prefill | 展开 MHA | `Q/K:[T,H,192]`, `V:[T,H,128]` | K/V 只展开一次；attention dim 小，适合 FA3/FA4 |
| Chunked/Prefix Prefill | gather latent cache → dequant → `kv_b_proj` → MHA → LSE merge | 历史 paged cache + 新 token | 需要把 prefix 与 suffix 的 attention state 正确合并 |
| Dense Decode | 吸收 MQA | `Q:[B,H,576]`, `KV:[pages,1,576]`, logical `V dim=512` | 用更多 FLOPs 换取极小 KV 流量 |
| Sparse Decode/Prefill | indexer + top-k sparse absorbed MLA | `indices:[B,Q,K]`, `K≈2048` | 主 attention 从 `S` 降为 `K`，但访问离散 |

Prefill 若也采用吸收形态，attention 每个 pair 的维度从 `192+128=320` 增至 `576+512=1088`，约为 3.4 倍；Decode 若使用未吸收形态，又必须保存或重构体积巨大的逐 head K/V。因此二者必须分开优化。

## 6. 理论计算量、访存量与性能上限

以下 FLOPs 约定：一次乘加计 2 FLOPs，不计 softmax 指数、mask 和地址计算。

### 6.1 Dense Decode attention core

每个新 token、每层、长度为 `S` 的上下文：

```text
F_QK = 2 · H · S · (d_c + d_r)
F_PV = 2 · H · S · d_c
F_attn = 2 · H · S · (2d_c + d_r)
```

理想情况下每个历史 latent cache 只从 HBM 读取一次：

```text
Bytes_KV ≈ S · (d_c + d_r) · bytes_per_element
AI_ideal ≈ 2H(2d_c+d_r) / ((d_c+d_r)·bytes_per_element)
```

代入 DeepSeek-V3 BF16：

```text
F_attn = 278,528 · S FLOPs
Bytes_KV = 1,152 · S Byte
AI_ideal = 241.8 FLOP/Byte
```

当 `S=32K` 时，约为 `9.13 GFLOPs/layer/token`、理想 KV 读取 `36 MiB/layer/token`。实际 Kernel 会因 head 分块、split-KV、L2 miss、page table、重复加载和中间 LSE/output 降低有效 AI。

FlashMLA 当前 README 在 H800 SXM5/CUDA 12.8 上报告 dense decode 的最佳微基准约 `3000 GB/s`（memory-bound shape）和 `660 TFLOPS`（compute-bound shape）。二者给出的有效 ridge point 约 `220 FLOP/Byte`，与上述 241.8 接近，说明 workload 会随 batch/context/split 方案在两侧切换。上述是上游最佳点，不是端到端服务指标。

### 6.2 Prefill

长度 `T`、无 prefix 的 causal prefill，展开 MHA 的有效 attention FLOPs 近似：

```text
F_attn,useful ≈ H · T² · (d_qk + d_v)
```

若按完整未裁剪矩阵计算则约为其 2 倍。展开 K/V 的投影成本：

```text
F_expand = 2 · T · d_c · H · (d_n + d_v)
```

在 `T=8192`、DeepSeek-V3 维度下，causal useful attention 约 `2.75 TFLOPs/layer`，K/V 展开约 `0.275 TFLOPs/layer`；长序列由二次 attention 主导。`T=512` 时展开投影约 `17.2 GFLOPs`，反而可能超过 attention 的约 `10.7 GFLOPs`，所以短 prefill 需要关注 projection、launch 与融合。

### 6.3 Sparse MLA/DSA

主 sparse attention 将上式中的 `S` 换为 `K=topk`，但总成本还包括 indexer 对全部 `S` 的轻量打分与 Top-K：

```text
F_total ≈ F_indexer(S) + F_topk(S,K) + 2·H·K·(2d_c+d_r)
```

当 `S≫K` 时主 attention 显著下降；但随机 gather 降低 coalescing，FP8 dequant、indices/scale 读取、Top-K 和 launch 占比上升。FlashMLA 的公开分析给出：H800 上 `B=128,H=128,Q=2,K=2048` 的 FP8 sparse decode 从旧实现约 250 TFLOPS 提高到 410 TFLOPS；与 dense decode 相比，运行时间大致相当于约 3K dense context，`S>3K` 后 sparse 优势更明显。该交叉点依赖形状和硬件，不应直接泛化。

### 6.4 临时显存与布局

- KV Cache：paged layout，大小随 `batch × context × layers × cache_bytes` 线性增长。
- Decode：split-KV 需要 partial output 与 LSE workspace，近似 `B × H × num_splits × (d_c+1) × 4 Byte`。
- Prefill：需要展开后的 K/V workspace；chunked prefix 还需要 gather/dequant buffer。
- DSA：额外保存 indexer K cache、`[B,Q,K]` indices、Top-K workspace；随机稀疏访问使 page/block 对齐更关键。
- FlashMLA dense decode 的原生 page size 为 64；不同 backend 的 page size 不一致，转换/重排可能抵消 Kernel 收益。

## 7. 主流实现与源码调用链

### 7.1 DeepSeek 官方 reference

固定到 DeepSeek-V3 commit `9b4e9788`：

```text
inference/model.py::MLA.forward
  -> wq_a / q_norm / wq_b
  -> wkv_a -> split(kv_c, k_pe) -> kv_norm + RoPE
  -> naive: wkv_b 展开 K/V，显式 MHA cache
  -> absorb: q_nope @ W_UK，写 kv_cache[512] + pe_cache[64]
  -> latent MQA attention
  -> latent output @ W_UV -> wo
```

官方代码清楚展示了 `naive` 与 `absorb` 两条代数等价路径，是理解优化边界的 correctness reference；它使用固定 dense buffer，不包含生产级 paged cache、continuous batching 或专用 Kernel。

### 7.2 vLLM 主线（commit `46638857`）

```text
DeepseekV2MLAAttention.forward
  -> MultiHeadLatentAttentionWrapper
  -> MLAAttention.forward
       -> unified_mla_kv_cache_update / do_kv_cache_update
       -> MLAAttention.forward_impl
            ├─ Prefill: MLACommonBaseImpl.forward_mha
            │    -> kv_b_proj -> split(k_nope,v) -> concat(k_pe)
            │    -> MLAPrefillBackend.run_prefill_*
            │    -> FlashAttention / FlashInfer / TRTLLM ragged
            └─ Decode: q_nope @ W_UK^T
                 -> backend.forward_mqa
                 -> FlashMLA / FlashInfer MLA / Triton MLA / CUTLASS / AITER
                 -> _v_up_proj(W_UV) -> o_proj
```

关键 dispatch：

- `MLAAttention` 以 `head_size=d_c+d_r=576`、`num_kv_heads=1` 选择 Decode backend，并另行选择 Prefill backend。
- Prefill 路径显式恢复 `k_nope:[N,H,128]`、`v:[N,H,128]`，拼接共享 `k_pe:[N,1,64]` 后交给 MHA Kernel。
- Decode 先用 batched GEMM 将 `q_nope:[B,H,128]` 投到 latent `[B,H,512]`，拼接 `q_pe` 后调用 MQA Kernel，最后做 Value up-projection。
- FlashMLA backend 调用 `flash_mla_with_kvcache`；BF16 dense 路径进入 extension 的 `dense_decode_fwd`，内部为 SM90 split-KV 主 Kernel + LSE combine Kernel。
- Triton fallback 使用 stage-1 paged decode + stage-2 partial state merge；FlashInfer 调用 `trtllm_batch_decode_with_kv_cache_mla`，并在 CuTe-DSL/TRTLLM-gen 之间按架构和 head 数选择。

### 7.3 SGLang（commit `04c1036b`）

SGLang 的模型层执行 weight absorption 后通过 `RadixAttention` 分派到 `forward_extend` 或 `forward_decode`。`flashmla_backend.py` 在 Decode 前用 Triton 构造 block table、调用 `get_mla_metadata` 生成 split 调度信息，再进入 `flash_mla_with_kvcache`。当前文档显示 dense MLA 可选 FA3、FA4、FlashInfer MLA、FlashMLA、CUTLASS MLA、TRTLLM MLA、CuTeDSL、TokenSpeed、Triton 和 Ascend；Hopper dense MLA 默认倾向 FA3，Blackwell 的 DeepSeek-V3 倾向 TRTLLM MLA/FlashInfer，其他架构通常回退 Triton。Prefill 与 Decode 可显式配置不同 backend。

### 7.4 FlashMLA、FlashInfer 与 TensorRT-LLM

- **FlashMLA `15f13e50`**：DeepSeek 生产级专用库。dense decode 为 SM90/BF16/MQA；sparse decode 为 SM90/SM100 + packed FP8；当前还含 SM100 dense MHA prefill 与 SM90/SM100 sparse prefill。核心技术包括 paged KV、split-KV、动态 tile scheduler、online softmax 和 combine。
- **FlashInfer `3bbfeba6`**：提供 `BatchMLAPagedAttentionWrapper`、`trtllm_batch_decode_with_kv_cache_mla` 等统一 API，后端可落到 TRTLLM-gen、CuTe-DSL/CUTLASS/XQA；适合框架集成、跨架构与更多 cache/page 组合。
- **TensorRT-LLM `b5875ec9`**：PyTorch backend 自动为 DeepSeek-V3/R1 集成 FlashMLA，并在 Blackwell 使用内部 `trtllm-gen`。其 DeepSeek-V3 指南支持 FP8 MLA/KV Cache，并明确区分 Hopper 社区 FlashMLA 与 Blackwell codegen 路径。
- **ROCm/其他**：vLLM 注册 ROCm AITER MLA/Triton MLA，SGLang 的 DSA 可使用 TileLang/AITER；这些后端不能直接沿用 Hopper WGMMA 的结论。

## 8. 基线实现与正确性验证

建议保留三层 oracle：

1. 纯 PyTorch 未吸收 reference：显式恢复 K/V，计算 causal attention。
2. 纯 PyTorch 吸收 reference：`q_nope @ W_UK^T` → latent MQA → `@ W_UV`。
3. 目标 backend：FlashMLA/FlashInfer/vLLM/SGLang。

测试矩阵至少覆盖：

- `B={1,8,32,128}`，Decode `S={1,127,512,2048,8192,32768,131072}`；
- Prefill `T={1,32,128,512,2048,8192}`，含 prefix hit、chunked prefill、非 64 对齐长度；
- BF16、FP16、`fp8_ds_mla`；page 边界、空序列、不同 request 长度；
- speculative decode `Q>1`、CUDA Graph capture/replay、TP/DCP；
- DSA 的重复/越界/无效 indices、`topk_length<K`、attention sink。

BF16 初始可用 `atol=2e-2, rtol=2e-2`，但必须同时报告最大绝对/相对误差和 cosine；FP8 阈值应依据 reference 分布校准，并补充模型级 PPL/任务精度，不能只用单 Kernel allclose。

## 9. 性能测试与瓶颈定位

### 推荐 benchmark 形状

| 场景 | Batch / Q | KV length | dtype | 目的 |
|---|---|---|---|---|
| 单请求低延迟 Decode | `B=1,Q=1` | 512–128K | BF16/FP8 | launch、split 调度、长上下文斜率 |
| Continuous batching | `B=8/32/128,Q=1` | variable 512–128K | BF16/FP8 | SM 占用、page table、吞吐 |
| Spec decode | `B=1/8,Q=2/4/8` | 8K/32K | BF16 | 多 token decode 与 backend 限制 |
| Prefill | total tokens 512–32K | prefix 0/8K/32K | BF16/FP8 cache | 展开 GEMM、FA、chunk merge |
| Sparse DSA | `B=1/32/128,Q=1/2` | 8K–128K, `K=2048` | packed FP8 | indexer、Top-K、稀疏 gather |

测量要求：固定 GPU clocks/功耗状态，记录 GPU、driver、CUDA、PyTorch、框架和 commit；warmup ≥20、正式迭代 ≥100；使用 CUDA Events 且在计时边界同步；报告 median/P90/P99、tokens/s、有效 GB/s、有效 TFLOPS、峰值显存和误差。

诊断顺序：

1. 用 PyTorch reference 校验输出、LSE 与 cache layout。
2. PyTorch Profiler/Nsight Systems 分解 cache update、Q absorption BMM、attention、combine、V up-projection、output projection和 CPU metadata。
3. Nsight Compute 观察 DRAM/L2 throughput、Tensor Core active、occupancy、寄存器/共享内存、warp stall、split 数和 CTA 尾效应。
4. 将实测 `FLOPs/time` 与 `Bytes/time` 放回 Roofline；若二者均低，优先查 launch、调度、shape 与不必要的数据变换。

## 10. 优化方案与取舍

### 10.1 阶段分流与 backend autotuning（低风险）

瓶颈证据：Prefill 与 Decode 的最优代数形态相反。按 `Q length、KV length、batch、dtype、page size、GPU arch` 选择 MHA/absorbed MQA 和具体 Kernel。收益来自避免 3.4× prefill attention FLOPs或 71× decode KV 流量。代价是 dispatch 复杂度和更多 correctness 矩阵；阈值必须用目标 GPU 实测，不能硬编码跨平台结论。

### 10.2 融合 Q absorption、RoPE、量化与 cache insert（中低风险）

Decode 热路径当前可能包含 Q projection、`q_nope @ W_UK^T`、concat、quant、cache 写入等多个 launch。可将 reshape/concat/RoPE/scale/cache insert 融合，并预分配 CUDA Graph 稳定 workspace。收益最大在 `B≤8` 和短 context；大 batch/长 context 时 attention 主体占比上升。必须保留非对齐 shape fallback。

### 10.3 split-KV 与持久化调度元数据（中风险）

按 `B×H×S` 动态选择 split 数，使 CTA 数覆盖 SM，同时控制 partial output/LSE 合并开销。metadata、block table 和 workspace 应在 batch/layer 间复用，CUDA Graph replay 只更新必要字段。过多 split 会增加 workspace、combine 和 L2 压力；为确定性强制单 split 会明显牺牲吞吐。

### 10.4 page/layout 与向量化（中风险）

让物理 page size 与 backend 原生 tile 对齐，128-bit/TMA/coalesced load；避免在 backend 切换时全量重排 KV。对 prefix hit，优先融合 gather + dequant + `kv_b_proj`，只处理活跃 rows。代价是 cache manager 与 prefix-cache 兼容性复杂，尤其是 656-Byte packed entry。

### 10.5 FP8 KV Cache 与 Hopper dequant pipeline（中高风险）

`fp8_ds_mla` 将 cache 从 1,152 降到 656 Byte/token/layer，但 Hopper 上 E4M3→BF16 的多步转换可能比 MMA 更慢。FlashMLA 的“crossover”方案用 2-CTA cluster、Distributed Shared Memory 和 `st.async` 交换各自反量化的一半 K/V，使两个 CTA 复用结果。收益取决于 H=128、CTA/head 映射和 SM90 cluster；不适用于所有架构。RoPE 保留 BF16和 FP32 scales 增加布局与精度成本。

### 10.6 Attention epilogue 融合（中高风险）

Decode 后仍有 `latent output @ W_UV` 和 `o_proj`。可研究将 V up-projection、layout transform、output quantization 融入 attention/combine epilogue，减少中间 `[B,H,512]` 与额外 launch。当前 vLLM 文档明确：MLA backend 尚不能直接输出 FP8/FP4，fusion pass 需要临时 BF16 输出后再量化，这是可验证的机会。风险是寄存器压力、通用 quant scheme 爆炸和跨 backend 维护成本。

### 10.7 DSA indexer 与 sparse gather（高风险）

长上下文将 main attention 限制到 `K=2048`，但必须优化全历史 indexer、Top-K、indices 排序/分块和稀疏 cache load。候选包括 indexer cache 低精度、Top-K 与 page/block 重排融合、按物理 page 聚类 indices、prefetch scales、双 CTA 共享 dequant。排序能改善 locality但会改变返回顺序和 metadata；任何近似 indexer 都有模型质量风险。

### 10.8 TP/DCP 与通信融合（高风险）

长上下文可沿 KV 维切分，使用 LSE 合并 partial attention；Query replication/gather 与 online-softmax reduce 尽量重叠。适用于单卡已被超长 KV 或单请求并行度限制的场景。短上下文、低 batch 时通信延迟可能大于节省的计算，必须设置实测阈值。

## 11. 优化实现建议

优先实现一个“可公平验证、侵入性低”的组合，而不是直接改写主 Kernel：

1. 为目标框架加入 shape-aware Prefill/Decode backend sweep 脚本；
2. 固定 cache layout，复用 metadata/workspace，消除循环内分配；
3. Profile 确认 Q absorption/cache update 是否占比显著；若是，再实现融合 Kernel；
4. BF16 路径稳定后加入 `fp8_ds_mla`，逐层比较 dequant、attention、V-up 时间；
5. 最后评估 DSA indexer + sparse kernel，避免在 dense baseline 不可靠时归因。

新路径必须显式检查：GPU compute capability、CUDA 版本、head dims、page size、dtype、Q length、是否 sparse/causal、spec decode 和 DCP；不满足时回退到现有 backend。

## 12. 实验结果与分析

当前仅整理上游公开数据：

| 来源/环境 | Kernel | 公布结果 | 解释限制 |
|---|---|---:|---|
| FlashMLA, H800 SXM5, CUDA 12.8 | dense decode BF16 | 3000 GB/s（memory-bound）；660 TFLOPS（compute-bound） | 不同 shape 的最佳点，非同一 workload |
| FlashMLA, H800 SXM5, CUDA 12.8 | sparse decode, FP8 cache/BF16 MMA | 410 TFLOPS | `B=128,H=128,Q=2,K=2048` 的 compute-bound 配置 |
| FlashMLA | sparse prefill | H800 640 TFLOPS；B200 1450 TFLOPS | 上游微基准，B200 CUDA 12.9 |
| DeepSeek-V2, 8×H800 | 完整模型服务 | generation >50K token/s；prompt >100K token/s | 同时含 MoE、FP8、KV 量化、批处理与系统优化 |

在没有目标 GPU 的情况下，本文不生成或估冒充实测 latency。下一阶段应运行第 9 节矩阵并保存 CSV/JSON、Nsight 命令与 profiler 摘要，再决定最值得实现的 Kernel 优化。

## 13. 结论、限制与后续工作

MLA 的本质是把大 KV Cache 问题转化为“小缓存 + 更多 Tensor Core 计算”。其成功依赖三件事同时成立：decoupled RoPE 允许权重吸收；Prefill/Decode 使用不同执行形态；框架能把 paged cache、split-KV、metadata、量化和 CUDA Graph 组织成低开销路径。

对 DeepSeek-V3/R1 dense MLA，Decode 的理想 AI 处于 Hopper 有效 Roofline 的拐点附近，因此“只减少访存”或“只优化 MMA”都可能在另一类 shape 退化。对 V3.2 sparse MLA，主 attention 复杂度从 `S` 降到 `K`，但瓶颈转向 indexer、Top-K、随机 gather 和反量化。最稳妥的优化顺序是先做 dispatch/融合/metadata/layout，再做 FP8 pipeline，最后做稀疏算法和跨卡并行。

已知限制：缺少本项目自有 profiler；未覆盖训练 backward；未对 Ascend/CPU 做源码级追踪；Blackwell/ROCm 后端仍快速演进。完成标准还差目标硬件上的 correctness、端到端占比、Roofline 对照和优化前后公平实验。

## 14. 参考资料

1. [DeepSeek-V2 论文](https://arxiv.org/abs/2405.04434)
2. [DeepSeek-V3 Technical Report](https://arxiv.org/abs/2412.19437)
3. [DeepSeek-V3 官方 inference/model.py（固定 commit）](https://github.com/deepseek-ai/DeepSeek-V3/blob/9b4e9788e4a3a731f7567338ed15d3ec549ce03b/inference/model.py)
4. [DeepSeek-V3.2-Exp 官方仓库](https://github.com/deepseek-ai/DeepSeek-V3.2-Exp)
5. [DeepSeek-V3.2-Exp config](https://huggingface.co/deepseek-ai/DeepSeek-V3.2-Exp-Base/blob/main/config.json)
6. [FlashMLA（固定 commit）](https://github.com/deepseek-ai/FlashMLA/tree/15f13e5030374295491c5ce31b02d7e63a7772c6)
7. [FlashMLA FP8 sparse decode 深入分析](https://github.com/deepseek-ai/FlashMLA/blob/15f13e5030374295491c5ce31b02d7e63a7772c6/docs/20250929-hopper-fp8-sparse-deep-dive.md)
8. [vLLM DeepSeek-V2/V3 模型实现（固定 commit）](https://github.com/vllm-project/vllm/blob/46638857fdbb30e0c232c9e8f9cb1ff6d6f545c3/vllm/model_executor/models/deepseek_v2.py)
9. [vLLM MLA 公共层（固定 commit）](https://github.com/vllm-project/vllm/blob/46638857fdbb30e0c232c9e8f9cb1ff6d6f545c3/vllm/model_executor/layers/attention/mla_attention.py)
10. [vLLM attention backend 设计](https://github.com/vllm-project/vllm/blob/46638857fdbb30e0c232c9e8f9cb1ff6d6f545c3/docs/design/attention_backends.md)
11. [SGLang attention backend 文档](https://github.com/sgl-project/sglang/blob/04c1036bb395cce7d9b5eab1a814163ab1dcefed/docs/docs/advanced_features/attention_backend.mdx)
12. [SGLang FlashMLA backend（固定 commit）](https://github.com/sgl-project/sglang/blob/04c1036bb395cce7d9b5eab1a814163ab1dcefed/python/sglang/srt/layers/attention/flashmla_backend.py)
13. [FlashInfer MLA API](https://github.com/flashinfer-ai/flashinfer/blob/3bbfeba6218b6de32d1e894243c010c8d3aacb21/docs/api/attention.rst)
14. [TensorRT-LLM DeepSeek-V3/R1 指南](https://github.com/NVIDIA/TensorRT-LLM/blob/b5875ec96c455e4e9f3aaee3de7f162bc2c57222/examples/models/core/deepseek_v3/README.md)
