# prof-005：post-op010 P4K 分阶段热点刷新

## 结论

`prof-005` 已完成 bounded P4096/D128/C64/N64 no-stack capture、8 个 TP rank
分段分析和无 profiler 服务恢复。该结果只用于归因，不是性能收益证据；op010 的端到端
收益仍以 P4096/D1024 同 contract A/B/R 的 `+3.4168%` 为准。

修正后的全 rank 分析显示：每个 rank 都有 1 个纯 Prefill、63 个 Mixed 和 129 个
Decode graph window。Mixed 是本轮主要墙钟区间，marker span 中位约 `40.1435s`；
Decode 约 `15.5792s`，纯 Prefill 约 `0.6462s`。Mixed 中 QSA sparse 与 fused MoE
分别占累计 device activity 中位约 `23.99%` 与 `23.63%`，其后是 AllReduce 和 native
GEMM。`mm_kernel_general` 已退出各阶段 top20，证明 op010 的 provider 替换真实进入
当前 graph 路径。

## 捕获与恢复

- 服务来源：service48，实例
  `9b65cc77d73c-8030-2650977-260572911`。
- profiler 服务：service49；唯一 launch-arg 变化为加入 torch profiler config。
- workload：P4096/D128/C64/N64；1 次无 profiler warmup + 1 次 profiled measured；
  seed 42；timeout 1800 秒。
- runner diagnostic：`complete`、`errors=[]`；两轮都 valid；measured 轮 64/64 请求
  成功、0 失败。diagnostic SHA-256：
  `7e6d615ba43a5ee3188e48024cb7b7a2a688b77bb38a4afc6da7b984ff946bdb`。
- trace：1 个 async + TP0–7 共 9 份，全部通过 `gzip -t`、runner parseability 和 SHA
  冻结。trace 清单 SHA-256：
  `549574ffc68599910424e86465c0e877d7781ca645b9191054f739429ef7fac1`。
- 恢复服务：service50，实例
  `9b65cc77d73c-8030-2655295-260762280`；无 profiler，保留 native `mm/mm_out`、
  QSA bound 8448、exact-M64 BM16 和 maxseq64/batched4096。readiness、full graph
  capture、canonical capture + 两次 replay 均通过。manifest SHA-256：
  `cd516594c40b4d666d17bcb8c6194a6d0ade641c9ff30d0aeddf4651050d2951`；canonical
  SHA-256：`54f05e02051a882c0b45503581c97389e987c8e8b7be6bd7a227e544b7d9cbf7`。

## 分段语义修复

首次分析把 `execute_new_1` 固定解释为 Prefill、`execute_new_4` 固定解释为 Mixed，
因此在没有 `execute_new_4` 时正确地以 `incomplete` 停止；该无效摘要保留在
`summaries/`，完整性文件 SHA-256 为
`cf334edbadea37f56c7fd6973d0014d695f070639a3589ba21696170fe77babe`。

运行源码证明 marker 是
`execute_new_{len(scheduled_new_reqs)}_cached_{len(scheduled_cached_reqs)}`。因此通用
语义应为：`new>0,cached=0` 是 Prefill，`new=0,cached>0` 是 Decode，二者都大于 0
才是 Mixed。P4K 的 4096-token budget 每步只能接纳一个完整 prompt，所以真实 Mixed
marker 是 `execute_new_1_cached_1..63`，不存在 `execute_new_4` 完全正常。

修正分析写入 `summaries-v2/`，8 rank 的三阶段覆盖、outside-window accounting 和
方法一致性全部通过。完整性 SHA-256：
`a80797d51fe25f8047cc66c724ac970a20680345612c9e6e4e228201d0026318`；全 rank 聚合
SHA-256：`ab22f50fe6d6d1e056310f550cf707297eb9a7b832de1f60c1b1d5e1ccc5a388`。

## 当前热点

以下都是 profiler-on 累计 activity，可能重叠；不能相加为 critical path 或收益上限。

| 阶段 | Device activity 中位 | 主要热点（跨 rank 中位） | 诊断 |
|---|---:|---|---|
| Prefill | 0.505s | QSA sparse 0.117s；MoE 0.108s；RING AllReduce 0.092s | 只有一个窗口，主要用于路径确认 |
| Mixed | 30.600s | QSA sparse 7.339s；MoE 7.227s；RING AllReduce 3.968s；三类 native GEMM 合计约 5.045s | 63 个 admission+decode 共存窗口，是当前首要阶段 |
| Decode | 7.082s | MoE 2.279s；two-shot AllReduce 1.742s；QSA sparse 0.435s | MoE 仍为算子首热点，但已尝试的相邻 tile/fusion 方向均退化 |

AllReduce 与 `cudaStreamSynchronize` 的调用次数在 rank 间基本一致，但累计时长高度不均：
Mixed sync 为 rank0 `10.694s`、rank1 `14.873s`；Decode 为 rank0 `3.635s`、rank1
`5.899s`。QSA/MoE 自身跨 rank 总时长接近，而 collective/sync 差异更大，因此需要先
定位确切同步/通信调用点，不能把 rank spread 直接归因于 QSA 或 MoE kernel。

## 决策边界

- 保留 op010：`mm_kernel_general` 已从 top20 消失，native GEMM 真实命中；但 profiler-on
  数据不产生新的 speedup 数字。
- 停止继续扫描已失败的 M40/48/56/63、GEMM2 BN128、GEMM1+SiLU 和 native TopK。
  独立 TopK probe 已证明其 control-adjusted stream sync 为 0。
- `op-013` shape-selective provider 只有在实际生产 shape 频率与 graph 微基准共同预测
  `>=8%` 加权完整 GEMM 收益时才允许进入实现；否则按 plan-014 停止。
- `fw-006` 只有在 stream-sync/collective 的 marker-scoped 归因能形成因果控制并预测
  `>=1%` 精确 P4K Mixed 收益时才晋级服务实验。
- P32K 仍为 `deferred-too-slow/incomplete`；正式精度仍被 GPQA 170/198（85.86%）低于
  冻结 88% 阈值阻塞。

## 外部证据

- 根目录：`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/prof-005-p4k-post-op010`
- v2 完整性：`summaries-v2/phase-completeness.json`
- v2 全 rank 聚合：`summaries-v2/hotspot-aggregate.json`
- trace SHA：`summaries-v2/trace-SHA256SUMS`
- 恢复 manifest：`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/manifests/post-prof005-native-service50.json`
