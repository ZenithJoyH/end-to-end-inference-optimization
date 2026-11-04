# 20260921-p4k-mixed-cpu-sync-attribution-07 P4K Mixed 主机同步归因

- 状态：`complete/no-source-change`
- 分类：`framework`
- 目标场景：P4096/D1024/C64/N128
- 目标阶段：Mixed；Prefill/Decode 作为边界对照
- Profiling 模式：`analyze`，复用已验证的 16-rank trace，不重新启动服务

## 问题与证据边界

现有 rank0 Mixed 汇总中 `aten::nonzero/to/_to_copy/copy_`、
`cudaStreamSynchronize`、`vllm::kda_attention`、`aten::index` 各有约
16–19.6 s inclusive 时间，但这些事件很可能是同一次同步等待的嵌套父子区间，
不能相加或直接当作可优化的 CPU 时间。

本实验使用同线程嵌套区间计算 CPU exclusive/self time，并将同步区间与同一
Mixed marker 内的设备活动 union/空洞对齐，回答：

1. 主机是否在设备空闲时制造了可削减的关键路径；
2. 还是 `cudaStreamSynchronize` 主要在等待真实设备工作，顶层 inclusive 排名只是重复计数；
3. 如果同步是关键屏障，其父链和相邻 device kernel 是什么。

## 停止条件

- CPU 独占时间或设备空洞与目标事件无明显关联：停止，不改源码。
- 同步期间设备基本持续忙碌：不宣称存在纯 CPU 优化空间，转到具体设备算子/算法。
- 证明有稳定、非重叠的主机关键路径：再创建独立单变量优化实验。

## 最近无 profiler 基线

`P4096/D1024/C64/N128`稳态 output throughput 中位数
`1071.416886659195 tok/s`；此处 trace 只用于归因，不用 profiler-on 时间计算收益。

## 外部证据

- trace：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p4096-d1024-c64-n128/profiling/p4k-d1k-maxseq64-retained-01`
- 预期分析产物：上述目录 `analysis/` 中的 CPU self-time/device-gap 结构化摘要。

## 结果

16 个 rank 均完成同一分析，边界均为 16 个 Mixed CPU marker 与
16 个 Mixed GPU marker。

- 设备 kernel/memcpy/memset 的 union busy fraction 在 rank 间为
  `96.236% / 96.796% / 96.893%`（最小/中位/最大）。
- `cudaStreamSynchronize` 的 CPU self-time 占 Mixed CPU marker 在 rank 间为
  `79.514% / 81.660% / 81.941%`。
- 但这些同步区间与真实设备活动的加权重叠为
  `99.746% / 99.791% / 99.807%`，所有 rank 一致。
- `83.47%–83.50%` 的同步 self-time 来自同一父链：
  `vllm::kda_attention > aten::index > aten::nonzero > aten::to >`
  `aten::_to_copy > aten::copy_ > cudaStreamSynchronize`。
- 拆除嵌套子区间后，`aten::nonzero` 真正 self-time 只占
  `0.438%–0.540%`（中位 `0.454%`），`aten::to/_to_copy` 为近似 0，
  `aten::copy_` 中位为 `0.267%`。

最长 rank0 同步为 `64.413 ms`，其中 `99.887%` 时间设备处于忙碌，
主要覆盖 Sparse MLA prefill、fused MoE、MQA logits、索引转换与
PCCL all-reduce。

结论：原 inclusive 排名是同一设备等待的嵌套重复计数，不存在一个可单独
削减的 16–19 s 纯 CPU 空转热点。直接黑名单/替换 `nonzero/to/copy`
不能产生对应收益，还可能改变数值或动态 shape 语义。本方向按停止条件结束，
未改源码；下一步回到设备侧具体路径，优先检查 Mixed 约 9.3% 的
MQA logits。

## 证据哈希

- 16-rank 分析：`analysis/mixed-cpu-sync-all-ranks.json`，SHA256
  `60147efa4fd46fcd4299644c3d1f851dd585c14944555dd2081fee117299bda6`。
- rank0 详情：`analysis/mixed-cpu-sync-rank0.json`，SHA256
  `a51f72e59fdc1e70c89521e06be74a5428adba5c8536ddbc2144c8470c729a13`。
- 分析器：`commands/p4k-phase-profile-20260920/analyze-mixed-cpu-sync.py`，
  SHA256 `9ed0bfcafb2f49b516cfd906e3c2f9824ab808321a40bdd4fa1e296a3deabc81`。
