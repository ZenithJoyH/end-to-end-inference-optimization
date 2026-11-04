# 20260920-p16k-scenario-entry-and-profile

- experiment-id：`20260920-p16k-scenario-entry-and-profile`
- 分类：`framework/diagnostic`
- 状态：`completed_current_parent_pending`
- 父场景：`P16384/D1024/C64/N128`

## 方向与假设

- 目标场景：`P16384/D1024/C64/N128`（`p16384-d1024-c64-n128`），finite batch，mixed。
- 入口基线：当前 P4K 阶段已保留的 Plugin / FlagGems-vllm / FlagGems 组合，不冒充未优化原路径 anchor。
- 主指标：output throughput。守护指标：失败请求、P99 TTFT/TPOT/ITL。
- 候选保留门槛：同配置 no-profiler output throughput 至少改善 `2%`，任一尾延迟回退不超过 `5%`，且正确性回归通过。
- 冷启动：按用户要求不纳入决策；仍保留一轮预热以区分编译/capture 与测量。

## 实验契约

1. 先用当前保留组合运行精确 `P16384/D1024/C64/N128`。首次诊断预算为 `7200 s`；超预算未完成则保留进度、日志和服务状态，标记 `deferred-too-slow/incomplete`。
2. 恢复 milestone 为 `P16384/D128/C16/N16`：保留 16K 输入，缩短 Decode 并减少并发/请求，用于低成本分解 Prefill、Decode 和 Mixed。
3. milestone 仅用于定位；任何保留候选都要先做 milestone 同配置 no-profiler A/B/revert，再回到父场景 Mixed checkpoint。
4. 服务条件冻结：PPU-07 / `hy4-opt-20260914` / TP16 / graph `FULL_DECODE_ONLY` / `max-num-batched-tokens=2048` / prefix cache disabled。

## Prefill / Decode / Mixed 证据状态

| 阶段 | 状态 | 方法 | 当前结论 |
|---|---|---|---|
| Prefill | measured | P16K 短输出 trace + TTFT/input-token 代理 | 初始 full-prefix chunk 主要命中 grouped sparse MLA；`scaled_mm`/MoE/AllReduce 也是主要成本 |
| Decode | measured_with_label_caveat | 父场景 TPOT/ITL + trace iteration/grid | 真正小 SQ Decode 命中 split-K；`execute_new_0_cached_1` 还包含 SQ2048 的 chunked-prefill continuation，不能按 marker 名直接当纯 Decode |
| Mixed | measured | 精确 P16K 父场景 no-profiler + 16-rank trace | 新请求 full-prefix 与 cached continuation 的 score-selected sparse MLA 同时存在，且对 Decode 产生明显干扰 |

TTFT/TPOT/ITL 只作客户端阶段代理，不当作纯设备时间。

## 实施、正确性与结果

- 源码改动：尚无。
- 正确性：未触发新代码回归；当前轮先建立运行证据。
- 性能结果：measured 轮 `128/128` 成功且无失败，用时 `1659.55 s`，output throughput `78.98 tok/s`，total throughput `1342.67 tok/s`，P99 TTFT / TPOT / ITL 分别为 `750815.25 ms` / `325.01 ms` / `1440.37 ms`。预热轮用时 `2820.45 s`、output throughput `46.47 tok/s`，按用户要求不纳入主结论。
- 运行观测：KV cache 容量 `424824` token，C64 下实际驻留约 `23–25` 请求，KV 使用率约 `93–100%`；未见 preemption/recompute。因此当前首个可证伪优化点是降低长 Prefill/Decode 共批干扰。
- 阶段窗口统计：合并预热与 measured 服务日志中，250 个 Prefill-active 窗口的 generation throughput 均值为 `24.56 tok/s`；197 个 prompt-throughput 为 0 且仍有 generation 的窗口均值为 `101.90 tok/s`。该代理统计仍包含阶段边界，不冒充纯设备耗时。
- 决定：保留为单 measured 轮的 diagnostic scenario-entry baseline；进入同配置 baseline/candidate/revert 筛选。

## P16K profiling 结果

- 有效 workload：`P16384/D128/C16/N16`，1 轮 no-profiler warmup + 1 轮 profiled measured；16/16 rank trace 均通过 gzip/JSON 校验，深入分析 rank 0/1/15。
- Prefill 采样设备活动主要占比：`scaled_mm 19.49%`、`fused_moe 18.97%`、Ring-LL AllReduce `15.78%`、full-prefix grouped sparse MLA `14.28%`。
- Mixed 主要占比：`scaled_mm 15.56%`、`fused_moe 15.14%`、generic sparse MLA `12.23%`、AllReduce `11.51%`、grouped sparse MLA `8.85%`。
- 原始 marker 分类中的 Decode bucket 里 generic sparse MLA 占 `36.34%`，但 grid 反查证明主要是 `SQ=2048` 的 cached chunked-prefill continuation，不是单 token Decode。真正小 SQ Decode 路径命中 split-K stage1/stage2。
- rank0 Indexer 互斥拆分：Prefill/Mixed/原 Decode 标签中本体分别占 `99.90%/94.42%/95.26%`；copy wrapper 仅 `0.10%/4.43%/4.68%`，memcpy wait `0/1.15%/0.13%`，显式同步为 0。复制/同步不是本轮主攻方向。
- grid 证据：`execute_new_0_cached_1` 内 generic kernel 以 `grid=(2048,1,1)` 运行，rank0 共 6381 次、平均 `6148 us`。这与已有 P4K `SQ2048/topk2048/HQ4` 路径形状一致，但 P16K 更长 KV 下的 score-selected gather 成本明显增大。
- 决定：结束调度参数扫描，首个算子候选改为 cached-prefill 的 score-selected sparse MLA hybrid；保留初始 full-prefix grouped 路径不变。

## 外部证据

- 远程案例目录：`/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e`
- 计划基线目录：`.../results/performance/20260920-p16k-d1k-c64-n128-scenario-entry-01`
- 有效 profiling 目录：`.../results/profiling/p16k-d128-c16-n16-scenario-entry-20260920-02`
- run record SHA256：`b5344b580a71ae51965573e87cc65282a4ca6a9a10bfdec124b2ce948c1df46b`
- 阶段窗口摘要 SHA256：`67ec803b81690e4a385a5365cd4050dcf54aae430424e02ab047c756273aad6d`
- compact profile SHA256：`62012aa584da36fd5c36d7fb31a63da37feaa541d409574f3232cc8c0224ceeb`
- trace inventory SHA256：`1621c3ed83e7ff50a0ffb7dcbf54269129431ecc7e9a9d9c9bdd1e6b56568a4a`
- sparse-MLA grid 归因 SHA256：`b61c35d741fd34eeea10992c7d9a403199cf2092c1b7b74e483922d28f28ed3b`
