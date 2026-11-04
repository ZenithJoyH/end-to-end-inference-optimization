# fw-001：P1K Mixed 的 Prefill/Decode 干扰与调度工作点

## 契约

- 分类：`framework`
- 父目标：`p1024-d1024-c64-n128`
- 状态：`rejected_reverted`
- 单一问题：当前 `max_num_seqs=32`、`max_num_batched_tokens=8192` 是否会在 C64/N128 的后续 admission/prefill 波次中暂停正在 decode 的请求，造成 16–21 秒单次 token gap 和 Mixed 尾延迟/吞吐抖动？
- 最近无 profiler 证据：Prefill probe 稳定；Decode 与 Mixed 均出现少数慢轮。Mixed 慢轮有 42 个请求 TTFT >80 秒，per-request 最大 ITL 的 P90 为 19.22 秒；正常轮最大 ITL <0.8 秒。Decode 慢轮恰有 32 个请求 TTFT >80 秒，最大 ITL 的 P90 为 21.17 秒。
- 竞争解释：随机 token 导致 MoE routing/rank imbalance；host/collective stall；客户端限制；周期性 graph break。客户端已完成 128/128、token 数一致且正常/慢轮使用同一客户端与服务，尚未用 trace 排除后两类服务内解释。

## Profiling 计划

- Skill/mode：`inference-profiling`，`capture` 后 `analyze`。
- profile-id：`prof-001-p1k-mixed-stall`
- 代表性 workload：P1024/D128/C64/N64，finite batch、greedy、ignore-EOS；相对父目标缩短输出并减少请求，用两波 admission 保留 Prefill/Decode 干扰机制。
- 轮次：1 个无 profiler warmup + 1 个 profiled measured；若单轮未出现长 gap，结论保持 incomplete，不根据 profiler-on 时长计算收益。
- profiler：vLLM torch profiler，record shapes、no stack；预期 TP16 全 rank trace。
- 问题：trace 中是否能看到 Prefill/调度波次与 decode graph replay 之间的长空档、通信等待或 rank 不平衡？
- 停止条件：trace 不可解析、rank 覆盖不足、profiling 未命中慢路径、服务身份漂移或 profiler 导出未完成。

## Profiling 结果

- 捕获成功：客户端 64/64 请求完成，`/start_profile` 与 `/stop_profile` 均成功，生成 async trace 与 TP rank 0–15 共 17 份 gzip trace，校验和已固化。
- profiler-on 轮次没有复现目标慢路径：P99 ITL 为 710.84 ms，而无 profiler 慢轮的 per-request 最大 ITL P90 为 16–21 秒。因此长停顿归因按停止条件记为 `incomplete_for_stall_attribution`。
- 正常路径设备时间的 rank 间相对极差为 2.95%；MoE 与 linear kernel 在 rank 间分别约 0.12% 和 0.43%，未显示持续的单 rank 计算不平衡。collective 累计时间相对极差约 31.34%，但慢路径未命中，不能作为长停顿根因。
- trace 中 `execute_new` annotation 存在嵌套/重复区间，不使用其累加时间作为互斥阶段耗时。服务日志确认捕获轮次出现 `Running: 32, Waiting: 32`后再清空 waiting，只证明两波 admission 机制被覆盖。
- profiler 服务已回切为无 profiler 的 8192 基线服务；新实例完成 6/6 graph capture、health 和烟测，且已重新固化 runtime/service manifest。

## 候选边界

trace 未命中慢路径，不支持确证归因；但无 profiler 的逐请求波次证据仍支持一次低风险、有界的配置证伪。首个单变量候选为 `max_num_batched_tokens=8192→4096`；其余配置和源码不变。targeted 成功条件预冻结为：Mixed P99 TPOT 至少改善 5%，output throughput 中位数回退不超过 3%，P99 TTFT 不回退超过 5%；per-request 最大 ITL 作为补充证据。若不满足则回退，不会把 profiler-on 时间作为性能收益。

### Targeted screen attempt 1

- `fw001-baseline-8192-01` 完成 3 warmup + 3 measured，预热最后两轮 output throughput 相对极差 0.45%，但 measured output throughput 相对极差 70.04%、P99 TPOT 相对极差 120.64%，超过预冻结 30% 上限，不允许进入自动比较。
- 慢轮 seed 74288 的 output throughput 为 178.59 tok/s、P99 TTFT 78.94 s、P99 TPOT 180.57 ms；证明缩减 workload 仍能命中长停顿。
- attempt 2 改为定向慢 seed 74288 的同种子 baseline/candidate/revert；它只用于证伪 4096 工作点是否值得进入更宽验证，不是正式性能结论。

### 候选与回退结果

- `max_num_batched_tokens=4096` 的三个 measured 轮稳定：output throughput 中位数 456.17 tok/s，相对极差 1.02%；P99 TPOT 68.67 ms。但其首个 warmup 仍发生长停顿，output throughput 仅 177.62 tok/s。
- 回切 `8192` 后的三个 measured 轮同样稳定：output throughput 464.52 tok/s，P99 TPOT 67.69 ms。相对回退轮，4096 的 output throughput 低 1.80%，P99 TPOT 差 1.45%，P99 TTFT 差 2.64%。
- 维护版比较器结论为 `incomplete`：原 8192 baseline 的轮内离散超限，且 TPOT/TTFT 的 baseline→revert 漂移超限。不把不稳定 baseline 造成的表面收益视为通过。
- 决定：`rejected_reverted`。不保留 4096，服务已回到 8192；后续转向 FlagGems 运行期 autotune/cache 停顿。

## 证据路径

- Prefill：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/performance/baseline-p1k-prefill-02/`
- Decode：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/performance/baseline-p1k-decode-01/`
- Mixed：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/performance/baseline-p1k-mixed-01/`
- 逐请求波次：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/p1k-request-wave-analysis/`
- Profiler 原始产物：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/profiling/prof-001-p1k-mixed-stall/`
- Profiler rank/phase 分析：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/profiling/prof-001-p1k-mixed-stall/summaries/phase-rank-analysis.json`
- 无 profiler 回切 manifest：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/manifests/post-prof001-restored-service.json`
- 回切门禁：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/transitions/prof-001-restore-no-profiler/`
- Targeted attempt 1：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/performance/fw001-baseline-8192-01/`
- 4096 candidate：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/performance/fw001-candidate-4096-01/`
- 8192 revert：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/performance/fw001-revert-8192-01/`
- 维护版比较：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/performance/fw001-8192-4096-8192-comparison.json`
