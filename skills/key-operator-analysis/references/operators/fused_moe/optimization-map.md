# Fused MoE 案例驱动优化地图

本文件只收录由实际端到端案例约束的可执行决策。先匹配 live dispatch、
stage、有效 M、expert 数、dtype 和 graph 模式；未匹配维度均视为未知。

## 已验证规则

### 平台特化必须通过 vendor backend 覆盖公共 fused MoE

- 证据等级：`reproduced`。
- 触发信号：候选根据设备名、平台 warp 行为或平台专用量化/归约特性改变
  config 或 kernel，但修改位于 `flag_gems/fused/` 公共实现。
- 第一检查：确认当前 revision 的 backend registrar、vendor `fused/__init__.py`
  导出和运行函数对象；不能因为公共函数内部有 device guard 就认为分层正确。
- 首个实验：把平台 config/kernel hook 移入对应 vendor backend，以公共路径作为
  baseline；断言顶层 API 的 `__module__` 命中 vendor 实现，同时验证公共文件相对
  原基线无平台改动。
- 通过证据：vendor dispatch 命中、非 vendor 公共路径不变、数值一致、graph
  capture 与至少两次 replay、聚焦测试，以及迁移前后完整算子收益不丢失。
- 停止条件：registrar 没有命中 vendor wrapper；wrapper 导致循环 import、线程不安全
  或明显 host 开销；公共实现仍残留平台判断；graph 或数值回归。
- 来源：[Hy4-preview/PPU case card](case-index.md#case20260914-hy4-preview-ppu-e2e)。

### Decode：按 live M 分离 M<=32 与 exact-M64 GEMM2 配置

- 证据等级：`reproduced`。
- 匹配范围：GLM-5.3-Flash-BF16、PPU、TP16、E288、cached32/cached64、
  `FULL_DECODE_ONLY`；实际函数为
  `flag_gems.fused.fused_moe.invoke_fused_moe_triton_kernel`。
- 触发信号：分阶段 trace 显示 Decode 中 fused MoE 是稳定首热点，但
  当前 stage 特化的运行时 gate 排除了实际 Decode M，或 `max_num_seqs`
  改变使 live M 跨过已有配置分支。
- 第一检查：从 trace 和运行函数确认 GEMM1/GEMM2 精确 shape、layout、
  当前 config、padding 边界和每步调用数；不从模型配置、并发上限或大 M
  gate 反推。M32 配置不得直接外推到 M64。
- 首个实验：在独立进程中复制 trace 证明的两个 stage shape，记录当前
  config，然后一次只更改 config 做有界扫描。
- 微基准晋级门槛：BF16 reference `allclose`、eager、graph capture 与
  两次 replay 全部通过；GEMM1/GEMM2 至少一个完整 stage 提升
  `>=5%`。
- 已验证分支：M<=32 GEMM2 使用严格范围 guard；exact-M64 GEMM2 还必须
  保持 incoming BM32/padding 边界。其他 M、config、dtype、量化和 layout
  回退原路径。
- 服务晋级方式：做无 profiler 的同一 workload 3+3 测量；主指标和延迟
  守护按任务冻结目标判定，不能把微基准结果直接写成端到端收益。
- 已复现结果：M<=32 P1K 吞吐 +19.432%；exact-M64 在前一版 max64 上
  吞吐 +18.447%，P99 TTFT/TPOT 分别改善 15.769%/15.561%。
- 优化后复核：exact-M64 reprofile 的 Decode marker span 下降 16.018%，
  fused-MoE 活动时长下降 30.617%、占比降到 44.12%；同 shape GEMM1 最佳
  仅 1.048522×，未过 1.05× 微基准门槛，应停止继续扫 config。
- 停止条件：实际 dispatch/stage 与推断不一致；数值不等价；graph capture
  或 replay 失败；完整候选的 stage 收益不足 5%；对齐、dispatch 或服务
  开销抵消 kernel 收益；端到端门槛失败。
- 来源：[GLM5.3/PPU case card](case-index.md#case20260911-glm53-flash-ppu-e2e)。

## 每次 Fused MoE 改动后的重新排序

1. 重新采集相同 workload 的短 profile，确认目标 config 和 kernel 真实命中。
2. 分开 GEMM1、GEMM2、align/routing 和 collective，不把重叠的 activity-duration
   相加为端到端收益上限。
3. 若 Fused MoE 已不再是首要可兑现瓶颈，停止继续扫描 config，回到
   跨算子候选排名。
4. 只有候选通过微基准与无 profiler 服务 A/B/R，才可从开放假设
   升级为已验证限域路径。
