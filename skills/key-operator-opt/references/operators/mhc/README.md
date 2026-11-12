# mHC 算子分析（vLLM / DeepSeek-V4）

## 1. 摘要

mHC（Manifold-Constrained Hyper-Connections）将 Transformer 的单路 residual stream 扩展为 `hc_mult=M` 路，并用动态生成的混合系数在层前、层后进行跨 stream 混合；其中残差混合矩阵通过 Sinkhorn-Knopp 近似投影到 Birkhoff polytope（双随机矩阵集合），以保持信号规模和 identity-like 稳定性。对 vLLM 而言，mHC 不是一个单独的 GEMM，而是一组紧邻主干层的 memory-bound 小算子：`MHCPreOp`、`MHCPostOp`、`HCHeadOp`，以及将 post 与下一层 pre 合并的 `MHCFusedPostPreOp`。

当前 vLLM 主线已提供 CUDA TileLang、ROCm AITER/TileLang、HIP/XPU 与 native fallback。最关键的优化是融合相邻 post+pre，避免中间 stream 与混合矩阵的重复读写；在没有融合、低 token 数或缺少专用后端时，瓶颈主要是显存带宽、Kernel launch 和小矩阵归一化，而不是 Tensor Core FLOPs。本文没有目标 GPU 实测，因此收益以模型和 Kernel 级 benchmark 为待验证项。

## 2. 分析范围与环境

- 对象：vLLM 中面向 DeepSeek-V4 的 mHC 推理实现。
- 阶段：Prefill 与 Decode 分开讨论；默认单机 GPU、BF16 residual/activation，FP32 参数与归一化中间量。
- 源码主线：vLLM `main`，检索日期 2026-08-27；正式实验应记录具体 commit/tag。
- 目标：首 token 延迟、单 token 延迟、吞吐、显存读写与 Kernel launch 开销。
- 限制：本地未发现 vLLM 源码副本，也没有可用目标 GPU，故源码依据使用 vLLM 官方 API 文档与 GitHub 主线链接，性能结论为理论分析和实验计划。

## 3. 定义、公式与张量形状

令 `T` 为 token 数，`H` 为 hidden size，`M` 为 residual stream 数（`hc_mult`）。第 `l` 层输入残差为 `R_l ∈ R^{T×M×H}`，层内 Transformer block 只处理聚合后的单路输入。

### 3.1 Pre block

对 flatten 后的 residual 做 RMSNorm，并由小型参数 `fn` 生成三类 logits：pre mixing、post layer mixing、combination mixing。经过 sigmoid/尺度变换和 Sinkhorn-Knopp 后得到：

`P_l ∈ R^{T×M}`，`A_l ∈ R^{T×M}`，`C_l ∈ R^{T×M×M}`。

进入 Transformer block 的输入为：

`X_l[t,h] = Σ_i P_l[t,i] R_l[t,i,h]`。

实现中 `fn` 的典型形状为 `[3M, M·H]`，`hc_scale`/`hc_base` 为 FP32 小参数；`P`、`A`、`C` 通常以 BF16 输出或在 Kernel 内保持更高精度计算。`C` 的最后两个维度在约束后近似双随机：行和、列和接近 1。

### 3.2 Post block

Transformer block 输出 `Y_l ∈ R^{T×H}` 后，post 将它写回 M 路 stream：

`R_{l+1}[t,j,h] = A_l[t,j]·Y_l[t,h] + Σ_i C_l[t,j,i]·R_l[t,i,h]`。

因此 post 的主计算量约为 `T·(M + M²)·H` 次乘加；当 `M` 很小（如 4）时，计算量不大，但会访问 `R`、`Y`、`A`、`C` 并产生 `M·H` 输出。

### 3.3 Head reduction

模型最终需要单路 hidden state。`HCHeadOp` 对 M 路 residual 做 RMSNorm，生成 head gate `g[t,i]`，再折叠：

`out[t,h] = Σ_i g[t,i]·R[t,i,h]`。

它只在模型输出端发生，不应与每层 post 混淆。

## 4. 大模型推理中的使用场景

mHC 位于每个 Transformer block 的 residual 边界：

`MHCPre → Attention/MLP/MoE → MHCPost → 下一层 MHCPre`。

