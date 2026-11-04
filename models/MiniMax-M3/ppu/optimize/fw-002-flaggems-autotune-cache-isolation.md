# fw-002：FlagGems online autotune 与 cache 隔离

## 契约

- 分类：`framework`
- 父目标：`p1024-d1024-c64-n128`
- 状态：`complete`
- 决定：`rejected_reverted`
- 问题：请求期间的 16–21 秒长停顿是否来自 FlagGems `LibTuner` 对新 shape 做同步多配置 benchmark，以及 AABS1/AABS0 共用未分区 ConfigCache 导致的旧配置复用？
- 阶段：Mixed 中 Prefill 与 Decode 均可能触发；当前只对已有证据最强的 `linear_kernel`/LibTuner 路径建立诊断，不把其他 tuner 排除。

## 当前证据

- profiler 正常路径中 `linear_kernel` 累计 7.65 s/78,374 次；慢路径未在 trace 中命中，因此该数据只证明频繁调用。
- 慢轮附近 16 个 worker 成组打印 `libentry.py:413` replay benchmarker fallback warning。警告在 tuner 构造时发生，不能单独证明 cache miss，但指向运行期 tuner 创建。
- 当前 `LibTuner.run()` 在 ConfigCache miss 时会同步对 pruned configs 调用 `_bench`，之后才执行真实 kernel。`linear_kernel` 配置集为 8 个，key 是 M/N/K 的 `align32`。
- 实际 SQLite 位于容器 writable layer 的 `/root/.flaggems/config_cache/TunedConfig_thead_triton_3_6.db`，未设置 `FLAGGEMS_CACHE_DIR`。库内 590 张表、6202 行；`linear_kernel` 有 535 个 config key 和 4171 条 benchmark 行。
- 535 个已选 config 中有 58 个（约 10.8%）不属于当前 AABS0 进程解析到的 8 个配置，包括 `BLOCK_SIZE_M=16` 等。之前 AABS1 诊断与 AABS0 服务共用该库，cache table identity 未编码 AABS 模式。

## 诊断与候选边界

1. 新建专用 `FLAGGEMS_CACHE_DIR` 目录，不删除、覆盖或复制旧数据库。
2. 诊断服务只额外设置 `TRITON_PRINT_AUTOTUNING=1`，在 P1024/D256/C64/N128 上记录冷轮与立即热复跑的 tuner 名称、config key 和 `bench_time`；这些 profiler/logging-on 数据不作为正式性能收益。
3. 若长停顿与明确的 cache miss/bench time 同时出现，重启为无诊断日志、使用同一隔离 cache 的候选服务，先做受控预热，再运行 baseline/candidate/revert 比较。
4. 停止条件：无新 autotune 日志但长停顿仍出现；隔离 cache 与旧 cache 在热态的吞吐/延迟无可重复差异；或受控预热无法覆盖生产 shape。

## 证据路径

- Cache inventory：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/fw001-flaggems-linear-config-distribution.json`
- 当前服务日志：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/logs/fw001-revert-8192-server.log`
- LibTuner 源码：`/workspace/FlagGems/src/flag_gems/utils/libentry.py`
- Linear 源码：`/workspace/FlagGems/src/flag_gems/ops/linear.py`

## 结果与决定

- 第一次直接使用 NFS 上的全新空 cache 启动 TP16 失败。首个真实异常是多个 worker 并发在 `sql.py:69` 执行 `PRAGMA journal_mode=WAL` 时触发 `sqlite3.OperationalError: database is locked`；后续 NCCL broken pipe 是连锁退出，不是根因。
- 不修改源码，改用优化容器私有目录 `/root/.flaggems-fw002-aabs0-clean-v2`，并在 TP16 启动前用单进程把空 SQLite 库预置为 WAL。服务随后通过 graph capture、health 和 smoke 门禁。
- 诊断服务启动/smoke 阶段累计打印 180 条 `Triton autotuning for function`；后续两个完整 P1024/D256/C64/N128 轮次期间该计数始终为 180，未发生新的请求期 cache-miss autotune。因此现有证据反驳“请求期新 shape 同步 autotune 直接造成长停顿”。
- 空隔离 cache 第 1/2 轮 output throughput 分别为 290.76/400.36 tok/s，P99 TPOT 为 110.13/78.46 ms；两轮预热的 throughput spread 为 31.72%，未达 10% 稳定门限，评测器正确停在 measured round 前。即使只看第 2 轮，也低于 `fw001-revert-8192-01` 的 464.52 tok/s，不具备晋级价值。
- 不保留隔离空 cache 候选，服务回切到默认 cache 的 8192 已验证路径。SQLite 首次并发建库问题作为独立健壮性缺陷记录，但不把它当作本场景的性能收益。

新增证据：

- 失败启动日志：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/logs/fw002-isolated-cache-diagnostic-server.log`
- 单进程建库回执：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/fw002-clean-cache-db-preparation.json`
- 诊断服务 manifest：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/manifests/fw002-preinitialized-clean-cache-diagnostic-service.json`
- 冷/热诊断：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/performance/fw002-preinitialized-clean-cache-cold-hot-02`
