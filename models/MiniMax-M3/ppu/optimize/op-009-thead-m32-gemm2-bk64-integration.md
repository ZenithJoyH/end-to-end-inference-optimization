# op-009：PPU-ZW810E M32 MoE GEMM2 BK64 集成

- 分类：`operator/improve`，目标 `p1024-d1024-c64-n128` Decode/Mixed。
- 状态：设计冻结，尚未修改运行中模型服务；正式精度与端到端收益未确认。
- 环境：PPU-07 独立优化容器 `minimaxM3-opt-20260921`；用户授权停止的原 8013 服务保持停止。只改独立容器私有 FlagGems，适配容器、权重、tokenizer 与 vLLM 不变。

## 证据与唯一变量

`prof-002` 当前 131K 路径 rank0 Decode-only `fused_moe_kernel` 累计活动 5.363s，但该时间可重叠，不能作为端到端收益。op-008 诊断在 16/16 TP worker 实测 M32 GEMM2 `A=(128,192), B=(128,6144,192), C=(32,4,6144)`，BF16、E128/topk4，传入 config BM16/BN64/BK128/warp4/stage4；M1/2/4/8/16/32 均有两段 stage。单卡实际 dispatch 边界 A/B/A 完整调用 M32 为 0.50043/0.42454/0.50044ms，BK64 +15.16%，其余 M 保持原路径；数值、finite、graph capture 和两次 replay 通过。原始证据：`results/op008-live-stage-bk64-micro.json` SHA256 `f7485f9abd1d5d69527666882b4ebc0c20e9ff1bf1973ac51dbaf690b17deeb4`。这是 fake weights 证据，不能证明真实服务收益或 GPQA。

唯一变量：仅 PPU-ZW810E、BF16、无量化/偏置/EP、w1=(128,384,6144)、w2=(128,6144,192)、topk4、M32 且当前 GEMM2 config BM16/BN64/BK128/warp4/stage4 时，复制 GEMM2 config 将 BK 改 64。GEMM1、Prefill、大/小 M、其他设备和不匹配配置全部原路径。

## 设计归属与回退

当前 Plugin `TritonExpertsFL.apply` 的 no-LoRA fast path 调顶层 `flag_gems.fused_experts_impl`；通用实现中的 `get_moe_config` 取得原配置，随后两段调用 `dispatch_fused_moe_kernel`。op-007 仅改 `get_default_config` 未命中 TP16 目标，因此本轮不再靠该 fallback。公共 FlagGems 的 `fused_experts_impl` 只新增默认 `None` 的可选 GEMM2 config callback；原调用者走原路径，T-Head vendor backend 导出同名 wrapper 并提供限域 callback，经现有 `SpecOpRegistrar` 覆盖顶层 API。平台和 shape 特例不留在公共函数；不修改 Plugin、vLLM 或全局安装。首个否证实验是同源码单卡顶层 API 是否解析到 `_thead` wrapper、真实 callback 命中、非目标 M 不变、图 replay 与数值是否通过。

修改前 FlagGems revision `3c6f7537d2d5d3aa680c55bbee5c70f2100c5b85`，仅保留的 `src/flag_gems/utils/models/sql.py` 已修改；`fused_moe.py` SHA256 `a780da6348ba611640b546b47c60b79baa1312094386ce8f49d99d0d8e4750af`、`_thead/fused/__init__.py` SHA256 `6a965e61477dde4bdc43e6c6587294a0e28debb9a91f4809eeb93e903c118994`，vendor `fused_moe.py` 尚不存在。Plugin revision `7e412e6f8b6d8a5e4350e0237e1a8548dfaf7b94`，原 `thead.yaml` 修改和现有 `.orig` 文件均保持不动。候选失败时只按原始 SHA/备份恢复这三个 FlagGems 目标文件，不清理其他工作区内容。`pr_readiness=experimental`。

## 晋级与验证

