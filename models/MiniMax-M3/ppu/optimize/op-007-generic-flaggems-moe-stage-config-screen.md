# op-007：真实 FlagGems MoE 路径的阶段配置筛选

- 分类：`operator/improve`；目标场景 `p1024-d1024-c64-n128`，Decode/Mixed，Prefill 守护。
- 状态：已冻结契约；目前仅允许进程内、单卡、假权重搜索。未修改模型服务或持久源码。
- 原因：prof-002 当前 131K TP16 trace 中 rank0 Decode-only MoE 累计设备 activity 5.363 s；Plugin fast path 经核对调用 `/workspace/FlagGems/src/flag_gems/fused/fused_moe.py`。op-006 直接替换 T-Head 完整调用在 M32 仅快 9.75%（未过 10%）且 M1–M8 回退，已拒绝。op-002/op-004 筛选的是另一套 T-Head 实现，不能排除当前 FlagGems 的配置优化。

先用进程内 wrapper 记录当前 FlagGems M32 两阶段真实 A/B/C shape、排序 buffer、expert map、配置和 grid 计算；若与 prof-002 TP16 网格仍不同，明确标注单卡/服务边界，不把合成调用冒充 live dispatch。然后一次只改变一阶段的一个 tile 参数，在 E128/H6144/I192/top-k4、BF16、运行时 SiLU、M=1/2/4/8/16/32 下比较完整调用 p50。固定数值门槛 `atol=0.12, rtol=0.03`，输出必须有限且输入/权重不变；M32 至少快 10% 且其他 M 不得慢超过 5%，并确认候选配置实际命中。否则不集成。

第一轮 M32 搜索仅尝试 `gemm1 BLOCK_SIZE_N={128,256}`、`gemm1 BLOCK_SIZE_K={64,32}`、`gemm2 BLOCK_SIZE_N={128,256}`、`gemm2 BLOCK_SIZE_K={64,32}`，每个候选只覆盖一个 stage/key。完整调用用同一输入和权重；当前实现测搜索前后两次，取两次 p50 的中位值作为搜索参照以观察漂移；所有候选数值检查后再计时。若最佳候选过 10%，才扩展其他 M 守护并做独立复测。候选排序只是搜索，不是正式性能比较。

通过单卡搜索也只代表候选；升级服务前还需证明真实 TP16 `expert_map`/权重分片与候选条件匹配，完成 graph capture + 两次 replay、固定 10 题 GPQA 最小回归、同 131K 无 profiler P1K Decode/Mixed A/B/A（含 Prefill/TTFT 守护），以及新服务上的完整 198 题 GPQA C64/60K、0.88 门禁。旧 180/198 gate 不绑定新服务，不能挪用。

