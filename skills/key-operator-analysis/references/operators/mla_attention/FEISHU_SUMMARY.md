# 2. MLA Attention 算子分析

> 状态：阶段性结果。本文已完成算法、主流实现、理论性能与优化方向分析；当前环境没有目标 GPU，因此性能数字均来自官方论文或上游项目，不作为本项目实测结果。

## 2.1 结论摘要

Multi-head Latent Attention（MLA）通过共享低秩 latent 压缩历史 K/V，并用 decoupled RoPE 保留推理时的权重吸收能力。以 DeepSeek-V3/R1 为例，每 token、每层只缓存 `512` 维 KV latent 与 `64` 维 RoPE Key，共 `576` 个元素；直接缓存展开后的多头 K/V 则需要 `128×(192+128)=40,960` 个元素。

当前高性能实现不会用同一套 Kernel 处理全部阶段，而是采用两条代数等价路径：

- **Prefill：展开后的 MHA 路径**。恢复逐 head K/V，使用 `qk_dim=192, v_dim=128` 的 FlashAttention 类 Kernel，避免 latent 维度带来的额外 attention FLOPs。
- **Decode：权重吸收后的 MQA 路径**。把 `W^UK` 吸收到 Query 侧、`W^UV` 吸收到输出侧，使用共享 latent KV Cache 执行 `qk_dim=576, v_dim=512` 的 paged/split-KV attention。

MLA 的本质是用更多 Tensor Core 计算换取大幅减少的 KV Cache 容量和带宽。DeepSeek-V3 dense Decode 的理想 arithmetic intensity 约为 `241.8 FLOP/Byte`，接近 FlashMLA 在 H800 上公开结果对应的有效 Roofline 拐点，因此它既可能 bandwidth-bound，也可能 compute-bound；小 batch/短上下文还常受 Kernel launch、调度和 occupancy 限制。

## 2.2 定义与典型形状

设 hidden state 为 `h_t∈R^d`，head 数为 `H`，KV latent 维度为 `d_c`，非位置 Q/K 维度为 `d_n`，RoPE 维度为 `d_r`，Value 维度为 `d_v`。

```text
c_t^KV = W^DKV h_t
k_t^C  = W^UK c_t^KV
v_t^C  = W^UV c_t^KV

c_t^Q  = W^DQ h_t
q_t^C  = W^UQ c_t^Q
q_t^R  = RoPE(W^QR c_t^Q)
k_t^R  = RoPE(W^KR h_t)          # 所有 Query head 共享

q_t,i = [q_t,i^C ; q_t,i^R]
k_t,i = [k_t,i^C ; k_t^R]
o_t,i = Σ_j softmax(q_t,i^T k_j,i / √(d_n+d_r)) · v_j,i^C
```

生成阶段只缓存 `c_t^KV` 和 `k_t^R`，规模为 `(d_c+d_r)` elements/token/layer。RoPE 必须从 content 分量中拆出：若直接对 `W^UK c_t^KV` 使用位置相关旋转，`W^UK` 无法吸收到 Query 侧，Decode 将不得不为整个历史前缀重新计算逐 head K。

DeepSeek-V3/R1 典型配置：

| 参数 | 数值 |
|---|---:|
| hidden size `d` | 7168 |
| attention heads `H` | 128 |
| Query LoRA rank | 1536 |
| KV LoRA rank `d_c` | 512 |
| non-RoPE dim `d_n` | 128 |
| RoPE dim `d_r` | 64 |
| Value dim `d_v` | 128 |

BF16 latent cache 为 `576×2=1,152 Byte/token/layer`；61 层约为 `68.6 KiB/token`，128K context 单请求约 `8.58 GiB`。直接缓存展开后的 K/V 为 `81,920 Byte/token/layer`，约大 71 倍。

DeepSeek packed FP8 Cache（`fp8_ds_mla`）并非简单的 576 个 FP8：512 维 latent 使用 4 个 `1×128` tile，每 tile 配一个 FP32 scale；64 维 RoPE 保留 BF16。因此实际为 `512+16+128=656 Byte/token/layer`，相比 BF16 减少 43.1%，容量提高约 1.76 倍。

## 2.3 Prefill 与 Decode 为什么必须分开

