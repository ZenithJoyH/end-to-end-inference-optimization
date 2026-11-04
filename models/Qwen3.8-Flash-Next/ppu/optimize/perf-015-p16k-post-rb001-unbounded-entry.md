# perf-015：P16K 回退 QSA 边界后的当前组合入口

## 目标与边界

- 模式：`baseline`，范围为 `performance_only`。
- 用户授权：2026-09-22 在 `acc-009` 仍为 174/198 后明确要求继续寻找并实施优化点；本实验仅作为 P16K 诊断性性能探索，不解除 0.88 正式精度门禁。
- 原因：`perf-014` 包含随后因精度失败而回退的 QSA static score bound，不能继续代表当前无边界运行态。
- 当前候选：`max-num-seqs=64`、`max-num-batched-tokens=4096`、async scheduling、`FULL_AND_PIECEWISE` graph、prefix cache disabled、M64 tuned MoE、native `mm/mm_out`、QSA unbounded。

## 冻结 workload

| 阶段 | workload | rounds |
|---|---|---|
| Prefill | P16384/D1/C32/N64 | 3 warmup + 3 measured |
| Decode | P16384/D1024/C32/N64 | 3 warmup + 3 measured |
| Mixed | P16384/D1024/C64/N128 | 3 warmup + 3 measured |

维护版入口为远端 `commands/performance/vllm_perf.py`。仅对 8000/PPU0-7 顺序压测，8010/PPU8-15 保持空闲；同一 Host 上并行压测所得 timing 无效。

## 门禁

- 精确绑定容器、PID/start ticks、源码 SHA、启动参数、无 QSA 静态边界及端口 8000。
- 每阶段零请求失败，warmup 稳定性通过，保留全部 measured rounds。
- 任一身份漂移、并发流量、服务错误、超时或稳定性失败即停止，不筛选慢轮。
- 结果只用于重建现态三阶段基线和选择下一个单变量实验，不是正式性能验收。

## 结果

状态：`complete_three_phase_historical_identity`。2026-09-24 的只读复核确认三份原生 `run-record.json` 均为 `complete`，每阶段 3 次预热 + 3 次计量、预热稳定性通过、正式轮次零失败。该服务为 maxseq64、M64 tuned folder、native `mm/mm_out`，并非后续 acc-011 的 maxseq32、无 tuned folder、FlagGems `mm_out`；以下三视图仅属于 perf-015 原身份，不能当成当前服务基线或与 op-027 计算加速比。

Prefill 已完成 3 warmup + 3 measured，全部 64/64、零失败，warmup spread
为 0.2233%。三个 measured 轮次的总吞吐为 5806.492/5813.266/5815.286 tok/s，
中位 5813.266 tok/s；duration 中位 180.387s，P99 TTFT 中位 90299.380ms。
原始回执：
`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/perf-015-p16k-post-rb001-unbounded-entry-20260922/perf015-p16k-unbounded-prefill-01/run-record.json`，SHA-256 `1941dbafc89cf30b64af4eabac8e74b1c0242ec1f8fe59f570bd810073ee5504`。

Decode P16384/D1024/C32/N64 的计量轮次均为 64/64、零失败：输出吞吐中位 184.497 tok/s、duration 355.214s、P99 TPOT 165.285ms、P99 ITL 744.852ms、P99 E2E 259126.255ms。回执 `perf015-p16k-unbounded-decode-01/run-record.json`，SHA-256 `0140f6546763b10e65f811208cc4a83c5d39c78f8cccc437cf884b161cb19e2e`。

Mixed P16384/D1024/C64/N128 的计量轮次均为 128/128、零失败：输出吞吐中位 239.972 tok/s、总吞吐 4079.525 tok/s、duration 546.197s，P99 TTFT/TPOT/ITL/E2E 分别为 182941.720/252.035/752.161/440879.985ms。回执 `perf015-p16k-unbounded-mixed-01/run-record.json`，SHA-256 `1a4f68475660c12bf0b043558ae2a278a8a5e1892e92b6f84fb4230b7c9bc023`。

历史 `perf-014` 的 7699.05 tok/s 包含已回退 QSA bound，不是同一新鲜 A/B/R；旧新服务又有其他配置差异，因此只把明显差距当作重新定位的信号，不签发因果加速比。当前 acc-011 仍缺同身份 P16K 三视图。
