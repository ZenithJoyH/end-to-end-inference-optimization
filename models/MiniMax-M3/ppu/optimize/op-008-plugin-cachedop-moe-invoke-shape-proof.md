# op-008：PPU 实际 Plugin MoE stage 调用形状核验

- 分类：`operator/improve` 的前置执行路径诊断；目标 `p1024-d1024-c64-n128` Decode/Mixed。
- 状态：已冻结只记录形状的诊断契约，尚未安装新的性能候选。
- 环境：PPU-07 独立容器 `minimaxM3-opt-20260921`，私有 FlagGems 源码。适配容器、模型权重/tokenizer 不变；原 8013 服务经用户允许已停止，8023 当前无服务。

## op-007 排除证据

op-007 在 E128/H6144/I192/top-k4 的独立单卡 `flag_gems.fused_experts_impl` 测试中，GEMM2 `BLOCK_SIZE_K=64` 的 M32 完整调用有 14.89% 搜索收益、16.13% 独立复测收益并通过图 replay。但 TP16 候选服务的 `get_default_config` 一次性标记 0 次；16 个 worker 的 Plugin 日志同时显示 `invoke_fused_moe_triton_kernel` 选择 `default.flagos`。Plugin PPU 路径经 `CachedOp` 调用 `flag_gems.invoke_fused_moe_triton_kernel`，配置由上层传入，完全绕开前述 `get_default_config` 改动。未命中服务未跑精度/E2E，已精确停止并从备份回退私有 MoE 文件 SHA256 `a780da6348ba611640b546b47c60b79baa1312094386ce8f49d99d0d8e4750af`。原 baseline D256 6/6 轮有效，测量输出吞吐 464.97/464.83/463.81 tok/s；可作为后续同契约 A/B/A 的新鲜 A，但新候选仍需独立 B 与回退 A。

## 冻结诊断契约

仅在私有 FlagGems `invoke_fused_moe_triton_kernel` 入口增加一次性、每个不同 M/stage 只记录 shape/config 的日志；不改变 config、tensor、kernel 或返回值。收集 A/B/C shape、`sorted_token_ids` 与 `expert_ids` 长度、`top_k`、`FUSE_SILU`、`config`、设备名，以及对应 worker/rank。启动同 131K TP16 BF16、prefix cache off、FULL_DECODE_ONLY graph sizes 1/2/4/8/16/32，要求 6/6 graph、health、两次 smoke 与至少一组真实 M32 stage 记录。日志只用于定位，profile-on/诊断服务不能产生正式性能结果。

若真实 GEMM2 `B.size(1)=6144`、`B.size(2)=192`、config BK128 与 op-007 的目标维度一致，下一步在**实际 Plugin→FlagGems invoke 边界**做独立同形状数值/耗时比较 BK64，其他 M/阶段回退；否则停止 BK64 假设、按实际形状重新排序。任何候选进 TP16 服务还须记录真实命中、图 replay、最小 GPQA 回归、无 profiler P1K Mixed 同配置 A/B/A 与新 198 题 GPQA 0.88 门禁。已有 180/198 gate 绑定已退出旧服务，不复用。

## 结果

诊断补丁 `patches/op008-moe-invoke-shape-log.patch` SHA256 `81fae2c6fe95c137ad712e6163b97f9a11cd412d33e31e55f10a411b629f4fac`，仅对 `FlagGems/src/flag_gems/fused/fused_moe.py` 的 `invoke_fused_moe_triton_kernel` 加 `@lru_cache` 去重的 shape/config 警告日志；`git apply --check` 已通过。源码切换脚本 `commands/performance/op008-switch-moe-diagnostic.sh` SHA256 `12d4ef048d061f92e9151f2523c08e67a032f834258bbcc7fc60f01d53d1b98d`，执行前检查原 SHA、8023 无监听和 PPU 空闲，备份到唯一 `patches/op008-fused-moe-original.py`，回退时核对目标 SHA。前一轮 op-007 无效补丁已恢复原 SHA；本次应用命令为：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op008-switch-moe-diagnostic.sh \
  apply op008-original-to-shape-diagnostic
```

运行结果待填。

2026-09-23 17:50 CST：诊断服务 `health=200`、启动及 smoke 成功，16 个 worker 均记录 `invoke_fused_moe_triton_kernel -> default.flagos`，但以 `A.size(0)∈{1,2,4,8,16,32}` 过滤的一次性日志为 0。Python 导出函数确认为 `/workspace/FlagGems/src/flag_gems/fused/fused_moe.py:1609`；尚不能据此断言真实 M，也可能是传入张量被 pad。为避免错误外推，执行一次仅放宽日志过滤的重启诊断，不更改 kernel/config。

补丁 `patches/op008-moe-invoke-all-m.patch` 来自本地 `/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261102-record-reconciliation-01/files/docs/cases/20260921-minimax-m3-ppu-e2e/op008-moe-invoke-all-m.transfer.patch`，SHA256 `62fb68a04636e6638bc465c01b7c244b947163fc08fc7f4d394aad1642b4fdff`。先精确停止当前 8023 诊断服务，再用 `git apply --check`、应用补丁、复启唯一诊断服务；停止命令已冻结如下：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/stop-minimax-service-for-microbenchmark.sh op008-shape-filtered-diagnostic-stop
```

