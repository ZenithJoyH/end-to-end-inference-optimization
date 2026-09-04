# 20260903-imported-qwen3-6-moe

## 1. 摘要

- 来源：[Qwen3.6-35B-A3B MoE 优化现状](https://o1pn62c31hl.feishu.cn/wiki/DOj3wYn5Si56IDkYvklc8Yerngc)
- 状态：`not-proven`（原文仍是优化现状/原型记录，无最终 E2E 验收表）
- 环境：Hygon BW（gfx936，80 CU），PyTorch 2.10.0，HIP 6.3.26093，BF16
- Workload：TP=2，64 prompts，input 1024 → output 256，`max_num_seqs=256`，`max_num_batched_tokens=8192`，关闭 prefix cache
- 证据等级：`observation`

## 2. 端到端瓶颈排序

原文 profile 的优先级不是按单次 kernel 慢多少，而是按累计占比与相对差距：

| 优先级 | 类别 | Hygon 占比 | 对照差距 |
|---|---|---:|---:|
| P0 | MoE `fused_moe_kernel` | 45.2% | 2.30× |
| P1 | DeltaRule 线性注意力 | 10.8% | 3.63× |
| P2 | all-reduce/all-gather 通信 | 7.8% | 3.07× |
| P3 | RMSNorm/pointwise Triton fusion | 6.2% | 4.19× |
| P4 | unified attention | 6.5% | 2.93× |
| P5 | causal Conv1d | 2.1% | 4.66× |

Dense GEMM 占比 11.2%，但相对对照仅 1.13×，原文判定已接近持平、无需优先优化。这是“累计可兑现差距优先”而非“占比优先”的典型案例。

## 3. MoE 数据流拆解

`fused_moe_kernel` 不是单个 kernel，而是一条编排链：router top-k → `moe_align_block_size` → GEMM1 gate/up → SiLU-and-mul → GEMM2 down → `moe_sum`。配置来自 `try_get_optimal_moe_config`，原路径让 GEMM1/GEMM2 共用 JSON tile。

这意味着：

- profile 标签必须映射回整条调用链，不能把 fused 名称误认为单一 kernel。
- GEMM1/GEMM2 的 shape、访存和最优 tile 不同，应允许独立配置。
- 如果两阶段 `BLOCK_SIZE_M` 不同，GEMM2 需要重新 align；额外 align 成本必须计入端到端收益。

## 4. 实验结果与反例

- 替换硬件匹配的 MoE JSON 后，M=64 decode 热点的原文总耗时从默认 413.4 降至 350.6（约 1.31×）；但 M=1 反而为 0.85×，说明配置收益不是跨 M 单调成立。
- 用 rocBLAS dense/grouped GEMM 替换：小 M 明显更差；随 M 增大，纯 BMM 才逐渐优于 FlagGems。但完整 gather + BMM + scatter 会显著吞噬纯 GEMM 收益。
- Decode 被判定为带宽受限，进一步融合收益有限；Prefill 数据量更大，才值得评估 GEMM1+activation、GEMM2+sum 的融合。
- Prefill 某候选 BN128 shared-memory 布局需要约 85 KiB，而设备每 block 只有 64 KiB；配置在理论上好看但硬件不可行。
- 推荐原型按阶段拆分：GEMM1 继续使用 FlagGems，GEMM2 使用 Hygon persistent grouped-GEMM；不要因为某 backend 在 GEMM2 最优就全局替换 GEMM1。
- WS2 weight sharing、expert-stationary 等尝试需把额外同步、调度和数据重排纳入完整路径，不能只比较核心 GEMM。

## 5. 可迁移经验

1. 先画出 fused op 的真实数据流和代码/dispatch 映射，再决定优化对象。
2. GEMM 调优必须覆盖生产 M 分布，不能只报一个热点或一个大 M。
3. GEMM1、GEMM2、Prefill、Decode 可以各自选择 backend/config；配置格式应支持分阶段覆盖和安全 fallback。
4. 纯 GEMM benchmark 只是上界，完整 gather/align/activation/scatter/sum 才决定服务收益。
5. 明确算力、HBM、shared memory、CU 数和 persistent program 上限后再搜索 tile，尽早排除不可能配置。

## 6. 未闭合项

- 原文没有给出最终候选的端到端 baseline/candidate/revert 多轮对比。
- GEMM2 Hygon 路径仍被描述为原型；正确性、稳定性和完整 shape fallback 尚需验收。
- 因此本案例只用于生成假设和检查清单，不能作为部署结论。
