# 端到端推理优化经验模式

## 文档定位

本文件汇总跨案例可复用的诊断模式。案例中的性能数字仍归属原测试环境；这里抽取的是决策方法、适用边界和反例，不把历史结果当作当前项目的复测结论。

证据来源：

- [DeepSeek-V4-Flash W8A8 INT8](cases/20260903-imported-deepseek-v4-flash-w8a8/README.md)
- [GLM-5.2 W8A8](cases/20260903-imported-glm-5-2-w8a8/README.md)
- [Qwen3.6-35B-A3B MoE](cases/20260903-imported-qwen3-6-moe/README.md)

## 已进入 SOP 的模式

### 1. 正确性和真实执行路径先于性能结论

- 证据等级：`invariant`
- 现象：DeepSeek 案例在发现 decode top-k 实际走 no-op/reference、graph capture 存在 CPU 同步后，宣布此前性能数据失效；GLM 案例也发现 Python wrapper/source guard 可能被 Inductor 内联，导致“写了分支”不等于运行时命中。
- 规则：基线与候选都必须证明语义正确、目标路径命中、fallback 行为明确。仅有源码改动或环境变量不足以构成证据。
- 最小证据：输出对照、启动日志、运行时计数器或 profiler kernel symbol 至少一种；高风险路径应同时具备正确性对照和运行时命中证据。

### 2. Prefill、Decode、Mixed 必须分治，生产 shape 必须白名单化

- 证据等级：`transferred`
- 现象：三个模型中，小 M decode 和大 M prefill 的最优 backend、tile、并行度均不同；Qwen 的 GEMM1/GEMM2 即使在同一 MoE 内也需要独立配置。
- 规则：调优键至少包含阶段、实际 M/序列形状、dtype、拓扑和 graph/eager 模式。仅对实测生产 shape 开启特化路径，其他 shape 保留正确 fallback。
- 反例：单套 Triton 配置覆盖 M=1 到大 M；把单一 decode 最优配置推广到 prefill；全局替换 GEMM backend。

### 3. 用端到端可兑现收益排序，而不是按单 kernel 倍数排序

- 证据等级：`transferred`
- 现象：DeepSeek 的 cache clone、top-k、MHC projection 都因高调用频次形成大累计成本；Qwen 中 dense GEMM 已接近目标平台，即便占比不低也不是优先项；GLM 的 node-local 通信虽然增加两次 all-to-all，但通过解决 H4 low-grid 仍取得净收益。
- 规则：候选优先级近似为 `累计时间 × 可消除比例 × 生产命中率 - 新增开销与风险`。必须从 microbenchmark 逐级验证到 kernel、服务和端到端。

### 4. 首先寻找与有效工作量无关的成本

- 证据等级：`transferred`
- 典型信号：整块 KV cache clone、逐请求循环产生大量 launch、CPU 同步、重复 Prompt Prefill、未使用的中间张量、固定启动开销、跨请求无效计算。
- 原因：这类成本常随容量、调用次数或并发增长，而不是随真实有效计算增长，通常比细调算术 kernel 更值得优先处理。

### 5. 调度容量按完整生命周期计算

- 证据等级：`transferred`
- 现象：GLM 案例表明只按 Prompt 阶段设置 `max-num-seqs` 会在 Decode 增长后触发 KV 抢占，vLLM V1 抢占又会清零已计算 token 并重做 Prefill；DeepSeek 案例中更大的 batched-token 上限也存在 TTFT 拐点。
- 规则：同时记录 KV 容量、抢占次数、重算 token、batch occupancy、TTFT 和 TPOT；目标是最大可持续驻留并发，而不是最大瞬时准入。

### 6. 冷启动、Profiler 和稳态数据严格分账

- 证据等级：`invariant`
- 现象：Triton autotune、lazy graph capture 可令冷轮显著变慢；Profiler 会改变时序。
- 规则：冷启动用于启动体验，Profiler 用于归因，预热后无 profiler 的重复轮次用于正式吞吐/延迟结论，三者不得混用。

### 7. 数值等价边界是优化设计输入，不是最后补测项

- 证据等级：`transferred`
- 现象：DeepSeek 的 decode/prefill top-k 不能因名称相同就复用实现，tie 语义不同会同时造成错误和负优化；GLM 的 scaled-MM、GEMM+SwiGLU 与 BF16 top-p 替换均需要显式保留 scale 角色、BF16 round-trip、舍入点、tie 和累积顺序。
- 规则：在 backend 替换、融合或算法替换前，先冻结数值契约，至少列出输入/输出 dtype、cast 与舍入位置、归约或排序顺序、tie 处理、归一化/累计阈值、空输入与边界行为。候选设计必须说明如何保持这些边界，再进入性能测试。
- 反例：仅用常规随机输入的最大误差通过，就把改变 tie、累计阈值或量化舍入顺序的实现标为“等价”。

### 8. split、chunk、packing 和调度参数按完整路径寻找拐点

