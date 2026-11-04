# op-001：Decode linear 旧 cache 配置与当前候选集

## 契约

- 分类：`operator/replace`
- 父目标：`p1024-d1024-c64-n128`
- 状态：`complete`
- 决定：`rejected_reverted`
- 假设：FlagGems ConfigCache 对 decode `align32(M)=32` 的 MiniMax-M3 BF16 linear shape 全部返回已不在当前 AABS0 配置集中的旧 config；其中至少部分 shape 可被当前合法 config 替换并降低 decode 累计耗时。

## 已有证据

- prof-001 正常路径中 `linear_kernel` 累计 7.65 s/78,374 次，与 fused MoE 同属最大计算热点；未命中长停顿，因此本实验只针对稳态算子耗时。
- 默认 cache 的 linear config table 共 535 行，58 行不在当前 8 个 config 中。
- `align32(M)=32` 共 9 行，9/9 均为旧 config；其中 8 行是 BF16 MiniMax-M3 投影 shape，包括 `32x6144 -> 384/768/1024/1536`、`32x192/512/768 -> 6144` 和 `32x6144 -> 12512`。

## 首个证伪实验

1. 停止当前优化服务并确认 16 卡进程排空；不修改 cache 或源码。
2. 在单卡上逐 shape 构造 BF16 input/weight，先调用当前 `flag_gems.ops.linear`并与 PyTorch reference 比较。
3. 使用当前 `LibTuner.benchmark_config` 对 cache 命中 config 与 8 个当前合法 config 进行同一 timing protocol 测量，搜索过程与后续独立确认分开。
4. 停止条件：所有当前合法 config 均不快于 cache config，或数值失败，则拒绝；若多个高频 shape 的 p50 稳定改善至少 5%，再设计最窄 dispatch/cache 修正和端到端 candidate/revert。

## 证据路径

- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/op001-linear-cache-targets.json`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/profiling/prof-001-p1k-mixed-stall/summaries/phase-rank-analysis.json`

## 结果

- 在 PPU-ZW810E 单卡上对 8 个 BF16 `M=32` 生产 shape 逐一比较 cache 命中 config 和当前 8 个合法 config；使用同一 event timing protocol（warmup 20 ms, rep 100 ms）。
- 所有 cache config 及当前 config 都通过 PyTorch reference 数值对照（BF16 `atol=0.08, rtol=0.02`）。
- 8/8 shape 的最快配置都是原 cache config，当前候选没有任何正收益。cache p50 从小到大分别为 0.00556、0.00956、0.01304、0.03384、0.03900、0.04168、0.04544 和 0.13944 ms。
- 因此“当前候选替换旧 cache config”被拒绝；这些旧 config 虽不再出现在搜索列表中，但对 MiniMax-M3 decode shape 是有效且更快的已调优结果，不应被清除。

新增证据：

- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/op001-linear-config-microbenchmark.json`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/op001-linear-config-microbenchmark.SHA256SUMS`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/transitions/op001-stop-for-linear-config-search`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/transitions/op001-restore-after-linear-config-search`