执行副本：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/benchmark-op007-generic-moe-config.py`，SHA256 `d090a8a48b861b2a012e2a9a0f69be26bb43d629de4a7c4182d3b887dfe907f6`；启动命令为同目录 `run-op007-generic-moe-config.sh`，SHA256 `f3a4b301560daf917b981544910023493e032d0781eb4df10cadbf6061c12f39`。唯一结果 `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/op007-generic-moe-config-screen.json`。

## 结果

首轮 M32 单卡搜索完成，原始结果 `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/op007-generic-moe-config-screen.json`，SHA256 `2ea7be7e8d4b67d3bd4022df0f744987bc3a030b536506802a0a6c94771ca174`。基线搜索前/后 p50 为 0.53992/0.53982 ms；候选 `gemm2 BLOCK_SIZE_K=64` p50 0.45948 ms，对两次基线中位值改善 14.89%，数值一致、实际 config hit。`gemm2 BLOCK_SIZE_K=32` 改善 13.51%，其余六个候选无有效增益或回退。进程内恢复 wrapper，未改持久源码或服务。

单卡当前路径 stage wrapper 捕获到 GEMM1 A[32,6144]/B[128,384,6144]、SiLU 融合、grid384，GEMM2 A[128,192]/B[128,6144,192]、grid12288。后者与真实 trace 一类网格相同；前者与真实 trace 的 grid768 不同。不能因此认定整个单卡调用等同于 TP16 live 路径。下一步按预冻结契约独立重复 M1/2/4/8/16/32 的候选守护、M32 graph capture/replay；若任一门槛失败，停止服务集成。

独立复测脚本保存为远端 `commands/performance/confirm-op007-generic-moe-bk64.py`（SHA256 `f84be1a58912d8700cbf9007febb8c112bde45b3948ec271aebb87dd1c8b9f89`），执行命令为 `commands/performance/run-op007-confirm-bk64.sh`（SHA256 `511e25d7cee2258c207575aff60bbd9a8cb1959dbb03dbce2df4b1f5b9a3dce5`），结果唯一写入 `results/op007-generic-moe-bk64-confirmation.json`。单卡按 M 分别做当前→候选→回退完整调用；若 M32 ≥10% 且其他 M 不慢于 5%，再做候选图捕获及两次 replay。

独立复测通过，仅代表单卡候选：`results/op007-generic-moe-bk64-confirmation.json` SHA256 `fe99f27aff04ccf15c1c7c3c8e8b8b38cd5f01abcea84d56b0d6e3cc67033885`。M32 当前/候选/回退 p50 = 0.45616/0.38248/0.45592 ms，候选较两基线中位值快 16.13%；M16 快 13.30%，M1/2/4/8 分别变化 -0.76%/-0.14%/+0.01%/+2.76%，均满足 5% 守护。所有 M 数值 allclose、有限值、输入权重未变，目标配置每次命中。M32 CUDA graph 捕获成功且两次 replay 与当前输出 allclose。下一步建立同配置 TP16 服务基线，再做私有源码集成及端到端 A/B/A；上述微基准不能直接外推服务收益。

## TP16 集成与里程碑契约

先运行未修改 MoE 的 131K TP16 基线，再只修改私有 `/workspace/FlagGems/src/flag_gems/fused/fused_moe.py`：在 PPU-ZW810E、BF16、E128/N6144/K192/top-k4、Decode 图的 M≤32、GEMM2 条件下，把 `BLOCK_SIZE_K` 从 128 降到 64；其他设备、shape、stage 保留原路。修改前备份原文件、记录 SHA/revision/dirty 状态，候选服务逐 worker 记录实际命中，并准备精确回退。原来的 fw-006 SQL 反射补丁与 op-003 黑名单保持不变。

里程碑同配置 P1024/D256/C64/N128 finite-batch Mixed，温机 3 轮 + 测量 3 轮，baseline→candidate→revert 各建独立服务及服务 manifest，全部无 profiler。primary 为 output throughput 至少 +3%；守护 total throughput 最大回退 3%、p99 TTFT 最大增加 5%、p99 TPOT 最大增加 3%、p99 ITL 最大增加 10%；轮间相对 spread ≤15%，baseline/revert 漂移 ≤10%。原生比较契约保存在远端 `commands/performance/op007-p1k-d256-milestone-{plan,comparison}.json`，与 op-005 相同 workload 但不复用其测量结果。若里程碑不满足，回退并拒绝；满足后才进入目标 D1024 中间正式测试与新服务完整 GPQA gate。

已保存服务启动脚本 `commands/performance/op007-comparison-131k-service.sh`（SHA256 `cfe870e340c0dd2b9a1a84f453054848001949e1ab5ff7545408e3db67f6d0c3`）及各角色 wrapper；baseline wrapper SHA256 `19de2ba0f5a77eeb8bba26f3a5a8a030277a7f6e9661954ce36bbd0c6488726c`。baseline 启动的精确命令是：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/launch-minimax-service-from-stopped.sh \
  op007-baseline-131k \
  /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op007-baseline-service.sh \
  /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/logs/op007-baseline-comparison-131k-server.log
```

里程碑 plan SHA256 `9c5f04cf0b8822d99250192f4f72a1ef9b28ce658168e86a77f655cce60bdd6b`；comparison SHA256 `7c3bac3313c7ede406d29a11f09c3f0242e02299e1a2a97f1b4eef388f01d2f3`。

baseline 启动转移 `transitions/op007-baseline-131k/` 已完成：6/6 FULL_DECODE_ONLY graph capture、HTTP health 200、北京 smoke 通过，启动日志为 `logs/op007-baseline-comparison-131k-server.log`。本角色身份采集命令已保存为 `commands/performance/op007-collect-service-identity.sh`，本次精确调用：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op007-collect-service-identity.sh baseline a780da6348ba611640b546b47c60b79baa1312094386ce8f49d99d0d8e4750af
```

该命令从活服务生成唯一 `results/op007-baseline-runtime.json` 和 `results/op007-baseline-performance-manifest.json`，验证源文件、启动日志、PID/ticks 和保留配置。

baseline 活服务 `bd37abcbf719:8023:1227909:287089190`；runtime SHA256 `c5301643de1602f3e3b2fb37e778227f2358a0b2db7078eb52ec7be2087180f2`，性能 manifest SHA256 `aeef69404d6a402d2c6f1027548b014f4e72cd0f3a86c7641df10538d852e5e5`。同契约无 profiler 基线的精确命令为：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op007-run-d256-role.sh \
  baseline op007-d256-baseline-01 \
  /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/op007-baseline-performance-manifest.json \
  a780da6348ba611640b546b47c60b79baa1312094386ce8f49d99d0d8e4750af
```