它不改变 attention 的 Q/K/V 或 MoE routing 语义，也不直接参与 KV Cache 的索引管理；但它会改变 block 输入和输出的 residual layout，并让每个 token 保留 M 路 stream。GQA/MQA、MLA、MoE、量化权重都可与 mHC 组合，mHC 本身的 residual mixing 通常仍要求 BF16/FP32 累加以控制误差。

## 5. Prefill 与 Decode 特征

Prefill 中 `T` 通常较大，`MHCPre/Post` 可按 token 并行，参数 `fn` 和混合系数在多个 token 上复用/批量生成；Kernel 更容易摊薄 launch 开销，但 `R` 的 M 倍写放大会增加显存流量。Prefill 的优化重点是融合 RMSNorm、logit 生成、Sinkhorn 与 residual mixing，并使访问沿 hidden 维连续。

Decode 中每条序列每步只有 1 个新 token，但 continuous batching 后有效 `T` 是活跃请求数，且每步形状动态变化。此时 mHC 的算术强度更低，launch、调度和不规则 batch 的尾部效率更突出；应优先使用 CUDA Graph/piecewise graph 可捕获的固定 shape、融合 post+next pre，并避免将 `M×M` 小矩阵单独落地到显存。

## 6. 理论计算量、访存量与性能上限

以下按一次乘加计 2 FLOPs，仅估算 residual mixing，不含生成 logits 的 `fn` 投影、RMSNorm 和 Sinkhorn。

- Pre 聚合：`2·T·M·H` FLOPs。
- Post：`2·T·(M+M²)·H` FLOPs。
- Head：`2·T·M·H` FLOPs。
- 若 M=4，post 的核心约为 `40·T·H` FLOPs；与 attention/MLP 相比很小。

以 BF16 为 2 bytes、`M=4` 估算，post 仅 residual 读写约为 `(M·H + H + M·H)·2 = 2·(2M+1)H` bytes/token，尚未计入 C、A 和中间结果；因此 arithmetic intensity 约为 `2(M+M²)H / [2(2M+1)H] = (M+M²)/(2M+1)` FLOP/byte，M=4 时约 20/9≈2.2 FLOP/byte，明显低于高端 GPU 的计算/带宽拐点，倾向 memory-bound。

M 增大时计算与 stream 显存均按 M 或 M² 增长，`C` 的存储按 M² 增长；但 `H` 较大且 M 很小时，hidden 维向量化仍可保持较好带宽。Sinkhorn 的 M×M 迭代成本为 `O(T·K·M²)`，K 为迭代次数；M=4 时绝对量小，但 Decode 小 batch 下会放大同步和 launch 相对开销。

## 7. vLLM 主流实现与源码调用链

模型层入口：DeepSeek-V4 decoder layer 导入 `vllm.model_executor.layers.mhc`，在 block 前后调用 mHC custom op。

算子层：

1. `MHCPreOp.forward_cuda/forward_hip`：优先 `torch.ops.vllm.mhc_pre_tilelang` 或 AITER；否则 native torch fallback。
2. `MHCPostOp.forward_cuda/forward_hip`：CUDA 使用 `mhc_post_tilelang`；ROCm 在满足 `hidden_size % 256 == 0` 且 AITER 可用时用 `mhc_post_aiter`，否则 TileLang/native。
3. `MHCFusedPostPreOp`：将当前层 post 和下一层 pre 合并，返回 `residual_cur`、`post_mix_cur`、`comb_mix_cur`、`layer_input_cur`，减少中间张量落地。
4. `HCHeadOp`：CUDA 优先 TileLang head kernel，否则 Triton `hc_head_triton`；输出折叠为 `[T,H]`。

Kernel/后端：`vllm/model_executor/kernels/mhc/` 下分为 `tilelang.py`、`triton.py`、`torch.py`、`aiter.py` 与注册封装。vLLM 使用 direct custom op 注册，将 Python dispatch 开销降到较低，并按 CUDA/ROCm/XPU 选择后端；缺少 TileLang/AITER 时回退到可读性更好的 native 实现。

## 8. 当前瓶颈与证据