仅日志补丁应用脚本 `commands/performance/op008-expand-moe-shape-diagnostic.sh` SHA256 `18c387992c891b69a198d4f45beb4f68f449c51728a6fdbd9bf0f19be5e26c02`，预检查来源、空闲设备、端口及补丁 SHA；执行命令：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op008-expand-moe-shape-diagnostic.sh
```

该首版补丁头计数错误，`git apply --check` 报 `corrupt patch at line 33`，未发生源码变更。更正后补丁另存 `patches/op008-moe-invoke-all-m-v2.patch` SHA256 `b0b2a562066accd93609d32ea864fcd93f371561809cabeb587298801bfd9121`；更正脚本另存 `commands/performance/op008-expand-moe-shape-diagnostic-v2.sh` SHA256 `137022233ca2ac7fce250600277d5527bfb35ce48912d21a51f8162c97bbf182`。唯一执行命令：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op008-expand-moe-shape-diagnostic-v2.sh
```

修正版应用成功，当前私有源码 SHA256 `ced8cef35d42deee5a84564bb82176843ae44f4e4cbbd5fc1f36947171ea2af4`，AST 与 `git diff --check` 均通过。重启仍用原冻结的 131K 服务配置，但产物使用新的 transition/log：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/launch-minimax-service-from-stopped.sh \
  op008-moe-invoke-all-m-131k \
  /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op008-shape-diagnostic-131k-service.sh \
  /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/logs/op008-moe-invoke-all-m-131k-server.log
```

该重启配置仍将日志硬编码为旧文件，旧文件存在导致服务脚本立即退出；launcher PID `316132` 独自等待 health，8023 无监听、PPU 空闲。先精确 TERM 此 launcher（不涉及服务进程），将新配置单独存为 `commands/performance/op008-all-m-131k-service.sh` 并写入新的唯一日志路径；之后以 `op008-moe-invoke-all-m-v2-131k` transition 执行：

新启动脚本 SHA256 `5304d7d64f25d55d1d537f4144138fdd445c1b1e8e6418d5bc20874069bebdd0`；除唯一日志路径外，全部环境和启动参数与上一版一致。

`op008-moe-invoke-all-m-v2-131k` 已通过 graph/startup/health/smoke，但去掉全部 M 过滤后日志标记依然为 0。因 Plugin dispatch 的选择日志仅证明选中了实现，不证明该函数真正执行，也可能是 FlagGems logger 被过滤，下一步须在函数入口增加一次性标准输出诊断以消除歧义。先精确停止这个任务服务：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/stop-minimax-service-for-microbenchmark.sh op008-all-m-logger-diagnostic-stop
```

第三版诊断仅在已缓存的一次性日志函数里加 `print(..., flush=True)`，补丁 `patches/op008-moe-invoke-print.patch` SHA256 `027f1552efed52c8536228da27b8d484c13c6baee20065b13b0bf2c06261e4c8`；受检应用脚本 `commands/performance/op008-add-print-diagnostic.sh` SHA256 `c63a248863c20ef4cdb6dcf1b51af88c1854a3c042d3750d4ca83473de5549b2`。新服务脚本 `commands/performance/op008-print-131k-service.sh` SHA256 `6d978238e46c0e753d608fff19b83ea551dd62fcd0320dad5141b691a45ad769`，仅日志路径变更。执行命令：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op008-add-print-diagnostic.sh
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/launch-minimax-service-from-stopped.sh \
  op008-moe-invoke-print-131k \
  /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op008-print-131k-service.sh \
  /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/logs/op008-moe-invoke-print-131k-server.log
```

首版 print 补丁在 `git apply --check` 未匹配已新增的诊断函数，未修改源码。改用在已校验 SHA 的当前文件第 39 行后插入的零上下文补丁，`patches/op008-moe-invoke-print-v2.patch` SHA256 `bde1fbe08077e918c1efedef94597fd01a356ccb4e49efbd734bcab0bba1bc22`；配套脚本 `commands/performance/op008-add-print-diagnostic-v2.sh` SHA256 `3cce6b25d06d42994394ae43fca54e9e6755d383114e49594619654059ebb600`，在执行前仍核对完整源文件 SHA。执行：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op008-add-print-diagnostic-v2.sh
```