| 阶段 | 执行形态 | 核心张量 | 主要瓶颈 |
|---|---|---|---|
| 新请求 Prefill | 展开 MHA | `Q/K:[T,H,192]`, `V:[T,H,128]` | 二次 attention、K/V 展开 GEMM |
| Prefix/Chunked Prefill | gather latent → dequant → `kv_b_proj` → MHA → LSE merge | paged prefix cache + 新 token | gather、workspace、在线 softmax 合并 |
| Dense Decode | 吸收 MQA | `Q:[B,H,576]`, `KV:[pages,1,576]`, logical `V=512` | cache 读取、Tensor Core、split 调度 |
| Sparse MLA/DSA | indexer + Top-K + sparse MQA | `indices:[B,Q,K]`, 常用 `K=2048` | 全历史打分、Top-K、随机 gather、反量化 |

Prefill 若采用吸收形态，attention 每个 Q-K pair 的维度从 `192+128=320` 增加到 `576+512=1088`，约多 3.4 倍计算；而 Decode 若采用未吸收形态，又需要保存或反复重构巨大的逐 head K/V。因此主流框架通常 Prefill 使用 MHA/FlashAttention，Decode 使用 absorbed MQA。

## 2.4 理论性能模型

一次乘加按 2 FLOPs 计。Dense Decode 每生成一个 token、每层、上下文长度为 `S`：

```text
F_QK   = 2·H·S·(d_c+d_r)
F_PV   = 2·H·S·d_c
F_attn = 2·H·S·(2d_c+d_r)

Bytes_KV,ideal ≈ S·(d_c+d_r)·bytes_per_element
```

代入 DeepSeek-V3 BF16：

```text
F_attn = 278,528·S FLOPs
Bytes_KV = 1,152·S Byte
AI_ideal = 241.8 FLOP/Byte
```

当 `S=32K` 时，每层、每个新 token 约为 `9.13 GFLOPs`，理想 KV 读取约 `36 MiB`。实际 Kernel 还会受 head 分块、page table、split-KV、L2 miss、重复加载、partial output 和 LSE merge 影响。

FlashMLA 当前 README 在 H800 SXM5/CUDA 12.8 上报告 dense decode 最佳微基准约 `3000 GB/s`（memory-bound shape）和 `660 TFLOPS`（compute-bound shape），对应有效 ridge point 约 `220 FLOP/Byte`。这说明 MLA Decode 的瓶颈会随 batch、context 和 split 策略变化，不能笼统判断为纯带宽算子。

Prefill 长度为 `T` 时，展开 MHA 的 causal useful attention FLOPs 近似：

```text
F_attn,useful ≈ H·T²·(d_qk+d_v)
F_expand      = 2·T·d_c·H·(d_n+d_v)
```

在 `T=8192` 时，二者约为 `2.75 TFLOPs/layer` 和 `0.275 TFLOPs/layer`，长序列由 attention 主导；在 `T=512` 时，展开 K/V 的 GEMM 反而可能超过 attention，因此短 Prefill 更需要关注 projection 与 Kernel 融合。

## 2.5 主流框架与 Kernel 调用链

### vLLM（源码主线）

```text
DeepseekV2MLAAttention.forward
  -> MultiHeadLatentAttentionWrapper
  -> MLAAttention.forward
       -> KV Cache update
       -> MLAAttention.forward_impl
            ├─ Prefill: forward_mha
            │    -> kv_b_proj -> split(k_nope,v) -> concat(k_pe)
            │    -> FlashAttention / FlashInfer / TRTLLM Ragged
            └─ Decode: q_nope @ W_UK^T
                 -> FlashMLA / FlashInfer MLA / Triton MLA / CUTLASS / AITER
                 -> V up-projection(W_UV) -> output projection
```

vLLM 对 Prefill 和 Decode 分别选择 backend。Decode 的 FlashMLA 路径进入 `flash_mla_with_kvcache`，再落到 C++/CUDA extension 的 dense `split-KV` 主 Kernel与 LSE combine Kernel；Triton fallback 同样采用分段计算与 partial state 合并；FlashInfer 路径调用 `trtllm_batch_decode_with_kv_cache_mla`，再按架构落到 TRTLLM-gen、CuTe-DSL/CUTLASS 等实现。