- 算法层：mHC 需要动态混合系数和 Sinkhorn 约束，无法像普通 residual add 一样只做一次向量加法。
- Kernel 层：M 很小而 H 很大，核心是向量读写；未融合时 residual、mix 矩阵和 layer input 多次读写。
- 调度层：Decode 的小 T 使 launch latency 与 shape dispatch 占比升高；动态 batch 也会造成尾部浪费。
- 依赖层：TileLang/AITER 是可选后端；ROCm 还存在 hidden size 对齐和 PDL/运行时兼容性限制，必须保留 fallback。
- 验证层：仅凭端到端 wall-clock 无法证明 mHC 是瓶颈，应使用 profiler 分解 mHC Kernel、主干 block、CPU 调度与同步时间。

## 9. 优化方案与取舍

1. **优先启用 post+next-pre fusion**：减少一次 kernel launch、一次 residual 中间写回和一次读取；适用于 Prefill/Decode，收益取决于 M、H、T 与后端。代价是 Kernel 更复杂、寄存器压力上升，边界层仍需单独路径。
2. **融合 RMSNorm、gate 生成、Sinkhorn 与 mixing**：减少中间 logits/mix 的显存往返；适合 H 大、M 小的 BF16 GPU。风险是数值误差、调试难度和不同 M/K 的 dispatch 数增加。
3. **Decode 使用 graph-friendly shape 与 continuous batching**：固定 M/H、按活跃 token 数分桶，降低 launch 和动态 dispatch；过度 padding 会增加无效计算。
4. **布局与向量化**：保持 residual `[T,M,H]` 的 H 维连续，沿 H 使用 vectorized load/store；避免 `[T,H,M]` 与 `[T,M,H]` 间 transpose。代价是与其他层的 layout 约束耦合。
5. **降低 Sinkhorn 迭代或采用近似约束**：只在模型已验证允许时尝试；可降低 Decode 延迟，但会削弱双随机约束，必须做模型级精度和稳定性评估，不能默认替换。

## 10. 基线、正确性与性能验证

正确性 oracle 使用 `mhc_pre_torch`/`mhc_post_torch` 或等价 PyTorch reference；覆盖 `M∈{1,2,4,8}`、H 对齐/非对齐、T=1/小 batch/大 prefill、BF16/FP16，报告 max absolute error 与 relative error。

性能命令应固定 GPU、CUDA/ROCm、vLLM commit、dtype、warmup、迭代次数和同步方式。分别测：单 op pre/post/head、fused post+pre、端到端 decoder layer。每组至少报告 median、P90、显存峰值、Kernel 数；Nsight Systems 看 launch/同步，Nsight Compute 看 DRAM throughput、occupancy、register pressure、warp stall。加速比统一为 `baseline_time / optimized_time`。

## 11. 结论、限制与后续工作

vLLM 对 mHC 的正确工程抽象是“残差流变换 Kernel 族”，而非把它当成一个普通 PyTorch 算子。当前最可靠的优化方向是后端专用的 post+pre fusion，加上 Decode 的 graph-friendly 调度和 H 维连续布局。mHC 的理论核心开销低于 attention/MLP，但它位于每层、每 token 的热路径，未融合时仍可能通过带宽和 launch 累积为可见端到端成本。

本文缺少目标硬件实测，不能给出普适加速百分比。下一步应在 NVIDIA H100/H200 或用户指定 GPU 上完成形状矩阵 benchmark，并以端到端 DeepSeek-V4、不同 batch/上下文长度和真实 continuous batching 验证上述判断。

## 12. 参考资料

1. DeepSeek-AI, *mHC: Manifold-Constrained Hyper-Connections*, arXiv:2512.24880, https://arxiv.org/abs/2512.24880
2. vLLM 官方 mHC API： https://docs.vllm.ai/en/stable/api/vllm/model_executor/layers/mhc/
3. vLLM 官方 mHC kernels API： https://docs.vllm.ai/en/latest/api/vllm/model_executor/kernels/mhc/
4. vLLM `mhc.py`： https://github.com/vllm-project/vllm/blob/main/vllm/model_executor/layers/mhc.py
5. vLLM mHC TileLang kernels： https://github.com/vllm-project/vllm/tree/main/vllm/model_executor/kernels/mhc
6. vLLM DeepSeek-V4 model implementation： https://github.com/vllm-project/vllm/tree/main/vllm/model_executor/models/deepseek_v4
7. Yang & Gao, *mHC-lite*, arXiv:2601.05732（用于对比约束/迭代优化方向）： https://arxiv.org/abs/2601.05732