最终 stdout 探针的源码 SHA256 `3ff857a02905fc631f76b5abe3291e2e76154a0f1bd82d5cea054d2e8f4e753a`。服务完成 6/6 graph、health=200、smoke 200 且输出含“北京”。原始日志 `logs/op008-moe-invoke-print-131k-server.log` SHA256 `a024aba5bf12cf5fb9cebf5ac91dcc26ab68bc741248b4225a59d6a9000b5f89`，16/16 worker 各 16 条、总 256 条一次性 stage 标记。此前 Python logger 被服务日志策略过滤，故 0 条 logger 标记并不代表函数未命中；以 stdout 标记为准。PPU 调用虽在 Plugin 中可见 `CachedOp` 选择日志，实际 `TritonExpertsFL.apply` 的 no-LoRA fast path 也可能进入 `flag_gems.fused_experts_impl`，两者不能仅凭静态源推断；但本次已直接证明 `flag_gems.invoke_fused_moe_triton_kernel` 真正执行。

rank0 graph 的 M32：GEMM1 `A=(32,6144), B=(128,384,6144), C=(32,4,384)`；GEMM2 `A=(128,192), B=(128,6144,192), C=(32,4,6144)`；`top_k=4/1`、两段 `BLOCK_SIZE_M/N/K=16/64/128, num_warps=4, num_stages=4`。M1/2/4/8/16/32 均有两段记录；启动 Prefill M8192 用 BK64/BM128/BN128，smoke Prefill M186 用 BK64/BM64/BN128。这说明仅 M32 GEMM2 的 BK64 仍有可证伪价值，但旧 op-007 改动位于 `get_default_config`，服务 0 次命中，不能沿用其服务集成结论。下一步在真实 stage 边界做显式配置替换小测。

诊断服务不承担正式性能计量；现精确停止并恢复私有 MoE 原文件：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/stop-minimax-service-for-microbenchmark.sh op008-print-shape-diagnostic-stop
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op008-switch-moe-diagnostic.sh \
  revert op008-print-shape-diagnostic-revert-source \
  3ff857a02905fc631f76b5abe3291e2e76154a0f1bd82d5cea054d2e8f4e753a
```

原源码已恢复 SHA256 `a780da6348ba611640b546b47c60b79baa1312094386ce8f49d99d0d8e4750af`、8023 服务结束、16 张 PPU 释放。冻结下一步单卡筛选：E128/H6144/I192/topk4/BF16，M=1/2/4/8/16/32；在实际 `dispatch_fused_moe_kernel` 参数边界截取所有 stage 原配置，只对 M32、`B=(128,6144,192)`、`top_k=1` 的 GEMM2 把 BK128 改为 BK64；其余 M 和 GEMM1 不变。随机权重/输入种子 20260923，BF16 原输出 `allclose(atol=0.12,rtol=0.03)`、finite、M32 命中 1 次/其他 M 0 次；完整调用 `triton.testing.do_bench` warmup 30ms、测量 150ms，M32 按 A/B/A 中位比较，预冻结晋级线 ≥10%；graph capture+2 replay 与原输出一致。此处为 fake weights 的算子小测，不是目标模型精度或服务性能。

脚本 `commands/performance/op008-live-stage-bk64-micro.py` SHA256 `dd91701ba5f30008454b7c107276d3889655315a05dc6ca469d7d91df69ac900`，执行器 `commands/performance/run-op008-live-stage-bk64-micro.sh` SHA256 `27b4f81b8da658ab4b22d14e251d0dd1fa75702524c821571a3d114c55dccc69`；执行前检查源码 SHA、脚本 SHA、端口与设备空闲。结果唯一保存 `results/op008-live-stage-bk64-micro.json`、日志 `logs/op008-live-stage-bk64-micro.log`。命令：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/run-op008-live-stage-bk64-micro.sh
```

```bash
kill -TERM 316132
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/launch-minimax-service-from-stopped.sh \
  op008-moe-invoke-all-m-v2-131k \
  /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op008-all-m-131k-service.sh \
  /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/logs/op008-moe-invoke-all-m-131k-server.log
```

补丁应用后私有 MoE 文件 SHA256 `e820363142bb4ad2941dcd3fd12b2428caff96acef559c49fb8dd8c162a78541`，原备份 SHA 仍为 `a780da6348ba611640b546b47c60b79baa1312094386ce8f49d99d0d8e4750af`；`git diff --check` 与 AST 解析通过。诊断服务启动副本为 `commands/performance/op008-shape-diagnostic-131k-service.sh`，同配置且唯一日志 `logs/op008-moe-invoke-shape-131k-server.log`。精确启动命令：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/launch-minimax-service-from-stopped.sh \
  op008-moe-invoke-shape-131k \
  /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op008-shape-diagnostic-131k-service.sh \
  /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/logs/op008-moe-invoke-shape-131k-server.log
```