- 证据等级：`transferred`
- 现象：DeepSeek 的 decode Sparse MLA 中 S=8 microbenchmark 快于 S=4，但服务更慢；batched-token 继续增大也会越过 TTFT 拐点。GLM 的 Indexer Prefill chunk 由中间 logits 内存预算约束，Query Head Packing 则必须用计算收益偿还两次 all-to-all。
- 规则：这类参数不是越大越好。实验前写出限制资源和新增成本，测量时包含 merge、通信、copy、临时内存、graph 覆盖及服务排队，保留满足主指标和守护指标的最小稳定工作点。
- 反例：只测拆分后的主 kernel，忽略 merge/通信；直接把历史案例的 S、M 阈值、内存预算或 batched-token 数值复制到新平台。

## 保留为候选的模式

以下模式有清晰机制，但目前只在有限平台或 shape 上出现，默认仍需目标环境复测：

| 模式 | 证据 | 适用边界 |
|---|---|---|
| 用 graph-opaque custom op 固定关键小 shape 路径 | `observation` | 编译器会内联/折叠 Python dispatch，且 custom op 的 fake/meta、fallback 和图捕获均完整 |
| 对大状态向量分段并重算少量标量 | `observation` | shared memory/register live range 是瓶颈，重算成本低于占用率收益 |
| 节点内聚合过小的 TP head/grid | `observation` | 单 rank low-grid 严重，通信开销小于 kernel 利用率收益 |
| 利用有限离散值域做精确 counting sort | `observation` | 输入值确实来自有限编码域，且 tie、softmax、累积顺序保持原语义 |
| GEMM epilogue 融合反量化/激活 | `observation` | 中间读写和 launch 占比足够高，并保留原 BF16/量化舍入边界 |
| 以真实 stride 传递 view，避免按 cache 容量物化连续副本 | `observation` | 下游实现支持该 layout，最内维连续且非兼容情况有明确 fallback |
| 按最大中间张量字节预算推导 Prefill chunk | `observation` | 中间张量是已证实的内存/调度瓶颈，预算包含并发与 graph 所需余量 |

## 案例驱动的首个实验卡

以下条目用于缩短“看到信号”到“开始单变量实验”的时间；它们不是未经测量即可启用的配置：

| 运行信号 | 第一检查 | 首个单变量实验 | 立即停止条件 |
|---|---|---|---|
| Python/source guard 存在，但 graph 中看不到目标实现 | 检查编译后 graph、kernel symbol 和运行时计数 | 用最窄的 graph-opaque/custom-op 边界包住已验证 shape，保持 fallback 不变 | fake/meta、capture/replay、fallback 或实际命中任一失败 |
| 每请求、每 token 重复发射相同 dequant/logits 小 kernel | 核对循环次数是否随并发线性增长及张量能否批处理 | 只把请求维合成 batch 级调用 | batch 化引入 padding/同步后服务净收益消失 |
| copy 时间随 cache 容量增长而非有效 token 增长 | 比较源 tensor 的 shape、stride、连续维和下游要求 | 保留 3D/view 和真实 stride，取消一次物化副本 | 下游 layout 不兼容、隐式 copy 仍存在或 fallback 不正确 |
| Prefill 中间 logits/score 张量限制 batch 或造成显存尖峰 | 先以 dtype×shape 计算最大中间字节数 | 固定其余参数，按显式字节预算扫描一个 chunk 上限 | chunk launch/重复计算吞噬 TTFT 或吞吐收益 |
| 单 rank head/grid 远小于设备并行能力 | 先区分 head padding、sequence split 与 TP 切分造成的 low-grid | 先试无通信的小 tile/split；仍不足时再单独试节点内 packing | merge 或两次通信未被计算收益覆盖 |
| 固定小 M GEMM 被通用大 M backend 捕获 | 证明生产 shape、调用频次和 graph 内实际 backend | 对单一 shape 比较已有小 M backend；无兼容实现时再试窄特化 | 只在 microbenchmark 命中，或完整调用无净收益 |
| 采样/排序输入来自有限表示域 | 证明可达值域、tie 和累计语义 | 对边界值与大量 ties 做精确 reference A/B，再测算法替换 | 任一 tie、阈值或概率累计结果不一致 |
| 增大 split/tile/warp/stage 的局部 kernel 时间继续下降 | 量化新增 merge、寄存器、shared memory 与服务阶段成本 | 只改变一个参数并扫描到第一个守护指标拐点 | 完整服务指标变差，即使主 kernel 继续变快 |

## 已知反例与止损条件

- microbenchmark 更快但服务 profile 未命中：不合入，先修 dispatch 或撤销。
- 更大的 `max-num-batched-tokens`：可能提高吞吐，也可能恶化 TTFT；必须扫描拐点。
- 更高 split 数、更多 warp/stage、更大 tile：都不是单调收益，可能增加 reduce、寄存器或 shared-memory 压力。
- dense/grouped GEMM 替换：大 M 纯 GEMM 的优势可能被 gather/scatter、padding 和调度开销吃掉。
- 融合：若被融合部分在 decode 只有数微秒，开发和正确性成本可能高于收益。
- 复用 decode top-k 到 prefill：可能因大行数和 tie 语义导致更慢或不等价。
