# 20260903-imported-glm-5-2-w8a8

## 1. 摘要

- 来源：[GLM-5.2 W8A8 优化文档](https://chitu-ai.feishu.cn/docx/FsTmdxIRxoobJLxLNOKcoCONnue)
- 状态：`kept`（持续演进的原案例）；本项目仅完成资料导入，未独立复测
- 主要范围：Indexer、Sparse MLA、MoE、采样、MCTlass GEMM、TP16 节点内通信和 vLLM 调度
- 证据等级：原文性能数据记为 `observation`

文档包含多个版本，不能把不同日期的结果直接拼成同一基线。8 月 18 日表中记录：

| 场景 | Duration | Output tok/s | Total tok/s | Mean TTFT | Mean TPOT |
|---|---:|---:|---:|---:|---:|
| 1K | 186.455 s | 351.485 | 702.965 | 24005.35 ms | 156.895 ms |
| 4K | 469.165 s | 139.685 | 698.430 | 171171.24 ms | 146.375 ms |

后续 v5 摘要又记录 P4K total tok/s 从 698.430 提升至 925.831（+32.56%）。该值属于后续版本，需与对应完整配置一起使用。

## 2. 瓶颈与有效改动

- Indexer Prefill 分块：按 FP32 logits 内存预算计算 `max_query_len=floor((max_logits_bytes/4)/seq_len)`，原文记录 total throughput +15.41%、Mean TTFT -13.28%。
- MoE runtime M bucket：Prefill 的大 M 与 Decode 的 M=8/16/24 使用不同 tuning key；大 M 配置减少 warp/stage，降低寄存器和片上压力。
- Scaled-MM 精确替换：为保持 BF16 scale 乘法和舍入顺序，使用转置 GEMM 交换矩阵/scale 角色，并通过转置写回避免额外 copy；只白名单验证 shape。
- Indexer-Q 融合：将 RoPE、amax、FP8 scale、量化和若干 scale 计算合为单个 decode kernel，减少 launch 与中间流量。
- `n_group=1` Router：删除不可能改变结果的组级路由步骤，保留 expert top-k、bias、归一化和 routed scale。
- Exact BF16 top-p counting sort：利用温度 1.0 时概率值来自有限 BF16 值域，替代大词表 generic stable sort，同时保持精确 tie 和累积语义。
- MCTlass GEMM1 + SwiGLU：对固定小 M decode shape 融合反量化、显式 BF16 round-trip 和激活，减少中间读写与 launch。
- Mixed Prefill Query Head Packing：TP16 下单 rank 仅 H4，8 个节点内 rank 通过两次 all-to-all 聚合为 H32 执行 Sparse MLA，再恢复布局；M≥512 才启用。原文按 78 层估算节省约 507 ms。

## 3. 调度经验

- `max-num-seqs` 要按 Prompt 完成后持续增长的 Decode KV 计算。vLLM V1 抢占会将 `num_computed_tokens` 清零，导致 Prompt Prefill 重算。
- 优化目标是“最大可持续驻留并发且零 KV 抢占”，而不是 Prefill 阶段一次接纳最多请求。
- `max-num-batched-tokens` 与 `long-prefill-token-threshold` 需要和对应 prefill GEMM shape 联动；调度参数会改变算子 shape 分布，不能与 kernel tuning 分开看。

## 4. 可迁移经验

1. 编译图中 Python 分支不一定存活；必须用 profiler symbol 或运行时计数证明 patch 命中。
2. backend 替换需保留数值运算顺序，尤其是 BF16/FP8 量化与 scale 边界。
3. 通信不是天然负优化；当单 rank low-grid 严重时，少量节点内通信可换取更大计算粒度。
4. 调度决定生产 shape，kernel 最优配置反过来会影响调度拐点，两者需要联动扫描。
5. 特殊数据表示可以带来“精确算法替换”，但必须证明值域、tie 和累计语义，而不能偷偷近似。

## 5. 限制

- 文档为持续更新状态，版本摘要与 8 月 18 日完整表并非同一时间点。
- 本次没有取得完整原始结果、代码 revision 和正确性报告，所有数字仅作历史观测。