先证明 vendor `impl.__module__` 与 M32 callback hit，M1–16 和不匹配 shape/配置 fallback 数值一致；graph capture+2 replay。再用相同 131K TP16 BF16 配置启动 graph 服务，检查 16 worker 真正命中且健康/smoke，通过固定 10 题 C8 最小回归。无 profiler 的 P1K/D256/C64/N128 按预冻结 3 预热+3 测量做同配置 A/B/A，主指标为稳态 output tok/s，TTFT 与 ITL/P99 为守护；如候选没有可兑现 Mixed 收益或守护失败则回退。若晋级 D1024，中间正式性能与 198 题/64 并发/60K/阈值0.88 的新服务绑定 gate 必须重做。单卡 15.16% 不直接外推为端到端收益。

验证状态：单卡实际 stage 数值/graph=`executed_passed`；TP16 vendor 命中/精度/E2E=`not_run`；非目标平台硬件=`not_run`，可先静态/导入核验默认 `None` 路径。完整原始日志与脚本统一归档在远端案例目录。

实验补丁 `patches/op009-thead-m32-gemm2-bk64.patch` SHA256 `46c7ac007507fb979ac58db12ed3db51adf4da48e5890f99e4507ed3d8511af5`；应用脚本 `commands/performance/op009-apply-vendor-candidate.sh` SHA256 `3d90509c580ec7bb3ae42ab4a285bea05f6057e33f579ec237c511107533d1f9`。脚本检查源码、设备/端口、补丁 SHA，备份两份原文件并执行 `git apply --check`、AST、`git diff --check`，新 vendor 文件仅存在于独立容器私有源码。执行命令：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op009-apply-vendor-candidate.sh
```

首版补丁 `git apply --check` 因 import hunk 缺少上下文被拒绝，源码未修改。更正补丁另存 `patches/op009-thead-m32-gemm2-bk64-v2.patch` SHA256 `f12bf9784309178be35fa7f8e934f96cb973ec482d067caec150faed32a1f79f`；配套脚本另存 `commands/performance/op009-apply-vendor-candidate-v2.sh` SHA256 `e1131848ee294a1981aab0d09e936ad01b793f48f66d7698bdc7c4cce9aba9d5`。执行命令：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op009-apply-vendor-candidate-v2.sh
```

修正候选补丁已在独立容器应用，AST、diff 与源 SHA 校验通过：公共 MoE `4f0d05e2aeb5c576a2e8342ede6de4c4df3e8e9f91fe8ea90ee88458c7629b03`，T-Head 导出 `f237d52c7bd47195c86f9ca2b295c17d2a8ff9070a3f6e68c475962806898336`，新增 vendor `293dc46c352e6b7bd21d89000bf161d6258039bd1c3ae32266d52e2c34665259`。新进程里顶层 `flag_gems.fused_experts_impl` 的 sourcefile 已指向 `_thead/fused/fused_moe.py`；`__module__` 实际为 `_thead.fused.fused_moe` 而非长包名，第一次只读断言写错并失败，源码/服务均未受影响。后续以函数对象同一性和 sourcefile 证明选择。

