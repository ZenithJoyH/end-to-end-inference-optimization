# op-002：T-Head fused MoE Decode stage/config 筛选

## 契约

- 分类：`operator/improve`
- 父目标：`p1024-d1024-c64-n128`
- 状态：`complete`
- 决定：`rejected_reverted`
- 假设：MiniMax-M3 的 E128/hidden6144/per-TP-intermediate192/top-k4 在 decode M=1/2/4/8/16/32 上，可用比当前 GEMM1 `16x256x64` + GEMM2 `16x128x32` stage-split 更快的有界配置。

## 证据与边界

- prof-001 正常路径 fused MoE 累计约 7.69 s/rank，占 rank device-sum 约 38%；TP16 rank spread 仅约 0.12%。
- 真实函数对象位于 `flaggems_vllm/runtime/backend/_thead/ops/fused_moe.py`，已有 PPU 专用配置、small-M fusion、权重 transpose cache 和 GEMV 分支。vLLM 的 `device_name=thead` 缺失 JSON 警告不能替代实际 backend 分析。
- 历史源码注释称 stage-split 在 M<=128 约快 3%，因此预期可消除比例不高；本实验只做精确模型 shape 的低成本证伪。

## 首个实验

- 单卡 BF16，M=1/2/4/8/16/32，E=128，K=6144，N=192，top-k=4，无 bias。
- 比较 current、不同 stage 数、group size 和 GEMM1/GEMM2 BN/BK 局部变体；不更改源码、服务或模型权重。
- current 输出作为数值 reference，每个候选必须通过 BF16 容差；搜索 timing 不作为最终收益。
- 晋级：按 M 权重的 p50 至少改善 5%，且无任何 shape 显著回退；晋级后需独立确认、focused correctness、graph 和端到端 candidate/revert。
- 停止：无候选达到 5%，或数值失败。

## 结果

- 全部 9 个候选在 M=1/2/4/8/16/32 上通过 current 输出的 BF16 数值对照（`atol=0.12, rtol=0.03`）。
- 最好局部收益：M1 为 0%；M2 1.99%；M4 1.52%；M8 3.82%；M16 的 `stages3` 为 15.95%；M32 的 `stages2` 为 3.81%。
- prof-001 正常 Decode timeline 中，根据 graph capture size 向上分桶的出现次数约为 M32=497、M16=2、M1=4；因此 M16 的大幅局部收益生产命中率极低，加权结果几乎由 M32 的 3.81% 决定。
- fused MoE 约占正常路径 rank device-sum 38%，故 M32 候选的端到端理论上限仅约 1.4%，尚未计入非设备时间。它不达预记录的 5% 算子加权门槛，不值得引入 shape 特化和整套服务回归成本。
- 不修改 FlagGems-vllm 源码，拒绝并恢复服务。

## 证据路径

- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/op002-fused-moe-config-screen.json`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/op002-fused-moe-config-screen.SHA256SUMS`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/profiling/prof-001-p1k-mixed-stall/summaries/phase-rank-analysis.json`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/transitions/op002-stop-for-fused-moe-config-screen`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/transitions/op002-restore-after-fused-moe-config-screen`