### SGLang、FlashInfer、TensorRT-LLM

- **SGLang**：模型层完成 weight absorption，经 `RadixAttention` 分派到 `forward_extend/forward_decode`；FlashMLA backend 在 Decode 前构造 block table 和 split metadata。支持为 Prefill/Decode 选择不同 backend。
- **FlashMLA**：DeepSeek 专用生产 Kernel，包含 dense/sparse decode、dense MHA prefill 和 sparse prefill；核心技术为 paged KV、split-KV、动态 tile scheduler、online softmax 和 combine。
- **FlashInfer**：提供统一 MLA paged-attention API，可落到 TRTLLM-gen、CuTe-DSL、CUTLASS/XQA，覆盖更多 GPU、page size 与量化组合。
- **TensorRT-LLM**：PyTorch backend 为 DeepSeek-V3/R1 集成 FlashMLA；Hopper 主要复用社区 FlashMLA，Blackwell 主要使用内部 `trtllm-gen`。
- **ROCm**：vLLM/SGLang 可使用 AITER、Triton 或 TileLang 路径，不能直接套用 Hopper WGMMA 的结论。

## 2.6 当前瓶颈

1. **阶段与 backend 选择不匹配**：Prefill 用 absorbed MQA 会浪费 FLOPs；Decode 展开 K/V 会放大 cache 流量。
2. **小 batch 调度开销**：Q absorption、RoPE、concat、cache insert、attention、combine、V-up 可能形成多个短 Kernel。
3. **split-KV 取舍**：split 太少无法占满 SM，太多会增加 workspace、LSE merge 和 L2 压力。
4. **Prefix Cache 路径**：历史 latent 需要 gather、反量化、展开 K/V，并与新 token 的 attention state 合并。
5. **FP8 反量化**：Hopper 不能一步完成 E4M3→BF16，dequant 可能比 MMA 更慢；RoPE 与 scales 又使布局不是普通连续 FP8。
6. **V up-projection 与输出量化**：attention 后仍需 `latent@W_UV` 和 `o_proj`；当前部分框架无法由 MLA Kernel 直接输出 FP8/FP4，需要额外临时张量和量化 Kernel。
7. **DSA 稀疏访问**：主 attention 从 `S` 降为 `K`，但 indexer、Top-K、离散 indices、随机 page load 和 scale 读取成为新瓶颈。
8. **分布式通信**：DCP 可切分超长 KV，但需要 Query gather 和基于 LSE 的 partial attention 合并，短序列可能得不偿失。

## 2.7 优化建议（按投入与风险排序）

1. **Shape-aware dispatch**：以 `Q length、KV length、batch、dtype、page size、GPU arch` 选择 Prefill/Decode 形态和 backend；阈值必须在目标 GPU 实测。
2. **融合热路径**：融合 Q absorption、RoPE、concat/quant 和 cache insert；预分配 workspace，并让 CUDA Graph replay 只更新必要 metadata。
3. **优化 split-KV scheduler**：按 `B×H×S` 选择 split 数，复用 block table、scheduler metadata 和 combine buffer。
4. **对齐 page/layout**：尽量使用 backend 原生 page size 和 128-bit/TMA load；Prefix hit 只处理活跃 cache rows，避免全量转换。
5. **优化 packed FP8 pipeline**：Hopper 可采用 CTA cluster + Distributed Shared Memory，让处理不同 Query heads 的 CTA 共享已反量化的 K/V。收益依赖 SM90 与固定 head 映射，需要独立 fallback。
6. **融合 attention epilogue**：研究把 V up-projection、layout transform 和输出量化并入 combine/epilogue，减少 `[B,H,512]` 中间结果和额外 launch。
7. **优化 DSA indexer/gather**：融合 indexer Top-K、按物理 page 聚类 indices、预取 scales；任何近似 indexer 都需模型级精度验证。
8. **DCP 通信重叠**：用 LSE 在线合并 partial attention，并重叠 Query gather/结果通信；只在超长 context 的实测收益超过通信延迟时启用。

## 2.8 验证方案

correctness oracle 保留三层：显式未吸收 PyTorch reference、吸收后的 latent MQA reference、目标 backend。覆盖 BF16/FP16/FP8、非 64 对齐长度、不同 page 边界、prefix hit、speculative decode、CUDA Graph、TP/DCP 与 DSA 无效 indices。

