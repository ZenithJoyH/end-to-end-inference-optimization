# P4K 缩减场景热点迁移（2026-09-15）

对比 `P4096/D128/C8/N8` 的优化前后 profile，16/16 rank trace 完整：

- `mm_out` 黑名单实际命中：旧 profile 的 `mm_kernel_general` 为 111,633 次、Decode 35.456 秒（33.40%），新 profile 中为 0。
- Indexer metadata 缓存实际命中：Prefill/Mixed/Decode 的 `cudaMemcpyAsync` host wait 分别从 652.255/4418.831/7825.059 ms 降至 6.930/4.253/25.130 ms，Indexer 总时长分别下降 47.4%/43.6%/55.3%。剩余主要是 Indexer 本体，不再是元数据复制等待。
- Split-K sparse MLA 实际命中：Decode stage1/stage2 各 28,885 次，累计 1475.111 ms。剩余通用 `triton_flash_mla_sparse_fwd` 为 1,835 次、11.768 秒（20.03%），launch grid 反推为 `SQ=2048`。
- 新的主要 device 热点为：Prefill 的通用 sparse MLA 22.64% 与 ring all-reduce 22.28%；Mixed 的 ring 23.30% 与通用 sparse MLA 21.91%；Decode 的通用 sparse MLA 20.03%、linear 14.27%、fused MoE 13.53%。
- rank0 Decode inclusive CPU 中，`cudaEventSynchronize` 从 20.896 秒降至 9.143 秒，`cudaGraphLaunch` 从 15.249 秒降至 6.916 秒。两者有嵌套，只作为迁移证据。

结论：`mm_out` 与 Indexer copy/sync 两个既定瓶颈已被消除或大幅压低，下一算子候选收敛为 `SQ2048/HQ4` 的通用 sparse MLA；通信与 MoE/linear 是随后的热点。Profiler 时间不用于性能收益判定。
