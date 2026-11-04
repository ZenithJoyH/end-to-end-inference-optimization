# op-006：真实 FlagGems MoE 路径与现成 T-Head 实现对比

- 分类：`operator/replace`；目标：`p1024-d1024-c64-n128` 的 Decode/Mixed。
- 状态：已冻结实验契约，单卡筛选待运行。当前保留组合仍是 fw-006 + op-003；未接入新算子。
- 环境：PPU-07 的独立容器 `minimaxM3-opt-20260921`；用户已允许精确停止原 8013 服务。prof-002 服务在采集结束后精确停止，当前 8023 无监听；适配容器不变。

## 证据与纠偏

prof-002 当前 131K TP16 trace 的 rank0 Decode-only `fused_moe_kernel` 累计 5.363 s / 28406 次，Mixed 累计 2.089 s。累计设备 activity 可重叠，不代表端到端关键路径百分比。按网格分组，Decode 的 `[768,1,1]` 和 `[12288,1,1]` 各 13975 次。直接读 Plugin `TritonExpertsFL.apply` 确认 fast path 调用 `flag_gems.fused_experts_impl`，实际函数位于 `/workspace/FlagGems/src/flag_gems/fused/fused_moe.py`。之前 op-002、op-004 测的是另一实现 `/workspace/FlagGems-vllm/src/flaggems_vllm/runtime/backend/_thead/ops/fused_moe.py`，不能当作真实 fast path 的 tile/算法排除证据。单卡 stage probe 的 128/6144 网格仅属于这另一实现；目前不能仅凭 profiler kernel 名把真实 TP16 的两类网格映射到具体 GEMM stage，实际 `expert_map`、分片和融合条件仍需核验。

证据：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/profiling/prof-002-current-131k-p1k-mixed/summaries/rank0-phase-device-analysis.json`（SHA256 `d0c84e1a3118420bb55ed0109cf208596eab28b7341e69e38ff6a6175a5a0527`）；`rank0-moe-grid-analysis.json`（SHA256 `26b83d471f89cc9b2796a0ab06113e24f8f031dd2fd6988449f7a8b9d813001f`）；`moe-stage-shape-probe.json`（SHA256 `cd5389d4227984aacb95de7f956c45e070b40b7182aca0ae76137921872af553`）。

## 冻结筛选契约

同一单卡、同一随机张量与权重，BF16、无 bias、运行时 `silu`、E128/H6144/每 TP 中间维192/top-k4，M=1/2/4/8/16/32。模型 config 虽写 `hidden_act=swigluoai`，但 `MiniMaxM2MoE` 构造 `FusedMoE` 时没有覆盖其默认 `activation="silu"`；两套待测实现也明确只接受 `silu`。比较完整 `flag_gems.fused_experts_impl` 和 `flaggems_vllm.ops_experts_impl` 调用，包含 routing、GEMM1、GEMM2、sum，不使用独立 kernel 时间替代。校验数值 `atol=0.12, rtol=0.03`、有限输出、输入权重不被改变；M32 完整调用 p50 至少改善 10% 且其他 M 无实质回退才进入独立复测，否则停止且不改服务。此为候选搜索，不是正式性能结果。

若筛选通过，须先核对真实 T-Head dispatch、生效源码、图捕获和至少两次 replay，再做固定最小精度回归；之后按相同 131K 服务契约执行无 profiler Decode/Mixed baseline/candidate/revert（守护 Prefill/TTFT），最后重新做完整 GPQA 198 题 C64/60K、阈值 0.88 的绑定 gate。旧 180/198 gate 仅属于已退出的原实例，不能复用。

执行副本：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/commands/performance/benchmark-op006-actual-moe-backends.py`，本地脚本 SHA256 `555168a9d29ebdd6137dc1d6feef1d6991625bb919bdf18fa6300def50f3829a`；启动命令保存为同目录 `run-op006-actual-moe-backends.sh`，唯一结果为 `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/op006-actual-moe-backends-screen.json`。执行前确认 PPUs 空闲、8023/8013 无模型服务及结果不存在。

## 结果与决定

单卡完整调用筛选成功，结果 `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/op006-actual-moe-backends-screen.json`，SHA256 `177d04617ee33229c1ad90d009dc0f434f181ef62bc678fbf0e0c4e97238595f`。候选与当前结果在全部 M 数值一致（`atol=0.12, rtol=0.03`）、均为有限值，输入及权重未变。p50（毫秒）如下：

| M | 当前 FlagGems | T-Head 候选 | 候选变化 |
|---:|---:|---:|---:|
| 1 | 0.21552 | 0.25876 | 慢 20.06% |
| 2 | 0.21890 | 0.25264 | 慢 15.41% |
| 4 | 0.23160 | 0.25914 | 慢 11.89% |
| 8 | 0.22652 | 0.25300 | 慢 11.69% |
| 16 | 0.36752 | 0.31344 | 快 14.71% |
| 32 | 0.50276 | 0.45372 | 快 9.75% |

M32 未达到预冻结的至少 10% 完整调用改善，同时小 M 有明显回退；按契约拒绝直接替换，不作服务集成。M16 单点收益不等于目标 Mixed 收益，暂不以观察结果改写 op-006 的门槛。该测试为单卡假权重搜索，未证明 TP16 live shape、graph replay 或端到端收益。当前代码与模型服务均未因 op-006 改动。