性能测试建议：

- Decode：`B={1,8,32,128}`，`S={512,2K,8K,32K,128K}`；
- Prefill：`T={128,512,2K,8K}`，prefix 为 `0/8K/32K`；
- Sparse：`K=2048`，同时统计 indexer、Top-K 和 attention；
- warmup ≥20、正式迭代 ≥100，使用 CUDA Events，报告 median/P90/P99、tokens/s、有效 GB/s/TFLOPS、峰值显存和误差。

先用 PyTorch Profiler/Nsight Systems 分解 cache update、Q absorption、attention、combine、V-up 与 CPU metadata，再用 Nsight Compute 观察 DRAM/L2 throughput、Tensor Core active、occupancy、寄存器/共享内存和 warp stall，并与第 2.4 节 Roofline 模型对照。

## 2.9 公开结果与适用范围

| 来源 | Kernel/环境 | 公开结果 |
|---|---|---:|
| FlashMLA | H800 SXM5, CUDA 12.8, dense decode BF16 | 3000 GB/s；660 TFLOPS（不同最佳 shape） |
| FlashMLA | H800, sparse decode, FP8 cache/BF16 MMA | 410 TFLOPS（`B=128,H=128,Q=2,K=2048`） |
| FlashMLA | sparse prefill | H800 640 TFLOPS；B200 1450 TFLOPS |
| DeepSeek-V2 | 8×H800 完整服务 | generation >50K token/s；prompt >100K token/s |

这些数字是上游最佳微基准或完整系统结果，不能当作本项目实测，也不能直接互相计算加速比。下一阶段需要在固定模型、GPU、shape、dtype 和计时方法下建立公平 baseline。

## 2.10 参考资料与版本

分析日期：2026-08-26。主要源码版本：DeepSeek-V3 `9b4e9788`、DeepSeek-V3.2-Exp `87e509a2`、vLLM `46638857`、FlashMLA `15f13e50`、FlashInfer `3bbfeba6`、SGLang `04c1036b`、TensorRT-LLM `b5875ec9`。

1. [DeepSeek-V2 论文](https://arxiv.org/abs/2405.04434)
2. [DeepSeek-V3 Technical Report](https://arxiv.org/abs/2412.19437)
3. [DeepSeek-V3 官方 inference](https://github.com/deepseek-ai/DeepSeek-V3/blob/9b4e9788e4a3a731f7567338ed15d3ec549ce03b/inference/model.py)
4. [DeepSeek-V3.2-Exp](https://github.com/deepseek-ai/DeepSeek-V3.2-Exp)
5. [FlashMLA](https://github.com/deepseek-ai/FlashMLA/tree/15f13e5030374295491c5ce31b02d7e63a7772c6)
6. [FlashMLA FP8 sparse decode 分析](https://github.com/deepseek-ai/FlashMLA/blob/15f13e5030374295491c5ce31b02d7e63a7772c6/docs/20250929-hopper-fp8-sparse-deep-dive.md)
7. [vLLM DeepSeek 模型实现](https://github.com/vllm-project/vllm/blob/46638857fdbb30e0c232c9e8f9cb1ff6d6f545c3/vllm/model_executor/models/deepseek_v2.py)
8. [vLLM MLA 公共层](https://github.com/vllm-project/vllm/blob/46638857fdbb30e0c232c9e8f9cb1ff6d6f545c3/vllm/model_executor/layers/attention/mla_attention.py)
9. [SGLang attention backend](https://github.com/sgl-project/sglang/blob/04c1036bb395cce7d9b5eab1a814163ab1dcefed/docs/docs/advanced_features/attention_backend.mdx)
10. [FlashInfer MLA API](https://github.com/flashinfer-ai/flashinfer/blob/3bbfeba6218b6de32d1e894243c010c8d3aacb21/docs/api/attention.rst)
11. [TensorRT-LLM DeepSeek-V3/R1 指南](https://github.com/NVIDIA/TensorRT-LLM/blob/b5875ec96c455e4e9f3aaee3de7f162bc2c57222/examples/models/core/deepseek_v3/README.md)