集成候选的源码起点是私有 FlagGems revision `3c6f7537d2d5d3aa680c55bbee5c70f2100c5b85`，修改前 `src/flag_gems/fused/fused_moe.py` SHA256 `a780da6348ba611640b546b47c60b79baa1312094386ce8f49d99d0d8e4750af`，工作区仅 `src/flag_gems/utils/models/sql.py` 有本案已保留的 fw-006 修改；`linear.py` 已回原 SHA。目标运行导入路径确认为 `/workspace/FlagGems/src/flag_gems/fused/fused_moe.py`。补丁 v1/v2 用 GNU `patch --dry-run` 时第二 hunk 未匹配，**均未改源码**；v2 经 `git apply --check` 通过。保留失败副本与检查输出，不覆盖旧文件。后续使用唯一 `patches/op007-generic-moe-gemm2-bk64-v2.patch`（SHA256 `d1c3b80a0857ea03932b01577db4c1dc54a7f0a274ed0964ef9d971c8915f5e6`）和精确 `commands/performance/op007-switch-moe-source-v3.sh`（SHA256 `d0b33cc4371f8eca3656ccc8c1af533172532eaefd8e08ec2df2d6a02186303f`）。switch 先核对服务/PIDs/端口空闲与原 SHA，备份到唯一 `patches/op007-generic-fused-moe-original.py`，再以 `git apply --check`/`git apply` 切换；回退用该备份恢复并核对 SHA。必须待基线 run-record 完成及基线服务精确停止后才运行。

基线 `performance/op007-d256-baseline-01/run-record.json` SHA256 `cc80489949a1184801d59d2c4c05b897e5d339603ac94ff8435d4769d8e43020`，`status=complete`、6/6 轮返回码 0、错误数组空；预热末两轮 output throughput 424.16/466.25 tok/s，spread 9.45% ≤10%。测量 3 轮输出吞吐 464.97/464.83/463.81 tok/s，p99 TTFT 20827/21209/20708 ms，p99 TPOT 67.45/67.81/67.98 ms；尚无候选对比结论。停止前再次核对该实例 PID/ticks，精确停止命令：

```bash
docker exec minimaxM3-opt-20260921 python3 /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/verify-live-baseline-service.py \
  /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/op007-baseline-performance-manifest.json
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/stop-minimax-service-for-microbenchmark.sh op007-baseline-after-d256-stop
```

基线实例已精确停止，转移证据在 `transitions/op007-baseline-after-d256-stop/`。候选源码切换的精确命令（仅在服务停止、GPU 空闲、原 SHA 匹配时生效）：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op007-switch-moe-source-v3.sh \
  candidate op007-baseline-to-candidate-source
```

切换成功，候选文件 SHA256 `c846844cfebc8793b7c2840fce8fad10bede6bb294cb4e87767e475ebeec1bec`；备份原文件 SHA256 `a780da6348ba611640b546b47c60b79baa1312094386ce8f49d99d0d8e4750af`。`git diff --check` 和 AST 解析通过，私有仓库 dirty 仅 `fused_moe.py` 候选与原有 fw-006 `sql.py`。转移证据在 `transitions/op007-baseline-to-candidate-source/`。候选同配置服务启动命令：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/launch-minimax-service-from-stopped.sh \
  op007-candidate-131k \
  /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op007-candidate-service.sh \
  /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/logs/op007-candidate-comparison-131k-server.log
```

候选服务完成 graph、health 与烟测，但 `get_default_config` 内的一次性命中标记计数为 0。进一步核对候选日志，16 个 worker 明确打印 `Op 'invoke_fused_moe_triton_kernel' using 'default.flagos'`。Plugin 的 PPU 分支没有走 `TritonExpertsFL.apply` 中 `current_platform.is_cuda()` 的完整 `flag_gems.fused_experts_impl` fast path，而是分阶段由 Plugin `CachedOp` 分发到 `flag_gems.invoke_fused_moe_triton_kernel`。因此本次候选的配置修改点**未命中**，不能继续精度或性能测量，也不能把单卡完整调用结果视为该服务收益。真实优化点应在 Plugin→FlagGems 的 `invoke_fused_moe_triton_kernel` 边界；必须先记录运行中的实际 A/B/C shape、配置和 sorted buffer，再决定 BK64 守护条件。上述静态 fast-path 归因已纠正。

本次未命中的候选服务仅作为诊断，需先保存运行身份后精确停止：

```bash
docker exec minimaxM3-opt-20260921 python3 \
  /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/capture-baseline-service.py \
  > /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/op007-ineffective-candidate-runtime.json
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/stop-minimax-service-for-microbenchmark.sh \
  op007-ineffective-candidate-stop
```

未命中服务已精确停止；先回退该无效补丁，确保下一步只做运行形状诊断。精确回退命令：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op007-switch-moe-source-v3.sh \
  revert op007-ineffective-candidate-revert-source \
  c846844cfebc8793b7c2840fce8fad10bede6bb294cb4e87767e475ebeec1bec
```
