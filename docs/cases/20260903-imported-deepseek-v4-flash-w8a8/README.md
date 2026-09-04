# 20260903-imported-deepseek-v4-flash-w8a8

## 1. 摘要

- 来源：[Deepseek v4 flash w8a8 int8 优化文档](https://chitu-ai.feishu.cn/wiki/Th7JwlkSqi6Y4ikHW8kcuJ6yngZ)
- 状态：`kept`（原案例）；本项目仅完成资料导入，未独立复测
- 模型/环境：DeepSeek-V4-Flash-W8A8-INT8，8× MetaX C550 64GB，vLLM 0.20.2 + vllm-plugin-FL + FlagGems，TP=8，KV FP8
- Workload：P1K/D1K/C64 与 P4K/D1K/C64
- 证据等级：原文性能数据记为 `observation`；跨案例方法论单独在经验模式文档评级

原案例先修复 decode top-k no-op/reference fallback 和 graph capture 中的 CPU 同步/动态 shape，并废弃此前无效数据。语义正确基线到最终组合的原文结果如下：

| 场景 | Output tok/s | TTFT | TPOT |
|---|---:|---:|---:|
| P1K baseline | 117.45 | 56.42 s | 486.69 ms |
| P1K final | 568.56（+384.1%） | 6.42 s（-88.6%） | 106.16 ms（-78.2%） |
| P4K baseline | 52.97 | 338.27 s | 861.59 ms |
| P4K final | 405.31（+665.2%） | 28.69 s（-91.5%） | 129.01 ms（-85.0%） |

这些数字来自原文，不代表当前仓库已复现。

## 2. 瓶颈与有效改动

| 层级 | 根因 | 原案例处理 | 关键边界 |
|---|---|---|---|
| 正确性/graph | top-k fallback 无效、CPU 同步和动态 shape | 精确 tree top-k；GPU `seq_lens`；graph-safe decode | 先废弃错误基线，再谈性能 |
| Decode Indexer | C64 每步按请求产生约 128 次 dequant/logits launch | batch 级 fused logits | 需在 graph 内证明实际命中 |
| Prefill Sparse MLA | HKV=1、Q head 多，BH16 重复读取 KV | BH32/BK16 | 受 64 KiB shared memory 上限约束 |
| Decode Sparse MLA | 单 split grid 小于 SM 数，利用率不足 | split-topk S=4 + merge | S=8 microbench 更快但服务更慢 |
| KV gather | 将带 padding 的 3D cache `.contiguous()` 为 2D，复制量随 cache 容量增长 | 直接传 3D tensor 和真实 stride | 最内维必须连续，其他情况 fallback |
| 小 M projection | `[M,16384]×[16384,24]` 被低效 GEMM 路径捕获 | graph-opaque custom op + shape-specific split-K GEMV | 其他 shape 回退 `torch.mm` |
| Prefill top-k | FlagGems iterative max-select 累计占时高 | blacklist 后走原生 `aten::topk`/mbtopk | 必须用 profiler symbol 验证 backend |
| Prefill DQK512 | FP32 accumulator live range 和 shared memory 压力大 | 两段 half-D，重算 score/softmax | 仅严格白名单 shape |
| Scheduler | batched token 上限影响吞吐/TTFT 平衡 | 2048→8192 保留 | 16384 因 TTFT 回退而拒绝 |

## 3. 重要失败与止损

- flushoff/flowfix 机制成立，但稳态无收益。
- 小 M GEMM backend 在 microbenchmark 获益，但服务 graph 未命中，暂缓。
- MoE `BM` 调整没有 fragmentation 证据，不继续。
- SWA fast path 只有约 2% kernel 收益，优先级不足。
- `BH8` 因 `tl.dot` 最小维度约束失败。
- decode tree top-k 直接用于 prefill，在 4096 rows 变慢且 tie 语义不匹配。
- Prefill paged FP8 直接读取因重复 dequant 反而约 1.5× 更慢。
- Python guard 未进入图，最终需要 custom op 固定 dispatch 边界。

## 4. 可迁移经验

1. 先证明语义和真实执行路径；错误 baseline 的任何加速都无效。
2. 排查成本是否随 cache 容量而不是实际 token 工作量增长。
3. 生产服务只接受 `microbench → kernel profile → service → E2E` 全链路兑现的收益。
4. Prefill/Decode 使用不同实现与 tile，shape 特化必须有 fallback。
5. 每次大优化后重新 profile；热点会迁移，旧排序会失效。
6. Triton autotune、lazy graph capture 的冷轮和 profiler 轮不进入正式稳态统计。

## 5. 缺失项

本次资料抽取未保存原始 trace、补丁、完整逐轮原始结果和正确性样本，因此不能把原文百分比升级为本项目 `reproduced` 证据。
