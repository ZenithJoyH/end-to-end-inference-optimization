# 20260920-p4k-phase-profile-03 P4K Prefill/Decode/Mixed 热点定位

- 状态：`complete`
- 分类：`framework`（诊断）
- 目标场景：P4096/D1024/C64/N128
- profile 模式：`capture_then_analyze`

## 优化方向与瓶颈依据

P4K 稳态基线已经完成，但客户端指标只能说明 TTFT/TPOT 和端到端结果，不能把
P1K 的 Decode fused-MoE 热点直接外推到 P4K。长 prompt 会放大 Prefill 的
Sparse MLA、KDA、large-M MoE、通信和 Mixed admission 干扰，需要重新采集
16-rank trace 并用执行 marker 分阶段归因。

## 优化内容与适用边界

本点不修改源码。启动与基线相同的 TP16/BF16/max64/token-budget16384 graph
服务，增加 torch profiler：record shapes、gzip、无 stack/flops/memory，最多
120 iteration。先运行一轮 profiler-off P4K warmup，再运行一轮 profiler-on
P4K，要求生成 ranks 0..15 的全新可解析 trace。

分析使用 `execute_new_<new>_cached_<cached>` 成对 CPU/device marker：new-only
为 Prefill，cached-only 为 Decode，同时存在为 Mixed。inclusive activity 允许
重叠，只用于热点排序，不解释为关键路径时间或正式吞吐。

## 正确性与路径命中

启动前核验三个仓库 revision、dirty 集合、exact-M64 guard、FlagGems DB SHA、
prefix cache disabled 和 profiler 参数。要求两个客户端轮次请求全部成功，DB
SHA 不变，16/16 rank trace 新鲜且每个阶段 marker 有效。

## 性能效果

一轮 profiler-off 与一轮 profiler-on 均为 128/128 成功。profiler-off 输出吞吐
1051.43 tok/s；profiler-on 为 641.97 tok/s，只说明 profiler 开销，不与无
profiler 基线计算收益。16/16 rank trace 均新鲜可解析，rank0 共 120 对执行
marker：1 Prefill、16 Mixed、103 Decode。

rank0 summed device activity（允许重叠）显示：

- Prefill：fused MoE 27.883%，Sparse MLA prefill 21.630%，Ring all-reduce
  11.603%，large-M GEMM 6.720%；
- Mixed：Sparse MLA prefill 24.694%，fused MoE 22.019%，large-M GEMM
  12.515%，FP8/FP4 MQA logits 9.313%，Ring all-reduce 6.004%；
- Decode：fused MoE 42.514%，two-shot all-reduce 6.376%，Sparse MLA
  prefill kernel 6.352%，mHC pre 6.262%，reduction 6.162%，MoE align 5.791%。

Mixed 的 16 个 marker 中，15 个每次引入 4 个新请求，正好对应
`16384/4096=4` 的 token budget；Mixed device activity 跨 rank 相对离散仅
0.744%，Decode 为 2.644%，不存在明显单 rank 拖尾。

## 决定、风险与回退

当前决定为 `complete`。首个 P4K 单变量选择
`max_num_batched_tokens=16384→32768`：它直接针对 16 个四请求 admission wave，
理论上可把每波提升为八请求并减少 Mixed 波次。P1K 的同变量失败不会外推为
P4K 结论；P4K 使用更严格的 fresh-service 6 warmup（仅最后三轮判稳）+3 measured
合同验证。profiler 服务已停止。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p4096-d1024-c64-n128/profiling/p4k-d1k-maxseq64-retained-01`
- `phase-analysis-v3.json` SHA-256：
  `589975e4e30284b0f95451d41f90e8c10373a4d3ec689557f6155c9fe08ead14`
- `runtime-evidence.txt` SHA-256：
  `7c131e0a18c59dc5201c9bc9584c6c1fb0c19d24f6c2d275c2f8e7aaad794b3c`
- `diagnostic.json` SHA-256：
  `a1d2b905a0cc09a451c91d46f171726be1a055f7011ddefa165f66fc46dc784e`