冻结集成后的单卡验证：顶层 vendor wrapper 与公共 generic 完整调用在 M1/2/4/8/16/32 上同输入对照，非目标 M 必须逐位相同且无命中，M32 首次命中 1 次、`allclose(atol=0.12,rtol=0.03)` 与 finite；M32 3×150ms 完整调用按 generic/vendor/generic A/B/A，≥10% 才晋级；vendor M32 graph capture +2 replay 数值通过。脚本 `commands/performance/op009-vendor-candidate-micro.py` SHA256 `61404f9504140459fed6b9ae72882a7afdc5803e910677cb740b2b2f787c6613`，受检执行器 `commands/performance/run-op009-vendor-candidate-micro.sh` SHA256 `4ced410503804cb7bb6720ca0b0acd299332abeb5288ebe17571ca86a406d2d7`；产物 `results/op009-vendor-candidate-micro.json` 与 `logs/op009-vendor-candidate-micro.log`。命令：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/run-op009-vendor-candidate-micro.sh
```

首轮集成小测的 M1–16 均逐位回退，但 M32 vendor hit=0，原始 `results/op009-vendor-candidate-micro.json` 标记 failed。op-008 假权重进程原 M32 config 的 `num_stages=3`，而 TP16 真服务的 M32 config 为 stage4；vendor 严格 guard 正确拒绝了 stage3。为检验线上配置且不放宽服务 guard，新的**仅小测 harness** 将同一 M32 E128/H6144/I192/topk4/BF16 的配置在基线、候选、回退三段均由 stage3 归一到实测 stage4，唯一比较变量仍为候选 GEMM2 BK128→64；其他 M 不变。若 stage4 后不足 10% 则不进服务。

归一脚本 `commands/performance/op009-vendor-live-config-micro.py` SHA256 `62c96f2955e59341d92ae023dda479f2fdbe243b347f792bb4145e6ad4d2ae74`；执行器 `commands/performance/run-op009-vendor-live-config-micro.sh` SHA256 `b3e9df1c162d39669cb7339e5a498b4cfd0ef9950dbf97b582cff08889a547a6`。结果 `results/op009-vendor-live-config-micro.json`，日志 `logs/op009-vendor-live-config-micro.log`。执行：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/run-op009-vendor-live-config-micro.sh
```

线上 stage4 归一单卡结果 `results/op009-vendor-live-config-micro.json` SHA256 `b2e949aa6e78474cbe6bb35fa9a5a7a5e942a020e63d489a56f5956472862aa0`：M1–16 bitwise identical/no hit；M32 vendor 首次命中 1 次、输出逐位一致，A/B/A 完整调用 p50=0.56894/0.45488/0.57036ms，相对基线-回退中位 0.56965ms 提升 20.15%；graph capture+2 replay 数值通过，配置归一命中 2463 次。日志 `logs/op009-vendor-live-config-micro.log` SHA256 `cf59a72bfea7618b37d9de5249abdafb1aa64b5b9485b1ccfa71e329914cce52`。单卡晋级线满足，但不是端到端结论。

启动候选 graph 服务使用冻结的 131K/TP16/BF16/max_num_seqs32/max_num_batched_tokens8192/prefix cache off/FULL_DECODE_ONLY 1,2,4,8,16,32，唯一服务脚本 `commands/performance/op009-candidate-131k-service.sh` SHA256 `3b6383d0feb053b7ed083fdb4e2b0a4218fb1b852c038a546bad8bfb0bb110b8`；产物 `logs/op009-candidate-131k-server.log` 与 transition `op009-candidate-131k`。执行：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/launch-minimax-service-from-stopped.sh \
  op009-candidate-131k \
  /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op009-candidate-131k-service.sh \
  /mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/logs/op009-candidate-131k-server.log
```

候选 TP16 服务已通过 graph 6/6、health=200、smoke 200，但 `logs/op009-candidate-131k-server.log` 中 `op009 THEAD_M32_GEMM2_BK64_HIT` 为 0；独立单卡 vendor 顶层调用虽命中，不能证明该 wrapper 接入真实服务。结合 op-008 真实 `flag_gems.invoke_fused_moe_triton_kernel` stdout 证据，拒绝本轮 full-call wrapper 集成，不运行无效的 GPQA/E2E。先精确停止该 8023 实例，再按原补丁反向应用并校验三文件恢复；命令记录如下：

```bash
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/stop-minimax-service-for-microbenchmark.sh op009-nohit-candidate-stop
/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/op009-revert-vendor-candidate.sh
```

回退脚本 SHA256 `37263bf7fe0c960d48423f7ae416ab6ac10caa6aeb61f51680b77df05a6422ad`；反向应用前逐文件核验候选 SHA，恢复后要求原始公共 MoE、vendor 导出 SHA 且新增文件不存在。此候选 `decision=rejected_no_live_hit_reverted`，单卡 stage4 20.15% 仅保留为下一轮真实 stage 入口的假设，不作端到端收益。
